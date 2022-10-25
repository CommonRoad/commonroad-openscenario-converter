import math
import re
import warnings
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass, field
from enum import auto, Enum
from os import path
from typing import Optional, List, Dict, Tuple, Union, Set, Type

from commonroad.geometry.shape import Rectangle
from commonroad.prediction.prediction import TrajectoryPrediction
from commonroad.scenario.obstacle import DynamicObstacle
from commonroad.scenario.scenario import Scenario, Tag
from commonroad.scenario.trajectory import Trajectory
from crdesigner.map_conversion.map_conversion_interface import opendrive_to_commonroad
from scenariogeneration.xosc import Vehicle

from BatchConversion.Converter import Converter
from OpenSCENARIO2CR.ConversionAnalyzer.Analyzer import Analyzer
from OpenSCENARIO2CR.ConversionAnalyzer.AnalyzerErrorResult import AnalyzerErrorResult
from OpenSCENARIO2CR.ConversionAnalyzer.AnalyzerResult import AnalyzerResult
from OpenSCENARIO2CR.OpenSCENARIOWrapper.ESimEndingCause import ESimEndingCause
from OpenSCENARIO2CR.OpenSCENARIOWrapper.Esmini.EsminiWrapperProvider import EsminiWrapperProvider
from OpenSCENARIO2CR.OpenSCENARIOWrapper.ScenarioObjectState import ScenarioObjectState, SimScenarioObjectState
from OpenSCENARIO2CR.OpenSCENARIOWrapper.SimWrapper import SimWrapper
from OpenSCENARIO2CR.OpenSCENARIOWrapper.SimWrapperResult import WrapperSimResult
from OpenSCENARIO2CR.Osc2CrConverterResult import Osc2CrConverterResult
from OpenSCENARIO2CR.util.ConversionStatistics import ConversionStatistics
from OpenSCENARIO2CR.util.ObstacleExtraInfoFinder import ObstacleExtraInfoFinder
from OpenSCENARIO2CR.util.PPSBuilder import PPSBuilder
from OpenSCENARIO2CR.util.UtilFunctions import trim_scenario, dataclass_is_complete


class EFailureReason(Enum):
    SCENARIO_FILE_INVALID_PATH = auto()
    SCENARIO_FILE_IS_CATALOG = auto()
    SCENARIO_FILE_IS_PARAMETER_VALUE_DISTRIBUTION = auto()
    SCENARIO_FILE_CONTAINS_NO_STORYBOARD = auto()
    SIMULATION_FAILED_CREATING_OUTPUT = auto()
    NO_DYNAMIC_BEHAVIOR_FOUND = auto()


@dataclass
class Osc2CrConverter(Converter):
    # Required
    author: str
    affiliation: str
    source: str
    tags: Set[Tag]

    dt_cr: float = 0.1
    sim_wrapper: SimWrapper = EsminiWrapperProvider().provide_esmini_wrapper()
    pps_builder: PPSBuilder = PPSBuilder()

    use_implicit_odr_file: bool = False
    trim_scenario: bool = False
    keep_ego_vehicle: bool = True
    analyzers: Union[Dict[Type[Analyzer], Optional[Analyzer]], List[Type[Analyzer]]] = \
        field(default_factory=lambda: list())

    # Optional
    dt_sim: Optional[float] = None
    odr_file_override: Optional[str] = None
    ego_filter: Optional[re.Pattern] = None

    def get_analyzer_objects(self) -> Dict[Type[Analyzer], Analyzer]:
        if self.analyzers is None:
            return {}
        elif isinstance(self.analyzers, list):
            return {t_analyzer: t_analyzer() for t_analyzer in self.analyzers}
        elif isinstance(self.analyzers, dict):
            ret = {}
            for t_analyzer, analyzer in self.analyzers.items():
                if analyzer is not None:
                    ret[t_analyzer] = analyzer
                else:
                    ret[t_analyzer] = t_analyzer()
            return ret

    def run_conversion(self, source_file: str) \
            -> Union[Osc2CrConverterResult, EFailureReason]:
        assert dataclass_is_complete(self)

        xosc_file = path.abspath(source_file)

        implicit_opendrive_path = self._pre_parse_scenario(xosc_file)

        if isinstance(implicit_opendrive_path, EFailureReason):
            return implicit_opendrive_path

        scenario, xodr_file, xodr_conversion_error = self._create_scenario(implicit_opendrive_path)
        if isinstance(scenario, EFailureReason):
            return scenario

        dt_sim = self.dt_sim if self.dt_sim is not None else self.dt_cr / 10
        res: WrapperSimResult = self.sim_wrapper.simulate_scenario(xosc_file, dt_sim)
        if res.ending_cause is ESimEndingCause.FAILURE:
            return EFailureReason.SIMULATION_FAILED_CREATING_OUTPUT
        if len(res.states) == 0:
            return EFailureReason.NO_DYNAMIC_BEHAVIOR_FOUND
        sim_time = res.sim_time
        ending_cause = res.ending_cause

        ego_vehicle, ego_vehicle_found_with_filter = self._find_ego_vehicle(list(res.states.keys()))
        keep_ego_vehicle = self.keep_ego_vehicle

        obstacles_extra_info = ObstacleExtraInfoFinder(xosc_file, set(res.states.keys())).run()
        obstacles_extra_info_finder_error = None
        if isinstance(obstacles_extra_info, AnalyzerErrorResult):
            obstacles_extra_info_finder_error = obstacles_extra_info
            obstacles_extra_info = {o_name: None for o_name in res.states.keys()}

        obstacles = self._create_obstacles_from_state_lists(
            scenario, ego_vehicle, res.states, res.sim_time, obstacles_extra_info
        )

        scenario.add_objects([
            obstacle for obstacle_name, obstacle in obstacles.items()
            if obstacle is not None and (self.keep_ego_vehicle or ego_vehicle != obstacle_name)
        ])
        if len(scenario.lanelet_network.lanelets) > 0:
            scenario.assign_obstacles_to_lanelets()

        if self.trim_scenario:
            scenario = trim_scenario(scenario, deep_copy=False)
        pps = self.pps_builder.build(obstacles[ego_vehicle])

        return Osc2CrConverterResult(
            statistics=self.build_statistics(
                obstacles=obstacles,
                ego_vehicle=ego_vehicle,
                ego_vehicle_found_with_filter=ego_vehicle_found_with_filter,
                keep_ego_vehicle=keep_ego_vehicle,
                ending_cause=ending_cause,
                sim_time=sim_time,
            ),
            analysis=self.run_analysis(
                scenario=scenario,
                obstacles=obstacles,
                ego_vehicle=ego_vehicle,
                keep_ego_vehicle=keep_ego_vehicle,
                obstacles_extra_info=obstacles_extra_info
            ),
            xosc_file=xosc_file,
            xodr_file=xodr_file,
            xodr_conversion_error=xodr_conversion_error,
            obstacles_extra_info_finder_error=obstacles_extra_info_finder_error,
            scenario=scenario,
            planning_problem_set=pps,
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

    def _create_scenario(self, implicit_odr_file: Optional[str]) \
            -> Tuple[Scenario, Optional[str], Optional[AnalyzerErrorResult]]:
        odr_file: Optional[str] = None
        if self.odr_file_override is not None:
            if path.exists(self.odr_file_override):
                odr_file = self.odr_file_override
            else:
                warnings.warn(
                    f"<OpenSCENARIO2CRConverter/_create_scenario> File {self.odr_file_override} does not exist")
        elif implicit_odr_file is not None and self.use_implicit_odr_file:
            if path.exists(implicit_odr_file):
                odr_file = implicit_odr_file
            else:
                warnings.warn(
                    f"<OpenSCENARIO2CRConverter/_create_scenario> File {implicit_odr_file} does not exist")

        odr_conversion_error = None
        if odr_file is not None:
            try:
                scenario = opendrive_to_commonroad(odr_file)
                scenario.dt = self.dt_cr
            except Exception as e:
                odr_conversion_error = AnalyzerErrorResult.from_exception(e)
                scenario = Scenario(self.dt_cr)
        else:
            scenario = Scenario(self.dt_cr)

        scenario.author = self.author
        scenario.affiliation = self.affiliation
        scenario.source = self.source
        scenario.tags = self.tags

        return scenario, odr_file, odr_conversion_error

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
            states: Dict[str, List[SimScenarioObjectState]],
            sim_time: float,
            obstacles_extra_info: Dict[str, Optional[Vehicle]]
    ) -> Dict[str, Optional[DynamicObstacle]]:
        final_timestamps = [step * self.dt_cr for step in range(math.floor(sim_time / self.dt_cr) + 1)]

        def create_obstacle(obstacle_name: str) -> Optional[DynamicObstacle]:
            return self._osc_states_to_dynamic_obstacle(
                obstacle_id=scenario.generate_object_id(),
                states=states[obstacle_name],
                timestamps=final_timestamps,
                obstacle_extra_info=obstacles_extra_info[obstacle_name]
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
            states: List[SimScenarioObjectState],
            timestamps: List[float],
            obstacle_extra_info: Optional[Vehicle],
    ) -> Optional[DynamicObstacle]:
        if len(states) == 0:
            return None
        first_occurred_timestamp = min([state.get_timestamp() for state in states])
        last_occurred_timestamp = max([state.get_timestamp() for state in states])
        first_used_timestamp = min([t for t in timestamps], key=lambda t: math.fabs(first_occurred_timestamp - t))
        last_used_timestamp = min([t for t in timestamps], key=lambda t: math.fabs(last_occurred_timestamp - t))
        first_used_time_step = round(first_used_timestamp / self.dt_cr)
        last_used_time_step = round(last_used_timestamp / self.dt_cr)
        used_timestamps = sorted([t for t in timestamps if first_used_timestamp <= t <= last_used_timestamp])
        used_states = [ScenarioObjectState.build_interpolated(states, t, obstacle_extra_info) for t in used_timestamps]

        shape = Rectangle(states[0].get_object_length(), states[0].get_object_width())
        trajectory = Trajectory(
            first_used_time_step,
            [state.to_cr_state(i + first_used_time_step) for i, state in enumerate(used_states)]
        )
        prediction = TrajectoryPrediction(trajectory, shape)
        prediction.final_time_step = last_used_time_step
        prediction.initial_time_step = first_used_time_step

        return DynamicObstacle(
            obstacle_id=obstacle_id,
            obstacle_type=states[0].get_obstacle_type(),
            obstacle_shape=shape,
            initial_state=trajectory.state_list[0],
            prediction=prediction
        )

    @staticmethod
    def build_statistics(
            obstacles: Dict[str, Optional[DynamicObstacle]],
            ego_vehicle: str,
            ego_vehicle_found_with_filter: bool,
            keep_ego_vehicle: bool,
            ending_cause: ESimEndingCause,
            sim_time: float
    ) -> ConversionStatistics:
        return ConversionStatistics(
            num_obstacle_conversions=len(obstacles),
            failed_obstacle_conversions=[o_name for o_name, o in obstacles.items() if o is None],
            ego_vehicle=ego_vehicle,
            ego_vehicle_found_with_filter=ego_vehicle_found_with_filter,
            ego_vehicle_removed=not keep_ego_vehicle,
            sim_ending_cause=ending_cause,
            sim_time=sim_time,
        )

    def run_analysis(
            self,
            scenario: Scenario,
            obstacles: Dict[str, Optional[DynamicObstacle]],
            ego_vehicle: str,
            keep_ego_vehicle: bool,
            obstacles_extra_info: Dict[str, Optional[Vehicle]],
    ) -> Dict[Type[Analyzer], Tuple[float, Dict[str, AnalyzerResult]]]:
        analyzers = self.get_analyzer_objects()
        if len(analyzers) == 0:
            return {}
        else:
            trimmed_scenario = trim_scenario(scenario)
            if not keep_ego_vehicle:
                trimmed_scenario.add_objects(obstacles[ego_vehicle])
                if len(scenario.lanelet_network.lanelets) > 0:
                    scenario.assign_obstacles_to_lanelets()
            return {
                e_analyzer: analyzer.run(
                    trimmed_scenario,
                    obstacles,
                    obstacles_extra_info
                ) for e_analyzer, analyzer in analyzers.items()
            }
