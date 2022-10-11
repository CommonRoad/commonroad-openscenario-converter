from abc import ABC
from dataclasses import dataclass
from typing import Optional

from OpenSCENARIO2CR.util.Serializable import Serializable


@dataclass(frozen=True)
class AnalyzerResult(Serializable, ABC):
    calc_time: Optional[float]
