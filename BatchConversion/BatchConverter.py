import os
import pickle
import re
import warnings
from concurrent.futures import ProcessPoolExecutor, Future
from dataclasses import dataclass
from typing import Optional, Dict, List

from tqdm import tqdm

from BatchConversion.Converter import Converter
from BatchConversion.Serializable import Serializable
from OpenSCENARIO2CR.ConversionAnalyzer.AnalyzerErrorResult import AnalyzerErrorResult


@dataclass(frozen=True)
class BatchConversionResult(Serializable):
    exception: Optional[AnalyzerErrorResult]
    result_file: Optional[str]

    def __getstate__(self) -> Dict:
        return self.__dict__.copy()

    def __setstate__(self, data: Dict):
        self.__dict__.update(data)

    @staticmethod
    def from_result_file(result_file: str) -> "BatchConversionResult":
        return BatchConversionResult(
            exception=None,
            result_file=os.path.abspath(result_file)
        )

    @staticmethod
    def from_exception(e: Exception) -> "BatchConversionResult":
        return BatchConversionResult(
            exception=AnalyzerErrorResult.from_exception(e),
            result_file=None
        )

    def get_result(self) -> Serializable:
        assert self.without_exception
        with open(self.result_file, "rb") as file:
            return pickle.load(file)

    def __post_init__(self):
        assert self.exception is not None or self.result_file is not None

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

    def run_batch_conversion(self, num_worker: Optional[int], timeout: Optional[int] = None):
        assert Serializable.storage_dir is not None
        assert os.path.exists(Serializable.storage_dir)
        storage_dir = Serializable.storage_dir

        if not Serializable.store_extra_files:
            warnings.warn("Running Batch Conversion without storing extra files")
            input("Do you ")
        if num_worker <= 0:
            num_worker = os.cpu_count()
        with ProcessPoolExecutor(max_workers=num_worker) as pool:
            results_async: Dict[str, Future] = {
                file: pool.submit(BatchConverter._convert_single, file, self.converter)
                for file in sorted(set(self.file_list))
            }
            results = {}
            for file, result in tqdm(results_async.items()):
                try:
                    results[file] = result.result(timeout=timeout)
                except Exception as e:
                    results[file] = BatchConversionResult.from_exception(e)

        os.makedirs(storage_dir, exist_ok=True)
        with open(os.path.join(storage_dir, "statistics.pickle"), "wb") as file:
            Serializable.storage_dir = storage_dir
            pickle.dump(results, file)

    @staticmethod
    def _convert_single(file: str, converter: Converter) -> BatchConversionResult:
        return BatchConversionResult.from_result_file(
            converter.run_in_batch_conversion(file)
        )
