# ICOc

The ICOc software is a collection of tools and scripts for the [ICOtronic system](https://www.mytoolit.com/ICOtronic/). Currently the main purpose of the software is

- data collection (via [`mwt.py`](mwt.py) or the [ICOc script](Scripts/ReadMe.md))
- and testing the functionality of the Sensory Holder Assembly (SHA) and Sensory Tool Holder (STH).

For these purposes the software reads data from the Stationary Transceiver Unit (STU) via CAN using the MyTooliT protocol. The STU itself reads from and writes data to the SHA/STH via Bluetooth.

The framework currently requires

- [Microsoft Windows 10](https://microsoft.com/windows), and
- [Python 3.7](https://www.python.org) or newer.

For more information about other required software components, please read the subsection “Software” in this document.

## Requirements

### Hardware

In order to setup a test bench you need at least:

- a [PCAN adapter](https://www.peak-system.com),
- a [Sensory Holder Assembly or Sensory Tool Holder](https://www.mytoolit.com/ICOtronic/),
- a [Stationary Transceiver Unit](https://www.mytoolit.com/ICOtronic/).

### Software

#### Python

##### Interpreter

MyToolIt Watch requires at least Python `3.7`. Later versions should work too. You can download Python [here](https://www.python.org/downloads).

When you install the package downloaded above, please do not forget to enable the checkbox “Add Python to PATH” in the setup window of the installer.

##### Packages

Since MyToolIt Watch requires additional Python packages you need to install them too. You can do that using the following command inside PowerShell or the old Windows command line interface `cmd.exe` in the _root of this repository_:

```sh
pip install -r requirements.txt
```

The command above will read the file [requirement.txt](requirement.txt) and install all the packages listed in this file.

#### ICOc

Please clone [this repository](https://github.com/MyTooliT/ICOc) to a directory of your choice. You can either use the [command line tool `git`](https://git-scm.com/downloads):

```
git clone https://github.com/MyTooliT/ICOc.git
```

or one of the many available [graphical user interfaces for Git](https://git-scm.com/downloads/guis) to do that.

The repository contains everything necessary to connect to an STU via CAN and pull data from the attached STHs.

#### Simplicity Studio

For the tests that require a firmware flash, such as the [production tests](mytoolit/test/production) you need to [install Simplicity Studio](https://www.silabs.com/products/development-tools/software/simplicity-studio). Please also make sure to install the Simplicity Commander tool inside Simplicity Studio.

## Usage

We recommend that you add the [scripts directory](Scripts) to your path environment variable. Afterwards you can use all [the scripts in this folder](Scripts/ReadMe.md) directly in your Terminal application of choice, without the need to change the current working directory.

### Control and Data Acquirement

#### Start the Program

The `ICOc` script can be used to control an STH (or SHA). After you enter the command

```sh
ICOc
```

in your terminal, a text based interface shows you the currently available options. For example, the text

```
MyToolIt Terminal

1: 08:6b:d7:01:de:81(Blubb)@-52dBm

q: Quit program
1-9: Connect to STH number (ENTER at input end)
E: EEPROM (Permanent Storage)
l: Log File Name
n: Change Device Name
t: Test Menu
u: Update Menu
x: Xml Data Base
```

shows that currently one STH was detected. The Bluetooth MAC address of the STH is `08:6b:d7:01:de:81`, while its advertisement name is “Blubb”. The last value after the `@` character shows the current received signal strength indication (RSSI). You can exit the program using the interface using the key <kbd>q</kbd>.

#### Read Acceleration Data

To read data from an STH (or SHA), start the ICOc script, and connect to an STH. To do that, enter the number of the detected STH and use the return key <kbd>⮐</kbd> to confirm your selection. The text based interface will now show you something like this:

```
08:6b:d7:01:de:81(Tanja)
Global Trade Identification Number (GTIN): 0
Hardware Revision(Major.Minor.Build): 1.3.5
Firmware Version(Major.Minor.Build): 2.1.10
Firmware Release Name: Tanja
Serial: -

Battery Voltage: 3.05V
Internal Chip Temperature: 29.6°C

Run Time: 0s
Interval Time: 0s
Adc Prescaler/AcquisitionTime/OversamplingRate/Reference(Samples/s): 2/8/64/VDD(9524)
Acc Config(XYZ/DataSets): 100/3

a: Config ADC
d: Display Time
e: Exit and disconnect from holder
f: OEM Free Use
n: Set Device Name
O: Off(Standby)
p: Config Acceleration Points(XYZ)
r: Config run time and interval time
s: Start Data Acquisition
```

To start the data acquisition press the key <kbd>s</kbd>. Afterwards a graphical window

![Acceleration](Documentation/Pictures/Acceleration.png)

will show the measured acceleration. To stop the data acquisition, click the close button on the top of the graph.

## Logging

The ICOc script writes measured acceleration values and other data into log files at the root of the repository. Each log entry is time stamped and tagged.

Tags are separated into

- information `[I]`,
- warnings `[W]`,
- and errors `[E]`.

For example, the following log entries

```
[I](2937092ms): MsgCounter: 8; TimeStamp: 236265914.467ms; AccX 32658;
[I](2937092ms): MsgCounter: 8; TimeStamp: 236265914.467ms; AccX 32668;
[I](2937092ms): MsgCounter: 8; TimeStamp: 236265914.467ms; AccX 32671;
[I](2937092ms): MsgCounter: 9; TimeStamp: 236265914.665ms; AccX 32564;
[I](2937092ms): MsgCounter: 9; TimeStamp: 236265914.665ms; AccX 32591;
[I](2937092ms): MsgCounter: 9; TimeStamp: 236265914.665ms; AccX 32693;
[I](2937092ms): MsgCounter: 10; TimeStamp: 236265914.857ms; AccX 32698;
[I](2937092ms): MsgCounter: 10; TimeStamp: 236265914.857ms; AccX 32670;
[I](2937092ms): MsgCounter: 10; TimeStamp: 236265914.857ms; AccX 32578;
```

show you data for 3 CAN messages (with message counter 8, 9 and 10) that the software received 2937092 milliseconds after the ICOc script started. As you can see every CAN message contains three acceleration values. Please note that

- `AccX` specifies the acceleration in x direction,
- `AccY` specifies the acceleration in y direction, and
- `AccZ` specifies the acceleration in z direction.

In our example ICOc only measured the acceleration in the x direction. The measured acceleration values around `32578` and `32698` show you that the sensor was probably in a stationary position. This assumption is based on the fact that a value of 0 represents the maximum negative acceleration value and the maximum ADC value (usually 2¹⁶-1 for a 16 bit ADC) represents the maximum positive acceleration value. For a 16 bit ADC, an acceleration of 0 m/s is represented by an value of about (2¹⁶-1)/2 ≅ 65535.

The time stamp inside the CAN message (`TimeStamp`) together with the cyclically incrementing message counter (0-255) may be used to determine

- the correct sampling frequency,
- message loss, and
- the message jitter.

For our example, the message jitter (maximum time - minimum time between messages) for our example data is 6µs (198µs-192µs).

Currently most of the STHs (or SHAs) only measure the acceleration in the x direction. For those that measure the acceleration in different directions, the log format for the acceleration is a little bit different. For example, a sensor that measures the acceleration in all three directions produces log entries that look like this:

```
[I](1076702ms): MsgCounter: 197; TimeStamp: 238783540.943ms; AccX 32682; AccY 10904; AccZ 10957;
[I](1076703ms): MsgCounter: 198; TimeStamp: 238783541.115ms; AccX 32654; AccY 10984; AccZ 10972;
[I](1076703ms): MsgCounter: 199; TimeStamp: 238783541.285ms; AccX 32683; AccY 11006; AccZ 10902;
```

As you can see instead of transmitting three x acceleration values, the STH instead stores one acceleration value in x, y and z direction.

## Production Tests

### STH

To run the production tests for the STH, please execute the following command in the root of the repository:

```sh
python mytoolit/test/production/sth.py
```

If you change the current working directory to the test directory:

```sh
cd mytoolit/test/production
```

then you can invoke the command directly via

```sh
python sth.py
```

Depending on your environment, using `py` instead of `python` might also work:

```sh
py sth.py
```

For a list of available command line options, please use the option `-h`:

```sh
python sth.py -h
```

#### Specific Tests

To only run a single test you need the specify its name. For example, to run the test `test__firmware_flash` you can use the following command:

```sh
python sth.py TestSTH.test__firmware_flash
```

You can also run specific tests using pattern matching. To do that use the command line option `-k`. For example to run the firmware flash and the connection test you can use the command:

```sh
python sth.py -k flash -k connection
```

, which executes all tests that contain the text `flash` or `connection`.

#### Wrapper Script

We provide a very simple wrapper script for the STH test called [`Test-STH.ps1`](../Scripts/Test-STH.ps1). This script just executes the script `sth.py` with the current Python interpreter forwarding the given command line arguments in the process. If you add the [Scripts](../Scripts) folder to your Windows path variable, you can call the wrapper script (and hence the STH test) regardless of the current path. For example, to execute the EEPROM test just call

```sh
Test-STH -k eeprom
```

inside the Terminal. If this command shows an execution policy error, then please read the section “How Can I Fix Execution Policy Errors?” in the [FAQ](Documentation/FAQ.md).

### STU

The explanation for the STH test apply also for the STU tests. Please just replace `STH` (or `sth`) in the previous section with the term `STU` (respective `stu`). For example, to execute all tests for the STU you can use the following command:

```sh
Test-STU
```
