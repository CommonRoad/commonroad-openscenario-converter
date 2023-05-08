# OpenSCENARIO-CommonROAD Converter
![image info](./docs/figures/converter-banner.png)
Automatic Traffic Scenario Conversion between [OpenSCENARIO](https://www.asam.net/standards/detail/openscenario/)
and [CommonRoad](commonroad.in.tum.de/). Currently, only the conversion from **O**pen**SC**ENARIO to **C**ommon**R**OAD (osc2cr) is developed.

## Using the Converter
The recommended way of installation if you only want to use the OpenSCENARIO-CommonROAD Converter
(i.e., you do not want to work with the code directly) is to use the PyPI package:
```bash
pip install openscenario-commonroad-converter
```
### Development
For developing purposes, we recommend using [Anaconda](https://www.anaconda.com/) to manage your environment so that
even if you mess something up, you can always have a safe and clean restart. 
A guide for managing python environments with Anaconda can be found [here](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html).

- First, clone the repository. 
- After installing Anaconda, create a new environment with (>=3.9):
``` bash
$ conda create -n commonroad-py39 python=3.9 -y
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

