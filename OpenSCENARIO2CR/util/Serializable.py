import base64
import pickle
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional, ClassVar

import numpy as np


@dataclass(frozen=True)
class Serializable(ABC):
    storage_dir: ClassVar[Optional[str]] = None
    store_extra_files: ClassVar[bool] = True
    import_extra_files: ClassVar[bool] = True

    @abstractmethod
    def __getstate__(self) -> Dict:
        raise NotImplementedError

    @abstractmethod
    def __setstate__(self, data: Dict):
        raise NotImplementedError

    @staticmethod
    def bytes_to_str(data: bytes) -> str:
        return base64.a85encode(data).decode("ASCII")

    @staticmethod
    def str_to_bytes(data: str) -> bytes:
        return base64.a85decode(data)

    @staticmethod
    def pickle_to_str(obj) -> Optional[str]:
        if obj is None:
            return None
        return Serializable.bytes_to_str(pickle.dumps(obj))

    @staticmethod
    def str_to_pickle(data: str):
        return pickle.loads(Serializable.str_to_bytes(data))

    @staticmethod
    def ndarray_to_str(ndarray: np.ndarray) -> str:
        return Serializable.bytes_to_str(ndarray.tobytes())

    @staticmethod
    def str_to_ndarray(data: str) -> np.ndarray:
        return np.frombuffer(Serializable.str_to_bytes(data))
