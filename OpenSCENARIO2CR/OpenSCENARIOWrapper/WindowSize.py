from dataclasses import dataclass


@dataclass(frozen=True)
class WindowSize:
    x: int = 0
    y: int = 0
    width: int = 640
    height: int = 480
