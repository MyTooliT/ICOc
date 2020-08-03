# Version 1.0.4

## Documentation

- We moved the release notes from the init code of the [`mytoolit` package](../mytoolit) into this file.

## Install

- We forgot to add the [requirements file](../requirements.txt) for pip in the last release. This problem should now be fixed.

## Scripts

- Add a simple wrapper script for the STH test. If you add its parent folder to your path you will be able to execute the test regardless of your current path. For more information, please take a look at the [ReadMe](../readme.md).
- We added a simple wrapper script for [`mwt.py`](../mwt.py). For more information, please take a look [here](../Scripts/ReadMe.md).

## STH Test

- We added a test that checks, if updating the over the air update via the [ota-dfu](https://www.silabs.com/documents/public/application-notes/an1086-gecko-bootloader-bluetooth.pdf) command line application works correctly.

# Version 1.0.3

## Bug Fixes

- The data acquisition should now work on additional machines

## Compatibility

- Since the latest code base uses f-Strings the software now requires at least
  Python 3.6.

## Requirements

- You can now install the required Python packages using the command

  ```sh
  pip install -r requirements.txt
  ```

  in the root of the repository.

## STH Test

- The test prints it output to the

  - standard and
  - standard error output

  instead of a log file. The program will still produces log files for the
  individual parts of the test, since the class that handles the CAN
  communication currently requires this behavior.

- The program now prints the various attributes of the tested STH, such as
  name and RSSI, on the standard output.

- The program stores the most important attributes of the STH and the result
  of the test in a PDF report (in the root of the repository).

- The various configuration data for the test is now stored in a single YAML
  file (`Configuration/config.yaml`).

- The test program is now location independent. This means you do not need to
  change the working directory to call the script any more. For example,
  executing the command:

  ```sh
  py mytoolit/test/production/sth.py -k battery -k connect
  ```

  or the commands:

  ```sh
  cd mytoolit/test/production
  py sth.py -k battery -k connect
  ```

  in the root of repository should have the same effect.

## Version 1.0.2

- Bug Elimination

## Version 1.0.0

Initial Release:

- Release Date: 6. September 2019
- MyToolIt Watch(MyToolItWatch.py): Supports MyToolIt Watch
  functionality
- MyToolItTerminal (`mwt.py`): Terminal access to MyToolIt functionality
- Data Base Functionality: configKeys.xml
- Access to EEPROM via Excel interface
- Uses CanFd.py module to access MyToolIt protocol
- Supports Tests for internal verification:

  - `MyToolItTestSth.py`
  - `MyToolItTestSthManually.py`
  - `MyToolItTestStu.py`
  - `MyToolItTestStuManually.py`

- Supports configuration files for tests:

  - `SthLimits.py`
  - `StuLimits.py`
  - `testSignal.py`

- Support graphical visualization in real time: `Plotter.py`
