from dataclasses import dataclass
from multiprocessing import Lock
from os import path
from typing import Dict, Optional, Tuple, ClassVar

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.scenario import Scenario

from OpenSCENARIO2CR.ConversionAnalyzer.AnalyzerErrorResult import AnalyzerErrorResult
from OpenSCENARIO2CR.ConversionAnalyzer.AnalyzerResult import AnalyzerResult
from OpenSCENARIO2CR.ConversionAnalyzer.EAnalyzer import EAnalyzer
from OpenSCENARIO2CR.util.ConversionStatistics import ConversionStatistics
from BatchConversion.Serializable import Serializable


@dataclass(frozen=True)
class Osc2CrConverterResult(Serializable):
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
        if self.scenario is not None and self.planning_problem_set is not None \
                and Serializable.storage_dir is not None:
            del data["scenario"]
            del data["planning_problem_set"]
            file_path_base = path.join(Serializable.storage_dir, path.splitext(path.basename(self.xosc_file))[0])
            with self.__lock:
                i = 1
                while path.exists(file_path := file_path_base + f"{i}.xml"):
                    i += 1
                CommonRoadFileWriter(
                    scenario=self.scenario,
                    planning_problem_set=self.planning_problem_set
                ).write_to_file(file_path, OverwriteExistingFile.SKIP)
                data["file_path"] = file_path

        return data

    def __setstate__(self, data: Dict):
        if "file_path" in data:
            scenario = None
            pps = None
            if path.exists(data["file_path"]) and Serializable.import_extra_files:
                scenario, pps = CommonRoadFileReader(data["file_path"]).open(lanelet_assignment=True)
            del data["file_path"]
            data["scenario"] = scenario
            data["planning_problem_set"] = pps

        self.__dict__.update(data)
