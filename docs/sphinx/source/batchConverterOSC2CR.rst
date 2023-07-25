############################################
Batch Conversion of OpenSCENARIO file
############################################

This tutorial explains how to use the batch processing to convert OpenSCENARIO to CommonRoad in parallel.

.. code-block:: python

      import os
      import re
      import pickle
      from datetime import datetime

      from osc_cr_converter.utility.configuration import ConverterParams
      from osc_cr_converter.converter.osc2cr import Osc2CrConverter
      from osc_cr_converter.converter.serializable import Serializable
      from osc_cr_converter.batch.converter import BatchConverter
      from osc_cr_converter.batch.analysis import analyze_results

      # ==== specify the directory contained openscenario files that to be batch-processed
      directory = '../scenarios/'
      # ==== specify the output dir
      output_dir = '../output/batch/'
      # ==== set the configuration and initialize single converter
      config = ConverterParams()
      converter = Osc2CrConverter(config)
      # === initialize the batch converter
      batch_converter = BatchConverter(converter)
      # ====specify the storage dictionary
      storage_dir = output_dir + "{}".format(datetime.now().isoformat(sep="_", timespec="seconds"))
      os.makedirs(storage_dir, exist_ok=True)
      Serializable.storage_dir = storage_dir

Batch conversion, analyse, and visualization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

      # ==== discover the files
      # * recursively: whether search recursively starting at the directory
      batch_converter.discover_files(directory, re.compile(r".*\.xosc", re.IGNORECASE), recursively=True)
      # ==== run batch conversion
      batch_converter.run_batch_conversion(num_worker=0)

      # === analyse the result
      with open(os.path.join(storage_dir, "statistics.pickle"), "rb") as stats_file:
          # We don't need the scenario files for this analysis, just slows us down
          Serializable.import_extra_files = False
          all_results = pickle.load(stats_file)
      if all_results:
          analyze_results(all_results)
