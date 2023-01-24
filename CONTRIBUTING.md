# How to Contribute to Eclipse Velocitas Vehicle Model Generator

First of all, thanks for considering to contribute to Eclipse Velocitas. We really
appreciate the time and effort you want to spend helping to improve things around here.

In order to get you started as fast as possible we need to go through some organizational issues first, though.

## Eclipse Contributor Agreement

Before your contribution can be accepted by the project team contributors must
electronically sign the Eclipse Contributor Agreement (ECA).

* http://www.eclipse.org/legal/ECA.php

Commits that are provided by non-committers must have a Signed-off-by field in
the footer indicating that the author is aware of the terms by which the
contribution has been provided to the project. The non-committer must
additionally have an Eclipse Foundation account and must have a signed Eclipse
Contributor Agreement (ECA) on file.

For more information, please see the Eclipse Committer Handbook:
https://www.eclipse.org/projects/handbook/#resources-commit

## Code Style Guide
* Use [Black](https://black.readthedocs.io/) to format your code.
* Use [isort](https://isort.readthedocs.io/) to sort imports.
* Use [pydocstyle](https://pydocstyle.readthedocs.io/) to check for PEP-8 style issues.
* Use [mypy](https://mypy.readthedocs.io/) to check for type errors.
* Use [flake8](https://flake8.readthedocs.io/) to check for style issues.
* Above and other tools will run automatically if you install
 [pre-commit](https://pre-commit.com/) using the instructions below.

## Making Your Changes

* Fork the repository on GitHub.
* Create a new branch for your changes.
* Install dependencies:

   ```bash
   pip3 install -r requirements.txt
   ```
* Make your changes following the code style guide (see Code Style Guide section above).
* When you create new files make sure you include a proper license header at the top of the file (see License Header section below).
* When there is a change in VSS Spec, regenerate the vehicle_model with the following command:

   ```bash
   python3 gen_vehicle_model.py -I ./vehicle_signal_specification/spec ./vehicle_signal_specification/spec/VehicleSignalSpecification.vspec
   ```
   Afterwards adjust relative imports as needed.

* Install and run [pre-commit](https://pre-commit.com/) to automatically check for style guide issues.
    ```bash
    pre-commit run --all-files
    ```
* Commit your changes into that branch.
* Use descriptive and meaningful commit messages. Start the first line of the commit message with the issue number and title e.g. `[#9865] Add token based authentication`.
* Squash multiple commits that are related to each other semantically into a single one.
* Make sure you use the `-s` flag when committing as explained above.
* Push your changes to your branch in your forked repository.

## Update Python dependencies

Please use [pip-tools](https://github.com/jazzband/pip-tools) to update pip-based packages up to date. Any additional devlopment dependencies needs to be added to the [requirements.in](./requirements.in) file in the root directory.
* `Please don't try to update the dependencies manually.`

## License Header

Please make sure any file you newly create contains a proper license header like this:

```python
# Copyright (c) <year> Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License 2.0 which is available at
# http://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
```
Please adjusted the comment character to the specific file format.

## Submitting the Changes

Submit a pull request via the normal GitHub UI.

## After Submitting

* Do not use your branch for any other development, otherwise further changes that you make will be visible in the PR.
