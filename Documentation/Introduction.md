---
title: ICOc Documentation
author: MyTooliT
description: Tools and scripts for the ICOtronic system
---

# ICOc

ICOc is a collection of tools and scripts for the [ICOtronic system](https://www.mytoolit.com/ICOtronic/). Currently the main purpose of the software is

- **data collection** (via the script `icoc`) and
- **testing** the functionality of
  - Stationary Transceiver Unit (STU) and
  - sensor devices/nodes, such as
    - Sensory Holder Assembly (SHA)/Sensory Tool Holder (STH)
    - Sensory Milling Head (SMH)

The software reads data from the Stationary Transceiver Unit (STU) via CAN using the MyTooliT protocol. The STU itself reads from and writes data to the sensor devices via Bluetooth.

The framework currently requires

- [Microsoft Windows 10](https://microsoft.com/windows), and
- [Python 3](#introduction:section:python).

**Notes**:

- In theory you can also use ICOc in Windows 11. However, we did not test the software on this operating system.
- The test suite (which uses a CAN class based on [python-can](https://python-can.readthedocs.io)) also works on Linux and macOS. The ICOc measurement software does [**not**](https://github.com/MyTooliT/ICOc/issues/4). For more information on how to use (parts of) the ICOc software on Linux, please take a look [here](#introduction:section:pcan-driver:linux).

For more information about other required software components, please read the subsection [“Software”](#section:software) in this document.

## Requirements

### Hardware

In order to use ICOc you need at least:

- a [PCAN adapter](https://www.peak-system.com):

  ![PCAN Adapter](Documentation/Pictures/PCAN.jpg)

  including:

  - power injector, and
  - power supply unit (for the power injector):

    ![Power Injector](Documentation/Pictures/Power-Injector.jpg)

- a [Stationary Transceiver Unit](https://www.mytoolit.com/ICOtronic/):

   <img src="https://cdn.bitrix24.de/b5488381/landing/5fa/5fa2ce04fd1326e07bf39866e44f4e61/IMG_6338_2x.jpg" alt="STU" width="400">

- a sensor device, such as a [Sensory Tool Holder](https://www.mytoolit.com/ICOtronic/):
  <img src="https://cdn.bitrix24.de/b5488381/landing/cbe/cbe07df56cea688299533819c1e8a8d3/IMG_6350_2x_2x.jpg" alt="Sensory Tool Holder" width="400">

#### Setup

1. Connect the power injector
   1. to the PCAN adapter, and
   2. the power supply unit.
2. Connect the USB connector of the PCAN adapter to your computer.
3. Make sure that your sensor device (SHA/STH/SMH) is connected to a power source. For an STH this usually means that you should check that the battery is (fully) charged.

<a name="section:software"></a>

### Software

<a name="introduction:section:python"></a>

#### Python

ICOc requires at least Python `3.7`. The software also supports Python `3.8`, `3.9` and `3.10`. You can download Python [here](https://www.python.org/downloads). When you install the software, please do not forget to enable the checkbox **“Add Python to PATH”** in the setup window of the installer.

#### PCAN Driver

To communicate with the STU you need a driver that works with the PCAN adapter. The text below describes how to install/enable this driver on

- [Linux](#introduction:section:pcan-driver:linux),
- [macOS](#introduction:section:pcan-driver:macos), and
- [Windows](#introduction:section:pcan-driver:windows).

<a name="introduction:section:pcan-driver:linux"></a>

##### Linux

You need to make sure that your CAN adapter is available via the [SocketCAN](https://en.wikipedia.org/wiki/SocketCAN) interface.

The following steps describe one possible option to configure the CAN interface on [Fedora Linux](https://getfedora.org) **manually**.

1. Connect the CAN adapter to the computer that runs Linux (or alternatively the Linux VM)
2. Check the list of available interfaces:

   ```sh
   networkctl list
   ```

   The command output should list the CAN interface with the name `can0`

3. Configure the CAN interface with the following command:

   ```
   sudo ip link set can0 type can bitrate 1000000
   ```

4. Bring up the CAN interface

   ```
   sudo ip link set can0 up
   ```

You can also bring up the CAN interface **automatically**. For that please store the following text:

```ini
[Match]
Name=can*

[CAN]
BitRate=1000000
```

in a file called `/etc/systemd/network/can.network`. After that you can either restart your computer/VM or reload the configuration with the command:

```sh
networkctl reload
```

**Sources**:

- [SocketCAN device on Ubuntu Core](https://askubuntu.com/questions/1082277/socketcan-device-on-ubuntu-core)
- [Question: How can I automatically bring up CAN interface using netplan?](https://github.com/linux-can/can-utils/issues/68#issuecomment-584505426)
- [networkd › systemd › Wiki › ubuntuusers](https://wiki.ubuntuusers.de/systemd/networkd/)

<a name="introduction:section:pcan-driver:macos"></a>

##### macOS

On macOS you can use the [PCBUSB](https://github.com/mac-can/PCBUSB-Library) library to add support for the PCAN adapter. For more information on how to install this library please take a look [here](https://github.com/mac-can/PCBUSB-Library/issues/10#issuecomment-1188682027).

<a name="introduction:section:pcan-driver:windows"></a>

##### Windows

You can find the download link for the PCAN Windows driver [here](https://www.peak-system.com/quick/DrvSetup). Please make sure that you include the “PCAN-Basic API” when you install the software.

#### Simplicity Commander (Optional)

For the tests that require a firmware flash you need to **either** install

- [Simplicity Studio](https://www.silabs.com/products/development-tools/software/simplicity-studio) or
- [Simplicity Commander](https://www.silabs.com/developers/mcu-programming-options).

If you choose the first option, then please make sure to install the Simplicity Commander tool inside Simplicity Studio.

If you download Simplicity Commander directly, then the tests assume that you unzipped the files into the directory `C:\SiliconLabs\Simplicity Commander` on Windows.

- If you do not use the standard install path on **Windows**, then please add the path to `commander.exe` to the list `COMMANDS` → `PATH` → `WINDOWS` in the configuration file `config.yaml`.
- If you use **Linux**, then please add the path to `commander` to the list `COMMANDS` → `PATH` → `LINUX`.
- If you install Simplicity Studio in the standard install path on **macOS** (`/Applications`) you do not need to change the config. If you

  - put the application in a different directory or
  - installed Simplicity Commander directly

  then please add the path to `commander` to the list `COMMANDS` → `PATH` → `MAC`.

If you do not want to change the config file, then please just make sure that `commander` is accessible via the `PATH` environment variable.

Please note, that you do not need to install Simplicity Commander if you just want to measure data with ICOc.

<a name="introduction:section:install"></a>

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

Afterwards you can use the various [scripts](#scripts:section:scripts) included in the package.

### Troubleshooting

#### Import Errors

If one of the tests or ICOc fails with an error message that looks similar to the following text:

```
Traceback (most recent call last):
…
    from numexpr.interpreter import MAX_THREADS, use_vml, __BLOCK_SIZE1__
ImportError: DLL load failed while importing interpreter: The specified module could not be found.

DLL load failed while importing interpreter: The specified module could not be found.
```

then you probably need to install the [“Microsoft Visual C++ Redistributable package” ](https://docs.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist). You can download the latest version (for the `x64` architecture) [here](https://aka.ms/vs/17/release/vc_redist.x64.exe).

#### Insufficient Rights

**If you do not have sufficient rights** to install the package you can also try to install the package in the user folder:

```sh
pip install --user -e .
```

The command above might not work on Linux due to [a bug in `pip`](https://github.com/pypa/pip/issues/7953). In that case you can try the following [workaround](https://github.com/pypa/pip/issues/7953#issuecomment-1027704899) to install ICOc:

```sh
python3 -m pip install --prefix=$(python3 -m site --user-base) -e .
```

#### Unknown Command `icoc`

If `pip install` prints **warnings about the path** that look like this:

> The script … is installed in `'…\Scripts'` which is not on PATH.

then please add the text between the single quotes (without the quotes) to your [PATH environment variable](https://helpdeskgeek.com/windows-10/add-windows-path-environment-variable/). Here `…\Scripts` is just a placeholder. Please use the value that `pip install` prints on your machine. If you used the [installer from the Python website](https://www.python.org/downloads) (and checked “Add Python to PATH”) or you used [winget](https://docs.microsoft.com/en-us/windows/package-manager/winget/) to install Python, then the warning above should not appear. On the other hand, the **Python version from the [Microsoft Store](https://www.microsoft.com/en-us/store/apps/windows) might not add the `Scripts` directory** to your path.

## Basic Usage

### Starting the Program

The `ICOc` script can be used to control a sensor device. After you enter the command

```sh
icoc
```

in your [terminal](https://aka.ms/terminal), a text based interface shows you the currently available options. For example, the text

```
                ICOc

       Name      Address            RSSI
———————————————————————————————————————————————
    1: Blubb     08:6b:d7:01:de:81  -44 dBm

┌──────────────────────────────┐
│ 1-9: Connect to STH          │
│                              │
│   f: Change Output File Name │
│   n: Change STH Name         │
│                              │
│   q: Quit ICOc               │
└──────────────────────────────┘
```

shows that currently one sensor device was detected. The

- Bluetooth MAC address of the device is `08:6b:d7:01:de:81`, while its
- advertisement name is “Blubb”.

The last value “-44” is the current [received signal strength indication (RSSI)](https://en.wikipedia.org/wiki/Received_signal_strength_indication). To exit the program use the key <kbd>q</kbd>.

### Reading Acceleration Data

To read data from an STH (or SHA), start the ICOc script, and connect to an STH. To do that, enter the number in front of an STH entry (e.g. `1` for the first detected STH) and use the return key <kbd>⮐</kbd> to confirm your selection. The text based interface will now show you something like this:

```
                ICOc
STH “Blubb” (08:6b:d7:01:de:81)
———————————————————————————————

Hardware Version      1.4.0
Firmware Version      2.1.10
Firmware Release Name Tanja
Serial Number         –

Supply Voltage        3.16 V
Chip Temperature      26.2 °C

Run Time              ∞ s

Prescaler             2
Acquisition Time      8
Oversampling Rate     64
⇒ Sampling Rate       9524
Reference Voltage     VDD

Sensors               X

┌───────────────────────────┐
│ s: Start Data Acquisition │
│                           │
│ n: Change STH Name        │
│ r: Change Run Time        │
│ a: Configure ADC          │
│ p: Configure Sensors      │
│ O: Set Standby Mode       │
│                           │
│ q: Disconnect from STH    │
└───────────────────────────┘
```

To start the data acquisition press the key <kbd>s</kbd>. Afterwards a graphical window

![Acceleration](Documentation/Pictures/Acceleration.png)

will show the measured acceleration. To stop the data acquisition, click the close button on the top of the graph. For more information on how to use ICOc and the test suite, please take a look at the [section “Tutorials”](#tutorials:section:tutorials).

<a name="introduction:section:measurement-data"></a>

## Measurement Data

The ICOc script stores measured acceleration values in [HDF5](https://www.hdfgroup.org/solutions/hdf5/) files. By default these files will be stored in the root of the repository with a

- name starting with the text `Measurement`
- followed by a date/time-stamp,
- and the extension `.hdf5`.

To take a look at the measurement data you can use the tool [HDFView][]. Unfortunately you need to create a free account to download the program. If you do not want to register, then you can try if [one of the accounts listed at BugMeNot](http://bugmenot.com/view/hdfgroup.org) works.

[hdfview]: https://www.hdfgroup.org/downloads/hdfview/

The screenshot below shows a measurement file produced by ICOc:

![Main Window of HDFView](Documentation/Pictures/HDFView-File.png)

As you can see the table with the name `acceleration` stores the acceleration data. The screenshot above displays the metadata of the table. The most important meta attributes here are probably:

- `Start_Time`, which contains the start time of the measurement run in ISO format, and
- `Sensor_Range`, which specifies the range of the used acceleration sensor in multiples of earth’s gravitation (g₀ ≅ 9.81 m/s²).

After you double click on the acceleration table on the left, HDFView will show you the actual acceleration data:

![Acceleration Table in HDFView](Documentation/Pictures/HDFView-Table.png)

As you can infer from the `x` column above the table shows the acceleration measurement data (in multiples of g₀) for a single axis. The table below describes the meaning of the columns:

| Column    | Description                                                                              | Unit             |
| --------- | ---------------------------------------------------------------------------------------- | ---------------- |
| counter   | A cyclic counter value (0–255) sent with the acceleration data to recognize lost packets | –                |
| timestamp | The timestamp for the measured value in microseconds since the measurement start         | μs               |
| x         | Acceleration in the x direction as multiples of earth’s gravitation                      | g₀ (≅ 9.81 m/s²) |

Depending on your sensor and your settings the table might also contain columns for the `y` and/or `z` axis.

If you want you can also use HDFView to print a simple graph for your acceleration data. To do that:

1. Select the values for the the ordinate (e.g. click on the x column to select all acceleration data for the x axis)
2. Click on the graph icon in the top left corner
3. Choose the data for the abscissa (e.g. the timestamp column)
4. Click on the “OK” button

The screenshot below shows an example of such a graph:

![Acceleration Graph in HDFView](Documentation/Pictures/HDFView-Graph.png)

### Adding Custom Metadata

Sometimes you also want to add additional data about a measurement. To do that you can also use [HDFView][]. Since the tool opens files in read-only mode by default you need to change the default file access mode to “Read/Write” first:

1. Open [HDFView][]
2. Click on “Tools” → “User Options”
3. Select “General Settings”
4. Under the text “Default File Access Mode” choose “Read/Write”
5. Close HDFView

Now you should be able to add and modify attributes. For example, to add a revolutions per minute (RPM) value of `15000` you can use the following steps:

1. Open the measurement file in [HDFView][]
2. Click on the table “acceleration” in the left part of the window
3. In the tab “Object Attribute Info” on the right, click on the button “Add attribute”
4. Check that “Object List” contains the value “/acceleration”
5. Enter the text “RPM” in the field “Name”
6. In the field “Value” enter the text “15000”
7. The “Datatype Class” should be set to “INTEGER”
8. For the size (in bits) choose a bit length that is large enough to store the value. In our example everything equal to or larger than 16 bits should work.
9. Optionally you can also check “Unsigned”, if you are sure that you only want to store positive values
10. Click the button “OK”

![HDFView: RPM Attribute](Documentation/Pictures/HDFView-RPM.png)

Sometimes you also want to add some general purpose data. For that you can use the “STRING” datatype class. For example, to store the text “hello world” in an attribute called “Comment” you can do the following

1. Repeat steps 1. – 4. from above
2. Choose “STRING” as “Datatype Class”
3. Under “Array Size” choose a length that is large enough to store the text such as “1000” (every size larger than or equal to 11 characters should work)
4. Click the button “OK”

![HDFView: Comment Attribute](Documentation/Pictures/HDFView-Comment.png)

If you want you can also add multiline text. Since you can not add newlines using <kbd>⏎</kbd> in HDFView directly, we recommend you open your favorite text editor to write the text and then copy and paste the text into the value field. HDFView will only show the last line of the pasted text. However, after you copy and paste the text into another program you will see that HDFView stored the text including the newlines.