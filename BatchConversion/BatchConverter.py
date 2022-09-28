import os
import re
from dataclasses import dataclass
from multiprocessing import Pool
from typing import Set, Optional, Any, Dict, Type

from tqdm import tqdm

from BatchConversion.Converter import Converter
from OpenSCENARIO2CR.ConversionAnalyzer.ErrorAnalysisResult import ErrorAnalysisResult


@dataclass(frozen=True)
class BatchConversionResult:
    exception: Optional[ErrorAnalysisResult]
    conversion_result: Optional[Any]

    @staticmethod
    def from_conversion_result(conversion_result: Any) -> "BatchConversionResult":
        return BatchConversionResult(
            exception=None,
            conversion_result=conversion_result
        )

    @staticmethod
    def from_exception(e: Exception) -> "BatchConversionResult":
        return BatchConversionResult(
            exception=ErrorAnalysisResult.from_exception(e),
            conversion_result=None
        )

    def __post_init__(self):
        assert self.exception is not None or self.conversion_result is not None

    @property
    def without_exception(self) -> bool:
        return self.exception is None


class BatchConverter:

    def __init__(self, converter_class: Type[Converter], **converter_kwargs):
        self.file_list = []
        self.converter_class = converter_class
        self.converter_kwargs = converter_kwargs

    @property
    def file_list(self) -> Set[str]:
        return self._file_list

    @file_list.setter
    def file_list(self, new_file_list: Set[str]):
        self._file_list = new_file_list

    @property
    def converter_class(self) -> Type[Converter]:
        return self._converter_class

    @converter_class.setter
    def converter_class(self, new_converter_class: Type[Converter]):
        self._converter_class = new_converter_class

    @property
    def converter_kwargs(self) -> Dict:
        return self._converter_kwargs

    @converter_kwargs.setter
    def converter_kwargs(self, new_converter_kwargs: Dict):
        self._converter_kwargs = new_converter_kwargs

    def discover_files(self, directory: str, file_matcher: re.Pattern, reset_file_list: bool = True,
                       recursively: bool = True):
        if reset_file_list:
            self.file_list = set()
        abs_directory = os.path.abspath(directory)
        for dir_path, dirs, files in os.walk(directory):
            if not recursively and os.path.abspath(dir_path) != abs_directory:
                continue
            for file in files:
                if file_matcher.match(file) is not None:
                    self.file_list.add(os.path.join(dir_path, file))

    def run_batch_conversion(self, num_worker: Optional[int] = None, timeout: Optional[int] = None) \
            -> Dict[str, BatchConversionResult]:
        if num_worker is None:
            return self._run_batch_conversion_squential()
        else:
            return self._run_batch_conversion_parallel(num_worker, timeout)

    def _run_batch_conversion_squential(self) -> Dict[str, BatchConversionResult]:
        results: Dict[str, BatchConversionResult] = {}
        for file in (pbar := tqdm(sorted(self.file_list))):
            pbar.set_description(file)
            results[file] = self._convert_single(file, self.converter_class, self.converter_kwargs)
        return results

    def _run_batch_conversion_parallel(self, num_worker: int, timeout: Optional[int]) \
            -> Dict[str, BatchConversionResult]:
        if num_worker <= 0:
            num_worker = os.cpu_count()
        with Pool(processes=num_worker) as pool:
            results_async = {
                file: pool.apply_async(
                    BatchConverter._convert_single, (file, self.converter_class, self.converter_kwargs)
                )
                for file in self.file_list
            }
            return {file: result.get(timeout=timeout) for file, result in tqdm(results_async.items())}

    @staticmethod
    def _convert_single(file: str, converter_class: Type[Converter], converter_kwargs: Dict) -> BatchConversionResult:
        try:
            return BatchConversionResult.from_conversion_result(
                converter_class.from_args(**converter_kwargs).run_conversion(file)
            )
        except Exception as e:
            return BatchConversionResult.from_exception(e)
