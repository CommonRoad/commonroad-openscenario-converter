__author__ = "Michael Ratzel, Yuanfei Lin"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["KoSi"]
__version__ = "0.1.0"
__maintainer__ = "Yuanfei Lin"
__email__ = "commonroad@lists.lrz.de"
__status__ = "beta"

import ctypes as ct
from typing import Type

import numpy as np
from commonroad.scenario.obstacle import ObstacleType
from commonroad.scenario.state import CustomState

from osc_cr_converter.wrapper.base.scenario_object import (
    ScenarioObjectState,
    SimScenarioObjectState,
)


class SEStruct(ct.Structure, SimScenarioObjectState):
    """
    Implementation of the SimScenarioObjectState ABC. Objects of this will be recorded while running the simulation
    """

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
        ("wheel_rotation", ct.c_float),
    ]

    def get_scenario_object_state_type(self) -> "Type[ScenarioObjectState]":
        return EsminiScenarioObjectState

    def get_timestamp(self) -> float:
        return self.timestamp

    def get_object_length(self) -> float:
        return self.length

    def get_object_width(self) -> float:
        return self.width

    def get_obstacle_type(self) -> ObstacleType:
        """
        Mapping the obstacle type of OpenSCENARIO to the CommonRoad obstacle type. OSC has a two level system with
        objectType and objectCategory.
        """
        if self.objectType == 0:  # TYPE_NONE
            return ObstacleType.UNKNOWN
        elif self.objectType == 1:  # VEHICLE
            return {
                0: ObstacleType.CAR,  # CAR
                1: ObstacleType.CAR,  # VAN
                2: ObstacleType.TRUCK,  # TRUCK
                3: ObstacleType.TRUCK,  # SEMITRAILER
                4: ObstacleType.TRUCK,  # TRAILER
                5: ObstacleType.BUS,  # BUS
                6: ObstacleType.MOTORCYCLE,  # MOTORBIKE
                7: ObstacleType.BICYCLE,  # BICYCLE
                8: ObstacleType.TRAIN,  # TRAIN
                9: ObstacleType.TRAIN,  # TRAM
            }.get(self.objectCategory, ObstacleType.UNKNOWN)
        elif self.objectType == 2:  # PEDESTRIAN
            return ObstacleType.PEDESTRIAN  # PEDESTRIAN, WHEELCHAIR, ANIMAL
        elif self.objectType == 3:  # MISC_OBJECT
            return {
                0: ObstacleType.UNKNOWN,  # NONE
                1: ObstacleType.UNKNOWN,  # OBSTACLE
                2: ObstacleType.ROAD_BOUNDARY,  # POLE
                3: ObstacleType.UNKNOWN,  # TREE
                4: ObstacleType.UNKNOWN,  # VEGETATION
                5: ObstacleType.ROAD_BOUNDARY,  # BARRIER
                6: ObstacleType.BUILDING,  # BUILDING
                7: ObstacleType.UNKNOWN,  # PARKINGSPACE
                8: ObstacleType.CONSTRUCTION_ZONE,  # PATCH
                9: ObstacleType.ROAD_BOUNDARY,  # RAILING
                10: ObstacleType.MEDIAN_STRIP,  # TRAFFICISLAND
                11: ObstacleType.UNKNOWN,  # CROSSWALK
                12: ObstacleType.PILLAR,  # STREETLAMP
                13: ObstacleType.UNKNOWN,  # GANTRY
                14: ObstacleType.ROAD_BOUNDARY,  # SOUNDBARRIER
                15: ObstacleType.UNKNOWN,  # WIND
                16: ObstacleType.UNKNOWN,  # ROADMARK
            }.get(self.objectCategory, ObstacleType.UNKNOWN)
        elif self.objectType == 4:  # N_OBJECT_TYPES
            return ObstacleType.UNKNOWN


class EsminiScenarioObjectState(ScenarioObjectState):
    """
    Class that converts from SEStructs to CommonRoad states
    """

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
        return 0.0

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
    def height(self) -> float:
        if not hasattr(self, "_height"):
            self._height = self._get_interpolated("height")
        return self._height

    def to_cr_state(self, time_step: int) -> CustomState:
        c_h, s_h = np.cos(self.h), np.sin(self.h)  # heading
        c_p, s_p = np.cos(self.p), np.sin(self.p)  # pitch
        c_r, s_r = np.cos(self.r), np.sin(self.r)  # roll

        center = np.array((self.x, self.y, self.z))
        rotation_matrix = np.array(
            (
                (c_h * c_p, c_h * s_p * s_r - s_h * c_r, c_h * s_p * c_r + s_h * s_r),
                (s_h * c_p, s_h * s_p * s_r + c_h * c_r, s_h * s_p * s_r - c_h * s_r),
                (-s_p, c_p * s_r, c_p * c_r),
            )
        )
        offset = np.array(
            (
                self.center_offset_x,
                self.center_offset_y,
                self.center_offset_z,
            )
        )
        position_3d = center + np.matmul(rotation_matrix, offset)
        return CustomState(
            time_step=time_step,
            position=position_3d[0:2],
            orientation=self.h,
            velocity=self.speed,
            steering_angle=self.steering_angle,
            # position_z=position_3d[2],
            # acceleration=self.acceleration,
            # roll_angle=self.r,
            # pitch_angle=self.p,
            yaw_rate=self.h_rate,
            # roll_rate=self.r_rate,
            # pitch_rate=self.p_rate,
            slip_angle=self.slip_angle,
        )
