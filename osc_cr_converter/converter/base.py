__author__ = "Michael Ratzel, Yuanfei Lin"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["KoSi"]
__version__ = "0.1.0"
__maintainer__ = "Yuanfei Lin"
__email__ = "commonroad@lists.lrz.de"
__status__ = "beta"

import pickle
from abc import ABC, abstractmethod
from enum import Enum, auto
from multiprocessing import Lock
from os import path
from typing import Union, ClassVar

from commonroad.scenario.scenario import Scenario

from osc_cr_converter.converter.serializable import Serializable
from osc_cr_converter.converter.result import Osc2CrConverterResult


class EFailureReason(Enum):
    """
    The enum of reasons why the conversion failed
    """

    SCENARIO_FILE_INVALID_PATH = auto()
    SCENARIO_FILE_IS_CATALOG = auto()
    SCENARIO_FILE_IS_PARAMETER_VALUE_DISTRIBUTION = auto()
    SCENARIO_FILE_CONTAINS_NO_STORYBOARD = auto()
    SIMULATION_FAILED_CREATING_OUTPUT = auto()
    NO_DYNAMIC_BEHAVIOR_FOUND = auto()


class Converter(ABC):
    """
    The Base class for a converter

    It only needs to implement the run_conversion function
    """

    __lock: ClassVar[Lock] = Lock()
    conversion_result: Union[Osc2CrConverterResult, EFailureReason] = None

    def run_in_batch_conversion(self, source_file: str) -> str:
        with self.__lock:
            file_path_base = path.join(
                Serializable.storage_dir,
                "Res_" + path.splitext(path.basename(source_file))[0],
            )
            i = 1
            while path.exists(result_file := file_path_base + f"{i}.pickle"):
                i += 1
        self.run_conversion(source_file)
        with open(result_file, "wb") as file:
            pickle.dump(self.conversion_result, file)
        return result_file

    @abstractmethod
    def run_conversion(self, source_file: str) -> Union[Scenario, Enum]:
        """
        The main entry point of a converter. Implement this.
        """
        raise NotImplementedError
