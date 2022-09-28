import math
import re
import warnings
import xml.etree.ElementTree as ElementTree
from enum import auto, Enum
from os import path
from typing import Optional, List, Dict, Tuple, Union

import numpy as np
from commonroad.common.util import Interval, AngleInterval
from commonroad.common.validity import is_valid_orientation
from commonroad.geometry.shape import Rectangle
from commonroad.planning.goal import GoalRegion
from commonroad.planning.planning_problem import PlanningProblemSet, PlanningProblem
from commonroad.prediction.prediction import TrajectoryPrediction
from commonroad.scenario.lanelet import LaneletNetwork
from commonroad.scenario.obstacle import DynamicObstacle, ObstacleType
from commonroad.scenario.scenario import Scenario
from commonroad.scenario.trajectory import Trajectory, State
from crdesigner.map_conversion.map_conversion_interface import opendrive_to_commonroad

from BatchConversion.Converter import Converter
from OpenSCENARIO2CR.AbsRel import AbsRel
from OpenSCENARIO2CR.ConversionAnalyzer.Analyzer import Analyzer
from OpenSCENARIO2CR.ConversionStatistics import ConversionStatistics, EAnalyzer
from OpenSCENARIO2CR.EsminiWrapper.EsminiWrapper import EsminiWrapper, ESimEndingCause
from OpenSCENARIO2CR.EsminiWrapper.EsminiWrapperProvider import EsminiWrapperProvider
from OpenSCENARIO2CR.EsminiWrapper.ScenarioObjectState import ScenarioObjectState, SEStruct
from OpenSCENARIO2CR.EsminiWrapper.StoryBoardElement import EStoryBoardElementType


class EFailureReason(Enum):
    SCENARIO_FILE_INVALID_PATH = auto()
    SCENARIO_FILE_IS_CATALOG = auto()
    SCENARIO_FILE_IS_PARAMETER_VALUE_DISTRIBUTION = auto()
    SCENARIO_FILE_CONTAINS_NO_STORYBOARD = auto()
    SIMULATION_FAILED_CREATING_OUTPUT = auto()
    NO_DYNAMIC_BEHAVIOR_FOUND = auto()


class Osc2CrConverter(Converter):

    def __init__(
            self,
            delta_t: float,

            goal_state_time_step: AbsRel[Interval],
            goal_state_position_length: float,
            goal_state_position_width: float,

            odr_file: Optional[str] = None,
            use_implicit_odr_file: Optional[bool] = None,
            esmini_dt: Optional[float] = None,
            do_trim_scenario: Optional[bool] = None,
            keep_ego_vehicle: Optional[bool] = None,
            ego_filter: Optional[re.Pattern] = None,

            goal_state_position_use_ego_rotation: Optional[bool] = None,
            goal_state_velocity: Optional[AbsRel[Interval]] = None,
            goal_state_orientation: Optional[AbsRel[AngleInterval]] = None,

            max_time: float = None,
            grace_time: Optional[float] = None,
            ignored_level: Optional[EStoryBoardElementType] = None,
            random_seed: Optional[int] = None,
            log_to_console: bool = None,
            log_to_file: Union[str, bool] = None,

            analyzers: Union[None, List[EAnalyzer], Dict[EAnalyzer, Analyzer]] = None,
    ):
        Converter.__init__(self)
        self.esmini_wrapper = EsminiWrapperProvider(preferred_version="v2.26.3").provide_esmini_wrapper()
        self.cr_dt = delta_t

        self.goal_state_time_step = goal_state_time_step
        self.goal_state_position_length = goal_state_position_length
        self.goal_state_position_width = goal_state_position_width

        self.odr_file = odr_file
        self.use_implicit_odr_file = use_implicit_odr_file
        self.esmini_dt = esmini_dt
        self.do_trim_scenario = do_trim_scenario
        self.keep_ego_vehicle = bool(keep_ego_vehicle)
        self.ego_filter = ego_filter

        self.goal_state_position_use_ego_rotation = goal_state_position_use_ego_rotation
        self.goal_state_velocity = goal_state_velocity
        self.goal_state_orientation = goal_state_orientation

        self.esmini_wrapper.max_time = max_time
        self.esmini_wrapper.grace_time = grace_time
        self.esmini_wrapper.ignored_level = ignored_level
        self.esmini_wrapper.random_seed = random_seed
        self.esmini_wrapper.log_to_console = log_to_console
        self.esmini_wrapper.log_to_file = log_to_file

        self.analyzers = analyzers

    @staticmethod
    def from_args(**kwargs) -> "Converter":

        converter = Osc2CrConverter(
            delta_t=kwargs["delta_t"],
            goal_state_time_step=kwargs["goal_state_time_step"],
            goal_state_position_length=kwargs["goal_state_position_length"],
            goal_state_position_width=kwargs["goal_state_position_width"],
        )
        for key, value in kwargs.items():
            if key in ["esmini_wrapper", ]:
                continue
            elif hasattr(converter.esmini_wrapper, "_" + key):
                setattr(converter.esmini_wrapper, key, value)
            elif hasattr(converter, "_" + key):
                setattr(converter, key, value)

        return converter

    @property
    def odr_file(self) -> Optional[str]:
        """ The file name of the OpenDRIVE file. If not specified the program will look"""
        return self._odr_file

    @odr_file.setter
    def odr_file(self, new_file_name: Optional[str]):
        if new_file_name is None or path.exists(new_file_name):
            self._odr_file = new_file_name
        else:
            warnings.warn(f"<OpenSCENARIO2CRConverter/osc_file> OpenDRIVE file {new_file_name} does not exist")
            if not hasattr(self, "_odr_file"):
                self._odr_file = None

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
    def keep_ego_vehicle(self) -> bool:
        return self._ego_filter is not None and self._keep_ego_vehicle

    @keep_ego_vehicle.setter
    def keep_ego_vehicle(self, new_keep_ego_vehicle: Optional[bool]):
        self._keep_ego_vehicle = new_keep_ego_vehicle

    @property
    def ego_filter(self) -> Optional[re.Pattern]:
        return self._ego_filter

    @ego_filter.setter
    def ego_filter(self, new_filter: Optional[re.Pattern]):
        self._ego_filter = new_filter

    @property
    def do_trim_scenario(self) -> bool:
        return self._do_trim_scenario

    @do_trim_scenario.setter
    def do_trim_scenario(self, new_do_trim_scenario: Optional[bool]):
        if new_do_trim_scenario is None:
            self._do_trim_scenario = False
        else:
            self._do_trim_scenario = new_do_trim_scenario

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

    @property
    def analyzers(self) -> Optional[Dict[EAnalyzer, Analyzer]]:
        return self._analyzers

    @analyzers.setter
    def analyzers(self, new_analyzers: Union[None, List[EAnalyzer], Dict[EAnalyzer, Analyzer]]):
        if new_analyzers is None or isinstance(new_analyzers, dict):
            self._analyzers = new_analyzers
        else:
            self._analyzers = {e_analyzer: e_analyzer.analyzer_type() for e_analyzer in new_analyzers}

    def run_conversion(self, source_file: str) \
            -> Union[Tuple[Scenario, PlanningProblemSet, ConversionStatistics], EFailureReason]:

        source_file = path.abspath(source_file)

        implicit_opendrive_path = self._pre_parse_scenario(source_file)
        if isinstance(implicit_opendrive_path, EFailureReason):
            return implicit_opendrive_path

        scenario, used_odr_file = self._create_scenario(implicit_opendrive_path)
        if isinstance(scenario, EFailureReason):
            return scenario

        states, sim_time, ending_cause = self.esmini_wrapper.simulate_scenario(source_file, self.esmini_dt)

        if states is None:
            return EFailureReason.SIMULATION_FAILED_CREATING_OUTPUT
        if len(states) == 0:
            return EFailureReason.NO_DYNAMIC_BEHAVIOR_FOUND
        ego_vehicle, ego_vehicle_found_with_filter = self._find_ego_vehicle(list(states.keys()))
        obstacles = self._create_obstacles_from_state_lists(scenario, ego_vehicle, states, sim_time)

        scenario.add_objects([
            obstacle for obstacle_name, obstacle in obstacles.items()
            if obstacle is not None and (self.keep_ego_vehicle or ego_vehicle != obstacle_name)
        ])
        if len(scenario.lanelet_network.lanelets) > 0:
            scenario.assign_obstacles_to_lanelets()

        if self.do_trim_scenario:
            scenario = self._trim_scenario(scenario, obstacles)

        return (
            scenario,
            self._create_planning_problem_set(obstacles[ego_vehicle]),
            self._build_statistics(
                source_file=source_file,
                used_odr_file=used_odr_file,
                scenario=scenario,
                obstacles=obstacles,
                ego_vehicle=ego_vehicle,
                ego_vehicle_found_with_filter=ego_vehicle_found_with_filter,
                ending_cause=ending_cause,
                sim_time=sim_time,
            )
        )

    @staticmethod
    def _pre_parse_scenario(source_file: str) -> Union[EFailureReason, None, str]:
        if not path.exists(source_file):
            return EFailureReason.SCENARIO_FILE_INVALID_PATH
        root = ElementTree.parse(source_file).getroot()
        if root.find("Storyboard") is None:
            if root.find("Catalog") is not None:
                return EFailureReason.SCENARIO_FILE_IS_CATALOG
            elif (pvd := root.find("ParameterValueDistribution")) is not None:
                if (alternative_file := pvd.find("ScenarioFile[@filepath]")) is not None:
                    warnings.warn(
                        f'<Osc2CrConverter/_pre_parse_scenario> {path.basename(source_file)} contains no source file, '
                        f'but references another OpenSCENARIO file: \"'
                        f'{path.join(path.dirname(source_file), alternative_file.attrib["filepath"])}\"'
                    )
                return EFailureReason.SCENARIO_FILE_IS_PARAMETER_VALUE_DISTRIBUTION
            return EFailureReason.SCENARIO_FILE_CONTAINS_NO_STORYBOARD

        if (implicit_odr_file := root.find("RoadNetwork/LogicFile[@filepath]")) is not None:
            return path.join(path.dirname(source_file), implicit_odr_file.attrib["filepath"])
        return None

    def _create_scenario(self, implicit_odr_file: Optional[str]) -> Tuple[Scenario, Optional[str]]:
        if self.odr_file is not None:
            scenario = opendrive_to_commonroad(self.odr_file)
            scenario.dt = self.cr_dt
            return scenario, self.odr_file
        elif implicit_odr_file is not None and self.use_implicit_odr_file and path.exists(implicit_odr_file):
            scenario = opendrive_to_commonroad(implicit_odr_file)
            scenario.dt = self.cr_dt
            return scenario, implicit_odr_file
        else:
            return Scenario(self.cr_dt), None

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
            states: Dict[str, List[SEStruct]],
            sim_time: float,
    ) -> Dict[str, Optional[DynamicObstacle]]:
        final_timestamps = [step * self.cr_dt for step in range(math.floor(sim_time / self.cr_dt) + 1)]

        def create_obstacle(obstacle_name: str) -> Optional[DynamicObstacle]:
            return self._osc_states_to_dynamic_obstacle(
                obstacle_id=scenario.generate_object_id(),
                states=states[obstacle_name],
                timestamps=final_timestamps,
            )

        # Make sure ego vehicle is always the obstacle with the lowest obstacle_id
        obstacles = {ego_vehicle: create_obstacle(ego_vehicle)}
        for object_name in sorted(states.keys()):
            if object_name != ego_vehicle:
                obstacles[object_name] = create_obstacle(object_name)
        return obstacles

    def _osc_states_to_dynamic_obstacle(
            self,
            obstacle_id: int,
            states: List[SEStruct],
            timestamps: List[float]
    ) -> Optional[DynamicObstacle]:
        if len(states) == 0:
            return None
        first_occurred_timestamp = min([state.timestamp for state in states])
        last_occurred_timestamp = max([state.timestamp for state in states])
        first_used_timestamp = min([t for t in timestamps], key=lambda t: math.fabs(first_occurred_timestamp - t))
        last_used_timestamp = min([t for t in timestamps], key=lambda t: math.fabs(last_occurred_timestamp - t))
        first_used_time_step = round(first_used_timestamp / self.cr_dt)
        last_used_time_step = round(last_used_timestamp / self.cr_dt)
        used_timestamps = sorted([t for t in timestamps if first_used_timestamp <= t <= last_used_timestamp])
        used_states = [ScenarioObjectState.build_interpolated(states, t) for t in used_timestamps]

        shape = Rectangle(states[0].length, states[0].width)
        trajectory = Trajectory(
            first_used_time_step,
            [state.to_cr_state(i + first_used_time_step) for i, state in enumerate(used_states)]
        )
        prediction = TrajectoryPrediction(trajectory, shape)
        prediction.final_time_step = last_used_time_step
        prediction.initial_time_step = first_used_time_step

        return DynamicObstacle(
            obstacle_id=obstacle_id,
            obstacle_type=Osc2CrConverter._osc_object_type_category_to_cr(states[0].objectType,
                                                                          states[0].objectCategory),
            obstacle_shape=shape,
            initial_state=trajectory.state_list[0],
            prediction=prediction
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
        orientation = final_state.orientation if self.goal_state_position_use_ego_rotation else 0.0
        while not is_valid_orientation(orientation):
            if orientation > 0:
                orientation -= 2 * np.pi
            else:
                orientation += 2 * np.pi

        goal_state = State()

        goal_state.position = Rectangle(
            length=self.goal_state_position_length,
            width=self.goal_state_position_width,
            center=final_state.position,
            orientation=orientation
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

    @staticmethod
    def _trim_scenario(scenario: Scenario, obstacles: Dict[str, Optional[DynamicObstacle]]) \
            -> Scenario:
        if len(scenario.lanelet_network.lanelets) == 0:
            return scenario
        scenario.assign_obstacles_to_lanelets()
        if any(obstacle.prediction.shape_lanelet_assignment is None for obstacle in obstacles.values()):
            return scenario
        used_lanelets = set()
        for obstacle in obstacles.values():
            for lanelet_set in obstacle.prediction.shape_lanelet_assignment.values():
                for lanelet in lanelet_set:
                    used_lanelets.add(lanelet)

        trimmed_scenario = Scenario(scenario.dt)

        trimmed_scenario.author = scenario.author
        trimmed_scenario.tags = scenario.tags
        trimmed_scenario.affiliation = scenario.affiliation
        trimmed_scenario.source = scenario.source
        trimmed_scenario.location = scenario.location

        trimmed_scenario.add_objects(scenario.obstacles)
        trimmed_scenario.add_objects(LaneletNetwork.create_from_lanelet_network(scenario.lanelet_network))

        removable_lanelets = []

        all_ids = {lanelet.lanelet_id for lanelet in trimmed_scenario.lanelet_network.lanelets}
        for lanelet_id in all_ids - used_lanelets:
            lanelet = trimmed_scenario.lanelet_network.find_lanelet_by_id(lanelet_id)
            if lanelet is not None:
                removable_lanelets.append(lanelet)
        trimmed_scenario.remove_lanelet(removable_lanelets)
        trimmed_scenario.assign_obstacles_to_lanelets()

        return trimmed_scenario

    def _build_statistics(
            self,
            source_file: str,
            used_odr_file: Optional[str],
            obstacles: Dict[str, Optional[DynamicObstacle]],
            scenario: Scenario,
            ego_vehicle: str,
            ego_vehicle_found_with_filter,
            ending_cause: ESimEndingCause,
            sim_time: float,
    ) -> "ConversionStatistics":

        trimmed_scenario = self._trim_scenario(scenario, obstacles)
        if not self.keep_ego_vehicle:
            trimmed_scenario.add_objects(obstacles[ego_vehicle])
            if len(scenario.lanelet_network.lanelets) > 0:
                scenario.assign_obstacles_to_lanelets()
        if self.analyzers is None:
            analysis = {}
        else:
            analysis = {
                e_analyzer: analyzer.run(trimmed_scenario, obstacles) for e_analyzer, analyzer in self.analyzers.items()
            }

        return ConversionStatistics(
            source_file=source_file,
            database_file=used_odr_file,
            num_obstacle_conversions=len(obstacles),
            failed_obstacle_conversions=[o_name for o_name, o in obstacles.items() if o is None],
            ego_vehicle=ego_vehicle,
            ego_vehicle_found_with_filter=ego_vehicle_found_with_filter,
            ego_vehicle_removed=not self.keep_ego_vehicle,
            sim_ending_cause=ending_cause,
            sim_time=sim_time,
            analysis=analysis,
        )
