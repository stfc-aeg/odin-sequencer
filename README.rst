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


How to add context
------------------

Call :code:`add_context during the other` adapters :code:`initialize` (see dummy_context.py for an example)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: python

    test_device = TestDevice(123)
    self.adapters['odin_sequencer'].add_context('test_device', test_device)

The context can now be used in a sequence by calling :code:`get_context` (see example_sequences.py for an example)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: python

    dev = get_context('test_device')

How to abort an executing sequence
----------------------------------

Long-running sequences can choose to check the value of the :code:`abort_sequence()` function, which is
exposed to every loaded sequence module. If `true` the sequence can be cleanly terminated early.
(See example_sequences.py for an example of an abortable sequence.)

How to report progress in an executing sequence
-----------------------------------------------

Executing sequences can report progress to the user by calling the :code:`set_progress` function,
which is exposed to every loaded sequence module. This takes two arguments reporting the `current`
and `total` steps in the sequence. This is used by the API and UI to display progress. (See
example_sequences.py for an example.)

How to start a local process worker
-----------------------------------

With the virtual enviroment activated, navigate to the supervisord directory and start the worker
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: bash
    
    $ cd odin_sequencer/src/odin_sequencer/supervisord
    $ supervisord -c supervisord.conf || supervisorctl -c supervisord.conf start celery


How to start a multiple remote process workers
----------------------------------------------

Navigate to the scripts directory, list the remote works in workers.txt, update the config at the start of start_worker.sh, and then run the script
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: bash
    
    $ cd scripts
    $ sh start_worker.sh


How to stop a multiple remote process workers
---------------------------------------------

Navigate to the scripts directory, list the remote works in workers.txt, update the config at the start of stop_worker.sh, and then run the script
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: bash
    
    $ cd scripts
    $ sh stop_worker.sh


How to run a process during a sequence
--------------------------------------

Ensure the process queue adapter is loaded in odin_sequencer.cfg 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: bash
    
    [adapter.process_queue_context]
    module = odin_sequencer.process_queue_context.ProcessQueueContextAdapter

Add processing tasks to tasks.py 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: python
    
    def add(x, y):
        return x + y

The process_writer context can then be loaded during a sequence to add tasks to queue using :code:`run` or :code:`group`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: python
    
    queue = get_context('process_writer')
    queue.run('add', True, 4, 3)
    queue.group('add', True, range(10), 3)
    output = queue.run('add', False, 4, 3)
    result = output.get()

:code:`run` allows for a single task to be run 
    Parameters:
        * :code:`String` task function name
        * :code:`Boolean` True if the result from the function doesn't need to be returned
        * arguments for the task function

:code:`group` allows for a group of task to be run 
    Parameters:
        * :code:`String` task function name
        * :code:`Boolean` True if the result from the function doesn't need to be returned
        * :code:`List` list of values of the argument that is to be iterated over
        * other arguments for the task function


Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
