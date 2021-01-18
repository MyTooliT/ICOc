# Version 1.0.5

## Configuration

- We moved the host and port configuration values of the [Matplotlib](https://matplotlib.org) GUI from the XML configuration file into the YAML configuration.

## Documentation

- We documented how to execute the [automatic tests](Guidelines/Test.md) for software.

## STH Test

- The EEPROM tests now also writes the firmware release name (`STH` → `Firmware` → `Release Name` in the configuration into the EEPROM.
- The EEPROM test now sets the

  - operating time,
  - power on cycles,
  - power off cycles,
  - under voltage counter, and the
  - watchdog reset counter

  to `0`.
