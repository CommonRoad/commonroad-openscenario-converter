__author__ = "Michael Ratzel, Yuanfei Lin"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["KoSi"]
__version__ = "0.1.0"
__maintainer__ = "Yuanfei Lin"
__email__ = "commonroad@lists.lrz.de"
__status__ = "beta"

from enum import Enum, auto


class ESimEndingCause(Enum):
    """
    Enum containing reasons why the simulation ended
    """

    FAILURE = auto()
    MAX_TIME_REACHED = auto()
    END_DETECTED = auto()
    SCENARIO_FINISHED_BY_SIMULATOR = auto()
