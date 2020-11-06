=================
ODIN Sequencer
=================


.. image:: https://travis-ci.com/stfc-aeg/odin-sequencer.svg?branch=master
    :target: https://travis-ci.com/stfc-aeg/odin-sequencer




A python command sequencer to allow easy scripting of ODIN control systems

* Free software: Apache Software License 2.0

Features
--------

* *Detect Changes* button - When enabled, it will detect any code changes that have been made to the loaded modules.
* *Reload* - When clicked, it will reload the loaded modules and any changes that have been made to them will be applied.
* *Execute* buttons - When clicked, it will execute the sequence.


How to set up
-------------

Clone the repository and navigate into the cloned directory
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: bash

    $ git clone git@github.com:stfc-aeg/odin-sequencer.git
    $ cd odin-sequencer

Create a Python 3 virtual environment and activate it
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: bash

    $ python3 -m venv ./odin-sequencer-3.8
    $ source odin-sequencer-3.8/bin/activate

Install the test dependencies (required for development and testing)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: bash

    $ pip install -e .[test]


How to run
----------

Run the odin server while in the odin-sequencer directory
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: bash

    $ odin_server --config config/odin_sequencer.cfg 

Access the UI by navigating to :code:`localhost:8888` in your browser
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Loading sequences
^^^^^^^^^^^^^^^^^
By default, the modules located inside the :code:`sequences` directory in :code:`~/odin-sequencer/src/examples` are loaded when the server is started. If you want to load modules from a different directory, then you will need to change the :code:`sequence_location` value inside the :code:`odin_sequencer.cfg` file located in :code:`~/odin_sequencer/config`. Modules get loaded into the manager when the server is started if there are any modules in the directory specified. The :code:`sequence_location` value does not necessarily have to point to a directory but it can point to a single module file too. 



Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
