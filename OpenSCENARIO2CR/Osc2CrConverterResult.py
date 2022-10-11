from dataclasses import dataclass
from os import path
from typing import Dict, Optional

from commonroad.common.file_reader import CommonRoadFileReader
from commonroad.common.file_writer import CommonRoadFileWriter, OverwriteExistingFile
from commonroad.planning.planning_problem import PlanningProblemSet
from commonroad.scenario.scenario import Scenario

from OpenSCENARIO2CR.ConversionAnalyzer.AnalyzerResult import AnalyzerResult
from OpenSCENARIO2CR.ConversionAnalyzer.EAnalyzer import EAnalyzer
from OpenSCENARIO2CR.util.ConversionStatistics import ConversionStatistics
from OpenSCENARIO2CR.util.Serializable import Serializable


@dataclass(frozen=True)
class Osc2CrConverterResult(Serializable):
    statistics: ConversionStatistics
    analysis: Dict[EAnalyzer, Dict[str, AnalyzerResult]]
    source_file: str

    scenario: Optional[Scenario]
    planning_problem_set: Optional[PlanningProblemSet]

    def __getstate__(self) -> Dict:
        data = self.__dict__.copy()
        if self.scenario is not None and self.planning_problem_set is not None \
                and Serializable.storage_dir is not None and Serializable.store_extra_files:
            del data["scenario"]
            del data["planning_problem_set"]
            file_path = path.join(Serializable.storage_dir, path.splitext(path.basename(self.source_file))[0]) + ".xml"
            CommonRoadFileWriter(
                scenario=self.scenario,
                planning_problem_set=self.planning_problem_set
            ).write_to_file(file_path, OverwriteExistingFile.ALWAYS)
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
