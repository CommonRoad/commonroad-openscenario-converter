from typing import Generic, TypeVar

from commonroad.common.util import Interval, AngleInterval

T = TypeVar("T", Interval, AngleInterval)


class AbsRel(Generic[T]):

    def __init__(self, interval: T, is_absolute: bool = False):
        self._interval = interval
        self._is_absolute = is_absolute

    @property
    def interval(self) -> T:
        return self._interval

    @property
    def is_absolute(self) -> bool:
        return self._is_absolute

    def with_offset_if_relative(self, offset: float):
        if self.is_absolute:
            return type(self.interval)(
                start=self.interval.start,
                end=self.interval.end
            )
        else:
            return type(self.interval)(
                start=self.interval.start + offset,
                end=self.interval.end + offset
            )
