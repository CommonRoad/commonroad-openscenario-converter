import pickle
from abc import ABC, abstractmethod
from enum import Enum
from multiprocessing import Lock
from os import path
from typing import Union, ClassVar

from BatchConversion.Serializable import Serializable


class Converter(ABC):
    __lock: ClassVar[Lock] = Lock()

    def run_in_batch_conversion(self, source_file: str) -> str:
        with self.__lock:
            file_path_base = path.join(Serializable.storage_dir, "Res_", path.splitext(path.basename(source_file))[0])
            i = 1
            while path.exists(result_file := file_path_base + f"{i}.pickle"):
                i += 1
        with open(result_file, "wb") as file:
            pickle.dump(self.run_conversion(source_file), file)
        return result_file

    @abstractmethod
    def run_conversion(self, source_file: str) -> Union[Serializable, Enum]:
        raise NotImplementedError
