#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [ ]

setup_requirements = ['pytest-runner', 'inotify', ]

with open('requirements_dev.txt') as f:
    test_requirements = f.read().splitlines()

setup(
    author="Tim Nicholls",
    author_email='tim.nicholls@stfc.ac.uk',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    extras_require={'test': test_requirements},
    description="A python command sequencer to allow easy scripting in ODIN control systems",
    install_requires=requirements,
    license="Apache Software License 2.0",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='odin_sequencer',
    name='odin_sequencer',
    packages=find_packages('src'),
    package_dir={'':'src'},
    setup_requires=setup_requirements,
    test_suite='tests',
    url='https://github.com/stfc-aeg/odin-sequencer',
    version='0.1.0',
    zip_safe=False,
)
