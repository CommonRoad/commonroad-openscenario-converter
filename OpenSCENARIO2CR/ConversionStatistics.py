from dataclasses import dataclass
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
