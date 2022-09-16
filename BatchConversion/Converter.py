from typing import Any


class Converter:
    @staticmethod
    def from_args(**kwargs) -> "Converter":
        raise NotImplementedError

    def run_conversion(self, source_file: str) -> Any:
        raise NotImplementedError
