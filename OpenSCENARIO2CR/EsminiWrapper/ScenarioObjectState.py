import ctypes as ct
from typing import List, Optional


class ScenarioObjectState(ct.Structure):
    _fields_ = [
        ("id", ct.c_int),
        ("model_id", ct.c_int),
        ("control", ct.c_int),
        ("timestamp", ct.c_float),
        ("x", ct.c_float),
        ("y", ct.c_float),
        ("z", ct.c_float),
        ("h", ct.c_float),
        ("p", ct.c_float),
        ("r", ct.c_float),
        ("roadId", ct.c_int),
        ("junctionId", ct.c_int),
        ("t", ct.c_float),
        ("laneId", ct.c_int),
        ("laneOffset", ct.c_float),
        ("s", ct.c_float),
        ("speed", ct.c_float),
        ("centerOffsetX", ct.c_float),
        ("centerOffsetY", ct.c_float),
        ("centerOffsetZ", ct.c_float),
        ("width", ct.c_float),
        ("length", ct.c_float),
        ("height", ct.c_float),
        ("objectType", ct.c_int),
        ("objectCategory", ct.c_int),
    ]
    acceleration: Optional[float]
    h_rate: Optional[float]
    p_rate: Optional[float]
    r_rate: Optional[float]

    def __int__(self, *args, **kwargs):
        ct.Structure.__init__(self, *args, **kwargs)
        self.acceleration = None
        self.h_rate = None
        self.p_rate = None
        self.r_rate = None

    @staticmethod
    def build_interpolated(states: List["ScenarioObjectState"], timestamp: float) -> "ScenarioObjectState":
        if len(states) == 0:
            raise ValueError("len(states)==0 which is less than 1")
        interpolated = ScenarioObjectState()
        if len(states) == 1:
            ct.pointer(interpolated)[0] = states[0]
            interpolated.acceleration = 0
            interpolated.h_rate = 0
            interpolated.p_rate = 0
            interpolated.r_rate = 0
            return interpolated
        closest_states = sorted(states, key=lambda state: abs(timestamp - state.timestamp))[:2]
        dt1 = closest_states[1].timestamp - closest_states[0].timestamp
        dt2 = timestamp - closest_states[0].timestamp

        def interpolate(field_name: str):
            val0, val1, = (getattr(closest_states[0], field_name), getattr(closest_states[1], field_name))
            gradient = (val1 - val0) / dt1
            setattr(interpolated, field_name, val0 + gradient * dt2)

        def equal(field_name: str):
            val0, val1, = (getattr(closest_states[0], field_name), getattr(closest_states[1], field_name))
            if val0 != val1:
                raise ValueError("Failed interpolating new state, expected {}s to be equal: {}!={}"
                                 .format(field_name, val0, val1))
            else:
                setattr(interpolated, field_name, val0)

        def closest(field_name: str):
            setattr(interpolated, field_name, getattr(closest_states[0], field_name))

        def differentiate(source_field_name: str, target_field_name: str):
            val0, val1, = (getattr(closest_states[0], source_field_name), getattr(closest_states[1], source_field_name))
            gradient = (val1 - val0) / dt1
            setattr(interpolated, target_field_name, gradient)

        equal("id")
        equal("model_id")
        closest("control")
        interpolate("timestamp")
        interpolate("x")
        interpolate("y")
        interpolate("z")
        interpolate("h")
        interpolate("p")
        interpolate("r")
        closest("roadId")
        closest("junctionId")
        interpolate("t")
        closest("laneId")
        interpolate("laneOffset")
        interpolate("s")
        interpolate("speed")
        interpolate("centerOffsetX")
        interpolate("centerOffsetY")
        interpolate("centerOffsetZ")
        interpolate("width")
        interpolate("length")
        interpolate("height")
        equal("objectType")
        equal("objectCategory")

        differentiate("speed", "acceleration")
        differentiate("h", "h_rate")
        differentiate("p", "p_rate")
        differentiate("r", "r_rate")

        return interpolated
