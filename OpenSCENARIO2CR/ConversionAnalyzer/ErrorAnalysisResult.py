import traceback
from dataclasses import dataclass, fields
from typing import Dict

from OpenSCENARIO2CR.ConversionAnalyzer.AnalysisResult import AnalysisResult


@dataclass(frozen=True)
class ErrorAnalysisResult(AnalysisResult):
    exception_text: str
    traceback_text: str

    def to_dict(self) -> Dict:
        return {field.name: getattr(self, field.name) for field in fields(ErrorAnalysisResult)}

    @staticmethod
    def is_error(data: Dict) -> bool:
        expected_fields = fields(ErrorAnalysisResult)
        return len(data) == len(expected_fields) and all([field.name in data for field in expected_fields])

    @staticmethod
    def from_exception(e: Exception) -> "ErrorAnalysisResult":
        return ErrorAnalysisResult(
            exception_text=str(e),
            traceback_text=traceback.format_exc(limit=50)
        )

    @staticmethod
    def from_dict(data: Dict) -> "ErrorAnalysisResult":
        return ErrorAnalysisResult(
            **data
        )
