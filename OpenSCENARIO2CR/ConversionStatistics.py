from dataclasses import dataclass, fields
from enum import Enum
from typing import Optional, List, Dict

import numpy as np

from OpenSCENARIO2CR.EsminiWrapper.EsminiWrapper import ESimEndingCause


@dataclass(frozen=True)
class ConversionStatistics:
    """

    """
    source_file: str
    database_file: Optional[str]
    failed_obstacle_conversions: List[str]
    ego_vehicle: str
    ego_vehicle_found_with_filter: bool
    ego_vehicle_removed: bool
    sim_ending_cause: ESimEndingCause
    sim_time: float
    cr_monitor_analysis: Optional[Dict[str, Optional[np.ndarray]]]

    def to_dict(self) -> dict:
        return {
            key: value if not issubclass(type(value), Enum) else value.name
            for key, value in vars(self).items()
        }

    @staticmethod
    def from_dict(data: dict) -> "ConversionStatistics":
        return ConversionStatistics(
            **{
                field.name: data[field.name]
                if not (isinstance(field.type, type) and issubclass(field.type, Enum))
                else field.type[data[field.name]]
                for field in fields(ConversionStatistics)
            }
        )
