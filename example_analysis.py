import pickle
from os import path


from BatchConversion.AnalysisFunctions import analyze_results, print_exception_tracebacks_for_analyzer, \
    print_exception_tracebacks, plot_sim_times, plot_exec_times, plot_num_obstacles, plot_scenarios, print_exception_tracebacks

from BatchConversion.Serializable import Serializable
from OpenSCENARIO2CR.analyzer.DrivabilityAnalyzer import DrivabilityAnalyzer
from OpenSCENARIO2CR.analyzer.STLAnalyzer import STLAnalyzer
from OpenSCENARIO2CR.analyzer.SpotAnalyzer import SpotAnalyzer

stats_dir = "./results/2023-04-24_11:22:47"
do_plot_scenarios = True

with open(path.join(stats_dir, "statistics.pickle"), "rb") as stats_file:
    # We don't need the scenario files for this analysis, just slows us down
    Serializable.import_extra_files = False
    all_results = pickle.load(stats_file)

results_to_analyze = all_results

conversions_to_analyze = {
    scenario_path: result.get_result() for scenario_path, result in all_results.items() if result.without_exception
}

analyze_results(results_to_analyze)

# print_exception_tracebacks(results_to_analyze, compressed=False)
#
# if do_plot_scenarios:
#     plot_scenarios(results_to_analyze)