from abc import ABC
from dataclasses import dataclass

from OpenSCENARIO2CR.converter.serializable import Serializable


@dataclass(frozen=True)
class AnalyzerResult(Serializable, ABC):
    """
    Baseclass of any AnalyzerReuslt
    """
    pass
