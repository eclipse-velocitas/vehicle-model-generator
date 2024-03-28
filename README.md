# Velocitas Vehicle Model Generator

[![License: Apache](https://img.shields.io/badge/License-Apache-yellow.svg)](http://www.apache.org/licenses/LICENSE-2.0)

## About
This generator creates a vehicle model from the given vspec specification for the target programming language.

## Supported languages

* Python 3
* C++

## Supported VSS versions
* 3.0
* 3.1
* 3.1.1
* 4.0

## Usage

Invoke the `src/velocitas/model_generator/cli.py` script with the path to the vspec or json file you wish to generate code for, additionally passing include pathes to directories which contain referenced vspec files. You need a `units.yaml` in the same directory. If you want to use the default one see [here](https://github.com/COVESA/vehicle_signal_specification/blob/master/spec/units.yaml). For stability use release branch with tags. For example branch `release/4.0`.
```bash
python3 src/velocitas/model_generator/cli.py -I <path_to_dir_with_included_vspec_files> <path_to_your_vspec_file>
```
or
```bash
python3 src/velocitas/model_generator/cli.py <path_to_your_json_file>
```
### Example
```bash
git clone -b v3.1 https://github.com/COVESA/vehicle_signal_specification.git
python3 src/velocitas/model_generator/cli.py -I ./vehicle_signal_specification/spec ./vehicle_signal_specification/spec/VehicleSignalSpecification.vspec
```

Or use VSCode Launch: Press ```F5```, select ```Python``` or ```cpp``` and pass in the include directory and input file path.

## Arguments

| Argument                                          | Description                                                                                                  |
|:--------------------------------------------------|:-------------------------------------------------------------------------------------------------------------|
`-h`, `--help`                                      | show this help message and exit
`-I dir`, `--include-dir dir`                       | Add include directory to search for included vspec files.
`-T TARGET_FOLDER`, `--target-folder TARGET_FOLDER` | The folder name (with relative path) where the code will be generated into.
`-N PACKAGE_NAME`, `--package-name PACKAGE_NAME`    | Name of the root module/package (Python) or root namespace (C++).
`-s`, `--strict`                                    | Use strict checking: Terminate when anything not covered or not recommended by the core VSS specs is found.
`-l {python}`, `--language {python}`                | The target language of the generated code.
`-o OVERLAY_FILE`, `--overlays OVERLAY_FILE`        | Add overlays that will be layered on top of the VSS file in the order they appear.
`-u UNITS`, `--units UNITS`                         | The file location of units file. If left empty it tries downloading default units file from https://github.com/COVESA/vehicle_signal_specification/blob/v4.0/spec/units.yaml.
`-e EXTENDED_ATTRIBUTES`,<br>`--extended-attributes EXTENDED_ATTRIBUTES` | Whitelisted extended attributes as comma separated list. Note, that extended attributes aren't considered by the generator. This paramter is only for suppressing warnings/errors."

## Known issues
VSS v3.0 has a typo in its specification. This clashes with vss tools 4.0 which is needed to support VSS v4.0 because it allows only lower case versions for types of signals. e.g the problem is with 'actuator' instead of 'Actuator' in https://github.com/COVESA/vehicle_signal_specification/blob/525e2bd00ddf061851bdc75e849178e5d3ad5833/spec/Powertrain/Battery.vspec#L229. Json files work just fine. See https://github.com/COVESA/vehicle_signal_specification/releases for getting the json files.

## Contribution
- [GitHub Issues](https://github.com/eclipse-velocitas/vehicle-model-generator/issues)
- [Mailing List](https://accounts.eclipse.org/mailing-list/velocitas-dev)
- [Contribution](./CONTRIBUTING.md)
