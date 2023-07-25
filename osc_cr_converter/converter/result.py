__author__ = "Michael Ratzel, Yuanfei Lin"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["KoSi"]
__version__ = "0.1.0"
__maintainer__ = "Yuanfei Lin"
__email__ = "commonroad@lists.lrz.de"
__status__ = "beta"

from dataclasses import dataclass
from multiprocessing import Lock
from os import path
from typing import Dict, Optional, Tuple, ClassVar

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.scenario import Scenario

from osc_cr_converter.analyzer.error import AnalyzerErrorResult
from osc_cr_converter.analyzer.result import AnalyzerResult
from osc_cr_converter.analyzer.enum_analyzer import EAnalyzer
from osc_cr_converter.utility.statistics import ConversionStatistics
from osc_cr_converter.converter.serializable import Serializable


@dataclass(frozen=True)
class Osc2CrConverterResult(Serializable):
    """
    The result of the Osc2CrConverter it contains the converted scenario and planning problem set as well as general
    statistics and other useful information.

    For faster import of the results the loading of the scenario and planning problem set can be deactivated using
    the Serializable interface
    """

    __lock: ClassVar[Lock] = Lock()
    statistics: ConversionStatistics
    analysis: Dict[EAnalyzer, Tuple[float, Dict[str, AnalyzerResult]]]
    xosc_file: str
    xodr_file: Optional[str]
    xodr_conversion_error: Optional[AnalyzerErrorResult]
    obstacles_extra_info_finder_error: Optional[AnalyzerErrorResult]

    scenario: Optional[Scenario]
    planning_problem_set: Optional[PlanningProblemSet]

    def __getstate__(self) -> Dict:
        data = self.__dict__.copy()
        if (
            self.scenario is not None
            and self.planning_problem_set is not None
            and Serializable.storage_dir is not None
        ):
            del data["scenario"]
            del data["planning_problem_set"]
            file_path_base = path.join(
                Serializable.storage_dir,
                path.splitext(path.basename(self.xosc_file))[0],
            )
            with self.__lock:
                i = 1
                while path.exists(file_path := file_path_base + f"{i}.xml"):
                    i += 1
                CommonRoadFileWriter(
                    scenario=self.scenario,
                    planning_problem_set=self.planning_problem_set,
                ).write_to_file(file_path, OverwriteExistingFile.SKIP)
                data["file_path"] = file_path

        return data

    def __setstate__(self, data: Dict):
        if "file_path" in data:
            scenario = None
            pps = None
            if path.exists(data["file_path"]) and Serializable.import_extra_files:
                scenario, pps = CommonRoadFileReader(data["file_path"]).open(
                    lanelet_assignment=True
                )
            del data["file_path"]
            data["scenario"] = scenario
            data["planning_problem_set"] = pps

        self.__dict__.update(data)
