__author__ = "Michael Ratzel, Yuanfei Lin"
__copyright__ = "TUM Cyber-Physical Systems Group"
__credits__ = ["KoSi"]
__version__ = "0.1.0"
__maintainer__ = "Yuanfei Lin"
__email__ = "commonroad@lists.lrz.de"
__status__ = "beta"

import dataclasses
import inspect
from dataclasses import dataclass, field
from typing import Union, Any, Dict, List, Optional
from datetime import datetime
import pathlib
import re
import os
import logging
from omegaconf import OmegaConf

from commonroad.scenario.scenario import Tag
from commonroad.common.util import Interval

from osc_cr_converter.utility.pps_builder import PPSBuilder
from osc_cr_converter.utility.abs_rel import AbsRel


def _dict_to_params(dict_params: Dict[str, Any], cls: Any) -> Any:
    """
    Converts dictionary to parameter class.

    :param dict_params: Dictionary containing parameters.
    :param cls: Parameter dataclass to which dictionary should be converted to.
    :return: Parameter class.
    """
    fields = dataclasses.fields(cls)
    cls_map = {f.name: f.type for f in fields}
    kwargs = {}
    for k, v in cls_map.items():
        if k not in dict_params:
            continue
        if inspect.isclass(v) and issubclass(v, BaseParam):
            kwargs[k] = _dict_to_params(dict_params[k], cls_map[k])
        else:
            kwargs[k] = dict_params[k]
    return cls(**kwargs)


@dataclass
class BaseParam:
    """Converter base parameters."""

    __initialized: bool = field(init=False, default=False, repr=False)

    def __post_init__(self):
        """Post initialization of base parameter class."""
        # pylint: disable=unused-private-member
        self.__initialized = True
        # Make sure that the base parameters are propagated to all sub-parameters
        # This cannot be done in the init method, because the sub-parameters are not yet initialized.
        # This is not a noop, as it calls the __setattr__ method.
        # Do not remove!
        # See commonroad-io how to set the base parameters

    def __getitem__(self, item: str) -> Any:
        """
        Getter for base parameter value.

        :param: Item for which content should be returned.
        :return: Item value.
        """
        try:
            value = self.__getattribute__(item)
        except AttributeError as e:
            raise KeyError(
                f"{item} is not a parameter of {self.__class__.__name__}"
            ) from e
        return value

    def __setitem__(self, key: str, value: Any):
        """
        Setter for item.

        :param key: Name of item.
        :param value: Value of item.
        """
        try:
            self.__setattr__(key, value)
        except AttributeError as e:
            raise KeyError(
                f"{key} is not a parameter of {self.__class__.__name__}"
            ) from e

    @classmethod
    def load(
        cls, file_path: Union[pathlib.Path, str], validate_types: bool = True
    ) -> "ConverterParams":
        """
        Loads config file and creates parameter class.

        :param file_path: Path to yaml file containing config parameters.
        :param validate_types: overwrite the default params
        :return: Base parameter class.
        """
        file_path = pathlib.Path(file_path)
        assert (
            file_path.suffix == ".yaml"
        ), f"File type {file_path.suffix} is unsupported! Please use .yaml!"
        loaded_yaml = OmegaConf.load(file_path)
        if validate_types:
            OmegaConf.merge(OmegaConf.structured(ConverterParams), loaded_yaml)
        params = _dict_to_params(OmegaConf.to_object(loaded_yaml), cls)
        return params


@dataclass
class GeneralParams(BaseParam):
    """Parameters specifying the general setup"""

    # path of the root
    # name of the OpenSCENARIO file and its path
    name_xosc: str = ""

    # path for the output files
    path_output_abs: str = (
        os.path.normpath(os.path.join(os.path.dirname(__file__), "../..")) + "/output/"
    )
    # path for logging information
    path_output_log: str = path_output_abs + "log/"
    string_date_time = datetime.now().strftime("%Y_%m_%d_%H-%M-%S")

    def __init__(self):
        super().__init__()
        os.makedirs(self.path_output_abs, exist_ok=True)

    @property
    def path_output(self):
        path_output = self.path_output_abs + self.name_xosc + "/"
        os.makedirs(path_output, exist_ok=True)
        return path_output


@dataclass
class DebugParams(BaseParam):
    """Parameters specifying debug-related information"""

    # show esmini simulation
    run_viewer: bool = False
    # convert the figures to gif
    render_to_gif: bool = False
    # write the scenario to xml file
    write_to_xml: bool = False

    # plotting limits for axis
    plot_limit: Union[List[Union[int, float]], None] = None
    # with which time steps
    time_steps: Union[List[int], None] = None

    # logging level
    logging_level: str = logging.INFO


@dataclass
class EsminiParams(BaseParam):
    """Parameters specifying the esmini settings"""

    @dataclass(frozen=True)
    class WindowSize:
        """
        Utility class storing information about the size and position of a window
        """

        x: int = 0
        y: int = 0
        width: int = 640
        height: int = 480

    # version
    version: str = "default"  # we use v2.29.3 as default version

    # lower and upper time limits for the simulation duration
    min_time: float = 5.0
    max_time: float = 60.0

    # logging information
    log_to_console: bool = False
    log_to_file: bool = True

    # run the simulation using this random seed
    random_seed: int = 0

    # simulation time step size
    dt_sim: float = 0.01

    # use the associated OpenDRIVE map
    use_implicit_odr_file: bool = True
    odr_file_override: Optional[str] = None

    # filter to select the ego vehicle
    ego_filter: str = re.compile(r".*ego.*", re.IGNORECASE)

    window_size: WindowSize = WindowSize()


@dataclass
class ScenarioParams(BaseParam):
    """Parameters specifying the scenario settings"""

    # header information of the scenario
    author: str = " "
    affiliation: str = "Technical University of Munich"
    source: str = "OpenSCENARIO"
    tags = {Tag.SIMULATED}

    # scenario information
    # CommonRoad time step size
    dt_cr: float = 0.1
    keep_ego_vehicle: bool = True
    # trim the map based on the vehicle information
    trim_scenario: bool = False
    # default config & pred for specifying the scenario name:
    config: str = "1"  # 1-9
    pred: str = "1"


@dataclass
class ConverterParams(BaseParam):
    """Configuration parameters for OpenSCENARIO2CommonRoad converter."""

    general: GeneralParams = field(default_factory=GeneralParams)
    debug: DebugParams = field(default_factory=DebugParams)
    esmini: EsminiParams = field(default_factory=EsminiParams)
    scenario: ScenarioParams = field(default_factory=ScenarioParams)

    @staticmethod
    def initialize_planning_problem_set():
        planning_problem_set = PPSBuilder()
        planning_problem_set.time_interval = AbsRel(
            Interval(-10, 0), AbsRel.EUsage.REL_ADD
        )
        planning_problem_set.pos_length = AbsRel(50, AbsRel.EUsage.ABS)
        planning_problem_set.pos_width = AbsRel(10, AbsRel.EUsage.ABS)
        planning_problem_set.pos_rotation = AbsRel(0, AbsRel.EUsage.REL_ADD)
        planning_problem_set.pos_center_x = AbsRel(0, AbsRel.EUsage.REL_ADD)
        planning_problem_set.pos_center_y = AbsRel(0, AbsRel.EUsage.REL_ADD)
        planning_problem_set.velocity_interval = AbsRel(
            Interval(-5, 5), AbsRel.EUsage.REL_ADD
        )
        planning_problem_set.orientation_interval = None
        return planning_problem_set
