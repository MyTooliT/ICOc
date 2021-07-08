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

- We now always assume the name of the STH (`STH` → `Name`) in the configuration is given as string. This improves the usability of the tests, since otherwise you might specify an integer as name (e.g. `1337`) and wonder why the test is unable to connect to the STH.
- The STH test now prints a message about a possible incorrect config value for the acceleration sensor (`STH` → `Acceleration Sensor` → `Sensor`), if [the self test of the accelerometer failed](https://github.com/MyTooliT/ICOc/issues/13).
- The STH test fails, if you use an sensor value (`STH` → `Acceleration Sensor` → `Sensor`) that is not one of the supported values

  - `ADXL1001` or
  - `ADXL1002`.

## Tests

- We now check the code base with [flake8][].
- We use [GitHub actions](https://github.com/MyTooliT/ICOc/actions)
  - to run non-hardware dependent parts of the automated tests, and
  - to check the code base with [flake8][]

[flake8]: https://flake8.pycqa.org
