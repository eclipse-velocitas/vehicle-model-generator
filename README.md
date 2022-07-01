# Velocitas Vehicle Model Generator

[![License: Apache](https://img.shields.io/badge/License-Apache-yellow.svg)](http://www.apache.org/licenses/LICENSE-2.0)

## About
This generator creates a vehicle model from the given vspec specification for the target programming language.

## Supported languages

* Python 3

## Usage

Invoke the `gen_vehicle_model.py` script with the path to the vspec file you wish to generate code for, additionally passing include pathes to directories which contain referenced vspec files:
```bash
python3 gen_vehicle_model.py -I <path_to_dir_with_included_vspec_files> <path_to_your_vspec_file>
```

### Example
```bash
python3 gen_vehicle_model.py -I ./vehicle_signal_specification/spec ./vehicle_signal_specification/spec/VehicleSignalSpecification.vspec
```

## Arguments

| Argument                                          | Description                                                                                                  |
|:--------------------------------------------------|:-------------------------------------------------------------------------------------------------------------|
`-h`, `--help`                                      | show this help message and exit
`-I dir`, `--include-dir dir`                       | Add include directory to search for included vspec files.
`-T TARGET_FOLDER`, `--target-folder TARGET_FOLDER` | The folder name (with relative path) where the code will be generated.
`-N PACKAGE_NAME`, `--package-name PACKAGE_NAME`                | Name of the module/package.
`-s`, `--strict`                                    | Use strict checking: Terminate when anything not covered or not recommended by the core VSS specs is found.
`-l {python}`, `--language {python}`                | The target language of the generated code.

## Contribution
- [GitHub Issues](https://github.com/eclipse-velocitas/vehicle-model-generator/issues)
- [Mailing List](https://accounts.eclipse.org/mailing-list/velocitas-dev)
- [Contribution](./CONTRIBUTING.md)
