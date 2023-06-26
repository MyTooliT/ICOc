# Development

## Install

You can install ICOc including the relevant development tools using the following command in the root of the repository:

```sh
pip install -e .[dev,test]
```

## Style

Please use the guidelines from [PEP 8](https://www.python.org/dev/peps/pep-0008/). For code formatting we currently use [Black](https://github.com/psf/black), which should format code according to PEP 8 by default.

To format the whole code base you can use the following command in the root of the repository:

```sh
black .
```

For development we recommend that you use a tool or plugin that reformats your code with Black every time you save. This way we can ensure that we use a consistent style for the whole code base.

<a name="development:section:tests"></a>

## Tests

The following text describes some of the measures we should take to keep the software stable.

Please only push your changes to the `master` branch, if you think there are no new bugs or regressions. The `master` branch **should always contain a working version of the software**. Please **always run**

- the **automatic test** (`make run`) for **every supported OS** (Linux, macOS, Windows) and
- the **manual tests** on Windows

before you push to the `master` branch.

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

#### mypy

To check the type hint in the code base we use the static code checker [mypy](https://mypy.readthedocs.io):

```sh
pip install mypy
```

Please use the following command in the root of the repository to check the code base for type problems:

```sh
mypy mytoolit
```

### Automatic Tests

#### Requirements

Please install the [pytest testing module](https://docs.pytest.org):

```sh
pip install pytest
```

##### Usage

Please run the following command in the root of the repository:

```sh
pytest -v
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

1. Call the command `test-stu` (or `test-stu -k eeprom -k connection` when you want to skip the flash test) for a working STU
2. Wait for the command execution
3. Check that the command shows no error messages
4. Open the PDF report (`STU Test.pdf`) in the repository root and make sure that it includes the correct test data

<a name="development:section:extended-tests"></a>

##### Extended Tests

The text below specifies extended manual test that should be executed before we [release a new version of ICOc](#development:section:release). Please note that the tests assume that you use more or less the [default configuration values](https://github.com/MyTooliT/ICOc/blob/master/mytoolit/config/config.yaml).

<a name="development:section:check-command-line-interface"></a>

###### Check Command Line Interface

1. Open your favorite terminal application and change your working directory to the root of the repository

2. Remove log and data files from the repository:

   ```sh
   clean-repo
   ```

3. Check that no HDF5 files exist in the repository. The following command should not produce any output:

   ```sh
   ls *.hdf5
   ```

4. Give your test STH the [name](#tutorials:section:sth-renaming) “Test-STH”
5. Measure data for 10 seconds using the following command:

   ```sh
   icoc -n 'Test-STH' -r 10
   ```

6. Check that the repo now contains a HDF5 (`*.hdf5`) file

   ```sh
   ls *.hdf5
   ```

7. Open the file in [HDFView](#readme:section:measurement-data)
8. Check that the table `acceleration` contains about 95 000 values
9. Check that the table contains three columns
10. Check that the meta attributes `Sensor_Range` and `Start_Time` exist
11. Check that `Sensor_Range` contains the correct maximum acceleration values for “Test-STH”
12. Check that `Start_Time` contains (roughly) the date and time when you executed the command from step 5
13. Check that ICOc handles the following incorrect program calls. The program should **not crash** and print a (helpful) **error description** (not a stak trace) before it exits.

    ```sh
    icoc -b '12-12-12-12-12'
    icoc -n 'TooooLong'
    icoc -s 1
    icoc -a 257
    icoc -o -1
    icoc -1 ' -1'
    icoc -2 256
    icoc -3 nine
    ```

###### Check User Interface

1. Repeat steps 1. – 4. from the [test above](#development:section:check-command-line-interface)
2. Open ICOc using the following command:

   ```sh
   icoc
   ```

3. The main menu of ICOc should show up

4. Try to connect to a non-existent STH

   1. Enter the text “1234”
   2. Press <kbd>⏎</kbd>
   3. ICOc should ignore the incorrect input and just display the main window

5. Change the output file name to “Test”

   1. Press <kbd>f</kbd>
   2. Remove the default name and enter the text “Test”
   3. Press <kbd>⏎</kbd>
   4. After two seconds ICOc should show the main menu again

6. Connect to your test STH/SHA

   1. Enter the number besides “Test-STH”: Usually this will be the number “1”
   2. Press <kbd>⏎</kbd>
   3. You should now be in the STH menu

7. Change the runtime to 20 seconds

   2. Press <kbd>r</kbd>
   3. Enter the text “hello”
   4. The last step should not have changed the default runtime of “0”
   5. Remove the default runtime (press <kbd>⌫</kbd>)
   6. Enter the text “20”
   7. Press <kbd>⏎</kbd>

8. Enable the first and second measurement channel

   1. Press <kbd>p</kbd>
   2. Remove the default axis config for the first measurement channel (press <kbd>⌫</kbd> at least one time)
   3. Enter the characters “23456789ab”
   4. The last step should not have changed the empty input value
   5. Enable the first measurement channel:
      1. Press <kbd>1</kbd>
      2. Press <kbd>⏎</kbd>
   6. Enable the second measurement channel:
      1. Press <kbd>⌫</kbd>
      2. Press <kbd>1</kbd>
      3. Press <kbd>⏎</kbd>
   7. Disable the third measurement channel:
      1. Press <kbd>⌫</kbd>
      1. Press <kbd>0</kbd>
      1. Press <kbd>⏎</kbd>

9. Start the data acquisition

   1. Press <kbd>s</kbd>
   2. Shake the STH
   3. Make sure that shaking the STH changes (at least) the displayed value for the first measurement channel
   4. Wait until the measurement took place

10. Check the output file

    1. Check that the HDF5 output file exists: The filename should start with the characters “Test” followed by a timestamp and the extension “.hdf5”
    2. Open the HDF measurement file in [HDFView](#readme:section:measurement-data)
    3. Check that the table contains four columns
    4. One of the columns should have the name `x`
    5. Another column should have the name `y`

### Combined Checks & Tests

While you need to execute some test for ICOc manually, other tests and checks can be automated.

> **Note:** For the text below we assume that you installed [`make`](<https://en.wikipedia.org/wiki/Make_(software)#Makefile>) on your machine.

To run all checks, the STH test and the STU test use the following `make` command:

```sh
make run
```

Afterwards make sure there were no (unexpected) errors in the output of the STH and STU test.

<a name="development:section:release"></a>

## Release

1.  Check that the [**CI jobs** for the `master` branch finish successfully](https://github.com/MyTooliT/ICOc/actions)
2.  Check that the **checks and tests** run without any problems on **Linux**, **macOS** and **Windows**

    1. Set the value of `sth` → `status` in `config.yaml` to `Epoxied`
    2. Execute the command:

       ```sh
       make run
       ```

       in the root of the repository

3.  Check that the **firmware flash** works in Windows

    - Execute `test-sth`

      1. once with `sth` → `status` set to `Epoxied`, and
      2. once set to `Bare PCB`

      in the [configuration](../mytoolit/config/config.yaml). To make sure, that the STU flash test also works, please use both STU test commands described in the section [“STU Test”](#development:section:stu-test).

      If you follow the steps above you make sure that the **flash tests work** for both STU and STH, and there are **no unintentional consequences of (not) flashing the chip** before you run the other parts of the test suite.

4.  Execute the **[extended manual tests](#development:section:extended-tests)** in Windows and check that everything works as expected

5.  Create a new release [here](https://github.com/MyTooliT/ICOc/releases/new)

    1. Open the [release notes](Releases) for the latest version
    2. Replace links with a permanent version:

       For example instead of

       - `../../something.txt` use
       - `https://github.com/MyTooliT/ICOc/blob/REVISION/something.txt`,

       where `REVISION` is the latest version of the master branch (e.g. `8568893f` for version `1.0.5`)

    3. Commit your changes
    4. Copy the release notes
    5. Paste them into the main text of the release web page
    6. Decrease the header level of each section by two
    7. Remove the very first header
    8. Check that all links work correctly

6.  Change the [`__version__`](../mytoolit/__init__.py) number inside the [`mytoolit`](../mytoolit) package
7.  [Update the Docker images](#tutorials:section:updating-images-on-docker-hub)
8.  Push the latest two commits
9.  Update the [official ICOc Python package on PyPI](https://pypi.org/project/icoc):

    1.  Install `build` and `twine`:

        ```sh
        pip install --upgrade build twine
        ```

    2.  Build the package (in the root directory of the repository):

        ```sh
        python3 -m build
        ```

    3.  Check the package:

        ```sh
        twine check dist/*
        ```

        The output of the command above should print the text `PASSED` twice.

    4.  Upload the package to PyPI:

        ```sh
        twine upload dist/*
        ```

        > **Note:** For the command above to work you need an API token, which you can create after [logging into the PyPI `mytoolit` account](https://pypi.org/account/login/). If you need access to the account, please contact [René Schwaiger](https://github.com/sanssecours).

10. Insert the version number (e.g. `1.0.5`) into the tag field
11. For the release title use “Version VERSION”, where `VERSION` specifies the version number (e.g. “Version 1.0.5”)
12. Click on “Publish Release”
13. Close the [milestone][] for the latest release number
14. Create a new [milestone][] for the next release

[milestone]: https://github.com/MyTooliT/ICOc/milestones
