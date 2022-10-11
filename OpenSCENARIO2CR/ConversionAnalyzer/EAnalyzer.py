from enum import Enum
from typing import Type

from OpenSCENARIO2CR.ConversionAnalyzer.Analyzer import Analyzer
from OpenSCENARIO2CR.ConversionAnalyzer.AnalyzerResult import AnalyzerResult
from OpenSCENARIO2CR.ConversionAnalyzer.DrivabilityChecker import DrivabilityChecker, DrivabilityCheckerResult
from OpenSCENARIO2CR.ConversionAnalyzer.STLMonitor import STLMonitorResult, STLMonitor
from OpenSCENARIO2CR.ConversionAnalyzer.SpotAnalyzer import SpotAnalyzerResult, SpotAnalyzer


class EAnalyzer(Enum):
    analyzer_type: Type[Analyzer]
    result_type: Type[AnalyzerResult]

    def __new__(cls, analyzer_type: Type[Analyzer], result_type: Type[AnalyzerResult]):
        obj = object.__new__(cls)
        obj._value_ = len(cls.__members__)
        obj.analyzer_type = analyzer_type
        obj.result_type = result_type
        return obj

    DRIVABILITY_CHECKER = (DrivabilityChecker, DrivabilityCheckerResult)
    STL_MONITOR = (STLMonitor, STLMonitorResult)
    SPOT_ANALYZER = (SpotAnalyzer, SpotAnalyzerResult)
