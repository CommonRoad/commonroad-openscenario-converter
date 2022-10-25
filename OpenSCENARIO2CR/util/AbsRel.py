from dataclasses import dataclass
from enum import Enum
from typing import Generic, TypeVar, ClassVar, Callable, Union

from commonroad.common.util import Interval, AngleInterval

T = TypeVar("T", Interval, AngleInterval, float, int)


@dataclass(frozen=True, init=False)
class AbsRel(Generic[T]):
    __create_key: ClassVar[object] = object()
    _value: T
    _usage: "AbsRel.EUsage"

    def __init__(self, value: T, usage: "AbsRel.EUsage"):
        object.__setattr__(self, "_value", value)
        object.__setattr__(self, "_usage", usage)

    class EUsage(Enum):
        def apply_value_to_reference(self, value: Union[float, int], reference: float):
            if isinstance(value, int):
                return int(round(self.formula(float(value), reference)))
            elif isinstance(value, float):
                return self.formula(float(value), reference)
            else:
                raise ValueError

        formula: Callable[[float, float], float]

        def __new__(cls, apply_to_reference_value: Callable[[float, float], float]):
            obj = object.__new__(cls)
            obj._value_ = len(cls.__members__)
            obj.formula = apply_to_reference_value
            return obj

        ABS = (lambda v, _: v,)
        REL_ADD = (lambda v, r: v + r,)
        REL_SUB = (lambda v, r: v - r)
        REL_MUL = (lambda v, r: v * r,)
        REL_DIV = (lambda v, r: v / r,)

    def get(self, reference_value: float) -> T:
        if isinstance(self._value, (Interval, AngleInterval)):
            return type(self._value)(
                start=self._usage.apply_value_to_reference(self._value.start, reference_value),
                end=self._usage.apply_value_to_reference(self._value.end, reference_value),
            )
        elif isinstance(self._value, (float, int)):
            return self._usage.apply_value_to_reference(self._value, reference_value)
