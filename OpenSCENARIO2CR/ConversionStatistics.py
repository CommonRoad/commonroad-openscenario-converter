from dataclasses import dataclass
from typing import Optional, List, Dict

import numpy as np


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
    cr_monitor_analysis: Optional[Dict[str, Optional[np.ndarray]]]
