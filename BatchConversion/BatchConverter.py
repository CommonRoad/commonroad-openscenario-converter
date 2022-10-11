import os
import re
from concurrent.futures import ProcessPoolExecutor, Future
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any, Dict, Union, List

from tqdm import tqdm

from BatchConversion.Converter import Converter
from OpenSCENARIO2CR.ConversionAnalyzer.AnalyzerErrorResult import AnalyzerErrorResult
from OpenSCENARIO2CR.util.Serializable import Serializable


@dataclass(frozen=True)
class BatchConversionResult(Serializable):
    exception: Optional[AnalyzerErrorResult]
    conversion_result: Union[None, Enum, Serializable]

    def __getstate__(self) -> Dict:
        return self.__dict__.copy()

    def __setstate__(self, data: Dict):
        self.__dict__.update(data)

    @staticmethod
    def from_conversion_result(conversion_result: Any) -> "BatchConversionResult":
        return BatchConversionResult(
            exception=None,
            conversion_result=conversion_result
        )

    @staticmethod
    def from_exception(e: Exception) -> "BatchConversionResult":
        return BatchConversionResult(
            exception=AnalyzerErrorResult.from_exception(e),
            conversion_result=None
        )

    def __post_init__(self):
        assert self.exception is not None or self.conversion_result is not None

    @property
    def without_exception(self) -> bool:
        return self.exception is None


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
            self.file_list = list()
        abs_directory = os.path.abspath(directory)
        for dir_path, dirs, files in os.walk(directory):
            if not recursively and os.path.abspath(dir_path) != abs_directory:
                continue
            for file in files:
                if file_matcher.match(file) is not None:
                    self.file_list.append(os.path.join(dir_path, file))

    def run_batch_conversion(self, num_worker: Optional[int] = 0, timeout: Optional[int] = None) \
            -> Dict[str, BatchConversionResult]:
        if num_worker <= 0:
            num_worker = os.cpu_count()
        with ProcessPoolExecutor(max_workers=num_worker) as pool:
            results_async: Dict[str, Future] = {
                file: pool.submit(BatchConverter._convert_single, file, self.converter)
                for file in sorted(set(self.file_list))
            }
            ret = {}
            for file, result in tqdm(results_async.items()):
                try:
                    ret[file] = result.result(timeout=timeout)
                except Exception as e:
                    ret[file] = BatchConversionResult.from_exception(e)
            return ret

    @staticmethod
    def _convert_single(file: str, converter: Converter) -> BatchConversionResult:
        return BatchConversionResult.from_conversion_result(
            converter.run_conversion(file)
        )
