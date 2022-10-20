from dataclasses import dataclass
from typing import Generic, TypeVar, ClassVar

from commonroad.common.util import Interval, AngleInterval

T = TypeVar("T", Interval, AngleInterval, float, int)


@dataclass(frozen=True, init=False)
class AbsRel(Generic[T]):
    __create_key: ClassVar[object] = object()
    value: T
    is_absolute: bool

    def __init__(self, create_key: object, value: T, is_absolute: bool = False):
        assert self.__create_key == create_key, "Create Objects via the absolute and relative function"
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "is_absolute", is_absolute)

    @staticmethod
    def absolute(value: T):
        return AbsRel(AbsRel.__create_key, value, is_absolute=True)

    @staticmethod
    def relative(value: T):
        return AbsRel(AbsRel.__create_key, value, is_absolute=False)

    def as_summand(self, offset: float) -> T:
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

    def as_factor(self, value) -> T:
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
