# Version 1.0.9

## Configuration

- We moved the [configuration file for the test scripts](../../mytoolit/config/config.yaml) into the `mytoolit` package.
- We moved the [configuration file for ICOc](../../mytoolit/old/configKeys.xml) into the `mytoolit` package.

## Compatibility

- This version of ICOc requires at least Python `3.7`, since we use the `annotations` directive from the `__futures__` module

## Package

- We added a [package description](../../setup.py) for ICOc. You can now install the software using `pip install -e .` in the root of the repository. To uninstall the package use `pip uninstall icoc`.

## Internal

- We removed old hardware test code

### Network (Old)

- Simplified code
