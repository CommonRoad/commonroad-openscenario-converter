############################################
Conversion of single OpenSCENARIO file
############################################

This tutorial demonstrates how to use the converter to translate
single OpenSCENARIO format to the CommonRoad scenarios.

.. code-block:: python


      from osc_cr_converter.utility.configuration import ConverterParams
      from osc_cr_converter.converter.osc2cr import Osc2CrConverter

      # ==== specify openscenario
      scenario_path = 'PathToYourOpenSCENARIOFile'
      openscenario = 'OpenSCENARIO_ID.xosc'

      # ==== build configuration
      config = ConverterParams.load('../configurations/' + openscenario.replace('.xosc', '.yaml'))
      # or use default config via: config = ConverterParams()

      # ==== initialize the converter
      converter = Osc2CrConverter(config)

Conversion & Visualization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: python

      # ==== run conversion
      scenario = converter.run_conversion(scenario_path + openscenario)

      # ==== plot converted results
      from osc_cr_converter.utility.visualization import visualize_scenario
      visualize_scenario(scenario, config)

