__author__ = "Michael Ratzel, Yuanfei Lin"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["KoSi"]
__version__ = "0.0.1"
__maintainer__ = "Yuanfei Lin"
__email__ = "commonroad@lists.lrz.de"
__status__ = "Pre-alpha"

from abc import ABC
from dataclasses import dataclass

from osc_cr_converter.converter.serializable import Serializable


@dataclass(frozen=True)
class AnalyzerResult(Serializable, ABC):
    """
    Baseclass of any AnalyzerReuslt
    """
    pass
