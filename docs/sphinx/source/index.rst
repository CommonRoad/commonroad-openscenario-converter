.. commonroad-openscenario-converter documentation master file, created by
   sphinx-quickstart on Tue Jul 25 09:00:08 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

****************************
CommonRoad OpenSCENARIO Converter
****************************

Scenarios play a significant role in the development,
testing, and validation of autonomous driving systems.
However, there is a shortage of both open-source and
commonly-used scenarios. Various representation formats for
scenarios are supported by different applications, depending
on their specific purposes.
Our converter is expected to be valuable to academic groups
and industry professionals alike, given the vast number of
openly accessible scenarios available in the **CommonRoad**
and **OpenSCENARIO** formats.


.. seealso::
   * `CommonRoad Input-Output <https://commonroad.in.tum.de/commonroad-io>`_
   * `CommonRoad Drivability Checker <https://commonroad.in.tum.de/drivability-checker>`_
   * `CommonRoad CriMe <https://commonroad.in.tum.de/tools/commonroad-crime>`_
   * `CommonRoad Scenario Designer <https://commonroad.in.tum.de/tools/scenario-designer>`_

Installation
===================
We have tested the toolbox with Python 3.9, 3.10, and 3.11.

The recommended way of installation if you only want to use the OpenSCENARIO-CommonROAD Converter
(i.e., you do not want to work with the code directly) is to use the PyPI package::

   pip install commonroad-openscenario-converter


Development
===================
For developing purposes, we recommend using `Anaconda <https://www.anaconda.com/>`_ to manage your environment so that
even if you mess something up, you can always have a safe and clean restart.
A guide for managing python environments with Anaconda can be found `here <https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html>`_.

First, clone `the repository <https://gitlab.lrz.de/tum-cps/commonroad-openscenario-converter>`_.

After installing Anaconda, create a new environment with (>=3.9) and enter it::

   conda create -n commonroad-py39 python=3.9 -y
   conda activate commonroad-py39

or::

   source activate commonroad-py39

Then, install the dependencies with::

   cd <path-to-this-repo>
   pip install .
   conda develop .

To test the installition, run unittest::

   cd tests
   python -m unittest -v

Overview
===================

.. toctree::
   :maxdepth: 2

    Getting Started <gettingStarted.rst>
    API <api/index.rst>

Open Simulation Interface (OSI) and UDP Driver
===================
If you want to use the `esmini <https://github.com/esmini/esmini>`_ UDPDriverController in combination with OSI for including
external driver models or vehicle simulators, you need to install OSI manually,
see the `user manual <https://github.com/OpenSimulationInterface/open-simulation-interface>`_.

Citation
===================
.. code-block:: text

   @inproceedings{Lin2023Osc2Cr,
       author = {Yuanfei Lin, Michael Ratzel, and Matthias Althoff},
       title = {Automatic Traffic Scenario Conversion from {OpenSCENARIO} to {CommonRoad}},
       booktitle = {Proc. of the IEEE Int. Conf. on Intell. Transp. Syst.},
       year = {2023},
       pages= {},
   }


Contact information
===================

.. only:: html

    :Release: |release|
    :Date: |today|

:Website: `http://commonroad.in.tum.de <https://commonroad.in.tum.de/>`_
:Forum: `CommonRoad forum <https://commonroad.in.tum.de/forum/>`_
:Email: `commonroad@lists.lrz.de <commonroad@lists.lrz.de>`_

Indices and tables
===================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
