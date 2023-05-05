from abc import ABC
from dataclasses import dataclass

from osc_cr_converter.converter.serializable import Serializable


@dataclass(frozen=True)
class AnalyzerResult(Serializable, ABC):
    """
    Baseclass of any AnalyzerReuslt
    """
    pass
