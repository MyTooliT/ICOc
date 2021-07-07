# Development

## Style

Please use the guidelines from [PEP 8](https://www.python.org/dev/peps/pep-0008/). For code formatting we currently use [YAPF](https://github.com/google/yapf), which should format code according to PEP 8 by default.

To format the whole code base you can use the following command in the root of the repository:

```sh
yapf --in-place --parallel --recursive .
```

YAPF will not

- split long strings and
- add newlines to long lines not surrounded by parentheses.

To make sure that code has a maximum line length of `79` characters please split up long strings and add parentheses yourself.

For development we recommend that you use a tool or plugin that reformats your code with YAPF every time you save. This way we can ensure that we use a consistent style for the whole code base.

<a name="development:section:tests"></a>

## Tests

The following text describes some of the measures we should take to keep the software stable.

Please only push your changes to the `master` branch, if you think there are no new bugs or regressions. The `master` branch **should always contain a working version of the software**. Please **always run the automatic and manual tests** described below before you push to the `master` branch.

### Code Checks

#### Flake8

We check the code with [flake8](https://flake8.pycqa.org):

```sh
pip install flake8
```

Please use the following command in the root of the repository to make sure you did not add any code that introduces warnings:

```sh
flake8
```

#### Mypy

To check the type hint in the code base we use the static code checker [Mypy](https://mypy.readthedocs.io):

```sh
pip install mypy
```

Please use the following command in the root of the repository to check the code base for type problems:

```sh
mypy --ignore-missing-imports mytoolit
```

### Automatic Tests

#### Requirements

Please install the [nose testing module](https://nose.readthedocs.io):

```sh
pip install nose
```

##### Usage

Please run the following command in the root of the repository:

```sh
nosetests --with-doctest --traverse-namespace mytoolit
```

and make sure that it reports no test failures.

### Manual Tests

#### ICOc

1. Call the command `icoc`.
2. Connect to a working STH (Enter the number and press <kbd>⏎</kbd>)
3. Start the data acquisition (<kbd>s</kbd>)
4. After some time a window displaying the current acceleration of the STH (or SHA) should show up
5. Shake the STH
6. Make sure the window shows the increased acceleration
7. Close the window
8. The programm should now exit, without any error messages

#### STH Test

1. Call the command `test-sth` for a working STH
2. Wait for the command execution
3. Check that the command shows no error messages
4. Open the PDF report (`STH Test.pdf`) in the repository root and make sure that it includes the correct test data

<a name="development:section:stu-test"></a>

#### STU Test

1. Call the command `test-stu` (or `test-stu -k eeprom -k connect` when you want to skip the flash test) for a working STU
2. Wait for the command execution
3. Check that the command shows no error messages
4. Open the PDF report (`STU Test.pdf`) in the repository root and make sure that it includes the correct test data

### Combined Checks & Tests

While you need to run the test for ICOc manually, the other tests and checks can be automated at least partially. To run all checks, the STH test and the STU test use the following command in a shell with support for the `&&` operator (e.g. [PowerShell **Core**](https://github.com/PowerShell/PowerShell)):

```sh
flake8 &&
mypy --ignore-missing-imports mytoolit &&
nosetests --with-doctest --stop --traverse-namespace mytoolit &&
test-sth -v &&
test-stu -v && # or `test-stu -k eeprom -k connect` to skip the flash test
Invoke-Item 'STH Test.pdf' &&
Invoke-Item 'STU Test.pdf'
```

Afterwards make sure there were no (unexpected) errors in the output of the STH and STU test.

## Release

1. Make sure that **none** of the [tests](#development:section:tests) fail

   - **Note**: Please execute `test-sth`

     1. once with `STH` → `Status` set to `Epoxied`, and
     2. once set to `Bare PCB`

     in the [configuration](../mytoolit/config/config.yaml). To make sure, that the STU flash test also works, please use both STU test commands described in the section [“STU Test”](#development:section:stu-test).

     If you follow the steps above you make sure that the **flash tests work** for both STU and STH, and there are **no unintentional consequences of (not) flashing the chip** before you run the other parts of the test suite.

2. Change the [`__version__`](../mytoolit/__init__.py) number inside the [`mytoolit`](../mytoolit) package
3. Push the commit that changes the version number
4. Create a new release [here](https://github.com/MyTooliT/ICOc/releases/new)

   1. Copy the [release notes](Releases) for the latest version
   2. Paste them into the main text
   3. Decrease the header level of each section by one
   4. Replace links with a permanent version:

      For example instead of

      - `../../something.txt` use
      - `https://github.com/MyTooliT/ICOc/blob/REVISION/something.txt`,

      where `REVISION` is the latest version of the master branch (e.g. `8568893f` for version `1.0.5`)

   5. Check that all links work correctly

5. Insert the version number (e.g. `1.0.5`) into the tag field
6. For the release title use “Version VERSION”, where `VERSION` specifies the version number (e.g. “Version 1.0.5”)
7. Click on “Publish Release”