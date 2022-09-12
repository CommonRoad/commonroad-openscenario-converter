from dataclasses import dataclass
from typing import Optional, List


@dataclass(frozen=True)
class ConversionStatistics:
    """

    """
    source_file: str
    database_file: Optional[str]
    failed_obstacle_conversions: List[str]
    ego_vehicle: str
    ego_vehicle_found_with_filter: bool
    ego_obstacle_removed: bool
