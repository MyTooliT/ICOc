---
title: ICOc Documentation
author: MyTooliT
---

# ICOc

The ICOc software is a collection of tools and scripts for the [ICOtronic system](https://www.mytoolit.com/ICOtronic/). Currently the main purpose of the software is

- data collection (via the script `icoc`)
- and testing the functionality of the Sensory Holder Assembly (SHA) and Sensory Tool Holder (STH).

For these purposes the software reads data from the Stationary Transceiver Unit (STU) via CAN using the MyTooliT protocol. The STU itself reads from and writes data to the SHA/STH via Bluetooth.

The framework currently requires

- [Microsoft Windows 10](https://microsoft.com/windows), and
- [Python 3.7](https://www.python.org) or newer.

For more information about other required software components, please read the subsection [“Software”](#section:software) in this document.

## Documentation

While you should be able to read the various Markdown files of the documentation (this file and the files in the directory `Documentation`) separately, we recommend you read the [bookdown](https://bookdown.org) manual instead. We provide a prebuilt version of the documentation [here](https://github.com/MyTooliT/ICOc/actions/workflows/documentation.yaml) (just select the latest run and click on the link “ICOc Manual”) or in the [Bitrix24 drive of MyToolit](https://mytoolit.bitrix24.de/docs/path/Documentation Repositories/ICOc/).

### Build

If you want to build the documentation yourself, you need the following software:

- [R](https://www.r-project.org),
- [bookdown](https://bookdown.org),
- [make](<https://en.wikipedia.org/wiki/Make_(software)>), and
- (optionally for the PDF version of the manual) the [TinyTeX R package](https://yihui.org/tinytex/).

After you installed the required software you can build the

- HTML (`make html`),
- EPUB (`make epub`), and
- PDF (`make pdf`)

version of the documentation. The output will be stored in the folder `Bookdown` in the root of the repository. If you want to build all versions of the documentation, just use the command

```
make
```

in the repo root.

## Requirements

### Hardware

In order to setup a test bench you need at least:

- a [PCAN adapter](https://www.peak-system.com):

  ![PCAN Adapter](Documentation/Pictures/PCAN.jpg)

  including:

  - power injector, and
  - power supply unit (for the power injector):

    ![Power Injector](Documentation/Pictures/Power-Injector.jpg)

- a [Stationary Transceiver Unit](https://www.mytoolit.com/ICOtronic/)

   <img src="https://cdn.bitrix24.de/b5488381/landing/5fa/5fa2ce04fd1326e07bf39866e44f4e61/IMG_6338_2x.jpg" alt="STU" width="400">

- a [Sensory Holder Assembly or Sensory Tool Holder](https://www.mytoolit.com/ICOtronic/)

   <img src="https://cdn.bitrix24.de/b5488381/landing/cbe/cbe07df56cea688299533819c1e8a8d3/IMG_6350_2x_2x.jpg" alt="STH" width="400">

#### Setup

1. Connect the power injector
   1. to the PCAN adapter, and
   2. the power supply unit
2. Connect the USB connector of the PCAN adapter to your computer
3. Make sure that your SHA/STH is connected to a power source. For an STH this usually means that you should check that the battery is (fully) charged.

<a name="section:software"></a>

### Software

#### Python

ICOc requires at least Python `3.7`. Later versions should work too. You can download Python [here](https://www.python.org/downloads).

When you install Python, please do not forget to enable the checkbox **“Add Python to PATH”** in the setup window of the installer.

<a name="readme:section:pytables"></a>

##### PyTables

ICOc uses the [PyTables][] Python package. Unfortunately only binaries for Linux are available in the Python package index for [PyTables][]. This means installing PyTables (and therefore ICOc) in Windows without a C compiler and the [HDF5 library](https://www.hdfgroup.org/downloads/hdf5/) library will fail. Since compiling the C extension of the package is not trivial we **recommend downloading a prebuilt binary package** [here](http://www.lfd.uci.edu/~gohlke/pythonlibs/#pytables). Just store the proper file for **your OS and Python version** in your **Downloads folder**.

**Example:** For a 64 bit version of Python `3.9` and PyTables `3.6.1` download the file `tables‑3.6.1‑cp39‑cp39‑win_amd64.whl` and afterwards execute the following command in a PowerShell session:

```pwsh
pip install $HOME\Downloads\tables-3.6.1-cp39-cp39-win_amd64.whl
```

We also offer **the same binaries** for all supported 64 bit Python versions in the [**branch binaries**](https://github.com/mytoolit/ICOc/tree/binaries) of the repository. For example, to **install [PyTables][] on Python 3.9** you can use the following commands in a PowerShell session:

```sh
cd "$HOME/Downloads"
git clone -b binaries https://github.com/MyTooliT/ICOc.git
cd ICOc
pip install tables-3.6.1-cp39-cp39-win_amd64.whl
cd ..
Remove-Item -Recurse -Force ICOc
```

[pytables]: http://www.pytables.org

#### PCAN Driver

To communicate with the STU you need to install the driver for the PCAN adapter. You can find the download link for Windows [here](https://www.peak-system.com/quick/DrvSetup). Please make sure that you include the “PCAN-Basic API” when you install the driver.

#### Simplicity Studio

For the tests that require a firmware flash you need to [install Simplicity Studio](https://www.silabs.com/products/development-tools/software/simplicity-studio). Please also make sure to install the Simplicity Commander tool inside Simplicity Studio.

<a name="readme:section:install"></a>

## Install

Please clone [this repository](https://github.com/MyTooliT/ICOc) to a directory of your choice. You can either use the [command line tool `git`](https://git-scm.com/downloads):

```sh
git clone https://github.com/MyTooliT/ICOc.git
```

or one of the many available [graphical user interfaces for Git](https://git-scm.com/downloads/guis) to do that.

The repository contains everything necessary to communicate with an STU over CAN to retrieve data from an STH.

Before you use the software you need to install it (in developer mode). To do that please run the following command in the root of the repository:

```sh
pip install -e .
```

Afterwards you can use the various [scripts](Documentation/Scripts.md) included in the package.

### Troubleshooting

#### Insufficient Rights

**If you do not have sufficient rights** to install the package you can also try to install the package in the user folder:

```sh
pip install --user -e .
```

#### Unknown Command `icoc`

If `pip install` prints **warnings about the path** that look like this:

> The script … is installed in `'…\Scripts'` which is not on PATH.

then please add the text between the single quotes (without the quotes) to your [PATH environment variable](https://helpdeskgeek.com/windows-10/add-windows-path-environment-variable/). Here `…\Scripts` is just a placeholder. Please use the value that `pip install` prints on your machine. If you used the [installer from the Python website](https://www.python.org/downloads) (and checked “Add Python to PATH”) or you used [winget](https://docs.microsoft.com/en-us/windows/package-manager/winget/) to install Python, then the warning above should not appear. On the other hand, the **Python version from the [Microsoft Store](https://www.microsoft.com/en-us/store/apps/windows) might not add the `Scripts` directory** to your path.

#### Installing `tables` Package Fails

If installing ICOc, specifically the `tables` ([PyTables](http://pytables.org)) package on your machine fails with the following error message:

> ERROR:: Could not find a local HDF5 installation

then please take a look [here](#readme:section:pytables).

## Control and Data Acquirement

### Start the Program

The `ICOc` script can be used to control an STH (or SHA). After you enter the command

```sh
icoc
```

in your terminal, a text based interface shows you the currently available options. For example, the text

```
ICOc

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

shows that currently one STH was detected. The Bluetooth MAC address of the STH is `08:6b:d7:01:de:81`, while its advertisement name is “Blubb”. The last value after the `@` character shows the current received signal strength indication (RSSI). To exit the program use the key <kbd>q</kbd>.

### Read Acceleration Data

To read data from an STH (or SHA), start the ICOc script, and connect to an STH. To do that, enter the number in front of an STH entry (e.g. `1` for the first detected STH) and use the return key <kbd>⮐</kbd> to confirm your selection. The text based interface will now show you something like this:

```
08:6b:d7:01:de:81(Blubb)
Global Trade Identification Number (GTIN): 0
Hardware Version(Major.Minor.Build): 1.3.5
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

In our example ICOc only measured the acceleration in the x direction. The measured acceleration values around `32578` and `32698` show you that the sensor was probably in a stationary position. This assumption is based on the fact that a value of 0 represents the maximum negative acceleration value and the maximum ADC value (usually 2¹⁶-1 for a 16 bit ADC) represents the maximum positive acceleration value. For a 16 bit ADC, an acceleration of 0 m/s is represented by an value of about 2¹⁶/2 = 2¹⁵ = 32768. The 16 bit ADC acceleration value for the gravitational acceleration on Earth (1·g) should be around:

$$(1+100) · \frac{2^{16}}{200} ≅ 33096$$

if we assume a ±100g sensor, which is close to the measured values (`32578` and `32698`). The smallest measured value `32578` should be roughly equivalent to $-0.6 · g$:

$$32578 · \frac{2^{16}}{200} - 100 ≅ -0.58 · g$$

The time stamp inside the CAN message (`TimeStamp`) together with the cyclically incrementing message counter (0-255) may be used to determine

- the correct sampling frequency,
- message loss, and
- the message jitter.

For our example, the message jitter (maximum time - minimum time between messages) is 6µs (198µs-192µs).

Currently most of the STHs (or SHAs) only measure the acceleration in the x direction. For those that measure the acceleration in different directions, the log format for the acceleration is a little bit different. For example, a sensor that measures the acceleration in all three directions produces log entries that look like this:

```
[I](1076702ms): MsgCounter: 197; TimeStamp: 238783540.943ms; AccX 32682; AccY 10904; AccZ 10957;
[I](1076703ms): MsgCounter: 198; TimeStamp: 238783541.115ms; AccX 32654; AccY 10984; AccZ 10972;
[I](1076703ms): MsgCounter: 199; TimeStamp: 238783541.285ms; AccX 32683; AccY 11006; AccZ 10902;
```

As you can see instead of transmitting three x acceleration values, the STH instead stores one acceleration value in x, y and z direction.
