import ctypes
import logging
import os.path
from sys import platform
from typing import Optional, List


class SEScenarioObjectState(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_int),
        ("model_id", ctypes.c_int),
        ("control", ctypes.c_int),
        ("timestamp", ctypes.c_float),
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("z", ctypes.c_float),
        ("h", ctypes.c_float),
        ("p", ctypes.c_float),
        ("r", ctypes.c_float),
        ("roadId", ctypes.c_int),
        ("junctionId", ctypes.c_int),
        ("t", ctypes.c_float),
        ("laneId", ctypes.c_int),
        ("laneOffset", ctypes.c_float),
        ("s", ctypes.c_float),
        ("speed", ctypes.c_float),
        ("centerOffsetX", ctypes.c_float),
        ("centerOffsetY", ctypes.c_float),
        ("centerOffsetZ", ctypes.c_float),
        ("width", ctypes.c_float),
        ("length", ctypes.c_float),
        ("height", ctypes.c_float),
        ("objectType", ctypes.c_int),
        ("objectCategory", ctypes.c_int),
    ]


class EsminiWrapper:
    _esmini_lib: ctypes.CDLL
    _scenario_engine_initialized: bool

    def __init__(self, esmini_bin_path: str):
        self._esmini_lib = ctypes.CDLL(self._get_esmini_lib_path(esmini_bin_path))
        self._esmini_lib.SE_StepDT.argtypes = [ctypes.c_float]
        self._scenario_engine_initialized = False

    @staticmethod
    def _get_esmini_lib_path(esmini_bin_path: str):
        if platform == "linux" or platform == "linux2":
            return os.path.join(esmini_bin_path, "libesminiLib.so")
        elif platform == "darwin":
            return os.path.join(esmini_bin_path, "libesminiLib.dylib")
        elif platform == "win32":
            return os.path.join(esmini_bin_path, "esminiLib.dll")
        else:
            print("Unsupported platform: {}".format(platform))
            quit()

    def set_window_pos_and_size(self, x: int, y: int, width: int, height: int):
        if self._scenario_engine_initialized:
            raise RuntimeError("Scenario Engine already initialized")
        self._esmini_lib.SE_SetWindowPosAndSize(x, y, width, height)

    def initialize_scenario_engine(self, scenario_path: str, use_viewer: bool = False, record: bool = False) -> bool:
        ret = self._esmini_lib.SE_Init(
            scenario_path.encode("ASCII"),
            0,
            1 if use_viewer else 0,
            0,
            1 if record else 0
        )
        self._scenario_engine_initialized = ret == 0
        return self._scenario_engine_initialized

    def sim_finished(self) -> bool:
        finished_while_initialized = False
        return (not self._scenario_engine_initialized) or finished_while_initialized

    def sim_step(self, dt: Optional[float]):
        if not self._scenario_engine_initialized:
            raise RuntimeError("Scenario Engine not initialized")
        if dt is not None:
            self._esmini_lib.SE_StepDT(dt)
        self._esmini_lib.SE_Step()

    def get_scenario_object_states(self) -> Optional[List[SEScenarioObjectState]]:
        if not self._scenario_engine_initialized:
            raise RuntimeError("Scenario Engine not initialized")
        obj_state = SEScenarioObjectState()
        try:
            return [
                self._esmini_lib.SE_GetObjectState(self._esmini_lib.SE_GetId(j), ctypes.byref(obj_state))
                for j in range(self._esmini_lib.SE_GetNumberOfObjects())
            ]
        except Exception as e:
            logging.warning("Unexpected exception during scenario object extraction: {}".format(e))
            return None

    def close_scenario_engine(self):
        if not self._scenario_engine_initialized:
            raise RuntimeError("Scenario Engine not initialized")
        self._esmini_lib.SE_Close()
        self._scenario_engine_initialized = False
