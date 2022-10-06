from typing import Tuple, List

from commonroad.scenario.obstacle import ObstacleType
from commonroad.scenario.trajectory import State


class SimScenarioObjectState:
    def get_timestamp(self) -> float:
        raise NotImplementedError

    def get_object_length(self) -> float:
        raise NotImplementedError

    def get_object_width(self) -> float:
        raise NotImplementedError

    def get_obstacle_type(self) -> ObstacleType:
        raise NotImplementedError


class ScenarioObjectState:
    _closest: Tuple[SimScenarioObjectState, SimScenarioObjectState]
    _timestamp: float
    _dt1: float
    _dt2: float

    def __init__(self, timestamp: float, closest_states: Tuple[SimScenarioObjectState, SimScenarioObjectState]):
        if abs(timestamp - closest_states[0].get_timestamp()) <= abs(timestamp - closest_states[1].get_timestamp()):
            self._closest = (closest_states[0], closest_states[1])
        else:
            self._closest = (closest_states[1], closest_states[0])

        self._timestamp = timestamp
        self._dt1 = self._closest[1].get_timestamp() - self._closest[0].get_timestamp()
        self._dt2 = self.timestamp - self._closest[0].get_timestamp()
        self._length = closest_states[0].get_object_length()
        self._width = closest_states[0].get_object_length()
        self._obstacle_type = closest_states[0].get_obstacle_type()

    @property
    def timestamp(self) -> float:
        return self._timestamp

    @property
    def length(self) -> float:
        return self._length

    @property
    def width(self) -> float:
        return self._width

    @property
    def obstacle_type(self) -> ObstacleType:
        return self._obstacle_type

    @staticmethod
    def build_interpolated(states: List[SimScenarioObjectState], timestamp: float) -> "ScenarioObjectState":
        """
        The build_interpolated function takes a list of states and a timestamp,
        and returns an interpolated state between the two closest states.


        :param states:List[SimScenarioObjectState]: All states as input
        :param timestamp:float: Specify the time at which the interpolated state should be created
        :return: The interpolated state of the object at a given timestamp
        """
        raise NotImplementedError

    def to_cr_state(self, time_step: int) -> State:
        """
        The to_cr_state function takes a time step and returns the corresponding CR state.
        The CR state is defined as a tuple of (time_step, number_of_cr).


        :param time_step:int: Passthrough for the commonroad state time_step
        :return: The state of the environment at time timestamp with attached to the time_step
        """
        raise NotImplementedError

    def _get_interpolated(self, field_name: str):
        """
        Interpolate the value of field_name between the two closest states
        """
        val0, val1, = (getattr(self._closest[0], field_name), getattr(self._closest[1], field_name))
        gradient = (val1 - val0) / self._dt1
        return val0 + gradient * self._dt2

    def _get_equal(self, field_name: str):
        """
        Assert that the values of field_name match in both closest states and return the value
        """
        val0, val1, = (getattr(self._closest[0], field_name), getattr(self._closest[1], field_name))
        if val0 != val1:
            raise ValueError("Failed interpolating new state, expected {}s to be equal: {}!={}"
                             .format(field_name, val0, val1))
        else:
            return val0

    def _get_closest(self, field_name: str):
        """
        Get the value of field_name of the closer of the two closest states
        """
        return getattr(self._closest[0], field_name)

    def _get_differentiate(self, field_name: str):
        """
        Get the rate of change of field_name between the two closest states
        """
        val0, val1, = (getattr(self._closest[0], field_name), getattr(self._closest[1], field_name))
        return (val1 - val0) / self._dt1
