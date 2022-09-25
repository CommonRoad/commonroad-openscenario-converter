import base64
from typing import Dict

import numpy as np


class AnalysisResult:
    def to_dict(self) -> Dict:
        raise NotImplementedError

    @staticmethod
    def from_dict(data: Dict) -> "AnalysisResult":
        raise NotImplementedError

    @staticmethod
    def ndarray_to_str(ndarray: np.ndarray) -> str:
        return base64.a85encode(ndarray.tobytes()).decode("ASCII")

    @staticmethod
    def str_to_ndarray(data: str) -> np.ndarray:
        return np.frombuffer(base64.a85decode(data))
