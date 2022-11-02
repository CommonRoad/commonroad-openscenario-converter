from enum import Enum, auto


class ESimEndingCause(Enum):
    """
    Enum containing reasons why the simulation ended
    """
    FAILURE = auto()
    MAX_TIME_REACHED = auto()
    END_DETECTED = auto()
    SCENARIO_FINISHED_BY_SIMULATOR = auto()
