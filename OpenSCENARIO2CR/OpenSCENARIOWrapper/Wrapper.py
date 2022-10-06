import warnings
from typing import Optional

from commonroad.common.validity import is_real_number

from OpenSCENARIO2CR.OpenSCENARIOWrapper.WindowSize import WindowSize
from OpenSCENARIO2CR.OpenSCENARIOWrapper.WrapperSimResult import WrapperSimResult


class Wrapper:
    def __init__(self, max_time: Optional[float]):
        self.max_time = max_time

    @property
    def max_time(self) -> float:
        """
        The maximum simulation time, after this is reached the simulation is expected to be ended
        """
        return self._max_time

    @max_time.setter
    def max_time(self, new_max_time: Optional[float]):
        if new_max_time is None:
            self._max_time = 3600.0
        elif is_real_number(new_max_time):
            self._max_time = new_max_time
        else:
            warnings.warn(f"<EsminiWrapper/max_time> Tried to set to non real number value {new_max_time}.")

    def simulate_scenario(self, scenario_path: str, sim_dt: float) -> WrapperSimResult:
        """
        Simulate a scenario and return its results

        :param scenario_path Path to the .xosc scenario file
        :param sim_dt delta time used for the simulation
        :return The WrapperSimResult
        """
        raise NotImplementedError

    def view_scenario(self, scenario_path: str, window_size: Optional[WindowSize] = None):
        """
        Render a XOSC file

        :param scenario_path Path to the .xosc scenario file
        :param window_size Wanted size of the rendering window
        """
        pass

    def render_scenario_to_gif(self, scenario_path: str, gif_file_path: str, fps: int = 30,
                               gif_size: Optional[WindowSize] = None) -> bool:
        """
        Create a gif of an XOSC file.

        :param scenario_path Path to the .xosc scenario file
        :param gif_file_path Path to the .gif product
        :param fps Frames per second of the gif
        :param gif_size Size of the gif
        :return Returns if gif creation was successful
        """
        pass
