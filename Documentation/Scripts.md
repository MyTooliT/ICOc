<a name="scripts:section:scripts"></a>

# Scripts

After you installed the ICOc package various helper scripts are available:

- [`convert-base64-mac`](#section:mac-address-conversion): Utility to convert a Base64 encoded 8 character text into a Bluetooth MAC address
- [`convert-mac-base64`](#section:mac-address-conversion): Convert Bluetooth MAC address into a (Base64) encoded 8 character string
- [`check-eeprom`](#section:eeprom-check): Write a byte value into the cells of an EEPROM page an check how many of the values are read incorrectly after an reset
- [`icoc`](#section:icoc): Controller and measurement software for the ICOtronic system
- [`icon`](#section:icon): Controller software for the ICOtronic system
- [`test-smh`](#section:test-smh): Test code for the SMH
- [`test-sth`](#section:test-sth): Test code for the STH/SHA
- [`test-stu`](#section:test-stu): Test code for the STU

<a name="section:eeprom-check"></a>

## EEPROM Check

The script `check-eeprom` connects to an STH using its MAC address. Afterwards it writes a given byte value (default: `10`) into all the cells of an EEPROM page. It then resets the STH, connects again and shows the amount of incorrect EEPROM bytes. It repeats the last steps 5 times before it prints all values in the EEPROM page.

The command below shows how to execute the EEPROM check for the STH with MAC address `08:6b:d7:01:de:81`:

```sh
check-eeprom 08:6b:d7:01:de:81
```

You can specify the value that should be written into the EEPROM cells using the option `--value`:

```sh
check-eeprom 08:6b:d7:01:de:81 --value 42
```

<a name="section:icoc"></a>

## ICOc

The command `icoc` calls `ui.py`. All command line arguments to the script will be directly forwarded to `ui.py`. For example, to read acceleration data for 10 seconds from the STH with the (Bluetooth advertisement) name `CGvXAd6B`, you can use the following command:

```sh
icoc -n CGvXAd6B -r 10
```

<a name="section:icon"></a>

## ICOn

The command ICOn uses the [new `Network` class](../mytoolit/can/network.py) (based on [`python-can`](https://python-can.readthedocs.io)) to communicate with the ICOtronic system. Compared to ICOc the script currently offers very limited functionality. However, in the future most of the functionality from ICOc should be integrated into this new command line tool. A big advantage of ICOn compared to ICOc is that the command **also works on Linux and macOS**. For more information, please take a look [here](#tutorials:section:icon-cli-tool).

<a name="section:mac-address-conversion"></a>

## MAC Address Conversion

The utility `convert-mac-base64` returns the Base64 encoded version of a MAC address. We use the encoded addresses as unique Bluetooth advertisement name for the STH (or SHA). Unfortunately we can not use the MAC address directly because the maximum length of the name is limited to 8 characters. To decode the Base64 name back into a Bluetooth address you can use the script `convert-base64-mac`.

### Examples

```sh
# Convert a MAC address into an 8 character name
convert-mac-base64 08:6b:d7:01:de:81
#> CGvXAd6B

# Convert the Base64 encoded name back into a MAC address
convert-base64-mac CGvXAd6B
#> 08:6b:d7:01:de:81
```

<a name="section:remove-log-and-pdf-files"></a>

## Test-STH

The command `test-sth` is a command that executes the tests for the STH ([`sth.py`][]). All command line arguments of the wrapper will be forwarded to [`sth.py`][].

[`sth.py`]: ../mytoolit/test/production/sth.py

<a name="section:test-stu"></a>

## Test-STU

The command `test-stu` is a wrapper that executes the tests for the STU ([`stu.py`][]). All command line arguments of the wrapper will be forwarded to [`stu.py`][].

[`stu.py`]: ../mytoolit/test/production/stu.py

<a name="section:test-smh"></a>

## Test-SMH

The command `test-smh` is a wrapper that executes the tests for the SMH ([`smh.py`][]). All command line arguments of the wrapper will be forwarded to [`smh.py`][].

[`smh.py`]: ../mytoolit/test/production/smh.py
