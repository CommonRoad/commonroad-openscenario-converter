__author__ = "Michael Ratzel, Yuanfei Lin"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["KoSi"]
__version__ = "0.0.1"
__maintainer__ = "Yuanfei Lin"
__email__ = "commonroad@lists.lrz.de"
__status__ = "Pre-alpha"

import pickle
from abc import ABC, abstractmethod
from enum import Enum
from multiprocessing import Lock
from os import path
from typing import Union, ClassVar

from osc_cr_converter.converter.serializable import Serializable


class Converter(ABC):
    """
    The Base class for a converter

    It only needs to implement the run_conversion function
    """
    __lock: ClassVar[Lock] = Lock()
    conversion_result = None

    def run_in_batch_conversion(self, source_file: str) -> str:
        with self.__lock:
            file_path_base = path.join(Serializable.storage_dir, "Res_" + path.splitext(path.basename(source_file))[0])
            i = 1
            while path.exists(result_file := file_path_base + f"{i}.pickle"):
                i += 1
        self.run_conversion(source_file)
        with open(result_file, "wb") as file:
            pickle.dump(self.conversion_result, file)
        return result_file

    @abstractmethod
    def run_conversion(self, source_file: str) -> Union[Serializable, Enum]:
        """
        The main entry point of a converter. Implement this.
        """
        raise NotImplementedError
