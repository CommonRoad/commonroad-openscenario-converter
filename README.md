# OpenSCENARIO2CR

Conversion from OpenSCENARIO to CommonRoad and vice versa.

# Running with Docker
You can use the provided `docker-compose.yml` file:

Starting:
```
docker-compose up
```
Stopping
```
docker-compose down
```
and click on the prompted link to access a jupyter notebook Server with all dependencies installed

### OpenSCENARIO
- Downloads: version v1.1.1 from this [link](https://www.asam.net/standards/detail/openscenario/)
- [Environment Simulator Minimalistic (esmini)](https://github.com/esmini/esmini)
- OpenDRIVE2CR: conversion from OpenDRIVE map to CommonRoad is implemented [here](https://gitlab.lrz.de/cps/commonroad-scenario-designer/-/tree/master), see [tutorial](https://gitlab.lrz.de/cps/commonroad-scenario-designer/-/blob/master/tutorials/conversion_examples/example_opendrive_to_commonroad.py)
- Selected scenarios ([start point](https://gitlab.lrz.de/kosi/wp6/openscenario/-/tree/main/scenarios)): 
    - DoubleLaneChange from openScenario standard examples
    - Pedestrian example Esmini

### CommonRoad
- Format: version 2021.02 - [link](https://commonroad-io.readthedocs.io/en/latest/user/getting_started/)

scenario editor hash: `13365aa714e61278b57ae6046fa9871ecbab527b`