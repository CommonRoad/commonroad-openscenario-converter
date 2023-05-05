from enum import Enum
from typing import Type

from osc_cr_converter.analyzer.base import Analyzer
from osc_cr_converter.analyzer.result import AnalyzerResult


class EAnalyzer(Enum):
    analyzer_type: Type[Analyzer]
    result_type: Type[AnalyzerResult]

    def __new__(cls, analyzer_type: Type[Analyzer], result_type: Type[AnalyzerResult]):
        obj = object.__new__(cls)
        obj._value_ = len(cls.__members__)
        obj.analyzer_type = analyzer_type
        obj.result_type = result_type
        return obj

