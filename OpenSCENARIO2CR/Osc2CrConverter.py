import math
import re
import warnings
import xml.etree.ElementTree as ElementTree
from os import path
from typing import Optional, List, Dict, Tuple, Union

import numpy as np
from commonroad.common.util import Interval, AngleInterval
from commonroad.geometry.shape import Rectangle
from commonroad.planning.goal import GoalRegion
from commonroad.planning.planning_problem import PlanningProblemSet, PlanningProblem
from commonroad.prediction.prediction import TrajectoryPrediction
from commonroad.scenario.obstacle import DynamicObstacle, ObstacleType
from commonroad.scenario.scenario import Scenario
from commonroad.scenario.trajectory import State, Trajectory
from crdesigner.map_conversion.map_conversion_interface import opendrive_to_commonroad

from OpenSCENARIO2CR.AbsRel import AbsRel
from OpenSCENARIO2CR.ConversionStatistics import ConversionStatistics
from OpenSCENARIO2CR.EsminiWrapper.EsminiWrapper import EsminiWrapper
from OpenSCENARIO2CR.EsminiWrapper.EsminiWrapperProvider import EsminiWrapperProvider
from OpenSCENARIO2CR.EsminiWrapper.ScenarioObjectState import ScenarioObjectState
from OpenSCENARIO2CR.EsminiWrapper.StoryBoardElement import EStoryBoardElementType


class Osc2CrConverter:
    def __init__(
            self,
            delta_t: float,
            osc_file: str,

            goal_state_time_step: AbsRel[Interval],
            goal_state_position_length: float,
            goal_state_position_width: float,

            odr_file: Optional[str] = None,
            use_implicit_odr_file: Optional[bool] = None,
            esmini_dt: Optional[float] = None,

            goal_state_position_use_ego_rotation: Optional[bool] = None,
            goal_state_velocity: Optional[AbsRel[Interval]] = None,
            goal_state_orientation: Optional[AbsRel[AngleInterval]] = None,

            keep_ego_vehicle: Optional[bool] = None,
            ego_filter: Optional[re.Pattern] = None,

            max_time: float = None,
            grace_time: Optional[float] = None,
            ignored_level: Optional[EStoryBoardElementType] = None,
            random_seed: Optional[int] = None,
            log_to_console: bool = None,
            log_to_file: Union[str, bool] = None
    ):
        self.esmini_wrapper = EsminiWrapperProvider().provide_esmini_wrapper()
        self.cr_dt = delta_t
        self.osc_file = osc_file

        self.goal_state_time_step = goal_state_time_step
        self.goal_state_position_length = goal_state_position_length
        self.goal_state_position_width = goal_state_position_width

        self.goal_state_position_use_ego_rotation = goal_state_position_use_ego_rotation
        self.goal_state_velocity = goal_state_velocity
        self.goal_state_orientation = goal_state_orientation

        self.odr_file = odr_file
        self.use_implicit_odr_file = use_implicit_odr_file
        self.esmini_dt = esmini_dt
        self.keep_ego_vehicle_obstacle = bool(keep_ego_vehicle)
        self.ego_filter = ego_filter

        if max_time is not None:
            self.esmini_wrapper.max_time = max_time
        if grace_time is not None:
            self.esmini_wrapper.grace_time = grace_time
        if ignored_level is not None:
            self.esmini_wrapper.ignored_level = ignored_level
        if random_seed is not None:
            self.esmini_wrapper.random_seed = random_seed
        if log_to_console is not None:
            self.esmini_wrapper.log_to_console = log_to_console
        if log_to_file is not None:
            self.esmini_wrapper.log_to_file = log_to_file

    @property
    def osc_file(self) -> str:
        """ The file name of the OpenSCENARIO file."""
        return self._osc_file

    @osc_file.setter
    def osc_file(self, new_file_name: str):
        if path.exists(new_file_name):
            self._osc_file = path.abspath(new_file_name)
            odr_file_element = ElementTree.parse(self.osc_file).getroot().find("RoadNetwork/LogicFile[@filepath]")
            if odr_file_element is not None:
                filepath = path.join(path.dirname(new_file_name), odr_file_element.attrib["filepath"])
                if path.exists(filepath):
                    self._odr_in_osc_file = path.abspath(filepath)
                else:
                    warnings.warn(f"<OpenSCENARIO2CRConverter/osc_file> OpenDRIVE file \"{filepath}\", " +
                                  f"specified inside OpenSCENARIO file \"{new_file_name}\" does not exist")
            else:
                self._odr_in_osc_file = None
        else:
            warnings.warn(f"<OpenSCENARIO2CRConverter/osc_file> OpenSCENARIO file \"{new_file_name}\" does not exist")

    @property
    def odr_in_osc_file(self) -> Optional[str]:
        """ The OpenDRIVE file specified inside the OpenSCENARIO file"""
        return self._odr_in_osc_file

    @property
    def odr_file(self) -> Optional[str]:
        """ The file name of the OpenDRIVE file. If not specified the program will look"""
        if self._odr_file is not None:
            return self._odr_file
        elif self.use_implicit_odr_file:
            return self._odr_in_osc_file
        else:
            return None

    @odr_file.setter
    def odr_file(self, new_file_name: Optional[str]):
        if new_file_name is None or path.exists(new_file_name):
            self._odr_file = new_file_name
        else:
            warnings.warn(f"<OpenSCENARIO2CRConverter/osc_file> OpenDRIVE file {new_file_name} does not exist")

    @property
    def use_implicit_odr_file(self) -> bool:
        return self._use_implicit_odr_file

    @use_implicit_odr_file.setter
    def use_implicit_odr_file(self, new_no_implicit_odr_file: Optional[bool]):
        if new_no_implicit_odr_file is None:
            self._use_implicit_odr_file = True
        else:
            self._use_implicit_odr_file = new_no_implicit_odr_file

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
        if hasattr(self, "_esmini_wrapper"):
            return self._esmini_wrapper
        else:
            return EsminiWrapperProvider().provide_esmini_wrapper()

    @esmini_wrapper.setter
    def esmini_wrapper(self, new_esmini_wrapper: EsminiWrapper):
        if new_esmini_wrapper is None:
            warnings.warn("<OpenSCENARIO2CRConverter/esmini_wrapper>: New EsminiWrapper is None.")
        else:
            self._esmini_wrapper = new_esmini_wrapper

    @property
    def goal_state_time_step(self) -> AbsRel[Interval]:
        return self._goal_state_timestamp

    @goal_state_time_step.setter
    def goal_state_time_step(self, new_goal_state_timestamp: AbsRel[Interval]):
        self._goal_state_timestamp = new_goal_state_timestamp

    @property
    def goal_state_position_length(self) -> float:
        return self._goal_state_position_length

    @goal_state_position_length.setter
    def goal_state_position_length(self, new_goal_state_position_length: float):
        self._goal_state_position_length = new_goal_state_position_length

    @property
    def goal_state_position_width(self) -> float:
        return self._goal_state_position_width

    @goal_state_position_width.setter
    def goal_state_position_width(self, new_goal_state_position_width: float):
        self._goal_state_position_width = new_goal_state_position_width

    @property
    def goal_state_position_use_ego_rotation(self) -> bool:
        return self._goal_state_position_use_ego_rotation

    @goal_state_position_use_ego_rotation.setter
    def goal_state_position_use_ego_rotation(self, new_goal_state_position_use_ego_rotation: Optional[bool]):
        if new_goal_state_position_use_ego_rotation is None:
            self._goal_state_position_use_ego_rotation = True
        else:
            self._goal_state_position_use_ego_rotation = new_goal_state_position_use_ego_rotation

    @property
    def goal_state_velocity(self) -> Optional[AbsRel[Interval]]:
        return self._goal_state_velocity

    @goal_state_velocity.setter
    def goal_state_velocity(self, new_velocity: Optional[AbsRel[Interval]]):
        self._goal_state_velocity = new_velocity

    @property
    def goal_state_orientation(self) -> Optional[AbsRel[AngleInterval]]:
        return self._goal_state_orientation

    @goal_state_orientation.setter
    def goal_state_orientation(self, new_goal_state_orientation: Optional[AbsRel[AngleInterval]]):
        self._goal_state_orientation = new_goal_state_orientation

    @property
    def keep_ego_vehicle_obstacle(self) -> bool:
        return self._ego_filter is not None and self._remove_ego_vehicle

    @keep_ego_vehicle_obstacle.setter
    def keep_ego_vehicle_obstacle(self, new_remove_ego_vehicle: float):
        self._remove_ego_vehicle = new_remove_ego_vehicle

    @property
    def ego_filter(self) -> Optional[re.Pattern]:
        return self._ego_filter

    @ego_filter.setter
    def ego_filter(self, new_filter: Optional[re.Pattern]):
        self._ego_filter = new_filter

    @property
    def max_time(self) -> float:
        return self.esmini_wrapper.max_time

    @max_time.setter
    def max_time(self, new_max_time: float):
        self.esmini_wrapper.max_time = new_max_time

    @property
    def grace_time(self) -> Optional[float]:
        return self.esmini_wrapper.grace_time

    @grace_time.setter
    def grace_time(self, new_grace_time: Optional[float]):
        self.esmini_wrapper.grace_time = new_grace_time

    @property
    def ignored_level(self) -> Optional[EStoryBoardElementType]:
        return self.esmini_wrapper.ignored_level

    @ignored_level.setter
    def ignored_level(self, new_ignored_level: Optional[EStoryBoardElementType]):
        self.esmini_wrapper.ignored_level = new_ignored_level

    @property
    def random_seed(self) -> Optional[int]:
        return self.esmini_wrapper.random_seed

    @random_seed.setter
    def random_seed(self, new_random_seed: int):
        self.esmini_wrapper.random_seed = new_random_seed

    @property
    def log_to_console(self) -> bool:
        return self.esmini_wrapper.log_to_console

    @log_to_console.setter
    def log_to_console(self, new_log_to_console: bool):
        self.esmini_wrapper.log_to_console = new_log_to_console

    @property
    def log_to_file(self) -> Optional[str]:
        return self.esmini_wrapper.log_to_file

    @log_to_file.setter
    def log_to_file(self, new_log_to_file: Union[None, bool, str]):
        self.esmini_wrapper.log_to_file = new_log_to_file

    def run_conversion(self) -> Tuple[Optional[Scenario], Optional[PlanningProblemSet], Optional[ConversionStatistics]]:
        scenario: Scenario = self._create_scenario_from_opendrive()

        states, sim_time = self.esmini_wrapper.simulate_scenario(self.osc_file, self.esmini_dt)
        if states is not None:
            ego_vehicle, ego_vehicle_found_with_filter = self._find_ego_vehicle(list(states.keys()))
            obstacles = self._create_obstacles_from_state_lists(scenario, ego_vehicle, states, sim_time)

            scenario.add_objects([
                o for o_name, o in obstacles.items()
                if o is not None and (self.keep_ego_vehicle_obstacle or ego_vehicle != o_name)
            ])

            return (
                scenario,
                self._create_planning_problem_set(obstacles[ego_vehicle]),
                ConversionStatistics(
                    source_file=self.osc_file,
                    database_file=self.odr_file,
                    failed_obstacle_conversions=[o_name for o_name, o in obstacles.items() if o is None],
                    ego_vehicle=ego_vehicle,
                    ego_vehicle_found_with_filter=ego_vehicle_found_with_filter,
                    ego_obstacle_removed=self.keep_ego_vehicle_obstacle,
                )
            )
        return None, None, None

    def _create_scenario_from_opendrive(self) -> Scenario:

        if self.odr_file is not None:
            scenario = opendrive_to_commonroad(self.odr_file)
            scenario.dt = self.cr_dt
            return scenario
        else:
            return Scenario(self.cr_dt)

    def _is_object_name_used(self, object_name: str):
        return self.ego_filter is None or self.ego_filter.match(object_name) is None

    def _find_ego_vehicle(self, vehicle_name_list: List[str]) -> Tuple[str, bool]:
        if self.ego_filter is not None:
            found_ego_vehicles = [name for name in vehicle_name_list if self.ego_filter.match(name) is not None]
            if len(found_ego_vehicles) > 0:
                return sorted(found_ego_vehicles)[0], True

        return sorted(vehicle_name_list)[0], False

    def _create_obstacles_from_state_lists(
            self,
            scenario: Scenario,
            ego_vehicle: str,
            states: Dict[str, List[ScenarioObjectState]],
            sim_time: float,
    ) -> Dict[str, Optional[DynamicObstacle]]:
        final_timestamps = [step * self.cr_dt for step in range(math.ceil(sim_time / self.cr_dt) + 1)]
        interpolated_states = {
            object_name: [ScenarioObjectState.build_interpolated(state_list, t) for t in final_timestamps]
            for object_name, state_list in states.items()
        }

        def create_obstacle(obstacle_name: str) -> Optional[DynamicObstacle]:
            return self._osc_states_to_dynamic_obstacle(
                obstacle_id=scenario.generate_object_id(),
                states=interpolated_states[obstacle_name]
            )

        obstacles = {ego_vehicle: create_obstacle(ego_vehicle)}
        for object_name in interpolated_states.keys():
            if object_name != ego_vehicle:
                obstacles[object_name] = create_obstacle(object_name)
        return obstacles

    @staticmethod
    def _osc_states_to_dynamic_obstacle(obstacle_id: int, states: List[ScenarioObjectState]) \
            -> Optional[DynamicObstacle]:
        if len(states) == 0:
            return None
        shape = Rectangle(states[0].length, states[0].width)
        trajectory = Trajectory(0, [Osc2CrConverter._osc_state_to_cr(state, i) for i, state in enumerate(states)])
        prediction = TrajectoryPrediction(trajectory, shape)

        return DynamicObstacle(
            obstacle_id=obstacle_id,
            obstacle_type=Osc2CrConverter._osc_object_type_category_to_cr(states[0].objectType,
                                                                          states[0].objectCategory),
            obstacle_shape=shape,
            initial_state=trajectory.state_list[0],
            prediction=prediction
        )

    @staticmethod
    def _osc_state_to_cr(state: ScenarioObjectState, time_step: int) -> State:
        c_h, s_h = np.cos(state.h), np.sin(state.h)  # heading
        c_p, s_p = np.cos(state.p), np.sin(state.p)  # pitch
        c_r, s_r = np.cos(state.r), np.sin(state.r)  # roll

        center = np.array((
            state.x,
            state.y,
            state.z
        ))
        rotation_matrix = np.array((
            (c_h * c_p, c_h * s_p * s_r - s_h * c_r, c_h * s_p * c_r + s_h * s_r),
            (s_h * c_p, s_h * s_p * s_r + c_h * c_r, s_h * s_p * s_r - c_h * s_r),
            (-s_p, c_p * s_r, c_p * c_r),
        ))
        offset = np.array((
            state.centerOffsetX,
            state.centerOffsetY,
            state.centerOffsetZ,
        ))
        position_3d = center + np.matmul(rotation_matrix, offset)
        cr_state = State(
            position=position_3d[0:2],
            position_z=position_3d[2],
            orientation=state.h,
            pitch_angle=state.p,
            roll_angle=state.r,
            velocity=state.speed,
            time_step=time_step,
        )
        if state.acceleration is not None:
            cr_state.acceleration = state.acceleration
        if state.h_rate is not None:
            cr_state.yaw_rate = state.h_rate
        if state.p_rate is not None:
            cr_state.pitch_rate = state.p_rate
        if state.r_rate is not None:
            cr_state.roll_rate = state.r_rate

        return cr_state

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
            }.get(object_category, ObstacleType.UNKNOWN)
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
            }.get(object_category, ObstacleType.UNKNOWN)
        elif object_type == 4:  # N_OBJECT_TYPES
            return ObstacleType.UNKNOWN

    def _create_planning_problem_set(self, obstacle: DynamicObstacle) -> PlanningProblemSet:
        initial_state = obstacle.prediction.trajectory.state_list[0]
        initial_state.slip_angle = 0.0
        final_state = obstacle.prediction.trajectory.final_state
        goal_state = State()

        goal_state.position = Rectangle(
            length=self.goal_state_position_length,
            width=self.goal_state_position_width,
            center=final_state.position,
            orientation=final_state.orientation if self.goal_state_position_use_ego_rotation else 0.0
        )

        goal_state.time_step = self.goal_state_time_step.with_offset_if_relative(final_state.time_step)

        if self.goal_state_velocity is not None:
            goal_state.velocity = self.goal_state_velocity.with_offset_if_relative(final_state.velocity)
        if self.goal_state_orientation is not None:
            goal_state.orientation = self.goal_state_orientation.with_offset_if_relative(final_state.orientation)

        return PlanningProblemSet(
            [
                PlanningProblem(
                    planning_problem_id=obstacle.obstacle_id,
                    initial_state=initial_state,
                    goal_region=GoalRegion(
                        state_list=[goal_state]
                    )
                )
            ]
        )
        pass
