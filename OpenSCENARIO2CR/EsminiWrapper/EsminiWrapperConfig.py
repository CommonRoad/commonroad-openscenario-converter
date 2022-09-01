from dataclasses import dataclass
from typing import Optional

from OpenSCENARIO2CR.EsminiWrapper.StoryBoardElement import EStoryBoardElementType


@dataclass(frozen=True)
class ScenarioEndDetectionConfig:
    max_time: float
    grace_time: Optional[float] = None
    ignored_level: Optional[EStoryBoardElementType] = EStoryBoardElementType.ACT


@dataclass(frozen=True)
class WindowSize:
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class EsminiWrapperConfig:
    scenario_path: str
    end_detection: ScenarioEndDetectionConfig
    viewer_mode: int
    use_threading: bool
    random_seed: Optional[int] = None
    window_size: Optional[WindowSize] = None
