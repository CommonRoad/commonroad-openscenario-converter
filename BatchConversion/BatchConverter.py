import os
import re
import traceback
from typing import List

from tqdm import tqdm

from BatchConversion.Converter import Converter


class BatchConverter:

    def __init__(self, converter: Converter):
        self.file_list = []
        self.converter = converter

    @property
    def file_list(self) -> List[str]:
        return self._file_list

    @file_list.setter
    def file_list(self, new_file_list: List[str]):
        self._file_list = new_file_list

    @property
    def converter(self) -> Converter:
        return self._converter

    @converter.setter
    def converter(self, new_converter: Converter):
        self._converter = new_converter

    def discover_files(self, directory: str, file_matcher: re.Pattern, reset_file_list: bool = True,
                       recursively: bool = True):
        if reset_file_list:
            self.file_list = []
        abs_directory = os.path.abspath(directory)
        for dir_path, dirs, files in os.walk(directory):
            if not recursively and os.path.abspath(dir_path) != abs_directory:
                continue
            for file in files:
                if file_matcher.match(file) is not None:
                    self.file_list.append(os.path.join(dir_path, file))

    def run_batch_conversion(self):
        results = {}
        for file in (pbar := tqdm(sorted(self.file_list))):
            pbar.set_description(file)
            try:
                self.converter.source_file = file
                results[file] = (True, self.converter.run_conversion())
            except Exception as e:
                results[file] = (False, (str(e), traceback.format_exc()))
        return results
