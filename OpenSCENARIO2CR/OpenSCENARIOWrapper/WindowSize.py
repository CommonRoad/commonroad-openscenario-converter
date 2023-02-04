from dataclasses import dataclass


@dataclass(frozen=True)
class WindowSize:
    """
    Utility class storing information about the size and position of a window
    """
    x: int = 0
    y: int = 0
    width: int = 640
    height: int = 480
