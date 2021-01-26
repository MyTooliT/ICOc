# Version 1.0.9

## Configuration

- We moved the [configuration file for the test scripts][config] into the `mytoolit` package.
- We moved the [configuration file for ICOc](../../mytoolit/old/configKeys.xml) into the `mytoolit` package.
- We now use uppercase letters for all configuration keys in [`config.yaml`][config]. The reason behind this update is that we can overwrite these values using environment variables – with the prefix `DYNACONF_` – even on Windows. Unfortunately Windows [converts all environment variables to uppercase](https://www.dynaconf.com/configuration).

[config]: ../../mytoolit/config/config.yaml

## Compatibility

- This version of ICOc requires at least Python `3.7`, since we use the `annotations` directive from the `__futures__` module

## Package

- We added a [package description](../../setup.py) for ICOc. You can now install the software using `pip install -e .` in the root of the repository. To uninstall the package use `pip uninstall icoc`.

## Scripts

- We added a new EEPROM checking tool. For more information please take a look at the section “EEPROM Check” of the [script documentation](../Scripts.md).

## Internal

- We removed old hardware test code

### Network (Old)

- Simplified code
