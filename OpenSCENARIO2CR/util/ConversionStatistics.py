from dataclasses import dataclass, fields
from typing import Optional, List, Dict

from OpenSCENARIO2CR.ConversionAnalyzer.AnalysisResult import AnalysisResult
from OpenSCENARIO2CR.ConversionAnalyzer.EAnalyzer import EAnalyzer
from OpenSCENARIO2CR.ConversionAnalyzer.ErrorAnalysisResult import ErrorAnalysisResult
from OpenSCENARIO2CR.OpenSCENARIOWrapper.Esmini.EsminiWrapper import ESimEndingCause

CR_MONITOR_TYPE = Optional[Dict[str, Optional[Dict[str, List[float]]]]]


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
