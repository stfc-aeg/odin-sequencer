import time

import numpy as np

provides = [
    "add",
    "abortable_sequence",
    "exceptional_add",
    "array_test",
    "sine_test",
]


def add(a=0, b=0):
    print("Adding {} and {}".format(a, b))
    for i in range(10):
        time.sleep(0.5)
        print("Add sequence loop count {}".format(i))

    print("Done adding, result is {}".format(a + b))
    return a + b


def exceptional_add(a=0, b=0):
    sum = a + b
    print("Exceptional add")
    if sum == 42:
        print("Boom")
        raise ValueError(
            "The answer to the ultimate question of life, the universe, and everything is not allowed here."
        )

    return a + b


def abortable_sequence(num_loops=100, loop_delay=0.1):
    set_progress(0, num_loops)

    for i in range(num_loops):
        if i % 10 == 0:
            print("Loop count {}".format(i))

        time.sleep(loop_delay)
        set_progress(i + 1, num_loops)
        if abort_sequence():
            print("Aborting sequence")
            break

    print("Sequence complete")
    return i


def array_test(shape=[10, 10]):
    arr = np.arange(np.prod(shape)).reshape(shape)
    print("Numpy array created with shape:", shape)
    return arr


def sine_test(freq=5, duration=1, rate=1000):
    t = np.linspace(0, duration, int(rate * duration), endpoint=False)
    signal = np.sin(2 * np.pi * freq * t)
    print("Sine wave generated with frequency:", freq)
    return t, signal
