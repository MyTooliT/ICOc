# Version 1.0.8

## Internal

### Message

- Added method to convert message to python-can message object
- Renamed initialization attribute `payload` to `data`
- Added support to initialize a message object with a message object of [python-can]

[python-can]: https://python-can.readthedocs.io

## Production Test

- The name of the PDF test report now reflects the tested node. The latest test data for the STH will be stored in a file called `STH Test.pdf`, while the STU test data is stored in a file called `STU Test.pdf`. Before this update both tests would use the file name `Report.pdf`.

## STH Test

- We now always assume the name of the STH (`STH` → `Name`) in the [configuration][configuration file] is given as string. This improves the usability of the tests, since otherwise you might specify an integer as name (e.g. `1337`) and wonder why the test is unable to connect to the STH.
- The STH test now prints a message about a possible incorrect config value for the acceleration sensor (`STH` → `Acceleration Sensor` → `Sensor`), if [the self test of the accelerometer failed](https://github.com/MyTooliT/ICOc/issues/13).
- The STH test fails, if you use an sensor value (`STH` → `Acceleration Sensor` → `Sensor`) that is not one of the supported values

  - `ADXL1001` or
  - `ADXL1002`.

# Version 1.0.7

## Logging

- The [main CAN class](../network.py) now logs the received CAN messages in a file called `can.log`, if you specify the level `DEBUG` in the [configuration file][].

[configuration file]: ../Configuration/config.yaml

## STH Test

- The STH test case now skips the flash test if the status in the [configuration file](../Configuration/config.yaml) (`STH` → `Status`) is set to `Epoxied`.
- The test now also supports the ±50 g digital accelerometer [ADXL1002](https://www.analog.com/media/en/technical-documentation/data-sheets/ADXL1001-1002.pdf). To choose which sensor is part of the STH (or SHA), please change the value `STH` → `Acceleration Sensor` → `Sensor` to the appropriate value in the [configuration file][].
- Removed the over the air (OTA) test, since it requires the command `ota-dfu`, which needs to be compiled first, and often does not work reliable.
- The [renaming of the STH in the EEPROM test](https://github.com/MyTooliT/ICOc/issues/10) should now work more reliable.

## STU Test

- Add first version of [new test for the STU](../mytoolit/test/production/stu.py). For more information, please take a look at the section “Production Tests” of the [main readme](../ReadMe.md).

# Version 1.0.6

## Documentation

- We added a [tutorial](Tutorials/Release.md) that explains the necessary steps for releasing a new version of ICOc.

# Version 1.0.5

## Configuration

- We moved the host and port configuration values of the [Matplotlib](https://matplotlib.org) GUI from the XML configuration file into the [YAML configuration](../Configuration/config.yaml).

## Documentation

- We documented how to execute the [automatic tests](Guidelines/Test.md) for software.

## STH Test

- The EEPROM tests now also writes the firmware release name (`STH` → `Firmware` → `Release Name` in the [configuration](../Configuration/config.yaml)) into the EEPROM.
- The EEPROM test now sets the

  - operating time,
  - power on cycles,
  - power off cycles,
  - under voltage counter, and the
  - watchdog reset counter

  to `0`.

# Version 1.0.4

## Documentation

- We moved the release notes from the init code of the [`mytoolit` package](../mytoolit) into this file.
- We added an [FAQ](FAQ.md) text that should answer questions not covered by the main readme.
- We rewrote the main readme file. The document should now contain more information that is relevant for the typical user of ICOc. Before this update the text contained more technical information that is only interesting for developers of the ICOc application, such as ADC settings and hardware configuration steps.
- We added a [tutorial](../Documentation/Tutorials/Testing.md) that shows you how to test an STH (or SHA).
- The documentation now includes a description of [manual tests for the software](Guidelines/Test.md).
- We added a document that describes the [style guidelines](Guidelines/Style.md) for the code base.

## Install

- We forgot to add the [requirements file](../requirements.txt) for pip in the last release. This problem should now be fixed.
- We now use the [Python CAN package](https://python-can.readthedocs.io) to access the PCAN-Basic API instead of including a copy of the Python API file in the repository.

## Scripts

- Add a simple wrapper script for the STH test. If you add its parent folder to your path you will be able to execute the test regardless of your current path. For more information, please take a look at the [readme](../ReadMe.md).
- We added a simple wrapper script for [`mwt.py`](../mwt.py). For more information, please take a look [here](../Scripts/ReadMe.md).
- The new scripts [`Convert-MAC-Base64`](../Scripts/ReadMe.md) and [`Convert-Base64-MAC`](../Scripts/ReadMe.md) convert a MAC address (e.g. `08:6b:d7:01:de:81`) into a Base64 encoded (8 character long) text (e.g. `CGvXAd6B`) and back. We use the Base64 encoded MAC address as Bluetooth advertisement name to uniquely identify a STH (or SHA).

## Style

- We formatted the code base with [YAPF](https://github.com/google/yapf).

## STH Test

- We added a test that checks, if updating the over the air update via the [ota-dfu](https://www.silabs.com/documents/public/application-notes/an1086-gecko-bootloader-bluetooth.pdf) command line application works correctly. Currently this test is not activated by default, since it requires that the operator compiles the `ota-dfu` application.
- The test now uses the Base64 encoded version of the MAC address as default name. The rationale behind this update was that the name we used until now was not unique for a certain STH (or SHA). For more information, please take a look [here](https://github.com/MyTooliT/ICOc/issues/1).
- The EEPROM test now resets the STH at the end. This way the STH will already use the Base64 encoded MAC address as name after the test was executed. Before this update we had to do a manual reset for the name change to take place.

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
