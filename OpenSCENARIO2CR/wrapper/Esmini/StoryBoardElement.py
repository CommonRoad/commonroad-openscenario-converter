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
        return isinstance(o, StoryBoardElement) and self.name == o.name and self.element_type == o.element_type
