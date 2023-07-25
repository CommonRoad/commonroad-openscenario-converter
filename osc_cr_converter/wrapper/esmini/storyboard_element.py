__author__ = "Michael Ratzel, Yuanfei Lin"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["KoSi"]
__version__ = "0.1.0"
__maintainer__ = "Yuanfei Lin"
__email__ = "commonroad@lists.lrz.de"
__status__ = "beta"

from dataclasses import dataclass
from enum import IntEnum


class EStoryBoardElementLevel(IntEnum):
    """
    Levels of the storyboard elements
    """

    STORY = 1
    ACT = 2
    MANEUVER_GROUP = 3
    MANEUVER = 4
    EVENT = 5
    ACTION = 6
    UNDEFINED_ELEMENT_TYPE = 0


class EStoryBoardElementState(IntEnum):
    """
    State of the storyboard elements
    """

    STANDBY = 1
    RUNNING = 2
    COMPLETE = 3
    UNDEFINED_ELEMENT_STATE = 0


@dataclass(frozen=True)
class StoryBoardElement:
    """
    A storyboard element
    """

    name: bytes
    element_type: EStoryBoardElementLevel

    def __eq__(self, o: object) -> bool:
        return (
            isinstance(o, StoryBoardElement)
            and self.name == o.name
            and self.element_type == o.element_type
        )
