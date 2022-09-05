import math
import re
import warnings
import xml.etree.ElementTree as ElementTree
from os import path
from typing import Optional, List, Dict, Tuple

import numpy as np
from commonroad.geometry.shape import Rectangle
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.prediction.prediction import TrajectoryPrediction
from commonroad.scenario.obstacle import DynamicObstacle, ObstacleType
from commonroad.scenario.scenario import Scenario
from commonroad.scenario.trajectory import State, Trajectory
from crdesigner.map_conversion.map_conversion_interface import opendrive_to_commonroad

from OpenSCENARIO2CR.EsminiWrapper.EsminiWrapper import EsminiWrapper
from OpenSCENARIO2CR.EsminiWrapper.EsminiWrapperProvider import EsminiWrapperProvider
from OpenSCENARIO2CR.EsminiWrapper.ScenarioObjectState import ScenarioObjectState


class OpenSCENARIO2CRConverter:
    def __init__(self, delta_t: float, osc_file: str):
        self.esmini_wrapper = EsminiWrapperProvider().provide_esmini_wrapper()
        self.cr_dt = delta_t
        self.osc_file = osc_file

        self.odr_file = None
        self.esmini_dt = None
        self.ego_filter = None

    @property
    def osc_file(self) -> str:
        """ The file name of the OpenSCENARIO file."""
        return self._osc_file

    @osc_file.setter
    def osc_file(self, new_file_name: str):
        if path.exists(new_file_name):
            self._osc_file = path.abspath(new_file_name)
            odr_file_element = ElementTree.parse(self.osc_file).getroot().find("RoadNetwork/logicFile")
            if odr_file_element is not None:
                if path.exists(odr_file_element.text):
                    self._odr_in_osc_file = path.abspath(odr_file_element.text)
                else:
                    warnings.warn(f"<OpenSCENARIO2CRConverter/osc_file> OpenDRIVE file {odr_file_element.text}, " +
                                  f"specified inside OpenSCENARIO file {new_file_name} does not exist")
            else:
                self._odr_in_osc_file = None
        else:
            warnings.warn(f"<OpenSCENARIO2CRConverter/osc_file> OpenSCENARIO file {new_file_name} does not exist")

    @property
    def odr_in_osc_file(self) -> Optional[str]:
        """ The OpenDRIVE file specified inside the OpenSCENARIO file"""
        return self._odr_in_osc_file

    @property
    def odr_file(self) -> Optional[str]:
        """ The file name of the OpenDRIVE file. If not specified the program will look"""
        if hasattr(self, "_odr_file"):
            return self._odr_file
        else:
            return self._odr_in_osc_file

    @odr_file.setter
    def odr_file(self, new_file_name: Optional[str]):
        if new_file_name is None or path.exists(new_file_name):
            self._odr_file = new_file_name
        else:
            warnings.warn(f"<OpenSCENARIO2CRConverter/osc_file> OpenDRIVE file {new_file_name} does not exist")

    @property
    def cr_dt(self) -> float:
        """ The delta time for the newly generated Commonroad scenario."""
        return self._cr_dt

    @cr_dt.setter
    def cr_dt(self, new_dt: float):
        self._cr_dt = new_dt

    @property
    def esmini_dt(self) -> float:
        """ The delta time used for simulation. Default is 1/10th of the Commonroad delta time. """
        return self._esmini_dt

    @esmini_dt.setter
    def esmini_dt(self, new_dt: Optional[float]):
        if new_dt is None:
            self._esmini_dt = self.cr_dt / 10
        else:
            self._esmini_dt = new_dt

    @property
    def esmini_wrapper(self) -> EsminiWrapper:
        return self._esmini_wrapper

    @esmini_wrapper.setter
    def esmini_wrapper(self, new_esmini_wrapper: EsminiWrapper):
        if new_esmini_wrapper is None:
            warnings.warn("<OpenSCENARIO2CRConverter/esmini_wrapper>: New EsminiWrapper is None.")
        else:
            self._esmini_wrapper = new_esmini_wrapper

    @property
    def ego_filter(self) -> Optional[re.Pattern]:
        return self._ego_filter

    @ego_filter.setter
    def ego_filter(self, new_filter: Optional[re.Pattern]):
        self._ego_filter = new_filter

    def run(self) -> Optional[Tuple[Scenario, Optional[PlanningProblemSet]]]:
        scenario: Scenario
        planning_problem_set: Optional[PlanningProblemSet] = None
        if self.odr_file is not None:
            scenario = opendrive_to_commonroad(self.odr_file)
            scenario.dt = self.cr_dt
        else:
            scenario = Scenario(self.cr_dt)
        states, sim_time = self.esmini_wrapper.simulate_scenario(
            scenario_path=self.osc_file,
            dt=self.esmini_dt,
            grace_time=1.0,
        )
        if states is not None:
            final_timestamps = [step * self.cr_dt for step in range(math.ceil(sim_time / self.cr_dt) + 1)]
            interpolated_states = {
                object_name: [ScenarioObjectState.build_interpolated(state_list, t) for t in final_timestamps]
                for object_name, state_list in states.items()
            }
            obstacles: List[DynamicObstacle] = []
            planning_problem_sets: Dict[str, PlanningProblemSet] = {}
            for object_name, state_list in interpolated_states.items():
                if self._is_object_name_used(object_name):
                    obstacle = self._osc_states_to_dynamic_obstacle(scenario, state_list)
                    if obstacle is not None:
                        obstacles.append(obstacle)
                else:
                    # Todo Do something here
                    planning_problem_sets[object_name] = PlanningProblemSet()
            scenario.add_objects(obstacles)

            if self.ego_filter is None:
                assert len(planning_problem_sets) == 0
            else:
                assert len(planning_problem_sets) == 1
                planning_problem_set = list(planning_problem_sets.values())[0]

            return scenario, planning_problem_set
        return None

    def _is_object_name_used(self, object_name: str):
        return self.ego_filter is None or self.ego_filter.match(object_name) is None

    def _osc_states_to_dynamic_obstacle(self, scenario: Scenario, states: List[ScenarioObjectState]) \
            -> Optional[DynamicObstacle]:
        if len(states) == 0:
            return None
        shape = Rectangle(states[0].length, states[0].width)
        trajectory = Trajectory(0, [OpenSCENARIO2CRConverter._osc_state_to_cr(state, i) for i, state in enumerate(states)])
        prediction = TrajectoryPrediction(trajectory, shape)

        return DynamicObstacle(
            obstacle_id=scenario.generate_object_id(),
            obstacle_type=OpenSCENARIO2CRConverter._osc_object_type_category_to_cr(states[0].objectType, states[0].objectCategory),
            obstacle_shape=shape,
            initial_state=trajectory.state_list[0],
            prediction=prediction
        )

    @staticmethod
    def _osc_state_to_cr(state: ScenarioObjectState, time_step: int) -> State:
        # Todo add 3rd dimension and roll/pitch angles
        c, s = np.cos(state.h), np.sin(state.h)
        rotation_matrix = np.array(((c, -s), (s, c)))
        return State(
            position=np.array((state.x, state.y)) + np.matmul(rotation_matrix, np.array(
                (state.centerOffsetX, state.centerOffsetY))),
            orientation=state.h,
            velocity=state.speed,
            time_step=time_step,
        )

    @staticmethod
    def _osc_object_type_category_to_cr(object_type: int, object_category: int) -> ObstacleType:
        if object_type == 0:  # TYPE_NONE
            return ObstacleType.UNKNOWN
        elif object_type == 1:  # VEHICLE
            return {
                0: ObstacleType.CAR,  # CAR
                1: ObstacleType.CAR,  # VAN
                2: ObstacleType.TRUCK,  # TRUCK
                3: ObstacleType.TRUCK,  # SEMITRAILER
                4: ObstacleType.TRUCK,  # TRAILER
                5: ObstacleType.BUS,  # BUS
                6: ObstacleType.MOTORCYCLE,  # MOTORBIKE
                7: ObstacleType.BICYCLE,  # BICYCLE
                8: ObstacleType.TRAIN,  # TRAIN
                9: ObstacleType.TRAIN,  # TRAM
            }[object_category]
        elif object_type == 2:  # PEDESTRIAN
            return ObstacleType.PEDESTRIAN  # PEDESTRIAN, WHEELCHAIR, ANIMAL
        elif object_type == 3:  # MISC_OBJECT
            return {
                0: ObstacleType.UNKNOWN,  # NONE
                1: ObstacleType.UNKNOWN,  # OBSTACLE
                2: ObstacleType.PILLAR,  # POLE
                3: ObstacleType.PILLAR,  # TREE
                4: ObstacleType.UNKNOWN,  # VEGETATION
                5: ObstacleType.BUILDING,  # BARRIER
                6: ObstacleType.BUILDING,  # BUILDING
                7: ObstacleType.UNKNOWN,  # PARKINGSPACE
                8: ObstacleType.UNKNOWN,  # PATCH
                9: ObstacleType.BUILDING,  # RAILING
                10: ObstacleType.MEDIAN_STRIP,  # TRAFFICISLAND
                11: ObstacleType.UNKNOWN,  # CROSSWALK
                12: ObstacleType.PILLAR,  # STREETLAMP
                13: ObstacleType.BUILDING,  # GANTRY
                14: ObstacleType.BUILDING,  # SOUNDBARRIER
                15: ObstacleType.UNKNOWN,  # WIND
                16: ObstacleType.UNKNOWN,  # ROADMARK
            }[object_category]
        elif object_type == 4:  # N_OBJECT_TYPES
            return ObstacleType.UNKNOWN


if __name__ == '__main__':
    conv = OpenSCENARIO2CRConverter(
        "/home/michael/SoftwareProjects/CommonRoad/openscenario/scenarios/from_openScenario_standard/DoubleLaneChanger.xosc",
        # "/home/michael/SoftwareProjects/CommonRoad/openscenario/scenarios/from_openScenario_standard/Databases/AB_RQ31_Straight.xodr",
        "/home/michael/SoftwareProjects/CommonRoad/openscenario/scenarios/from_openScenario_standard/Databases/SampleDatabase.xodr",
        0.1,
        0.03,
    )
    conv.run(view=True)
