import os
import re
from datetime import datetime
from os import path

from commonroad.common.util import Interval
from commonroad.scenario.scenario import Tag

from BatchConversion.BatchConverter import BatchConverter
from BatchConversion.Serializable import Serializable
from OpenSCENARIO2CR.OpenSCENARIOWrapper.Esmini.EsminiWrapperProvider import EsminiWrapperProvider
from OpenSCENARIO2CR.OpenSCENARIOWrapper.Esmini.StoryBoardElement import EStoryBoardElementLevel
from OpenSCENARIO2CR.Osc2CrConverter import Osc2CrConverter
from OpenSCENARIO2CR.util.AbsRel import AbsRel
from OpenSCENARIO2CR.util.PPSBuilder import PPSBuilder

esmini_wrapper = EsminiWrapperProvider().provide_esmini_wrapper()
esmini_wrapper.min_time = 5
esmini_wrapper.max_time = 120.0
esmini_wrapper.grace_period = 1
esmini_wrapper.ignored_level = EStoryBoardElementLevel.ACT
esmini_wrapper.log_to_console = False
esmini_wrapper.log_to_file = False
esmini_wrapper.random_seed = 0

pps_builder = PPSBuilder()
pps_builder.time_interval = AbsRel(Interval(-10, 0), AbsRel.EUsage.REL_ADD)
pps_builder.pos_length = AbsRel(50, AbsRel.EUsage.ABS)
pps_builder.pos_width = AbsRel(10, AbsRel.EUsage.ABS)
pps_builder.pos_rotation = AbsRel(0, AbsRel.EUsage.REL_ADD)
pps_builder.pos_center_x = AbsRel(0, AbsRel.EUsage.REL_ADD)
pps_builder.pos_center_y = AbsRel(0, AbsRel.EUsage.REL_ADD)
pps_builder.velocity_interval = AbsRel(Interval(-5, 5), AbsRel.EUsage.REL_ADD)
pps_builder.orientation_interval = None


converter = Osc2CrConverter(
    author="ADD AUTHOR HERE",
    affiliation="ADD AFFILIATION HERE",
    source="ADD SOURCE HERE",
    tags={Tag.SIMULATED},
)

# directory = '/home/yuanfei/commonroad2/openscenario_files/esmini-master'
# openscenario-v1.1.1
directory = '/home/yuanfei/commonroad2/openscenario_files/OSC-ALKS-scenarios'
converter.sim_wrapper = esmini_wrapper
converter.pps_builder = pps_builder

converter.dt_cr = 0.1
converter.keep_ego_vehicle = True
converter.trim_scenario = False
converter.use_implicit_odr_file = True
converter.analyzers = {
}
# If you only want to run with default parameters for analyzers you can also use:
# converter.analyzers = [EAnalyzer.SPOT_ANALYZER, EAnalyzer.DRIVABILITY_CHECKER, EAnalyzer.STL_MONITOR]

converter.dt_sim = 0.01
converter.odr_file_override = None
converter.ego_filter = re.compile(r".*ego.*", re.IGNORECASE)

batch_converter = BatchConverter(converter)

batch_converter.discover_files(directory, re.compile(r".*\.xosc", re.IGNORECASE), recursively=True)

storage_dir = "results/{}".format(datetime.now().isoformat(sep="_", timespec="seconds"))
os.makedirs(storage_dir, exist_ok=True)
Serializable.storage_dir = storage_dir

batch_converter.run_batch_conversion(num_worker=0)
print(f"Finished and stored results in {path.abspath(storage_dir)}")