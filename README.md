# CommonROAD-OpenSCENARIO Converter
![image info](https://gitlab.lrz.de/tum-cps/commonroad-openscenario-converter/-/raw/master/docs/figures/converter-banner.png)

Automatic Traffic Scenario Conversion between [OpenSCENARIO](https://www.asam.net/standards/detail/openscenario/)
and [CommonRoad](commonroad.in.tum.de/). Currently, only the conversion from **O**pen**SC**ENARIO to **C**ommon**R**OAD (osc2cr) is developed.<br>
[![Linux](https://img.shields.io/badge/os-linux?&logo=Linux&logoColor=white&labelColor=gray)](https://pypi.python.org/pypi/commonroad-openscenario-converter/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/commonroad-openscenario-converter.svg)](https://pypi.python.org/pypi/commonroad-openscenario-converter/)
[![PyPI license](https://img.shields.io/pypi/l/commonroad-openscenario-converter.svg)](https://pypi.python.org/pypi/commonroad-openscenario-converter/)
[![PyPI version fury.io](https://badge.fury.io/py/commonroad-openscenario-converter.svg)](https://pypi.python.org/pypi/commonroad-openscenario-converter/)<br>
[![PyPI download month](https://img.shields.io/pypi/dm/commonroad-openscenario-converter.svg?style=plastic&label=PyPI%20downloads)](https://pypi.python.org/pypi/commonroad-openscenario-converter/) 
[![PyPI download week](https://img.shields.io/pypi/dw/commonroad-openscenario-converter.svg?style=plastic&label=PyPI%20downloads)](https://pypi.python.org/pypi/commonroad-openscenario-converter/)<br>

### Using the Converter
The recommended way of installation if you only want to use the OpenSCENARIO-CommonROAD Converter
(i.e., you do not want to work with the code directly) is to use the PyPI package:
```bash
pip install commonroad-openscenario-converter
```
### Development
For developing purposes, we recommend using [Anaconda](https://www.anaconda.com/) to manage your environment so that
even if you mess something up, you can always have a safe and clean restart. 
A guide for managing python environments with Anaconda can be found [here](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html).

- First, clone the repository. 
- After installing Anaconda, create a new environment with (>=3.9) and enter it:
``` bash
$ conda create -n commonroad-py39 python=3.9 -y
$ conda activate commonroad-py39
or
$ source activate commonroad-py39
```
- Then, install the dependencies with:

```sh
$ cd <path-to-this-repo>
$ pip install .
$ conda develop .
```

- To test the installition, run unittest:
```bash
$ cd tests
$ python -m unittest -v
```

### Open Simulation Interface (OSI) and UDP Driver
If you want to use the [esmini](https://github.com/esmini/esmini) UDPDriverController in combination with OSI for including
external driver models or vehicle simulators, you need to install OSI manually, 
see [here](https://github.com/OpenSimulationInterface/open-simulation-interface).

### Contributors (in alphabetical order by last name)
- Yuanfei Lin
- Michael Ratzel

### Documentation

The documentation of our toolbox is available on our website: https://cps.pages.gitlab.lrz.de/commonroad/commonroad-openscenario-converter/.

In order to generate the documentation via Sphinx locally, run the following commands in the root directory:

```bash
$ pip install -r ./docs/requirements_doc.txt
$ cd docs/sphinx
$ make html
```
The documentation can then be launched by browsing ``./docs/sphinx/build/html/index.html/``.
### Acknowledgments
We would like to extend our heartfelt gratitude to the team behind [esmini](https://github.com/esmini/esmini) for 
their remarkable effort in developing the simulation tool. Specifically, we would like to express our sincere 
appreciation to [Emil Knabe](https://www.linkedin.com/in/emil-knabe-216a1a11/?originalSubdomain=se)
for his invaluable contribution in reviewing and accepting the proposed changes to the esmini interface, 
and to [Sebastian Maierhofer](https://www.ce.cit.tum.de/air/people/sebastian-maierhofer-msc/)
for maintaining the converter from OpenDRIVE to lanelets.
We gratefully acknowledge partial financial support by the German Federal Ministry for Digital and Transport (BMDV) 
within the project _Cooperative Autonomous Driving with Safety Guarantees_
([KoSi](https://www.ce.cit.tum.de/air/research/kosi/)).

### Citation
If you use `commonroad-openscenario-converter` for academic work, we highly encourage you to cite our [paper](https://mediatum.ub.tum.de/doc/1716501/1716501.pdf):
```text
@inproceedings{Lin2023Osc2Cr,
	author = {Yuanfei Lin, Michael Ratzel, and Matthias Althoff},
	title = {Automatic Traffic Scenario Conversion from {OpenSCENARIO} to {CommonRoad}},
	booktitle = {Proc. of the IEEE Int. Conf. on Intell. Transp. Syst.},
	year = {2023},
	pages= {},
}
```
If you use this project's code in industry, we'd love to hear from you as well; 
feel free to reach out to [Yuanfei Lin](mailto:yuanfei.lin@tum.de) directly.

