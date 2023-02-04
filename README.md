# OpenSCENARIO2CR

Conversion from OpenSCENARIO to CommonRoad and utilizing the commonroad analysis framework.

## Installation

- Create a anaconda python environment >=3.8 (Tested only on 3.9)

  ```
  pip install -r requirements.txt
  ```

- Pull the [CommonRoad Scenario Designer](https://gitlab.lrz.de/cps/commonroad-scenario-designer) under 
branch `fix_openSCENARIO`. Afterwards install the designer within the same virtual environment following its README.


### (Optional): for testing the scenarios

- Install the commonroad stl monitor with this command:

  ```
  pip install git+ssh://git@gitlab.lrz.de/cps/commonroad-stl-monitor.git
  ```

- Pull the [SPOT](https://gitlab.lrz.de/cps/spot-cpp) repository and checkout the master, or the
hash `9a49ce279f33f441d932ce788de7b69b5481bae2`.
Afterwards install SPOT with Python Interface (using `commonroad-io`) within the same virtual environment following its
README.

### OpenSCENARIO

- Downloads: version v1.1.1 from this [link](https://www.asam.net/standards/detail/openscenario/)
- [Environment Simulator Minimalistic (esmini)](https://github.com/esmini/esmini)
- OpenDRIVE2CR: conversion from OpenDRIVE map to CommonRoad is
  implemented [here](https://gitlab.lrz.de/cps/commonroad-scenario-designer/-/tree/master),
  see [tutorial](https://gitlab.lrz.de/cps/commonroad-scenario-designer/-/blob/master/tutorials/conversion_examples/example_opendrive_to_commonroad.py)
- Selected scenarios ([start point](https://gitlab.lrz.de/kosi/wp6/openscenario/-/tree/main/scenarios)):
    - **DoubleLaneChange**: from openScenario standard examples, you should first download the openSCENARIO package and then go to `./standard/examples/DoubleLaneChanger.xosc`
    - **Pedestrian example**: Esmini, see https://github.com/esmini/esmini/tree/master/resources/xosc

### CommonRoad

- Format: version 2022.01 - [link](https://commonroad-io.readthedocs.io/en/latest/user/getting_started/)
