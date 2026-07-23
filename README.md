# ODIN Sequencer

[![Build Status](https://travis-ci.com/stfc-aeg/odin-sequencer.svg?branch=master)](https://travis-ci.com/stfc-aeg/odin-sequencer)

A Python command sequencer to allow easy scripting of ODIN control systems.

- **Free software:** Apache Software License 2.0

## Features

- **Detect Changes** button – When enabled, it detects any code changes made to the loaded modules.
- **Reload** – Reloads the loaded modules and applies any changes that have been made.
- **Execute** buttons – Executes the selected sequence.

## How to Set Up

### Clone the repository

```bash
git clone git@github.com:stfc-aeg/odin-sequencer.git
cd odin-sequencer
```

### Create a Python 3 virtual environment

```bash
python3 -m venv ./odin-sequencer-3.8
source odin-sequencer-3.8/bin/activate
```

### Install the development and test dependencies

```bash
pip install -e .[test]
```

## How to Run

Start the ODIN server while in the `odin-sequencer` directory.

```bash
odin_control --config config/odin_sequencer.cfg
```

Follow the instructions in the
[`odin-sequencer-ui`](https://github.com/stfc-aeg/odin-sequencer-ui)
repository to use the UI components in your own application.

Alternatively, download the test application:

```bash
wget https://github.com/stfc-aeg/odin-sequencer-ui/releases/download/<version>/app_build.tgz
tar -xvzf app_build.tgz
```

Then update the `static_path` entry in your `.cfg` file to point to the extracted `dist/` directory.

You can then access the UI at:

```text
http://<http_addr>:<http_port>
```

For example:

```text
http://127.0.0.1:8888
```

Example configuration:

```ini
http_port = 8888
http_addr = 127.0.0.1
static_path = dist
```

### Loading sequences

By default, the modules in the `sequences` directory under `~/odin-sequencer/src/examples` are loaded when the server starts.

To load modules from a different location, change the `sequence_location` value in `~/odin_sequencer/config/odin_sequencer.cfg`.

`sequence_location` can point either to a directory containing sequence modules or to a single module file.

## How to Add Context

Call `add_context` during another adapter's `initialize` method (see `dummy_context.py` for an example).

```python
test_device = TestDevice(123)
self.adapters['odin_sequencer'].add_context('test_device', test_device)
```

The context can then be used in a sequence by calling `get_context` (see `example_sequences.py`).

```python
dev = get_context('test_device')
```

## How to Abort an Executing Sequence

Long-running sequences can periodically check the value returned by `abort_sequence()`, which is exposed to every loaded sequence module.

If it returns `true`, the sequence can terminate cleanly before completion.

See `example_sequences.py` for an example of an abortable sequence.

## How to Report Progress During a Sequence

Executing sequences can report progress by calling `set_progress(current, total)`.

This function is exposed to every loaded sequence module and allows both the API and UI to display execution progress.

See `example_sequences.py` for an example.

## How to Start a Local Process Worker

With the virtual environment activated, navigate to the `supervisord` directory and start the worker.

```bash
cd odin_sequencer/src/odin_sequencer/supervisord
supervisord -c supervisord.conf || supervisorctl -c supervisord.conf start celery
```

## How to Start Multiple Remote Process Workers

Navigate to the `scripts` directory, list the remote workers in `workers.txt`, update the configuration at the top of `start_worker.sh`, and then run:

```bash
cd scripts
sh start_worker.sh
```

## How to Stop Multiple Remote Process Workers

Navigate to the `scripts` directory, list the remote workers in `workers.txt`, update the configuration at the top of `stop_worker.sh`, and then run:

```bash
cd scripts
sh stop_worker.sh
```

## How to Run a Process During a Sequence

Ensure the process queue adapter is loaded in `odin_sequencer.cfg`:

```ini
[adapter.process_queue_context]
module = odin_sequencer.process_queue_context.ProcessQueueContextAdapter
```

Add processing tasks to `tasks.py`:

```python
def add(x, y):
    return x + y
```

The `process_writer` context can then be used within a sequence to submit tasks using `run()` or `group()`.

```python
queue = get_context('process_writer')

queue.run('add', True, 4, 3)
queue.group('add', True, range(10), 3)

output = queue.run('add', False, 4, 3)
result = output.get()
```

### `run()`

Runs a single task.

Parameters:

- `str` — Task function name.
- `bool` — `True` if the return value is not required.
- Remaining arguments are passed directly to the task function.

### `group()`

Runs a group of tasks.

Parameters:

- `str` — Task function name.
- `bool` — `True` if the return value is not required.
- `list` — Values to iterate over for one argument.
- Remaining arguments are passed directly to the task function.

## Credits

This package was created with
[Cookiecutter](https://github.com/audreyr/cookiecutter) and the
[audreyr/cookiecutter-pypackage](https://github.com/audreyr/cookiecutter-pypackage)
project template.
````
