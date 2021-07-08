# Version 1.0.7

## Logging

- The [main CAN class](../network.py) now logs the received CAN messages in a file called `can.log`, if you specify the level `DEBUG` in the configuration file.

## STH Test

- The STH test case now skips the flash test if the status in the configuration file (`STH` → `Status`) is set to `Epoxied`.
- The test now also supports the ±50 g digital accelerometer [ADXL1002](https://www.analog.com/media/en/technical-documentation/data-sheets/ADXL1001-1002.pdf). To choose which sensor is part of the STH (or SHA), please change the value `STH` → `Acceleration Sensor` → `Sensor` to the appropriate value in the configuration file.
- Removed the over the air (OTA) test, since it requires the command `ota-dfu`, which needs to be compiled first, and often does not work reliable.
- The [renaming of the STH in the EEPROM test](https://github.com/MyTooliT/ICOc/issues/10) should now work more reliable.

## STU Test

- Add first version of [new test for the STU](../mytoolit/test/production/stu.py). For more information, please take a look at the section “Production Tests” of the [main readme](../ReadMe.md).
