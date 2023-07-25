__author__ = "Michael Ratzel, Yuanfei Lin"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["KoSi"]
__version__ = "0.1.0"
__maintainer__ = "Yuanfei Lin"
__email__ = "commonroad@lists.lrz.de"
__status__ = "beta"

import os
import pickle
import re
from concurrent.futures import ProcessPoolExecutor, Future
from dataclasses import dataclass
from typing import Optional, Dict, List

from tqdm import tqdm

from osc_cr_converter.converter.base import Converter
from osc_cr_converter.converter.serializable import Serializable
from osc_cr_converter.analyzer.error import AnalyzerErrorResult


@dataclass(frozen=True)
class BatchConversionResult(Serializable):
    """
    Contains either an AnalyzerErrorResult, or the path to an file, where the pickled result of the converter run is
    stored
    """

    exception: Optional[AnalyzerErrorResult]
    result_file: Optional[str]

    def __post_init__(self):
        """
        Enforcing that exactly one of the two parameters is set
        """
        assert (
            self.exception is not None
            or self.result_file is not None
            and (self.exception is None or self.result_file is None)
        )

    def __getstate__(self) -> Dict:
        return self.__dict__.copy()

    def __setstate__(self, data: Dict):
        self.__dict__.update(data)

    @staticmethod
    def from_result_file(result_file: str) -> "BatchConversionResult":
        return BatchConversionResult(
            exception=None, result_file=os.path.abspath(result_file)
        )

    @staticmethod
    def from_exception(e: Exception) -> "BatchConversionResult":
        return BatchConversionResult(
            exception=AnalyzerErrorResult.from_exception(e), result_file=None
        )

    def get_result(self) -> Serializable:
        """
        Load the result of the conversion run from disk
        Use this to actually access the data, but it might take a bit of time depending on the conversion run
        """
        assert self.without_exception
        with open(self.result_file, "rb") as file:
            return pickle.load(file)

    @property
    def without_exception(self) -> bool:
        return self.exception is None


class BatchConverter:
    """
    A utility class enabling to run a Converter object on a batch of data on multiple processors in parallel
    """

    def __init__(self, converter: Converter):
        self.file_list = []
        self.converter = converter

    @property
    def file_list(self) -> List[str]:
        """
        The file_list the converter will run on
        """
        return self._file_list

    @file_list.setter
    def file_list(self, new_file_list: List[str]):
        self._file_list = new_file_list

    @property
    def converter(self) -> Converter:
        """
        The converter that will be used on the batch
        """
        return self._converter

    @converter.setter
    def converter(self, new_converter: Converter):
        self._converter = new_converter

    def discover_files(
        self,
        directory: str,
        file_matcher: re.Pattern,
        reset_file_list: bool = True,
        recursively: bool = True,
    ):
        """
        Utility method to search a repository and discover files, that can be run in the batch conversion.

        The results will be added to the file_list attribute of the object

        :param directory:str: The directory where to start the search
        :param file_matcher:re.Pattern: A regular expression to filter the files in the directory
        :param reset_file_list:bool: If true clean the file_list attribute of the object, if False append to it
        :param recursively:bool: If true search recursively starting at the directory
        """
        if reset_file_list:
            self.file_list = list()
        abs_directory = os.path.abspath(directory)
        for dir_path, dirs, files in os.walk(directory):
            if not recursively and os.path.abspath(dir_path) != abs_directory:
                continue
            for file in files:
                if file_matcher.match(file) is not None:
                    self.file_list.append(os.path.join(dir_path, file))

    def run_batch_conversion(
        self, num_worker: Optional[int] = None, timeout: Optional[int] = None
    ):
        """
        Run the batch conversion

        :param num_worker:int: If None or leq than 0, it will default to all available processors
        :timeout:int: If present a single conversion run will time out if this amount of seconds passed
        """
        assert Serializable.storage_dir is not None
        assert os.path.exists(Serializable.storage_dir)
        storage_dir = Serializable.storage_dir

        if num_worker <= 0:
            num_worker = None
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
