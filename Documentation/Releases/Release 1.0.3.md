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
