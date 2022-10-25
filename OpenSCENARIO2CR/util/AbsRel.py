from dataclasses import dataclass
from enum import Enum
from typing import Generic, TypeVar, ClassVar, Callable

from commonroad.common.util import Interval, AngleInterval

T = TypeVar("T", Interval, AngleInterval, float, int)


class EAbsRelUsage(Enum):
    apply_to_reference_value: Callable[[float, float], float]

    def __new__(cls, apply_to_reference_value: Callable[[float, float], float]):
        obj = object.__new__(cls)
        obj._value_ = len(cls.__members__)
        obj.apply_to_reference_value = apply_to_reference_value
        return obj

    ABSOLUTE = (lambda value, _: value,)
    IDENTITY = (lambda _, reference: reference,)
    ADDITION = (lambda value, reference: value + reference,)
    MULTIPLICATION = (lambda value, reference: value * reference,)


@dataclass(frozen=True, init=False)
class AbsRel(Generic[T]):
    __create_key: ClassVar[object] = object()
    _value: T
    _usage: EAbsRelUsage

    def __init__(self, create_key: object, value: T, usage: EAbsRelUsage):
        assert self.__create_key == create_key, "Create Objects via one of the static methods"
        object.__setattr__(self, "_value", value)
        object.__setattr__(self, "_usage", usage)

    @staticmethod
    def absolute(value: T):
        return AbsRel(AbsRel.__create_key, value, EAbsRelUsage.ABSOLUTE)

    @staticmethod
    def addition(value: T):
        return AbsRel(AbsRel.__create_key, value, EAbsRelUsage.ADDITION)

    @staticmethod
    def multiplication(value: T):
        return AbsRel(AbsRel.__create_key, value, EAbsRelUsage.MULTIPLICATION)

    def get(self, reference_value: float) -> T:
        if isinstance(self._value, (Interval, AngleInterval)):
            return type(self._value)(
                start=self._usage.apply_to_reference_value(self._value.start, reference_value),
                end=self._usage.apply_to_reference_value(self._value.end, reference_value),
            )
        elif isinstance(self._value, (float, int)):
            return self._usage.apply_to_reference_value(self._value, reference_value)
