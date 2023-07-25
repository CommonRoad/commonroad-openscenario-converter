__author__ = "Michael Ratzel, Yuanfei Lin"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["KoSi"]
__version__ = "0.1.0"
__maintainer__ = "Yuanfei Lin"
__email__ = "commonroad@lists.lrz.de"
__status__ = "beta"

from dataclasses import dataclass
from enum import Enum
from typing import Generic, TypeVar, ClassVar, Callable, Union

from commonroad.common.util import Interval, AngleInterval

T = TypeVar("T", Interval, AngleInterval, float, int)


@dataclass(frozen=True, init=False)
class AbsRel(Generic[T]):
    """
    A class used for configuration parameters storing absolute or relative values.
    If _value is used as a relative configuration value, one of the four elementary arithmetic operations is applied to
    it
    If _value is used as an absolute configuration value, it is returned without modification
    """

    __create_key: ClassVar[object] = object()
    _value: T
    _usage: "AbsRel.EUsage"

    def __init__(self, value: T, usage: "AbsRel.EUsage"):
        object.__setattr__(self, "_value", value)
        object.__setattr__(self, "_usage", usage)

    class EUsage(Enum):
        """
        Encapsulate the different usage modes of the AbsRel object
        """

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
        REL_SUB = lambda v, r: v - r
        REL_MUL = (lambda v, r: v * r,)
        REL_DIV = (lambda v, r: v / r,)

    def get(self, reference_value: float) -> T:
        """
        Applying the applicable usage formula and returning the reference value

        :param reference_value:float: The reference value this is relative to (if it is not an absolute AbsRel)
        :return: The modified _value if relative or _value if absolute
        """
        if isinstance(self._value, (Interval, AngleInterval)):
            return type(self._value)(
                start=self._usage.apply_value_to_reference(
                    self._value.start, reference_value
                ),
                end=self._usage.apply_value_to_reference(
                    self._value.end, reference_value
                ),
            )
        elif isinstance(self._value, (float, int)):
            return self._usage.apply_value_to_reference(self._value, reference_value)
