
import os
import re
import pickle
from datetime import datetime

from osc_cr_converter.utility.configuration import ConverterParams
from osc_cr_converter.converter.osc2cr import Osc2CrConverter
from osc_cr_converter.converter.serializable import Serializable
from osc_cr_converter.batch.converter import BatchConverter
from osc_cr_converter.batch.analysis import analyze_results, plot_scenarios

# directory of the scenario to be batch-processed
directory = os.path.dirname(os.path.realpath(__file__)) + '/../scenarios/'
output_dir = os.path.dirname(os.path.realpath(__file__)) + '/../output/batch/'

# initialize the converter
config = ConverterParams()
converter = Osc2CrConverter(config)
batch_converter = BatchConverter(converter)

# discover the files
batch_converter.discover_files(directory, re.compile(r".*\.xosc", re.IGNORECASE), recursively=True)

# specify the storage dictionary
storage_dir = output_dir + "{}".format(datetime.now().isoformat(sep="_", timespec="seconds"))
os.makedirs(storage_dir, exist_ok=True)
Serializable.storage_dir = storage_dir

# run batch conversion
batch_converter.run_batch_conversion(num_worker=1)

# obtain the statistic
with open(os.path.join(storage_dir, "statistics.pickle"), "rb") as stats_file:
    # We don't need the scenario files for this analysis, just slows us down
    Serializable.import_extra_files = False
    all_results = pickle.load(stats_file)

results_to_analyze = all_results

conversions_to_analyze = {
    scenario_path: result.get_result() for scenario_path, result in all_results.items() if result.without_exception
}

# analyse the result
analyze_results(results_to_analyze)

