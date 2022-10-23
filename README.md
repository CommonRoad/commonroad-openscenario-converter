# OpenSCENARIO2CR

Conversion from OpenSCENARIO to CommonRoad and utilizing the commonroad analysis framework.

# Installation

Create a anaconda python environment >=3.8 (Tested only on 3.9)

```
pip install -r requirements.txt
```

Install the commonroad stl monitor with this command:

```
pip install git+ssh://git@gitlab.lrz.de/cps/commonroad-stl-monitor.git
```

Pull the [CommonRoad Scenario Designer](https://gitlab.lrz.de/cps/commonroad-scenario-designer) and check out the
following hash `13365aa714e61278b57ae6046fa9871ecbab527b`
Afterwards install the designer within the same virtual environment following its README.

Pull the [SPOT](https://gitlab.lrz.de/cps/spot-cpp) repository and checkout the master, or the
hash `9a49ce279f33f441d932ce788de7b69b5481bae2`.
Afterwards install SPOT with Python Interface (using commonroad-io) within the same virtual environment following its
README.

# How to run
To run the BatchConverter and analyze the results two Jupyter Notebooks can be found in the BatchConverter package
and for the Osc2CrConverter have a look at the jupyter notebook inside the OpenSCENARIO2CR package. 