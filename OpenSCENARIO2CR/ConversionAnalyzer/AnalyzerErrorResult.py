import traceback
from dataclasses import dataclass, fields
from typing import Dict

from OpenSCENARIO2CR.ConversionAnalyzer.AnalyzerResult import AnalyzerResult


@dataclass(frozen=True)
class AnalyzerErrorResult(AnalyzerResult):
    """
    A result containing a exception text and traceback
    """
    exception_text: str
    traceback_text: str

    def __getstate__(self) -> Dict:
        return self.__dict__.copy()

    def __setstate__(self, data: Dict):
        self.__dict__.update(data)

    def __str__(self):
        return f"{self.exception_text}\n{self.traceback_text}"

    @staticmethod
    def is_error(data: Dict) -> bool:
        expected_fields = fields(AnalyzerErrorResult)
        return len(data) == len(expected_fields) and all([field.name in data for field in expected_fields])

    @staticmethod
    def from_exception(e: Exception) -> "AnalyzerErrorResult":
        return AnalyzerErrorResult(
            exception_text=str(e),
            traceback_text=traceback.format_exc(limit=50)
        )
