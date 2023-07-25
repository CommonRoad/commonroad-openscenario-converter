__author__ = "Michael Ratzel, Yuanfei Lin"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["KoSi"]
__version__ = "0.1.0"
__maintainer__ = "Yuanfei Lin"
__email__ = "commonroad@lists.lrz.de"
__status__ = "beta"

import ctypes as ct
import logging
import math
import os.path
import re
import time
import warnings
from multiprocessing import Lock
from os import path
from sys import platform
from typing import Optional, List, Dict, Union

import imageio

from osc_cr_converter.wrapper.base.ending_cause import ESimEndingCause
from osc_cr_converter.wrapper.esmini.esmini_scenario_object import SEStruct
from osc_cr_converter.wrapper.esmini.storyboard_element import (
    EStoryBoardElementState,
    EStoryBoardElementLevel,
    StoryBoardElement,
)
from osc_cr_converter.wrapper.base.sim_wrapper import SimWrapper, WrapperSimResult
from osc_cr_converter.utility.configuration import ConverterParams, EsminiParams


class EsminiWrapper(SimWrapper):
    """
    The implementation of the SimWrapper to simulate, render to gif, and view scenarios in a window based in the
    Environment Simulator Minimalistic (esmini).

    Due to the possible usage of udp sockets this wrapper will only run sequential which is enforced by the __lock.
    """

    __lock: Lock = Lock()

    _all_sim_elements: Dict[StoryBoardElement, EStoryBoardElementState]

    _scenario_engine_initialized: bool
    _first_frame_run: bool

    _callback_functor: ct.CFUNCTYPE
    _sim_end_detected_time: Optional[float]

    def __init__(self, esmini_bin_path: str, config: ConverterParams):
        super().__init__(config=config)
        self._esmini_lib_bin_path = esmini_bin_path

        self.min_time = config.esmini.min_time
        self.random_seed = config.esmini.random_seed

        self.log_to_console = config.esmini.log_to_console
        self.log_to_file = config.esmini.log_to_file

        self._reset()

    @property
    def min_time(self) -> float:
        """
        Minimum simulation time.
        """
        return self._min_time

    @min_time.setter
    def min_time(self, new_min_time: Optional[float]):
        if new_min_time is None:
            self._min_time = 0.0
        else:
            self._min_time = new_min_time

    @property
    def esmini_lib(self) -> ct.CDLL:
        """
        The ctypes wrapper of the esmini lib.
        The object will be created by setting the esmini_lib_bin_path property
        """
        return self._esmini_lib

    @property
    def _esmini_lib_bin_path(self) -> str:
        """
        Path to the esmini lib bin directory path: "path/to/esmini/bin"
        """
        return self._esmini_lib_bin_path_

    @_esmini_lib_bin_path.setter
    def _esmini_lib_bin_path(self, new_esmini_lib_bin_path: str):
        if hasattr(self, "_esmini_lib"):
            warnings.warn(
                "<EsminiWrapper/esmini_lib> EsminiLib ctypes object is immutable"
            )
        elif path.exists(new_esmini_lib_bin_path):
            self._esmini_lib_bin_path_ = new_esmini_lib_bin_path
            if platform.startswith("linux"):
                self._esmini_lib = ct.CDLL(
                    path.join(new_esmini_lib_bin_path, "libesminiLib.so")
                )
            elif platform.startswith("darwin"):
                self._esmini_lib = ct.CDLL(
                    path.join(new_esmini_lib_bin_path, "libesminiLib.dylib")
                )
            elif platform.startswith("win32"):
                self._esmini_lib = ct.CDLL(
                    path.join(new_esmini_lib_bin_path, "esminiLib.dll")
                )
            else:
                warnings.warn(
                    f"<EsminiWrapper/esmini_lib> Unsupported platform: {platform}"
                )
                return

            self._esmini_lib.SE_StepDT.argtypes = [ct.c_float]
            self._esmini_lib.SE_GetSimulationTime.restype = ct.c_float
            self._esmini_lib.SE_SetSeed.argtypes = [ct.c_uint]
            self._esmini_lib.SE_GetObjectName.restype = ct.c_char_p

        else:
            warnings.warn(
                f"<EsminiWrapper/esmini_lib> Path {new_esmini_lib_bin_path} does not exist"
            )

    @property
    def random_seed(self) -> int:
        """
        Run the simulation using this random seed, default is 0
        """
        return self._random_seed

    @random_seed.setter
    def random_seed(self, new_random_seed: Optional[int]):
        if new_random_seed is None:
            self._random_seed = 0
        else:
            self._random_seed = new_random_seed

    @property
    def log_to_console(self) -> bool:
        """
        If true esmini will log to console
        """
        return self._log_to_console

    @log_to_console.setter
    def log_to_console(self, new_log_to_console: Optional[bool]):
        if new_log_to_console is None:
            self._log_to_console = True
        else:
            self._log_to_console = new_log_to_console

    @property
    def log_to_file(self) -> Optional[str]:
        """
        If true esmini will log to file
        """
        return self._log_to_file

    @log_to_file.setter
    def log_to_file(self, new_log_to_file: Union[None, bool, str]):
        if new_log_to_file is None:
            self._log_to_file = None
        elif isinstance(new_log_to_file, bool):
            if new_log_to_file:
                log_dir = (
                    os.path.dirname(os.path.realpath(__file__)) + "/../../../output/log"
                )
                os.makedirs(
                    log_dir, exist_ok=True
                )  # create directory if it doesn't exist
                self._log_to_file = os.path.join(
                    self.config.general.path_output_log,
                    f"esmini_{self.config.general.string_date_time}.log",
                )
            else:
                self._log_to_file = None

    def __getstate__(self):
        state = self.__dict__.copy()
        del state["_esmini_lib"]

        del state["_all_sim_elements"]
        del state["_scenario_engine_initialized"]
        del state["_first_frame_run"]
        del state["_callback_functor"]
        del state["_sim_end_detected_time"]
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._esmini_lib_bin_path = state["_esmini_lib_bin_path_"]
        self._reset()

    def simulate_scenario(self, scenario_path: str, sim_dt: float) -> WrapperSimResult:
        with EsminiWrapper.__lock:
            if not self._initialize_scenario_engine(
                scenario_path, viewer_mode=0, use_threading=False
            ):
                warnings.warn(
                    "<EsminiWrapper/simulate_scenario> Failed to initialize scenario engine"
                )
                return WrapperSimResult.failure()
            sim_time = 0.0
            runtime_start = time.time()
            all_states: Dict[int, List[SEStruct]]
            all_states = {
                object_id: [state]
                for object_id, state in self._get_scenario_object_states().items()
            }
            while (cause := self._sim_finished()) is None:
                self._sim_step(sim_dt)
                sim_time += sim_dt
                for object_id, new_state in self._get_scenario_object_states().items():
                    if object_id not in all_states:
                        all_states[object_id] = [new_state]
                    elif math.isclose(
                        new_state.timestamp, all_states[object_id][-1].timestamp
                    ):
                        all_states[object_id][-1] = new_state
                    else:
                        all_states[object_id].append(new_state)
            runtime = time.time() - runtime_start
            return WrapperSimResult(
                states={
                    self._get_scenario_object_name(object_id): states
                    for object_id, states in all_states.items()
                },
                sim_time=sim_time,
                runtime=runtime,
                ending_cause=cause,
            )

    def view_scenario(
        self, scenario_path: str, window_size: Optional[EsminiParams.WindowSize] = None
    ):
        with EsminiWrapper.__lock:
            if not self._initialize_scenario_engine(
                scenario_path, viewer_mode=1, use_threading=True
            ):
                warnings.warn(
                    "<EsminiWrapper/view_scenario> Failed to initialize scenario engine"
                )
                return
            if window_size is not None:
                self._set_set_window_size(window_size)
            while self._sim_finished() is None:
                self._sim_step(None)
            self._close_scenario_engine()

    def render_scenario_to_gif(
        self,
        scenario_path: str,
        gif_file_path: str,
        fps: int = 30,
        window_size: Optional[EsminiParams.WindowSize] = None,
    ) -> bool:
        with EsminiWrapper.__lock:
            if not self._initialize_scenario_engine(
                scenario_path, viewer_mode=7, use_threading=False
            ):
                warnings.warn(
                    "<EsminiWrapper/render_scenario_to_gif> Failed to initialize scenario engine"
                )
                return False
            if window_size is not None:
                self._set_set_window_size(window_size)
            image_regex = re.compile(r"screen_shot_\d{5,}\.tga")
            ignored_images = set(
                [p for p in os.listdir(".") if image_regex.match(p) is not None]
            )
            while self._sim_finished() is None:
                self._sim_step(1 / fps)
            self._close_scenario_engine()
            images = sorted(
                [
                    p
                    for p in os.listdir(".")
                    if image_regex.match(p) is not None and p not in ignored_images
                ]
            )
            with imageio.get_writer(gif_file_path, mode="I", fps=fps) as writer:
                for image in images:
                    writer.append_data(imageio.v3.imread(image))
                    os.remove(image)
            return True

    def _reset(self):
        self._all_sim_elements = {}
        self._scenario_engine_initialized = False
        self._first_frame_run = False
        self._callback_functor = None
        self._sim_end_detected_time = None

    def _initialize_scenario_engine(
        self, scenario_path: str, viewer_mode: int, use_threading: bool
    ) -> bool:
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
            int(0),
        )
        if ret != 0:
            return False

        self.esmini_lib.SE_SetSeed(self.random_seed)

        self.esmini_lib.SE_OpenOSISocket("127.0.0.1")

        self._callback_functor = ct.CFUNCTYPE(None, ct.c_char_p, ct.c_int, ct.c_int)(
            self.__state_change_callback
        )
        self.esmini_lib.SE_RegisterStoryBoardElementStateChangeCallback(
            self._callback_functor
        )
        self._scenario_engine_initialized = True
        return True

    def _set_set_window_size(self, window_size: EsminiParams.WindowSize):
        self.esmini_lib.SE_SetWindowPosAndSize(
            window_size.x, window_size.y, window_size.width, window_size.height
        )

    def _close_scenario_engine(self):
        if not self._scenario_engine_initialized:
            raise RuntimeError("Scenario Engine not initialized")
        self.esmini_lib.SE_Close()
        self._scenario_engine_initialized = False

    def __state_change_callback(self, name: bytes, element_type: int, state: int):
        self._all_sim_elements[
            StoryBoardElement(name, EStoryBoardElementLevel(element_type))
        ] = EStoryBoardElementState(state)

    def _sim_step(self, dt: Optional[float]):
        if not self._scenario_engine_initialized:
            raise RuntimeError("Scenario Engine not initialized")
        self._first_frame_run = True

        if dt is not None:
            assert self.esmini_lib.SE_StepDT(dt) == 0
        else:
            assert self.esmini_lib.SE_Step() == 0

    def _sim_finished(self) -> Optional[ESimEndingCause]:
        if not self._scenario_engine_initialized:
            return None
        if not self._first_frame_run:
            return None
        now = self.esmini_lib.SE_GetSimulationTime()
        if self.esmini_lib.SE_GetQuitFlag() == 1:
            self._log(
                "{:.3f}: esmini requested quitting -> Scenario finished completely ".format(
                    now
                )
            )
            return ESimEndingCause.SCENARIO_FINISHED_BY_SIMULATOR
        if now >= self.max_time:
            self._log("{:.3f}: Max Execution time reached ".format(now))
            return ESimEndingCause.MAX_TIME_REACHED
        return None

    def _get_scenario_object_states(self) -> Optional[Dict[int, SEStruct]]:
        if not self._scenario_engine_initialized:
            raise RuntimeError("Scenario Engine not initialized")
        try:
            objects = {}
            for j in range(self.esmini_lib.SE_GetNumberOfObjects()):
                object_id = self.esmini_lib.SE_GetId(j)
                objects[object_id] = SEStruct()
                self.esmini_lib.SE_GetObjectState(
                    object_id, ct.byref(objects[object_id])
                )

            return objects
        except Exception as e:
            logging.warning(
                "Unexpected exception during scenario object extraction: {}".format(e)
            )
            return None

    def _get_scenario_object_name(self, object_id: int) -> Optional[str]:
        raw_name: bytes = self.esmini_lib.SE_GetObjectName(object_id)
        return f"no-name-{object_id}" if raw_name is None else raw_name.decode("utf-8")

    def _log(self, text: str):
        if self.log_to_console:
            print(text)
