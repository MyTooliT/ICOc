# ICOc

The ICOc software is a collection of tools and scripts for the [ICOtronic system](https://www.mytoolit.com/ICOtronic/). Currently the main purpose of the software is

- data collection (via [`mwt.py`](mwt.py) or the [ICOc script](Scripts/ReadMe.md))
- and testing the functionality of the Sensory Holder Assembly (SHA) and Sensory Tool Holder (STH).

For these purposes the software reads data from the Stationary Transceiver Unit (STU) via CAN using the MyTooliT protocol. The STU itself reads from and writes data to the SHA/STH via Bluetooth.

The framework currently requires

- [Microsoft Windows 10](https://microsoft.com/windows), and
- [Python 3.6](https://www.python.org) or newer.

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

MyToolIt Watch requires at least Python `3.6`. Later versions should work too. You can download Python [here](https://www.python.org/downloads).

When you install the package downloaded above, please do not forget to enable the checkbox “Add Python to PATH” in the setup window of the installer.

If you want to also install additional tools, such as the IDE [Spyder](https://www.spyder-ide.org), we recommend you use [Anaconda](https://www.anaconda.com) – instead of the official Python installer – to install Python on your machine.

##### Packages

Since MyToolIt Watch requires additional Python packages you need to install them too. You can do that using the following command inside PowerShell or the old Windows command line interface `cmd.exe` in the _root of this repository_:

```sh
pip install -r requirements.txt
```

The command above will read the file [requirement.txt](requirement.txt) and install all the packages listed in this file.

If you want to manually install the required Python libraries you can use the following command instead:

```sh
pip install dynaconf matplotlib openpyxl pdfrw python-can reportlab windows-curses
```

#### ICOc

Please clone this repository (`git@github.com:MyTooliT/ICOc.git`) to a directory of your choice. You can either use the [command line tool `git`](https://git-scm.com/downloads):

```
git clone git@github.com:MyTooliT/ICOc.git
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

Each log entry is time stamped and tagged. Tags are separated into Information [I], Warnings [W] and Errors [E]. Furthermore, the time stamp is put into the log at logging time and this time stamp has an accuracy of 500ms or better (The operating system and the python interpreter are not real time capable). Not that the common accuracy is usually about 5ms or better.

### Measuring Entry

Each data points gets logged into the log file. Note that AccX stands for acceleration point X, AccY stands for the acceleration point y and AccZ stands for the acceleration point z.

#### Single Measurements

Three measuring points are stored into a single CAN 2.0 message. A CAN message contains a message counter that cyclically increments from 0-255. Thus each message generates three entries in the log with the same message counter (MsgCounter). Moreover, at a reception of a CAN message generates a time stamp (Time Stamp) . Time Stamps in reference to the message counters may be used to determine the correct sampling frequency, message losses and to determine the message jitter (Maximum-Minimums Time determines a jitter). Furthermore, the message value represents the ADC value from the conversion from a sensor voltage to a sensor value. The sensory value transforms to the calibrated International System of Unit (SI) by processing kx+d and the corresponding k and d may be taken from the EEPROM by the configuration commands 0x60(Calibration Factor k) and 0x61(Calibration Factor d). Please see the following example:

[I](2937092ms): MsgCounter: 8; TimeStamp: 236265914.467ms; AccX 32658;
[I](2937092ms): MsgCounter: 8; TimeStamp: 236265914.467ms; AccX 32668;
[I](2937092ms): MsgCounter: 8; TimeStamp: 236265914.467ms; AccX 32671;
[I](2937092ms): MsgCounter: 9; TimeStamp: 236265914.665ms; AccX 32564;
[I](2937092ms): MsgCounter: 9; TimeStamp: 236265914.665ms; AccX 32591;
[I](2937092ms): MsgCounter: 9; TimeStamp: 236265914.665ms; AccX 32693;
[I](2937092ms): MsgCounter: 10; TimeStamp: 236265914.857ms; AccX 32698;
[I](2937092ms): MsgCounter: 10; TimeStamp: 236265914.857ms; AccX 32670;
[I](2937092ms): MsgCounter: 10; TimeStamp: 236265914.857ms; AccX 32578;

In this example 3 CAN messages are received and these messages contain 9 data points (x-dimension in that case). Each CAN message keeps a message counter value(8,9, 10) and the message jitter is 198µs-192µs -> 6µs for that interval.

#### Double and Triple Measurements

A single vector fits into a single CAN 2.0 message. A CAN message contains a message counter that cyclically increments from 0-255. Thus each vector generates a single entry that contains a message counter value(MsgCounter). Moreover, each received CAN message gets time stamped (Time Stamp). Time Stamps in reference to the message counters may be used to determine the correct sampling frequency, message losses and to determine the message jitter (Maximum-Minimums Time determines a jitter). Furthermore, the message value represents the ADC value from the conversion from a sensor voltage to a sensor value. Each sensory value transforms to the calibrated International System of Unit (SI) by processing kx+d and the corresponding k and d may be taken from the EEPROM by the configuration commands 0x60(Calibration Factor k) and 0x61(Calibration Factor d). Please see the following example:

[I](1076702ms): MsgCounter: 197; TimeStamp: 238783540.943ms; AccX 32682; AccY 10904; AccZ 10957;
[I](1076703ms): MsgCounter: 198; TimeStamp: 238783541.115ms; AccX 32654; AccY 10984; AccZ 10972;
[I](1076703ms): MsgCounter: 199; TimeStamp: 238783541.285ms; AccX 32683; AccY 11006; AccZ 10902;

In this example 3 CAN messages are received and these messages contains 3 vectors(x,y, z-dimension in that case). Each CAN message keeps a message counter value(197,198, 199) and the message jitter is 172µs-170µs -> 2µs for that interval.

### Bluetooth Send Counter

Number of send Bluetooth Frames. Note that multiple MyToolIt messages are put into a single Bluetooth frame.

### Bluetooth Receive Counter

Number of received Bluetooth Frames. Note that multiple MyToolIt messages are put into a single Bluetooth frame.

### Bluetooth RSSI

The Receive Signal Strength Indicator determines (approximately) the received signal power. Note that a RSSI over -70dBm determines a good signal quality and below -90dBm determines a poor signal quality. Please mention that this value is taken at the end of the log once (but may be supported during measuring).

### Send Counter

Number of sent messages to a port e.g. STH to STU

### Send Fail Counter

Number of trashed messages at a port. A send message may get trashed in overload cases.

### Send Byte Counter

Number of send bytes at a port. This number correlates to the Send Counter and is determined approximately.

### Receive Counter

Number of received messages from a port e.g. STU to STH

### Receive Fail Counter

Number of dropped messages. This must not happen at all and determines and overloaded computer system.

### Receive Byte Counter

Number of received bytes at a port. This number correlates to the Send Counter and is determined approximately.

### Status Word

The log show the status word of the STU. Please do not take any information out of this log entry.

### Error Word

Error Status Word of the STU and this <u>**Error Status Word must be 0.**</u>

## Production Tests

## STH

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

### Specific Tests

To only run a single test you need the specify its name. For example, to run the test `test__firmware_flash` you can use the following command:

```sh
python sth.py TestSTH.test__firmware_flash
```

You can also run specific tests using pattern matching. To do that use the command line option `-k`. For example to run the firmware flash and the connection test you can use the command:

```sh
python sth.py -k flash -k connection
```

, which executes all tests that contain the text `flash` or `connection`.

### Wrapper Script

We provide a very simple wrapper script for the STH test called [`Test-STH.ps1`](../Scripts/Test-STH.ps1). This script just executes the script `sth.py` with the current Python interpreter forwarding the given command line arguments in the process. If you add the [Scripts](../Scripts) folder to your Windows path variable, you can call the wrapper script (and hence the STH test) regardless of the current path. For example, to execute the EEPROM test just call

```sh
Test-STH -k eeprom
```

inside the Terminal. If this command shows an execution policy error, then please read the section “How Can I Fix Execution Policy Errors?” in the [FAQ](Documentation/FAQ.md).
