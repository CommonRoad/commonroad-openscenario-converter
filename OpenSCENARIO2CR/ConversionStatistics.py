from dataclasses import dataclass, fields
from typing import Optional, List, Dict

from OpenSCENARIO2CR.EsminiWrapper.EsminiWrapper import ESimEndingCause

CR_MONITOR_TYPE = Optional[Dict[str, Optional[Dict[str, List[float]]]]]


@dataclass(frozen=True)
class ConversionStatistics:
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
    cr_monitor_analysis: CR_MONITOR_TYPE

    def to_dict(self) -> dict:
        ret = {}
        for attr_name, attr_value in vars(self).items():
            if attr_name == "sim_ending_cause":
                ret[attr_name] = attr_value.name
            else:
                ret[attr_name] = attr_value
        return ret

    @staticmethod
    def from_dict(data: dict) -> "ConversionStatistics":
        ret = {}
        for field in fields(ConversionStatistics):
            value = data[field.name]
            if field.name == "sim_ending_cause":
                ret[field.name] = ESimEndingCause[value]
            else:
                ret[field.name] = value
        return ConversionStatistics(**ret)
