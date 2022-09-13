from typing import Any, Optional


class Converter:
    def __init__(self):
        self.source_file = None

    def run_conversion(self) -> Any:
        raise NotImplementedError

    @property
    def source_file(self) -> Optional[str]:
        return self._source_file

    @source_file.setter
    def source_file(self, new_source_file: Optional[str]):
        self._source_file = new_source_file
        self._source_file_changed_callback()

    def _source_file_changed_callback(self):
        pass
