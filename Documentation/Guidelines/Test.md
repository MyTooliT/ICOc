# Tests

The following text describes some of the measures we should take to keep the software stable.

Please only push your changes to the `master` branch, if you think there are no new bugs or regressions. The `master` branch **should always contain a working version of the software**. Please **always run the automatic and manual tests** described below before you push to the `master` branch.

## Code Checks

We check the code with [flake8](https://flake8.pycqa.org):

```sh
pip install flake8
```

Please use the following command in the root of the repository to make sure you did not add any code that introduces warnings:

```sh
flake8
```

## Automatic Tests

### Requirements

Please install the [nose testing module](https://nose.readthedocs.io):

```sh
pip install nose
```

#### Usage

Please run the following command in the root of the repository:

```sh
nosetests --with-doctest --traverse-namespace mytoolit
```

and make sure that it reports no test failures.

## Manual Tests

### ICOc

1. Call the command `ICOc`.
2. Connect to a working STH (Enter the number and press <kbd>⏎</kbd>)
3. Start the data acquisition (<kbd>s</kbd>)
4. After some time a window displaying the current acceleration of the STH (or SHA) should show up
5. Shake the STH
6. Make sure the window shows the increased acceleration
7. Close the window
8. The programm should now exit, without any error messages

### STH Test

1. Call the command `Test-STH` for a working STH
2. Wait for the command execution
3. Check that the command shows no error messages
4. Open the PDF report (`STH Test.pdf`) in the repository root and make sure that it includes the correct test data

### STU Test

1. Call the command `Test-STU -k eeprom -k connect` for a working STU
2. Wait for the command execution
3. Check that the command shows no error messages
4. Open the PDF report (`STU Test.pdf`) in the repository root and make sure that it includes the correct test data
