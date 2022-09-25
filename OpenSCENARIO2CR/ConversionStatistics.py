from dataclasses import dataclass, fields
from enum import Enum
from typing import Optional, List, Dict, Type

from OpenSCENARIO2CR.ConversionAnalyzer.AnalysisResult import AnalysisResult
from OpenSCENARIO2CR.ConversionAnalyzer.Analyzer import Analyzer
from OpenSCENARIO2CR.ConversionAnalyzer.DriveAbilityChecker import DriveAbilityChecker, DriveAbilityCheckerResult
from OpenSCENARIO2CR.ConversionAnalyzer.ErrorAnalysisResult import ErrorAnalysisResult
from OpenSCENARIO2CR.ConversionAnalyzer.STLMonitor import STLMonitor, STLMonitorResult
from OpenSCENARIO2CR.EsminiWrapper.EsminiWrapper import ESimEndingCause

CR_MONITOR_TYPE = Optional[Dict[str, Optional[Dict[str, List[float]]]]]


class EAnalyzer(Enum):
    analyzer_type: Type[Analyzer]
    result_type: Type[AnalysisResult]

    def __new__(cls, analyzer_type: Type[Analyzer], result_type: Type[AnalysisResult]):
        obj = object.__new__(cls)
        obj._value_ = len(cls.__members__)
        obj.analyzer_type = analyzer_type
        obj.result_type = result_type
        return obj

    DRIVE_ABILITY_CHECKER = (DriveAbilityChecker, DriveAbilityCheckerResult)
    STL_MONITOR = (STLMonitor, STLMonitorResult)


@dataclass(frozen=True)
class ConversionStatistics(AnalysisResult):
    """

    """
    source_file: str
    database_file: Optional[str]
    num_obstacle_conversions: int
    failed_obstacle_conversions: List[str]
    ego_vehicle: str
    ego_vehicle_found_with_filter: bool
    ego_vehicle_removed: bool
    sim_ending_cause: ESimEndingCause
    sim_time: float
    analysis: Dict[EAnalyzer, Dict[str, AnalysisResult]]

    def __post_init__(self):
        for e_analyzer, values_per_car in self.analysis.items():
            for value in values_per_car.values():
                assert isinstance(value, (e_analyzer.result_type, ErrorAnalysisResult)), str(type(value))

    def to_dict(self) -> dict:
        ret = {}
        for attr_name, attr_value in vars(self).items():
            if attr_name == "sim_ending_cause":
                ret[attr_name] = attr_value.name
            elif attr_name == "analysis":
                ret[attr_name] = {}
                for e_analyzer, value in self.analysis.items():
                    ret[attr_name][e_analyzer.name] = {vehicle_name: v.to_dict() for vehicle_name, v in value.items()}
            else:
                ret[attr_name] = attr_value
        return ret

    @staticmethod
    def from_dict(data: dict) -> "ConversionStatistics":
        ret = {}
        for field in fields(ConversionStatistics):
            if field.name in data:
                value = data[field.name]
            else:
                value = None
            if field.name == "sim_ending_cause":
                ret[field.name] = ESimEndingCause[value]
            elif field.name == "analysis":
                ret[field.name] = {}
                if value is not None:
                    for analyzer_name, a_data in value.items():
                        e_analyzer = EAnalyzer[analyzer_name]
                        ret[field.name][e_analyzer] = {}
                        for vehicle_name, v_data in a_data.items():
                            if ErrorAnalysisResult.is_error(v_data):
                                ret[field.name][e_analyzer][vehicle_name] = ErrorAnalysisResult.from_dict(v_data)
                            else:
                                ret[field.name][e_analyzer][vehicle_name] = e_analyzer.result_type.from_dict(v_data)
            else:
                ret[field.name] = value
        return ConversionStatistics(**ret)
