import ctypes as ct
import logging
import os.path
import re
from sys import platform
from typing import Optional, List, Dict, Tuple

import imageio

from OpenSCENARIO2CR.EsminiWrapper.EsminiWrapperConfig import EsminiWrapperConfig, ScenarioEndDetectionConfig, \
    WindowSize, LogConfig
from OpenSCENARIO2CR.EsminiWrapper.ScenarioObjectState import ScenarioObjectState
from OpenSCENARIO2CR.EsminiWrapper.StoryBoardElement import EStoryBoardElementState, EStoryBoardElementType, \
    StoryBoardElement


class EsminiWrapper:
    _esmini_lib: ct.CDLL

    _end_detection: Optional[ScenarioEndDetectionConfig]
    _all_sim_elements: Dict[StoryBoardElement, EStoryBoardElementState]

    _scenario_engine_initialized: bool
    _first_frame_run: bool
    _sim_end_detection_grace_period_reached: bool
    _max_time_reached: bool

    _callback_functor: ct.CFUNCTYPE
    _sim_end_detected_time: Optional[float]

    def __init__(self, esmini_bin_path: str):
        self._esmini_lib = ct.CDLL(self._get_esmini_lib_path(esmini_bin_path))
        self._esmini_lib.SE_StepDT.argtypes = [ct.c_float]
        self._esmini_lib.SE_GetSimulationTime.restype = ct.c_float
        self._esmini_lib.SE_SetSeed.argtypes = [ct.c_uint]
        self._esmini_lib.SE_GetObjectName.restype = ct.c_char_p

        self._reset()

    def simulate_scenario(
            self,
            scenario_path: str,
            dt: float,
            max_time: float = 3600.0,
            grace_time: Optional[float] = None,
            ignored_level: Optional[EStoryBoardElementType] = EStoryBoardElementType.ACT,
            random_seed: Optional[int] = None,
            log_config: LogConfig = LogConfig(),
    ) -> Tuple[Optional[Dict[str, List[ScenarioObjectState]]], float]:
        if not self._initialize_scenario_engine(
                EsminiWrapperConfig(
                    scenario_path=scenario_path,
                    end_detection=ScenarioEndDetectionConfig(
                        max_time=max_time,
                        grace_time=grace_time,
                        ignored_level=ignored_level
                    ),
                    viewer_mode=0,
                    use_threading=False,
                    log_config=log_config,
                    random_seed=random_seed,
                    window_size=None,
                )
        ):
            return None, 0.0
        sim_time = 0.0
        all_states: Dict[int, List[ScenarioObjectState]]
        all_states = {object_id: [state] for object_id, state in self._get_scenario_object_states().items()}
        while not self._sim_finished():
            self._sim_step(dt)
            sim_time += dt
            for object_id, new_state in self._get_scenario_object_states().items():
                all_states[object_id].append(new_state)

        return {self._get_scenario_object_name(object_id): states for object_id, states in all_states.items()}, sim_time

    def view_scenario(
            self,
            scenario_path: str,
            max_time: float = 3600.0,
            grace_time: Optional[float] = None,
            ignored_level: Optional[EStoryBoardElementType] = EStoryBoardElementType.ACT,
            random_seed: Optional[int] = None,
            window_size: Optional[WindowSize] = None,
            log_config: LogConfig = LogConfig(),
    ) -> None:
        if not self._initialize_scenario_engine(
                EsminiWrapperConfig(
                    scenario_path=scenario_path,
                    end_detection=ScenarioEndDetectionConfig(
                        max_time=max_time,
                        grace_time=grace_time,
                        ignored_level=ignored_level
                    ),
                    viewer_mode=1,
                    use_threading=True,
                    log_config=log_config,
                    random_seed=random_seed,
                    window_size=window_size,
                )
        ):
            return None
        while not self._sim_finished():
            self._sim_step(None)
        self._close_scenario_engine()

    def render_scenario_to_gif(
            self,
            scenario_path: str,
            gif_file_path: str,
            fps: int = 30,
            max_time: float = 3600.0,
            grace_time: Optional[float] = None,
            ignored_level: Optional[EStoryBoardElementType] = EStoryBoardElementType.ACT,
            random_seed: Optional[int] = None,
            window_size: Optional[WindowSize] = None,
            log_config: LogConfig = LogConfig(),
    ) -> Optional[str]:
        if not self._initialize_scenario_engine(
                EsminiWrapperConfig(
                    scenario_path=scenario_path,
                    end_detection=ScenarioEndDetectionConfig(
                        max_time=max_time,
                        grace_time=grace_time,
                        ignored_level=ignored_level
                    ),
                    viewer_mode=7,
                    use_threading=False,
                    log_config=log_config,
                    random_seed=random_seed,
                    window_size=window_size,
                )
        ):
            return None
        image_regex = re.compile(r"screen_shot_\d{5,}\.tga")
        ignored_images = set([p for p in os.listdir(".") if image_regex.match(p) is not None])
        while not self._sim_finished():
            self._sim_step(1 / fps)
        self._close_scenario_engine()
        images = sorted([p for p in os.listdir(".") if image_regex.match(p) is not None and p not in ignored_images])
        with imageio.get_writer(gif_file_path, mode="I", fps=fps) as writer:
            for image in images:
                writer.append_data(imageio.v3.imread(image))
                os.remove(image)

    def _reset(self):
        self._end_detection = None
        self._all_sim_elements = {}
        self._scenario_engine_initialized = False
        self._first_frame_run = False
        self._callback_functor = None
        self._sim_end_detected_time = None
        self._max_time_reached = False
        self._sim_end_detection_grace_period_reached = False

    def _initialize_scenario_engine(self, config: EsminiWrapperConfig) -> bool:
        self._reset()

        self._esmini_lib.SE_LogToConsole(config.log_config.to_console)
        log_file = config.log_config.to_file
        if isinstance(log_file, bool) and log_file is True:
            self._esmini_lib.SE_SetLogFilePath("log.txt".encode("ASCII"))
        elif isinstance(log_file, str):
            self._esmini_lib.SE_SetLogFilePath(config.log_config.to_file.encode("ASCII"))
        else:
            self._esmini_lib.SE_SetLogFilePath("".encode("ASCII"))

        ret = self._esmini_lib.SE_Init(
            config.scenario_path.encode("ASCII"),
            int(0),
            int(config.viewer_mode),
            int(config.use_threading),
            int(0)
        )
        if ret != 0:
            return False

        if config.random_seed is not None:
            self._esmini_lib.SE_SetSeed(config.random_seed)
        if config.window_size is not None:
            size = config.window_size
            self._esmini_lib.SE_SetWindowPosAndSize(size.x, size.y, size.width, size.height)

        self._callback_functor = ct.CFUNCTYPE(None, ct.c_char_p, ct.c_int, ct.c_int)(self.__state_change_callback)
        self._esmini_lib.SE_RegisterStoryBoardElementStateChangeCallback(self._callback_functor)
        self._scenario_engine_initialized = True
        self._end_detection = config.end_detection
        return True

    def _close_scenario_engine(self):
        if not self._scenario_engine_initialized:
            raise RuntimeError("Scenario Engine not initialized")
        self._esmini_lib.SE_Close()
        self._scenario_engine_initialized = False

    @staticmethod
    def _get_esmini_lib_path(esmini_bin_path: str):
        if platform.startswith("linux"):
            return os.path.join(esmini_bin_path, "libesminiLib.so")
        elif platform.startswith("darwin"):
            return os.path.join(esmini_bin_path, "libesminiLib.dylib")
        elif platform.startswith("win32"):
            return os.path.join(esmini_bin_path, "esminiLib.dll")
        else:
            print("Unsupported platform: {}".format(platform))
            quit()

    def __state_change_callback(self, name: bytes, element_type: int, state: int):
        self._all_sim_elements[StoryBoardElement(name, EStoryBoardElementType(element_type))] = EStoryBoardElementState(
            state)

    def _sim_step(self, dt: Optional[float]):
        if not self._scenario_engine_initialized:
            raise RuntimeError("Scenario Engine not initialized")
        self._first_frame_run = True

        if dt is not None:
            self._esmini_lib.SE_StepDT(dt)
        else:
            self._esmini_lib.SE_Step()

    def _sim_finished(self) -> bool:
        if not self._scenario_engine_initialized:
            return False
        if not self._first_frame_run:
            return False
        now = self._esmini_lib.SE_GetSimulationTime()
        if now >= self._end_detection.max_time:
            print("{:.3f}: Max Execution tim reached ".format(now))
            return True
        if self._all_sim_elements_finished():
            if self._end_detection.grace_time is None:
                print("{:.3f}: End detected now".format(now))
                return True

            if self._sim_end_detected_time is None:
                self._sim_end_detected_time = now
            if now >= self._sim_end_detected_time + self._end_detection.grace_time:
                print("{:.3f}: End detected {:.3f}s ago".format(now, self._end_detection.grace_time))
                return True
        else:
            self._sim_end_detected_time = None

        return False

    def _all_sim_elements_finished(self) -> bool:
        all_relevant: List[EStoryBoardElementState]
        lvl = self._end_detection.ignored_level
        if lvl is not None:
            all_relevant = [v for k, v in self._all_sim_elements.items() if k.element_type.value > lvl.value]
        else:
            all_relevant = list(self._all_sim_elements.values())
        return all([v is EStoryBoardElementState.COMPLETE for v in all_relevant])

    def _get_scenario_object_states(self) -> Optional[Dict[int, ScenarioObjectState]]:
        if not self._scenario_engine_initialized:
            raise RuntimeError("Scenario Engine not initialized")
        try:
            objects = {}
            for j in range(self._esmini_lib.SE_GetNumberOfObjects()):
                objects[j] = ScenarioObjectState()
                self._esmini_lib.SE_GetObjectState(self._esmini_lib.SE_GetId(j), ct.byref(objects[j]))

            return objects
        except Exception as e:
            logging.warning("Unexpected exception during scenario object extraction: {}".format(e))
            return None

    def _get_scenario_object_name(self, object_id: int) -> Optional[str]:
        raw_name: bytes = self._esmini_lib.SE_GetObjectName(object_id)
        return raw_name.decode("utf-8")
