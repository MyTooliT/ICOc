# Scripts

This folder contains various helper scripts that should make working with ICOc easier. We recommend that you add this folder to your path variable so you can execute the scripts, regardless of the current working path.

- `ICOc`: This is a wrapper around `mwt.py`. The script executes `mwyt.py` with the current Python interpreter. All command line arguments to the script will be directly forwarded to `mwt.py`. For example, to read acceleration data for 10 seconds from the STH with the (Bluetooth advertisement) name `01:de:81`, you can use the following command:

  ```sh
  ICOc -n 01:de:81 -r 10
  ```

- `Test-STH`: This wrapper executes the tests for the STH ([`sth.py`][]). All command line arguments of the wrapper will be forwarded to [`sth.py`][].

If one of the above command fails with an execution policy error, then please read the section “How Can I Fix Execution Policy Errors?” in the [FAQ](Documentation/FAQ.md).

[`sth.py`]: ../mytoolit/test/production/sth.py
