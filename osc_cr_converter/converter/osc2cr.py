__author__ = "Michael Ratzel, Yuanfei Lin"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["KoSi"]
__version__ = "0.1.0"
__maintainer__ = "Yuanfei Lin"
__email__ = "commonroad@lists.lrz.de"
__status__ = "beta"

import math
import os
import re
import time
import warnings
import logging
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass
from os import path
from typing import Optional, List, Dict, Tuple, Union, Set

from commonroad.geometry.shape import Rectangle, Circle
from commonroad.prediction.prediction import TrajectoryPrediction
from commonroad.scenario.obstacle import DynamicObstacle, ObstacleType
from commonroad.scenario.scenario import Scenario, Tag
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.state import InitialState
from commonroad.scenario.trajectory import Trajectory
from commonroad.common.file_writer import CommonRoadFileWriter
from commonroad.common.file_writer import OverwriteExistingFile
from crdesigner.map_conversion.map_conversion_interface import opendrive_to_commonroad
from scenariogeneration.xosc import Vehicle

from osc_cr_converter.converter.base import Converter, EFailureReason
from osc_cr_converter.analyzer.base import Analyzer
from osc_cr_converter.analyzer.error import AnalyzerErrorResult
from osc_cr_converter.analyzer.result import AnalyzerResult
from osc_cr_converter.analyzer.enum_analyzer import EAnalyzer
from osc_cr_converter.wrapper.base.ending_cause import ESimEndingCause
from osc_cr_converter.wrapper.esmini.esmini_wrapper_provider import (
    EsminiWrapperProvider,
)
from osc_cr_converter.wrapper.base.scenario_object import (
    ScenarioObjectState,
    SimScenarioObjectState,
)
from osc_cr_converter.wrapper.base.sim_wrapper import SimWrapper, WrapperSimResult
from osc_cr_converter.converter.result import Osc2CrConverterResult
from osc_cr_converter.utility.statistics import ConversionStatistics
from osc_cr_converter.utility.obstacle_info import ObstacleExtraInfoFinder
from osc_cr_converter.utility.pps_builder import PPSBuilder
from osc_cr_converter.utility.general import trim_scenario, dataclass_is_complete
from osc_cr_converter.utility.configuration import ConverterParams
import osc_cr_converter.utility.logger as util_logger

# Configure the logging module
logger = logging.getLogger(__name__)


@dataclass
class Osc2CrConverter(Converter):
    """
    The main class of the OpenSCENARIO to CommonRoad conversion
    """

    def __init__(self, config: ConverterParams):
        self.author: str = config.scenario.author  # Author of the scenario
        self.affiliation: str = (
            config.scenario.affiliation
        )  # Affiliation of the author of the scenario
        self.source: str = config.scenario.source  # Source of the scenario
        self.tags: Set[Tag] = config.scenario.tags  # Tags of the scenario

        self.dt_cr: float = (
            config.scenario.dt_cr
        )  # Time step size of the CommonRoad scenario

        self.config: ConverterParams = config  # Configurations

        # The used SimWrapper implementation
        self.sim_wrapper: SimWrapper = EsminiWrapperProvider(
            config
        ).provide_esmini_wrapper()
        # The used PPSBuilder instance
        self.pps_builder: PPSBuilder = config.initialize_planning_problem_set()

        # indicating whether the openDRIVE map defined in the openSCENARIO is used
        self.use_implicit_odr_file: bool = config.esmini.use_implicit_odr_file
        # indicating whether the huge mag contained in the scenario is trimmed
        self.trim_scenario: bool = config.scenario.trim_scenario
        # indicating whether the ego vehicle is kept or not in the saved scenario
        self.keep_ego_vehicle: bool = config.scenario.keep_ego_vehicle
        # indicating whether the scenario needs to be visualized with esmini
        self.view_scenario: bool = config.debug.run_viewer
        self.render_to_gif: bool = config.debug.render_to_gif

        # analyzers of the scenario with CommonRoad tools
        self.analyzers: Union[Dict[EAnalyzer, Optional[Analyzer]], List[EAnalyzer]] = {}

        self.dt_sim: Optional[
            float
        ] = config.esmini.dt_sim  # User-defined time step size for esmini simulation
        self.odr_file_override: Optional[
            str
        ] = config.esmini.odr_file_override  # User-defined OpenDRIVE map to be used
        self.ego_filter: Optional[
            re.Pattern, str
        ] = config.esmini.ego_filter  # Pattern of recognizing the ego vehicle

    def get_analyzer_objects(self) -> Dict[EAnalyzer, Analyzer]:
        if self.analyzers is None:
            return {}
        elif isinstance(self.analyzers, list):
            return {
                e_analyzer: e_analyzer.analyzer_type() for e_analyzer in self.analyzers
            }
        elif isinstance(self.analyzers, dict):
            ret = {}
            for e_analyzer, analyzer in self.analyzers.items():
                if analyzer is not None:
                    ret[e_analyzer] = analyzer
                else:
                    ret[e_analyzer] = e_analyzer.analyzer_type()
            return ret

    def run_conversion(self, source_file: str) -> Union[Scenario, EFailureReason]:
        """
        The main function, that runs the simulation wrapper (SimWrapper) and converts its results.
        :param source_file: the given openSCENARIO source file
        :return converted results if converted successfully. Otherwise, the reason for the failure.
        """
        self.config.general.name_xosc = os.path.basename(source_file).split(".")[0]
        util_logger.print_and_log_info(
            logger,
            f"* Converting the OpenSCENARIO file: {self.config.general.name_xosc}.xosc",
        )

        assert dataclass_is_complete(self)

        xosc_file = path.abspath(source_file)

        implicit_opendrive_path = self._pre_parse_scenario(xosc_file)

        if isinstance(implicit_opendrive_path, EFailureReason):
            self.conversion_result = implicit_opendrive_path
            util_logger.print_and_log_error(
                logger, f"*\t Failed since : {self.conversion_result.name}"
            )
            return self.conversion_result

        start_time = time.time()
        scenario, xodr_file, xodr_conversion_error = self._create_basic_scenario(
            implicit_opendrive_path
        )
        runtime = time.time() - start_time
        util_logger.print_and_log_info(
            logger, f"*\t Map conversion takes {runtime:.2f} s"
        )

        if isinstance(scenario, EFailureReason):
            self.conversion_result = scenario
            util_logger.print_and_log_error(
                logger, f"*\t Failed since : {self.conversion_result.name}"
            )
            return self.conversion_result

        if self.view_scenario:
            self.sim_wrapper.view_scenario(source_file, self.config.esmini.window_size)
        if self.render_to_gif:
            self.sim_wrapper.render_scenario_to_gif(
                source_file,
                self.config.general.path_output
                + self.config.general.name_xosc
                + ".gif",
            )

        dt_sim = self.dt_sim if self.dt_sim is not None else self.dt_cr / 10
        res: WrapperSimResult = self.sim_wrapper.simulate_scenario(xosc_file, dt_sim)
        if res.ending_cause is ESimEndingCause.FAILURE:
            self.conversion_result = EFailureReason.SIMULATION_FAILED_CREATING_OUTPUT
            util_logger.print_and_log_error(
                logger, f"*\t Failed since : {self.conversion_result.name}"
            )
            return self.conversion_result
        if len(res.states) == 0:
            self.conversion_result = EFailureReason.NO_DYNAMIC_BEHAVIOR_FOUND
            util_logger.print_and_log_error(
                logger, f"*\t Failed since : {self.conversion_result.name}"
            )
            return self.conversion_result
        sim_time = res.sim_time
        runtime += res.runtime
        ending_cause = res.ending_cause
        util_logger.print_and_log_info(
            logger, f"*\t Esmini simulation takes {res.runtime:.2f} s"
        )

        start_time = time.time()

        ego_vehicle, ego_vehicle_found_with_filter = self._find_ego_vehicle(
            list(res.states.keys())
        )
        keep_ego_vehicle = self.keep_ego_vehicle

        obstacles_extra_info = ObstacleExtraInfoFinder(
            xosc_file, set(res.states.keys())
        ).run()
        obstacles_extra_info_finder_error = None
        if isinstance(obstacles_extra_info, AnalyzerErrorResult):
            obstacles_extra_info_finder_error = obstacles_extra_info
            obstacles_extra_info = {o_name: None for o_name in res.states.keys()}

        obstacles = self._create_obstacles_from_state_lists(
            scenario, ego_vehicle, res.states, res.sim_time, obstacles_extra_info
        )

        scenario.add_objects(
            [
                obstacle
                for obstacle_name, obstacle in obstacles.items()
                if obstacle is not None
                and (self.keep_ego_vehicle or ego_vehicle != obstacle_name)
            ]
        )
        if len(scenario.lanelet_network.lanelets) > 0:
            scenario.assign_obstacles_to_lanelets()

        if self.trim_scenario:
            scenario = trim_scenario(scenario, deep_copy=False)
        pps = self.pps_builder.build(obstacles[ego_vehicle])
        runtime += time.time() - start_time
        util_logger.print_and_log_info(
            logger, f"*\t Other conversion tasks take {time.time() - start_time:.2f} s"
        )
        util_logger.print_and_log_info(
            logger, f"* {self.config.general.name_xosc} is successfully converted 🏆!"
        )

        if self.config.debug.write_to_xml:
            self.write_to_xml(scenario, pps)

        self.conversion_result = Osc2CrConverterResult(
            statistics=self.build_statistics(
                obstacles=obstacles,
                ego_vehicle=ego_vehicle,
                ego_vehicle_found_with_filter=ego_vehicle_found_with_filter,
                keep_ego_vehicle=keep_ego_vehicle,
                ending_cause=ending_cause,
                sim_time=sim_time,
                runtime=runtime,
            ),
            analysis=self.run_analysis(
                scenario=scenario,
                obstacles=obstacles,
                ego_vehicle=ego_vehicle,
                keep_ego_vehicle=keep_ego_vehicle,
                obstacles_extra_info=obstacles_extra_info,
            ),
            xosc_file=xosc_file,
            xodr_file=xodr_file,
            xodr_conversion_error=xodr_conversion_error,
            obstacles_extra_info_finder_error=obstacles_extra_info_finder_error,
            scenario=scenario,
            planning_problem_set=pps,
        )
        return self.conversion_result.scenario

    @staticmethod
    def _pre_parse_scenario(source_file: str) -> Union[EFailureReason, None, str]:
        """
        Pre-parsing the scenario.
        :param source_file: the given source file
        :return: None or failure of the parsing.
        """
        if not path.exists(source_file):
            return EFailureReason.SCENARIO_FILE_INVALID_PATH
        root = ElementTree.parse(source_file).getroot()
        if root.find("Storyboard") is None:
            if root.find("Catalog") is not None:
                return EFailureReason.SCENARIO_FILE_IS_CATALOG
            elif (pvd := root.find("ParameterValueDistribution")) is not None:
                if (
                    alternative_file := pvd.find("ScenarioFile[@filepath]")
                ) is not None:
                    warnings.warn(
                        f"<Osc2CrConverter/_pre_parse_scenario> {path.basename(source_file)} contains no source file, "
                        f'but references another OpenSCENARIO file: "'
                        f'{path.join(path.dirname(source_file), alternative_file.attrib["filepath"])}"'
                    )
                return EFailureReason.SCENARIO_FILE_IS_PARAMETER_VALUE_DISTRIBUTION
            return EFailureReason.SCENARIO_FILE_CONTAINS_NO_STORYBOARD

        if (
            implicit_odr_file := root.find("RoadNetwork/LogicFile[@filepath]")
        ) is not None:
            return path.join(
                path.dirname(source_file), implicit_odr_file.attrib["filepath"]
            )
        return None

    def _create_basic_scenario(
        self, implicit_odr_file: Optional[str]
    ) -> Tuple[Scenario, Optional[str], Optional[AnalyzerErrorResult]]:
        """
        Creating the scenario with basic information and road networks (map)
        :param implicit_odr_file: the source file of openDRIVE map
        :return: the scenario with/without map, path of the openDRIVE, the reason of the failure if applicable
        """
        odr_file: Optional[str] = None
        if self.odr_file_override is not None:
            if path.exists(self.odr_file_override):
                odr_file = self.odr_file_override
            else:
                warnings.warn(
                    f"<OpenSCENARIO2CRConverter/_create_scenario> File {self.odr_file_override} does not exist"
                )
        elif implicit_odr_file is not None and self.use_implicit_odr_file:
            if path.exists(implicit_odr_file):
                odr_file = implicit_odr_file
            else:
                warnings.warn(
                    f"<OpenSCENARIO2CRConverter/_create_scenario> File {implicit_odr_file} does not exist"
                )

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

    def _find_ego_vehicle(self, vehicle_name_list: List[str]) -> Tuple[str, bool]:
        """
        Finding the ego vehicle based on the given pattern if applicable.
        :param vehicle_name_list: the list of vehicle names
        :return: ego vehicle found/first vehicle in the list, indication of which situation
        """
        if self.ego_filter is not None:
            found_ego_vehicles = [
                name
                for name in vehicle_name_list
                if self.ego_filter.match(name) is not None
            ]
            if len(found_ego_vehicles) > 0:
                return sorted(found_ego_vehicles)[0], True

        return sorted(vehicle_name_list)[0], False

    def _create_obstacles_from_state_lists(
        self,
        scenario: Scenario,
        ego_vehicle: str,
        states: Dict[str, List[SimScenarioObjectState]],
        sim_time: float,
        obstacles_extra_info: Dict[str, Optional[Vehicle]],
    ) -> Dict[str, Optional[DynamicObstacle]]:
        """
        Creating obstacles based on the given vehicle state lists.
        :param scenario: basic scenario
        :param ego_vehicle: name of the ego vehicle
        :param states: state list
        :param sim_time: total simulation time (in esmini)
        :param obstacles_extra_info: extra information about the Vehicle
        :return: created CommonRoad obstacles
        """
        final_timestamps = [
            step * self.dt_cr for step in range(math.floor(sim_time / self.dt_cr) + 1)
        ]

        def create_obstacle(obstacle_name: str) -> Optional[DynamicObstacle]:
            return self._osc_states_to_dynamic_obstacle(
                obstacle_id=scenario.generate_object_id(),
                states=states[obstacle_name],
                timestamps=final_timestamps,
                obstacle_extra_info=obstacles_extra_info[obstacle_name],
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
        first_used_timestamp = min(
            [t for t in timestamps],
            key=lambda t: math.fabs(first_occurred_timestamp - t),
        )
        last_used_timestamp = min(
            [t for t in timestamps],
            key=lambda t: math.fabs(last_occurred_timestamp - t),
        )
        first_used_time_step = round(first_used_timestamp / self.dt_cr)
        last_used_time_step = round(last_used_timestamp / self.dt_cr)
        used_timestamps = sorted(
            [t for t in timestamps if first_used_timestamp <= t <= last_used_timestamp]
        )
        used_states = [
            ScenarioObjectState.build_interpolated(states, t, obstacle_extra_info)
            for t in used_timestamps
        ]

        obstacle_type = states[0].get_obstacle_type()
        if obstacle_type == ObstacleType.PEDESTRIAN:
            # for pedestrian, we consider an overapproximated circular area.
            # see: Koschi, Markus, et al. "Set-based prediction of pedestrians in urban environments considering
            # formalized traffic rules." IEEE ITSC, 2018
            shape = Circle(
                max(states[0].get_object_length() / 2.0, states[0].get_object_width())
                / 2.0
            )
        else:
            shape = Rectangle(
                states[0].get_object_length(), states[0].get_object_width()
            )

        trajectory = Trajectory(
            first_used_time_step,
            [
                state.to_cr_state(i + first_used_time_step)
                for i, state in enumerate(used_states)
            ],
        )
        prediction = TrajectoryPrediction(trajectory, shape)

        initial_state = trajectory.state_list[0]
        return DynamicObstacle(
            obstacle_id=obstacle_id,
            obstacle_type=obstacle_type,
            obstacle_shape=shape,
            initial_state=InitialState(
                position=initial_state.position,
                orientation=initial_state.orientation,
                time_step=initial_state.time_step,
                velocity=initial_state.velocity,
                yaw_rate=0.0,
                slip_angle=0.0,
            ),
            prediction=prediction,
        )

    def write_to_xml(
        self,
        scenario: Scenario,
        pps: PlanningProblemSet,
    ) -> None:
        """
        Writing the CommonRoad scenario to xml file together with the planning problem set
        :param scenario: CommonRoad scenario
        :param pps: planning problem set
        """
        COUNTRY = "OSC"  # OpenSCENARIO
        SCENE = self.config.general.name_xosc
        CONFIG = self.config.scenario.config
        # T: single trajectories
        PRED = self.config.scenario.pred
        file_name = COUNTRY + "_" + SCENE + "_" + CONFIG + "_" + "T-" + PRED + ".xml"
        fw = CommonRoadFileWriter(
            scenario, pps, self.author, self.affiliation, self.source, self.tags
        )
        fw.write_to_file(
            self.config.general.path_output + file_name, OverwriteExistingFile.ALWAYS
        )

    @staticmethod
    def build_statistics(
        obstacles: Dict[str, Optional[DynamicObstacle]],
        ego_vehicle: str,
        ego_vehicle_found_with_filter: bool,
        keep_ego_vehicle: bool,
        ending_cause: ESimEndingCause,
        sim_time: float,
        runtime: float,
    ) -> ConversionStatistics:
        """
        Building the statistics of the conversion.
        :param obstacles: created obstacles
        :param ego_vehicle: name of the ego vehicle
        :param ego_vehicle_found_with_filter: the way of ego creation
        :param keep_ego_vehicle: whether the ego vehicle is kept
        :param ending_cause: why simulation is finished
        :param sim_time: simulation time in total
        :param runtime: runtime of converting the scenario
        :return: statistics
        """
        util_logger.print_and_log_info(
            logger, "# ===========  Conversion Statistics  ========== #"
        )
        util_logger.print_and_log_info(logger, f"#\t Nr of obstacles: {len(obstacles)}")
        util_logger.print_and_log_info(
            logger, f"#\t Scenario duration: {sim_time:.2f} s"
        )
        util_logger.print_and_log_info(
            logger,
            f"#\t The ego vehicle is removed" f""
            if not keep_ego_vehicle
            else "#\t the ego vehicle is kept",
        )
        util_logger.print_and_log_info(
            logger, f"#\t The ending cause {ending_cause.name}"
        )
        util_logger.print_and_log_info(
            logger, "# ============================================== #"
        )
        return ConversionStatistics(
            num_obstacle_conversions=len(obstacles),
            failed_obstacle_conversions=[
                o_name for o_name, o in obstacles.items() if o is None
            ],
            ego_vehicle=ego_vehicle,
            ego_vehicle_found_with_filter=ego_vehicle_found_with_filter,
            ego_vehicle_removed=not keep_ego_vehicle,
            sim_ending_cause=ending_cause,
            sim_time=sim_time,
            runtime=runtime,
        )

    def run_analysis(
        self,
        scenario: Scenario,
        obstacles: Dict[str, Optional[DynamicObstacle]],
        ego_vehicle: str,
        keep_ego_vehicle: bool,
        obstacles_extra_info: Dict[str, Optional[Vehicle]],
    ) -> Dict[EAnalyzer, Tuple[float, Dict[str, AnalyzerResult]]]:
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
                    trimmed_scenario, obstacles, obstacles_extra_info
                )
                for e_analyzer, analyzer in analyzers.items()
            }
