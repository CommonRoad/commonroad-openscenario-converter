import ctypes as ct
import logging
import math
import os.path
import re
import warnings
from dataclasses import dataclass
from enum import Enum, auto
from multiprocessing import Lock
from os import path
from sys import platform
from typing import Optional, List, Dict, Tuple, Union

import imageio
from commonroad.common.validity import is_real_number

from OpenSCENARIO2CR.EsminiWrapper.ScenarioObjectState import SEStruct
from OpenSCENARIO2CR.EsminiWrapper.StoryBoardElement import EStoryBoardElementState, EStoryBoardElementType, \
    StoryBoardElement


@dataclass(frozen=True)
class WindowSize:
    x: int = 0
    y: int = 0
    width: int = 640
    height: int = 480


class ESimEndingCause(Enum):
    NONE = auto()
    MAX_TIME = auto()
    DETECTED = auto()
    SCENARIO_FINISHED_BY_ESMINI = auto()


class EsminiWrapper:
    __lock: Lock = Lock()

    _all_sim_elements: Dict[StoryBoardElement, EStoryBoardElementState]

    _scenario_engine_initialized: bool
    _first_frame_run: bool

    _callback_functor: ct.CFUNCTYPE
    _sim_end_detected_time: Optional[float]

    def __init__(self, esmini_bin_path: str):
        self.esmini_lib = esmini_bin_path

        self.max_time = None
        self.grace_time = None
        self.ignored_level = None
        self.random_seed = None

        self.log_to_console = None
        self.log_to_file = None

        self._reset()

    @property
    def esmini_lib(self) -> ct.CDLL:
        return self._esmini_lib

    @esmini_lib.setter
    def esmini_lib(self, new_esmini_lib_bin_path: str):
        if hasattr(self, "_esmini_lib"):
            warnings.warn("<EsminiWrapper/esmini_lib> EsminiLib ctypes object is immutable")
        elif path.exists(new_esmini_lib_bin_path):
            if platform.startswith("linux"):
                self._esmini_lib = ct.CDLL(path.join(new_esmini_lib_bin_path, "libesminiLib.so"))
            elif platform.startswith("darwin"):
                self._esmini_lib = ct.CDLL(path.join(new_esmini_lib_bin_path, "libesminiLib.dylib"))
            elif platform.startswith("win32"):
                self._esmini_lib = ct.CDLL(path.join(new_esmini_lib_bin_path, "esminiLib.dll"))
            else:
                warnings.warn(f"<EsminiWrapper/esmini_lib> Unsupported platform: {platform}")
                return

            self._esmini_lib.SE_StepDT.argtypes = [ct.c_float]
            self._esmini_lib.SE_GetSimulationTime.restype = ct.c_float
            self._esmini_lib.SE_SetSeed.argtypes = [ct.c_uint]
            self._esmini_lib.SE_GetObjectName.restype = ct.c_char_p
        else:
            warnings.warn(f"<EsminiWrapper/esmini_lib> Path {new_esmini_lib_bin_path} does not exist")

    @property
    def max_time(self) -> float:
        return self._max_time

    @max_time.setter
    def max_time(self, new_max_time: Optional[float]):
        if new_max_time is None:
            self._max_time = 3600.0
        elif is_real_number(new_max_time):
            self._max_time = new_max_time
        else:
            warnings.warn(f"<EsminiWrapper/max_time> Tried to set to non real number value {new_max_time}.")

    @property
    def grace_time(self) -> Optional[float]:
        return self._grace_time

    @grace_time.setter
    def grace_time(self, new_grace_time: Optional[float]):
        if new_grace_time is None or is_real_number(new_grace_time):
            self._grace_time = new_grace_time
        else:
            warnings.warn(f"<EsminiWrapper/grace_time> Tried to set to non real number value {new_grace_time}.")

    @property
    def ignored_level(self) -> Optional[EStoryBoardElementType]:
        return self._ignored_level

    @ignored_level.setter
    def ignored_level(self, new_ignored_level: Optional[EStoryBoardElementType]):
        self._ignored_level = new_ignored_level

    @property
    def random_seed(self) -> int:
        return self._random_seed

    @random_seed.setter
    def random_seed(self, new_random_seed: Optional[int]):
        if new_random_seed is None:
            self._random_seed = 0
        else:
            self._random_seed = new_random_seed

    @property
    def log_to_console(self) -> bool:
        return self._log_to_console

    @log_to_console.setter
    def log_to_console(self, new_log_to_console: Optional[bool]):
        if new_log_to_console is None:
            self._log_to_console = True
        else:
            self._log_to_console = new_log_to_console

    @property
    def log_to_file(self) -> Optional[str]:
        return self._log_to_file

    @log_to_file.setter
    def log_to_file(self, new_log_to_file: Union[None, bool, str]):
        if new_log_to_file is None:
            self._log_to_file = None
        elif isinstance(new_log_to_file, bool):
            if new_log_to_file:
                self._log_to_file = path.abspath("log.txt")
                warnings.warn(f"Using default log file {self._log_to_file}")
            else:
                self._log_to_file = None
        elif path.exists(path.dirname(new_log_to_file)):
            self._log_to_file = path.abspath(new_log_to_file)
        else:
            warnings.warn(f"<EsminiWrapper/log_to_file> Logging dir {path.dirname(new_log_to_file)} does not exist.")

    @classmethod
    def __get_lock(cls):
        return cls.__lock

    def simulate_scenario(self, scenario_path: str, dt: float) \
            -> Tuple[Optional[Dict[str, List[SEStruct]]], float, Optional[ESimEndingCause]]:
        with self.__get_lock():
            if not self._initialize_scenario_engine(scenario_path, viewer_mode=0, use_threading=False):
                warnings.warn("<EsminiWrapper/simulate_scenario> Failed to initialize scenario engine")
                return None, 0.0, None
            sim_time = 0.0
            all_states: Dict[int, List[SEStruct]]
            all_states = {object_id: [state] for object_id, state in self._get_scenario_object_states().items()}
            while (cause := self._sim_finished()) == ESimEndingCause.NONE:
                self._sim_step(dt)
                sim_time += dt
                for object_id, new_state in self._get_scenario_object_states().items():
                    if object_id not in all_states:
                        all_states[object_id] = [new_state]
                    elif math.isclose(new_state.timestamp, all_states[object_id][-1].timestamp):
                        all_states[object_id][-1] = new_state
                    else:
                        all_states[object_id].append(new_state)

        return (
            {self._get_scenario_object_name(object_id): states for object_id, states in all_states.items()},
            sim_time,
            cause
        )

    def view_scenario(self, scenario_path: str, window_size: Optional[WindowSize] = None):
        with self.__get_lock():
            if not self._initialize_scenario_engine(scenario_path, viewer_mode=1, use_threading=True):
                warnings.warn("<EsminiWrapper/view_scenario> Failed to initialize scenario engine")
                return
            if window_size is not None:
                self._set_set_window_size(window_size)
            while self._sim_finished() == ESimEndingCause.NONE:
                self._sim_step(None)
            self._close_scenario_engine()

    def render_scenario_to_gif(self, scenario_path: str, gif_file_path: str, fps: int = 30,
                               window_size: Optional[WindowSize] = None) -> Optional[str]:
        with self.__get_lock():
            if not self._initialize_scenario_engine(scenario_path, viewer_mode=7, use_threading=False):
                warnings.warn("<EsminiWrapper/render_scenario_to_gif> Failed to initialize scenario engine")
                return None
            if window_size is not None:
                self._set_set_window_size(window_size)
            image_regex = re.compile(r"screen_shot_\d{5,}\.tga")
            ignored_images = set([p for p in os.listdir(".") if image_regex.match(p) is not None])
            while self._sim_finished() == ESimEndingCause.NONE:
                self._sim_step(1 / fps)
            self._close_scenario_engine()
            images = sorted(
                [p for p in os.listdir(".") if image_regex.match(p) is not None and p not in ignored_images])
            with imageio.get_writer(gif_file_path, mode="I", fps=fps) as writer:
                for image in images:
                    writer.append_data(imageio.v3.imread(image))
                    os.remove(image)

    def _reset(self):
        self._all_sim_elements = {}
        self._scenario_engine_initialized = False
        self._first_frame_run = False
        self._callback_functor = None
        self._sim_end_detected_time = None

    def _initialize_scenario_engine(self, scenario_path: str, viewer_mode: int, use_threading: bool) -> bool:
        self._reset()

        self.esmini_lib.SE_LogToConsole(self.log_to_console)
        if self.log_to_file is None:
            self.esmini_lib.SE_SetLogFilePath("".encode("ASCII"))
        else:
            self.esmini_lib.SE_SetLogFilePath(self.log_to_file.encode("ASCII"))

        ret = self.esmini_lib.SE_Init(
            scenario_path.encode("ASCII"),
            int(0),
            int(viewer_mode),
            int(use_threading),
            int(0)
        )
        if ret != 0:
            return False

        self.esmini_lib.SE_SetSeed(self.random_seed)

        self._callback_functor = ct.CFUNCTYPE(None, ct.c_char_p, ct.c_int, ct.c_int)(self.__state_change_callback)
        self.esmini_lib.SE_RegisterStoryBoardElementStateChangeCallback(self._callback_functor)
        self._scenario_engine_initialized = True
        return True

    def _set_set_window_size(self, window_size: WindowSize):
        self.esmini_lib.SE_SetWindowPosAndSize(window_size.x, window_size.y, window_size.width, window_size.height)

    def _close_scenario_engine(self):
        if not self._scenario_engine_initialized:
            raise RuntimeError("Scenario Engine not initialized")
        self.esmini_lib.SE_Close()
        self._scenario_engine_initialized = False

    def __state_change_callback(self, name: bytes, element_type: int, state: int):
        self._all_sim_elements[StoryBoardElement(name, EStoryBoardElementType(element_type))] = EStoryBoardElementState(
            state)

    def _sim_step(self, dt: Optional[float]):
        if not self._scenario_engine_initialized:
            raise RuntimeError("Scenario Engine not initialized")
        self._first_frame_run = True

        if dt is not None:
            assert self.esmini_lib.SE_StepDT(dt) == 0
        else:
            assert self.esmini_lib.SE_Step() == 0

    def _sim_finished(self) -> ESimEndingCause:
        if not self._scenario_engine_initialized:
            return ESimEndingCause.NONE
        if not self._first_frame_run:
            return ESimEndingCause.NONE
        now = self.esmini_lib.SE_GetSimulationTime()
        if self.esmini_lib.SE_GetQuitFlag() == 1:
            self._log("{:.3f}: Esmini requested quitting -> Scenario finished completely ".format(now))
            return ESimEndingCause.SCENARIO_FINISHED_BY_ESMINI
        if now >= self.max_time:
            self._log("{:.3f}: Max Execution tim reached ".format(now))
            return ESimEndingCause.MAX_TIME
        if self.grace_time is not None and self._all_sim_elements_finished():
            if self._sim_end_detected_time is None:
                self._sim_end_detected_time = now
            if now >= self._sim_end_detected_time + self.grace_time:
                self._log("{:.3f}: End detected {:.3f}s ago".format(now, self.grace_time))
                return ESimEndingCause.DETECTED
        else:
            self._sim_end_detected_time = None

        return ESimEndingCause.NONE

    def _all_sim_elements_finished(self) -> bool:
        all_relevant: List[EStoryBoardElementState]
        lvl = self.ignored_level
        if lvl is not None:
            all_relevant = [v for k, v in self._all_sim_elements.items() if k.element_type.value > lvl.value]
        else:
            all_relevant = list(self._all_sim_elements.values())
        return all([v is EStoryBoardElementState.COMPLETE for v in all_relevant])

    def _get_scenario_object_states(self) -> Optional[Dict[int, SEStruct]]:
        if not self._scenario_engine_initialized:
            raise RuntimeError("Scenario Engine not initialized")
        try:
            objects = {}
            for j in range(self.esmini_lib.SE_GetNumberOfObjects()):
                object_id = self.esmini_lib.SE_GetId(j)
                objects[object_id] = SEStruct()
                self.esmini_lib.SE_GetObjectState(object_id, ct.byref(objects[object_id]))

            return objects
        except Exception as e:
            logging.warning("Unexpected exception during scenario object extraction: {}".format(e))
            return None

    def _get_scenario_object_name(self, object_id: int) -> Optional[str]:
        raw_name: bytes = self.esmini_lib.SE_GetObjectName(object_id)
        return raw_name.decode("utf-8")

    def _log(self, text: str):
        if self.log_to_console:
            print(text)
