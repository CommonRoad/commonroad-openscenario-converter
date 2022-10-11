from typing import Generic, TypeVar

from commonroad.common.util import Interval, AngleInterval

T = TypeVar("T", Interval, AngleInterval, float, int)


class AbsRel(Generic[T]):

    def __init__(self, value: T, is_absolute: bool = False):
        self._interval = value
        self._is_absolute = is_absolute

    @property
    def value(self) -> T:
        return self._interval

    @property
    def is_absolute(self) -> bool:
        return self._is_absolute

    def as_summand(self, offset: float):
        if isinstance(self.value, Interval):
            if self.is_absolute:
                return type(self.value)(
                    start=self.value.start,
                    end=self.value.end
                )
            else:
                return type(self.value)(
                    start=self.value.start + offset,
                    end=self.value.end + offset
                )
        else:
            if self.is_absolute:
                return self.value
            else:
                return self.value + offset

    def as_factor(self, value):
        if isinstance(self.value, Interval):
            if self.is_absolute:
                return type(self.value)(
                    start=self.value.start,
                    end=self.value.end,
                )
            else:
                return type(self.value)(
                    start=self.value.start * value,
                    end=self.value.end * value,
                )
        else:
            if self.is_absolute:
                return self.value
            else:
                return self.value * value
