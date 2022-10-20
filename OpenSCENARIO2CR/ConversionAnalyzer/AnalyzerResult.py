from abc import ABC
from dataclasses import dataclass

from BatchConversion.Serializable import Serializable


@dataclass(frozen=True)
class AnalyzerResult(Serializable, ABC):
    pass
