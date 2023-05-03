from dataclasses import dataclass
from typing import Optional, List, Dict

from OpenSCENARIO2CR.wrapper.esmini.esmini_wrapper import ESimEndingCause
from OpenSCENARIO2CR.converter.serializable import Serializable

CR_MONITOR_TYPE = Optional[Dict[str, Optional[Dict[str, List[float]]]]]


@dataclass(frozen=True)
class ConversionStatistics(Serializable):
    num_obstacle_conversions: int
    failed_obstacle_conversions: List[str]
    ego_vehicle: str
    ego_vehicle_found_with_filter: bool
    ego_vehicle_removed: bool
    sim_ending_cause: ESimEndingCause
    sim_time: float

    def __getstate__(self) -> dict:
        return self.__dict__.copy()

    def __setstate__(self, data: dict):
        self.__dict__.update(data)
