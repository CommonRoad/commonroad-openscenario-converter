import ctypes as ct
from typing import List, Tuple

import numpy as np
from commonroad.scenario.trajectory import State


class SEStruct(ct.Structure):
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
        ("wheel_angle", ct.c_float),
        ("wheel_rotation", ct.c_float)
    ]


class ScenarioObjectState:
    _closest: Tuple[SEStruct, SEStruct]

    def __init__(self, timestamp: float, closest_states: Tuple[SEStruct, SEStruct]):
        if abs(timestamp - closest_states[0].timestamp) <= abs(timestamp - closest_states[1].timestamp):
            self._closest = (closest_states[0], closest_states[1])
        else:
            self._closest = (closest_states[1], closest_states[0])

        self._timestamp = timestamp
        self._dt1 = self._closest[1].timestamp - self._closest[0].timestamp
        self._dt2 = self.timestamp - self._closest[0].timestamp

    def _get_single(self, field_name: str):
        return getattr(self._closest, field_name)

    def _get_interpolated(self, field_name: str):
        val0, val1, = (getattr(self._closest[0], field_name), getattr(self._closest[1], field_name))
        gradient = (val1 - val0) / self._dt1
        return val0 + gradient * self._dt2

    def _get_equal(self, field_name: str):
        val0, val1, = (getattr(self._closest[0], field_name), getattr(self._closest[1], field_name))
        if val0 != val1:
            raise ValueError("Failed interpolating new state, expected {}s to be equal: {}!={}"
                             .format(field_name, val0, val1))
        else:
            return val0

    def _get_closest(self, field_name: str):
        return getattr(self._closest[0], field_name)

    def _get_differentiate(self, field_name: str):
        val0, val1, = (getattr(self._closest[0], field_name), getattr(self._closest[1], field_name))
        return (val1 - val0) / self._dt1

    @property
    def timestamp(self) -> float:
        return self._timestamp

    @property
    def id(self) -> int:
        if not hasattr(self, "_id"):
            self._id = self._get_equal("id")
        return self._id

    @property
    def model_id(self) -> int:
        if not hasattr(self, "_model_id"):
            self._model_id = self._get_equal("model_id")
        return self._model_id

    @property
    def control(self) -> int:
        if not hasattr(self, "_control"):
            self._control = self._get_closest("control")
        return self._control

    @property
    def object_type(self) -> int:
        if not hasattr(self, "_object_type"):
            self._object_type = self._get_equal("objectType")
        return self._object_type

    @property
    def object_category(self) -> int:
        if not hasattr(self, "_object_category"):
            self._object_category = self._get_equal("objectCategory")
        return self._object_category

    @property
    def x(self) -> float:
        if not hasattr(self, "_x"):
            self._x = self._get_interpolated("x")
        return self._x

    @property
    def y(self) -> float:
        if not hasattr(self, "_y"):
            self._y = self._get_interpolated("y")
        return self._y

    @property
    def z(self) -> float:
        if not hasattr(self, "_z"):
            self._z = self._get_interpolated("z")
        return self._z

    @property
    def speed(self) -> float:
        if not hasattr(self, "_speed"):
            self._speed = self._get_interpolated("speed")
        return self._speed

    @property
    def acceleration(self) -> float:
        if not hasattr(self, "_acceleration"):
            self._acceleration = self._get_differentiate("speed")
        return self._acceleration

    @property
    def h(self) -> float:
        if not hasattr(self, "_h"):
            self._h = self._get_interpolated("h")
        return self._h

    @property
    def p(self) -> float:
        if not hasattr(self, "_p"):
            self._p = self._get_interpolated("p")
        return self._p

    @property
    def r(self) -> float:
        if not hasattr(self, "_r"):
            self._r = self._get_interpolated("r")
        return self._r

    @property
    def h_rate(self) -> float:
        if not hasattr(self, "_h_rate"):
            self._h_rate = self._get_differentiate("h")
        return self._h_rate

    @property
    def p_rate(self) -> float:
        if not hasattr(self, "_p_rate"):
            self._p_rate = self._get_differentiate("p")
        return self._p_rate

    @property
    def r_rate(self) -> r:
        if not hasattr(self, "_r_rate"):
            self._r_rate = self._get_differentiate("r")
        return self._r_rate

    @property
    def steering_angle(self) -> float:
        if not hasattr(self, "_steering_angle"):
            self._steering_angle = self._get_interpolated("wheel_angle")
        return self._steering_angle

    @property
    def wheel_rotation(self) -> float:
        if not hasattr(self, "_wheel_rotation"):
            self._wheel_rotation = self._get_interpolated("wheel_rotation")
        return self._wheel_rotation

    @property
    def slip_angle(self) -> float:
        if not hasattr(self, "_slip_angle"):
            if np.isclose(self.speed, 0.0):
                self._slip_angle = 0.0
            else:
                slip_angle_x = np.arccos(self._get_differentiate("x") / self.speed) - self.h
                slip_angle_y = np.arcsin(self._get_differentiate("y") / self.speed) - self.h
                self._slip_angle = (slip_angle_x + slip_angle_y) / 2
        return self._slip_angle

    @property
    def road_id(self) -> int:
        if not hasattr(self, "_road_id"):
            self._road_id = self._get_closest("roadId")
        return self._road_id

    @property
    def junction_id(self) -> int:
        if not hasattr(self, "_junction_id"):
            self._junction_id = self._get_closest("junctionId")
        return self._junction_id

    @property
    def t(self) -> float:
        if not hasattr(self, "_t"):
            self._t = self._get_interpolated("t")
        return self._t

    @property
    def s(self) -> float:
        if not hasattr(self, "_s"):
            self._s = self._get_interpolated("s")
        return self._s

    @property
    def lane_id(self) -> int:
        if not hasattr(self, "_lane_id"):
            self._lane_id = self._get_interpolated("laneId")
        return self._lane_id

    @property
    def lane_offset(self) -> float:
        if not hasattr(self, "_lane_offset"):
            self._lane_offset = self._get_interpolated("laneOffset")
        return self._lane_offset

    @property
    def center_offset_x(self) -> float:
        if not hasattr(self, "_center_offset_x"):
            self._center_offset_x = self._get_interpolated("centerOffsetX")
        return self._center_offset_x

    @property
    def center_offset_y(self) -> float:
        if not hasattr(self, "_center_offset_y"):
            self._center_offset_y = self._get_interpolated("centerOffsetY")
        return self._center_offset_y

    @property
    def center_offset_z(self) -> float:
        if not hasattr(self, "_center_offset_z"):
            self._center_offset_z = self._get_interpolated("centerOffsetZ")
        return self._center_offset_z

    @property
    def width(self) -> float:
        if not hasattr(self, "_width"):
            self._width = self._get_interpolated("width")
        return self._width

    @property
    def length(self) -> float:
        if not hasattr(self, "_length"):
            self._length = self._get_interpolated("length")
        return self._length

    @property
    def height(self) -> float:
        if not hasattr(self, "_height"):
            self._height = self._get_interpolated("height")
        return self._height

    def to_cr_state(self, time_step: int) -> State:
        c_h, s_h = np.cos(self.h), np.sin(self.h)  # heading
        c_p, s_p = np.cos(self.p), np.sin(self.p)  # pitch
        c_r, s_r = np.cos(self.r), np.sin(self.r)  # roll

        center = np.array((
            self.x,
            self.y,
            self.z
        ))
        rotation_matrix = np.array((
            (c_h * c_p, c_h * s_p * s_r - s_h * c_r, c_h * s_p * c_r + s_h * s_r),
            (s_h * c_p, s_h * s_p * s_r + c_h * c_r, s_h * s_p * s_r - c_h * s_r),
            (-s_p, c_p * s_r, c_p * c_r),
        ))
        offset = np.array((
            self.center_offset_x,
            self.center_offset_y,
            self.center_offset_z,
        ))
        position_3d = center + np.matmul(rotation_matrix, offset)
        return State(
            time_step=time_step,
            position=position_3d[0:2],
            position_z=position_3d[2],
            velocity=self.speed,
            acceleration=self.acceleration,
            orientation=self.h,
            roll_angle=self.r,
            pitch_angle=self.p,
            yaw_rate=self.h_rate,
            roll_rate=self.r_rate,
            pitch_rate=self.p_rate,
            steering_angle=self.steering_angle,
            slip_angle=self.slip_angle,
        )

    @staticmethod
    def build_interpolated(states: List[SEStruct], timestamp: float) -> "ScenarioObjectState":
        assert len(states) > 0
        if len(states) == 1:
            return ScenarioObjectState.build_interpolated([states[0], states[0]], timestamp)
        sorted_states = sorted(states, key=lambda state: abs(timestamp - state.timestamp))[:2]
        return ScenarioObjectState(timestamp=timestamp, closest_states=(sorted_states[0], sorted_states[1]))

    @staticmethod
    def calc_slip_angle(steering_angle: float) -> float:
        raise NotImplementedError
