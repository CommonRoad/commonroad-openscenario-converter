__author__ = "Michael Ratzel, Yuanfei Lin"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["KoSi"]
__version__ = "0.1.0"
__maintainer__ = "Yuanfei Lin"
__email__ = "commonroad@lists.lrz.de"
__status__ = "beta"

import base64
import pickle
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional, ClassVar


@dataclass(frozen=True)
class Serializable(ABC):
    """
    The main interface to enforce that classes can be pickled.

    Also when unpickle any file implementing is assumed to contain a small amount of data, unless the
    import_extra_files field is set to True here
    """

    storage_dir: ClassVar[Optional[str]] = None
    import_extra_files: ClassVar[bool] = True

    @abstractmethod
    def __getstate__(self) -> Dict:
        raise NotImplementedError

    @abstractmethod
    def __setstate__(self, data: Dict):
        raise NotImplementedError

    @staticmethod
    def bytes_to_str(data: bytes) -> str:
        """
        Utility function to convert a bytes object into a base85 encoded string
        """
        return base64.a85encode(data).decode("ASCII")

    @staticmethod
    def str_to_bytes(data: str) -> bytes:
        """
        Utility function to convert a base85 encoded string into a bytes object
        """
        return base64.a85decode(data)

    @staticmethod
    def pickle_to_str(obj) -> Optional[str]:
        """
        Utility function to pickle an object and convert it into a base85 encoded string
        """
        if obj is None:
            return None
        return Serializable.bytes_to_str(pickle.dumps(obj))

    @staticmethod
    def str_to_pickle(data: str):
        """
        Utility function to convert a base85 encoded string into an object by unpickling
        """
        return pickle.loads(Serializable.str_to_bytes(data))
