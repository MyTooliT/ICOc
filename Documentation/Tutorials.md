<a name="tutorials:section:tutorials"></a>

# Tutorials

<a name="tutorials:section:sth-renaming"></a>

## Sensor Device Renaming

1. Please start ICOc:

   ```sh
   icoc
   ```

2. The text based interface will show you a selection of the available devices:

   ```
                   ICOc

          Name      Address            RSSI
   ———————————————————————————————————————————————
       1: Serial    08:6b:d7:01:de:81  -44 dBm

   ┌──────────────────────────────┐
   │ 1-9: Connect to STH          │
   │                              │
   │   f: Change Output File Name │
   │   n: Change STH Name         │
   │                              │
   │   q: Quit ICOc               │
   └──────────────────────────────┘
   ```

   Choose the STH you want to rename by entering the number to the left of the device (here `1`). To confirm your selection press the return key <kbd>⮐</kbd>.

3. Now the menu should look like this:

   ```
                   ICOc
   STH “Serial” (08:6b:d7:01:de:81)
   ————————————————————————————————

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

   Press the button `n` to change the name.

4. Enter the new device name.

   ```
   New STH name (max. 8 characters): Blubb
   ```

   Confirm the name with the return key <kbd>⮐</kbd>.

5. The interface should now show you the menu of step 3. To disconnect from the holder press <kbd>e</kbd>.

6. Now you see the main menu of ICOc. The STH will show up under the name you used in step 4.

7. To exit ICOc, please use the key <kbd>q</kbd>.

## Command Line Usage of ICOc

The ICOc program accepts optional command line arguments at startup. This way you can set default values for often used options. If you specify

- the name or
- Bluetooth address

of a sensor device, then you can even use ICOc without any user interaction, since in this case the program will immediately connect to the specified device and start the measurement process.

<a name="tutorials:section:available-options"></a>

### Available Options

To show the available command line options you can use the option `-h`:

```sh
icoc -h
```

which should show you the following output:

```
usage: icoc [-h] [-b BLUETOOTH_ADDRESS | -n NAME] [-f FILENAME] [-r SECONDS] [-1 FIRST_CHANNEL]
            [-2 SECOND_CHANNEL] [-3 THIRD_CHANNEL] [-s 2–127] [-a {1,2,3,4,8,16,32,64,128,256}]
            [-o {1,2,4,8,16,32,64,128,256,512,1024,2048,4096}]
            [-v {1V25,Vfs1V65,Vfs1V8,Vfs2V1,Vfs2V2,2V5,Vfs2V7,VDD,5V,6V6}]
            [--log {debug,info,warning,error,critical}]

Configure and measure data with the ICOtronic system

options:
  -h, --help            show this help message and exit

Connection:
  -b BLUETOOTH_ADDRESS, --bluetooth-address BLUETOOTH_ADDRESS
                        connect to device with specified Bluetooth address (e.g. “08:6b:d7:01:de:81”)
  -n NAME, --name NAME  connect to device with specified name

Measurement:
  -f FILENAME, --filename FILENAME
                        base name of the output file (default: Measurement)
  -r SECONDS, --run-time SECONDS
                        run time in seconds (values equal or below “0” specify infinite runtime)
                        (default: 0)
  -1 FIRST_CHANNEL, --first-channel FIRST_CHANNEL
                        sensor channel number for first measurement channel (1 - 255; 0 to disable)
                        (default: 1)
  -2 SECOND_CHANNEL, --second-channel SECOND_CHANNEL
                        sensor channel number for second measurement channel (1 - 255; 0 to disable)
                        (default: 0)
  -3 THIRD_CHANNEL, --third-channel THIRD_CHANNEL
                        sensor channel number for third measurement channel (1 - 255; 0 to disable)
                        (default: 0)

ADC:
  -s 2–127, --prescaler 2–127
                        Prescaler value (default: 2)
  -a {1,2,3,4,8,16,32,64,128,256}, --acquisition {1,2,3,4,8,16,32,64,128,256}
                        Acquisition time value (default: 8)
  -o {1,2,4,8,16,32,64,128,256,512,1024,2048,4096}, --oversampling {1,2,4,8,16,32,64,128,256,512,1024,2048,4096}
                        Oversampling rate value (default: 64)
  -v {1V25,Vfs1V65,Vfs1V8,Vfs2V1,Vfs2V2,2V5,Vfs2V7,VDD,5V,6V6}, --voltage-reference {1V25,Vfs1V65,Vfs1V8,Vfs2V1,Vfs2V2,2V5,Vfs2V7,VDD,5V,6V6}
                        Reference voltage (default: VDD)

Logging:
  --log {debug,info,warning,error,critical}
                        Minimum level of messages written to log (default: warning)
```

All options below the section “Measurement” and “ADC” in the [help output of ICOc](tutorials:section:available-options) allow you to change the value of a specific configuration values before you start ICOc.

### Channel Selection

To enable the measurement for the first (“x”) channel and second (“y”) channel of an “older” STH (Firmware `2.x`, `BGM113` chip) you can use the following command:

```sh
icoc -1 1 -2 1 -3 0
```

Here `0` indicates that you want to disable the channel while a positive number (such as `1`) specifies that the measurement for the channel should take place. Since the default value

- for the option `-1` is already `1`, and
- for the option `-3` is already `0`

you can also leave out these options to arrive at the shorter command:

```
icoc -2 1
```

> **Note:** Due to a problem in the current firmware the amount of **paket loss is much higher**, if you
>
> - use the standard ADC configuration values, and
> - enable data transmission for **exactly 2 (channels)**.
>
> We strongly recommend you **use either one or three channels**.

For newer STH versions (Firmware `3.x`, `BGM121` chip) or SMHs (Sensory Milling Heads) you can also change the hardware/sensor channel for the first, second and third measurement channel. For example, to select

- hardware channel 8 for the first measurement channel
- hardware channel 1 for the second measurement channel, and
- hardware channel 3 for the third measurement channel

you can use the following command:

```sh
icoc -1 8 -2 1 -3 3
```

**Note:** If you connect to an older STH using the command above, then the command would just enable the measurement for all three measurement channels, but not change the selected hardware channel.

If you just want to enable/set a measurement channel and use the hardware channel with the same number you can also just leave the argument for the specific measurement channel empty. For example, to use

- hardware channel 1 for measurement channel 1,
- hardware channel 2 for measurement channel 2, and
- hardware channel 3 for measurement channel 3

you can use the following command:

```sh
icoc -1 -2 -3
```

or even shorter, since the default value for measurement channel 1 is hardware channel 1:

```
icoc -2 -3
```

### Changing the Run Time

To change the run time of the measurement you can use the option `-r`, which takes the runtime in seconds as argument. The command

```sh
icoc -r 300
```

for example, would change the runtime to 5 minutes (5·60 seconds = 300 seconds).

### Start the Measurement

If you specify one of the options

- `-b`/`--bluetooth-address` or
- `-n`/`--name`

then ICOC will try to connect immediately to the specified device and start the measurement run. For example, to acquire acceleration data from the device with the (Bluetooth advertisement) **name “Blubb”** you can use the following command:

```sh
icoc -n Blubb
```

To read acceleration values for **`5` seconds** from the device with the **Bluetooth address `08:6b:d7:01:de:81`** you can use the following command:

```sh
icoc -b 08:6b:d7:01:de:81 -r 5
```

### Changing the Logging Level

By default ICOc only writes log messages of level `ERROR` or higher. In some situations, for example when ICOc behaves incorrectly, you might want to set a lower level. You can do that using the option `--log`. For example, to activate logging of level `WARNING` and higher when you start ICOc you can use the following command:

```sh
icoc --log warning
```

The different logs for ICOc are stored in the root directory of the repository in the following files:

- `cli.log`: Log messages of ICOc
- `network.log`: Log messages of CAN network class
- `plotter.log`: Log messages of plotter (window process)

### Changing the Reference Voltage

For certain sensor devices you have to change the reference voltage to retrieve a proper measurement value. For example, STHs that use a ± 40 g acceleration sensor ([ADXL356](https://www.analog.com/en/products/adxl356.html)) require a reference voltage of 1.8 V instead of the usual supply voltage (`VDD`) of 3.3 V. To select the correct reference voltage for these devices at startup use the option `-v Vfs1V8`:

```sh
icoc -v Vfs1V8
```

<a name="tutorials:section:icon-cli-tool"></a>

## ICOn CLI Tool

One issue of the ICOc (command line tool) is that it **only works on Windows**. Another problem is that it **requires a CAN adapter from [PEAK-System](https://www.peak-system.com)**.

[python-can]: https://python-can.readthedocs.io

To improve this situation we offer an API based on [python-can][], which works on

- Linux,
- macOS, and
- Windows

and should (at least in theory) support the [same CAN hardware as python-can](https://python-can.readthedocs.io/en/master/interfaces.html). You can access most of this API using the [“new” Network class](../mytoolit/can/network.py).

We also offer a (currently very limited) CLI tool based on this API called ICOn. The text below describes how you can use this tool.

### Listing Available Sensor Devices

To print a list of all available sensor devices please use the subcommand `list`:

```sh
icon list
```

### Rename a Sensor Device

To change the name of a sensor you can use the subcommand `rename`. For example to change the name of the sensor device with the Bluetooth MAC address `08-6B-D7-01-DE-81` to `Test-STH` use the following command:

```sh
icon rename -m 08-6B-D7-01-DE-81 Test-STH
```

For more information about the command you can use the option `-h/--help`:

```sh
icon rename -h
```

## Production Tests

This tutorial lists the usual steps to test a sensory holder assembly or a sensory tool holder.

<a name=tutorials:section:general></a>

### General

To run the production tests for one of the ICOtronic devices, please execute one of the following commands:

| Device                                                   | Command    |
| -------------------------------------------------------- | ---------- |
| Stationary Transceiver Unit (STU)                        | `test-stu` |
| Sensory Holder Assembly (SHA), Sensory Tool Holder (STH) | `test-sth` |
| Sensory Milling Head (SMH)                               | `test-smh` |

For a list of available command line options, please use the option `-h` after one of the commands e.g.:

```sh
test-sth -h
```

#### Specific Tests

To only run a single test you need the specify its name. For example, to run the test `test__firmware_flash` of the STU you can use the following command:

```sh
test-stu TestSTU.test__firmware_flash
```

You can also run specific tests using pattern matching. To do that use the command line option `-k`. For example to run the firmware flash and the connection test of the STH test you can use the command:

```sh
test-sth -k flash -k connection
```

which executes all tests that contain the text `flash` or `connection`.

<a name="tutorials:section:sth"></a>

### STH

The text below gives you a more detailed step-by-step guide on how to run the tests of the STH.

1. > **Note:** You can **skip this step, if you do not want to run the flash test**. To skip the flash test, please set `STH` → `STATUS` in the [configuration file][config] to `Epoxied`.

   Please either

   - create a directory called `STH`, or
   - clone the [STH repository](https://github.com/mytoolit/STH) to a location

   beside this repository inside your file system. Then create a directory called `builds` and put the [current version of the STH firmware](https://github.com/MyTooliT/STH/releases/download/2.1.10/manufacturingImageSthv2.1.10.hex) into this directory. Afterwards the directory and file structure should look like this.

   ```
   .
   ├── ICOc
   └── STH
       └── builds
             └── manufacturingImageSthv2.1.10.hex
   ```

   As alternative to the steps above you can also change the variable `STH` → `Firmware` → `Location` → `Flash` in the [configuration file][config] to point to the firmware that should be used for the flash test.

2. Make sure that the configuration value in the [config file][config] are set correctly. You probably need to change at least the following variables:

   - **Name**: Please change the Bluetooth advertisement name (`STH` → `NAME` ) to the name of the STH you want to test.

   - **Serial Number of Programming Board**: Please make sure, that the variable `STH` → `PROGRAMMING BOARD` → `SERIAL NUMBER` contains the serial number of the programming board connected to the STH. This serial number should be displayed on the bottom right of the LCD on the programming board.

3. Now please open your favorite Terminal application and execute, the STH test using the command `test-sth`. For more information about this command, please take a look at the section [“General”](#tutorials:section:general) above.

   Please note, that the test will rename the tested STH

   - to a [**Base64 encoded version of the Bluetooth MAC address**](#section:mac-address-conversion), if `STH` → `STATUS` is set to `Bare PCB`, or

   - to the **serial number** (`STH` → `PROGRAMMING BOARD` → `SERIAL NUMBER`), if you set the status to `Epoxied`.

[config]: ../../mytoolit/config/config.yaml

### SMH

The preparation steps for the SMH test are very similar to the ones of the [STH test](#tutorials:section:sth).

1. Please make sure that the config value that stores the SMH firmware filepath (`SMH` → `Firmware` → `Location` → `Flash`) points to the correct firmware. If you have not downloaded a firmware image for the SMH you can do so [here](https://github.com/MyTooliT/STH/releases).

2. Check that the [configuration values][config] like SMH name (`SMH` → `NAME`) and programming board serial number (`SMH` → `PROGRAMMING BOARD` → `SERIAL NUMBER`) are set correctly.

3. Please execute the test using the following command:

   ```sh
   test-smh
   ```

### STU

The following description shows you how to run the STU tests.

1. > **Note:** You can **skip this step, if you do not want to run the flash test**.

   Please take a look at step 1 for the STH and replace every occurrence of STU with `STU`. In the end of this step the directory structure should look like something like this:

   ```
   .
   ├── ICOc
   └── STU
       └── builds
             └── manufacturingImageStuv2.1.10.hex
   ```

   You can find the current version of the STU firmware [here](https://github.com/MyTooliT/STU/releases).

2. Please take a look at the section [“General”](#tutorials:section:general) to find out how to execute the production tests for the STU. If you want to run the connection and EEPROM test (aka **all tests except the flash test**), then please execute the following command:

   ```sh
   test-stu -k eeprom -k connection
   ```

**Note:** For the STU (flash) test to work correctly please connect the **programming board** to the USB port of the computer and the programming port of the STU **first**. Only after that connect the power injector to the power adapter. If you reverse this order, then the programmer might not work. If you do not connect the power injector, then the STU test might fail because of a CAN bus error:

> Bus error: an error counter reached the 'heavy'/'warning' limit

### Firmware Versions

The (non-exhaustive) table below shows the compatible firmware for a certain device. The production tests assume that you use **firmware that includes the bootloader**.

| Device | Hardware Version | Microcontroller | Firmware                                                                                                                                                                 |
| ------ | ---------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| STH    | `1.3`            | BGM113          | • [Version 2.1.10](https://github.com/MyTooliT/STH/releases/tag/2.1.10)                                                                                                  |
| STH    | `2.2`            | BGM123          | • [Aladdin](https://github.com/MyTooliT/STH/releases/tag/Aladdin)                                                                                                        |
| SMH    | `2.1`            | BGM121          | • [Version 3.0.0](https://github.com/MyTooliT/STH/releases/tag/3.0.0) <br/>• [Version E3016 Beta](<https://github.com/MyTooliT/STH/releases/tag/E3016_BETA(11_Sensors)>) |

## Verification Tests

### Preparation

- The tests assume that the name of the STH is stored in `STH` → `NAME` in the configuration file `config.yaml`.
- Some of the STH tests assume that you connected the SHA/STH or STU via the programming cable. Please do that, since otherwise these tests will fail.

### Execution

To run the verification tests for the STH, please enter the following command:

```sh
test-sth-verification -v
```

To execute the STU verification tests, you can use the command:

```sh
test-stu-verification -v
```

Please note that while most of the tests should run successfully, if you use working hardware and firmware, some of them might fail occasionally. In this case please rerun the specific test using the option `-k` and specifying a text that matches the name of the test. For example to return the STH test `test0107BlueToothConnectMin` you can use the following command:

```sh
test-sth-verification -v -k test0107
```

### Problematic Tests

The tables below contains a list of tests that failed using a working SHA/STH and STU before. It should provide you with a good overview of which of the verification tests might fail, even if the hardware and firmware works correctly.

#### STH

| Date       | Failed Tests                                                                                                                                                                                                                   |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 2021-09-29 | • test0107BlueToothConnectMin <br/> • test0332SignalIndicatorsAccZ <br/> • test0334SignalIndicatorsMulti <br/> • test0345MixedStreamingAccYZVoltBat                                                                            |
| 2021-09-30 | • test0332SignalIndicatorsAccZ <br/> • test0334SignalIndicatorsMulti <br/> • test0345MixedStreamingAccYZVoltBat                                                                                                                |
| 2021-09-30 | • test0332SignalIndicatorsAccZ <br/> • test0334SignalIndicatorsMulti <br/> • test0532MessageCountersAccZBattery                                                                                                                |
| 2021-10-05 | • test0334SignalIndicatorsMulti <br/> • test0347StreamingAccXSingleBattery                                                                                                                                                     |
| 2021-10-06 | • test0109BlueToothRssi <br/> • test0334SignalIndicatorsMulti                                                                                                                                                                  |
| 2021-10-06 | • test0107BlueToothConnectMin <br/> • test0334SignalIndicatorsMulti <br/> • test0345MixedStreamingAccYZVoltBat                                                                                                                 |
| 2021-10-07 | • test0107BlueToothConnectMin <br/> • test0332SignalIndicatorsAccZ <br/> • test0334SignalIndicatorsMulti <br/> • test0344MixedStreamingAccXYVoltBat <br/> • test0345MixedStreamingAccYZVoltBat                                 |
| 2021-10-11 | • test0015PowerConsumptionEnergySaveMode2 <br/> • test0016PowerConsumptionEnergySaveModeAdv4000ms <br/> • test0332SignalIndicatorsAccZ <br/> • test0334SignalIndicatorsMulti <br/> • test0508AdcConfigSingle                   |
| 2021-10-12 | • test0332SignalIndicatorsAccZ <br/> • test0334SignalIndicatorsMulti <br/> • test0532MessageCountersAccZBattery                                                                                                                |
| 2021-10-13 | • test0332SignalIndicatorsAccZ <br/> • test0334SignalIndicatorsMulti <br/> • test0508AdcConfigSingle <br/> • test0509AdcConfigDouble <br/> • test0510AdcConfigTripple <br/> • test0525MessageCounterAccZ                       |
| 2021-12-09 | • test0107BlueToothConnectMin <br/> • test0510AdcConfigTripple <br/> • test0523MessageCounterAccX <br/> • test0527MessageCounterAccXZ <br/> • test0529MessageCounterAccXYZ <br/>                                               |
| 2021-12-14 | • test0107BlueToothConnectMin                                                                                                                                                                                                  |
| 2022-05-17 | • test0015PowerConsumptionEnergySaveMode2 <br/> • test0016PowerConsumptionEnergySaveModeAdv4000ms <br/> • test0334SignalIndicatorsMulti <br/> • test0344MixedStreamingAccXYVoltBat <br/> • test0357StreamingAccXYSingleBattery |

#### STU

| Date       | Failed Tests                               |
| ---------- | ------------------------------------------ |
| 2021-12-14 | • test0102BlueToothConnectDisconnectDevice |

## Virtualization

You can also use (parts of) ICOc with various virtualization software. For that to work you have to make sure that (at least) the PEAK CAN adapter is attached to the virtual guest operating system. For some virtualization software you might have to install additional software for that to work. For example, [VirtualBox][] requires that you install the VirtualBox Extension Pack before you can use USB 2 and USB 3 devices.

**Note:** Please be advised that the [**VirtualBox Extension Pack is paid software**](https://www.virtualbox.org/wiki/Licensing_FAQ) even though you can download and use it without any license key. **[Oracle might come after you, if you do not pay for the license](https://www.reddit.com/r/sysadmin/comments/d1ttzp/oracle_is_going_after_companies_using_virtualbox/)**, even if you use the Extension Pack in an educational setting.

The table below shows some of the virtualization software we tried and that worked (when we tested it).

| Virtualization Software    | Host OS | Host Architecture | Guest OS     | Guest Architecture |
| -------------------------- | ------- | ----------------- | ------------ | ------------------ |
| [Parallels Desktop][]      | macOS   | `x64`             | Ubuntu 20.04 | `x64`              |
| [Parallels Desktop][]      | macOS   | `x64`             | Windows 10   | `x64`              |
| [Parallels Desktop][]      | macOS   | `ARM64`           | Fedora 36    | `ARM64`            |
| [VirtualBox][]             | macOS   | `x64`             | Windows 10   | `x64`              |
| [VirtualBox][]             | Windows | `x64`             | Fedora 36    | `x64`              |
| [WSL 2](http://aka.ms/wsl) | Windows | `x64`             | Ubuntu 20.04 | `x64`              |

[virtualbox]: https://www.virtualbox.org
[parallels desktop]: https://www.parallels.com

### Windows Subsystem for Linux 2

Using ICOc in the WSL 2 currently [requires using a custom Linux kernel](https://github.com/microsoft/WSL/issues/5533). We **would not recommend** using ICOc with this type of virtualization software, since the setup requires quite some amount of work and time. Nevertheless the steps below should show you how you can use the PEAK CAN adapter and hence ICOc with WSL 2.

1. Install WSL 2 (Windows Shell):

   ```
   wsl --install
   ```

2. Install Ubuntu 22.04 VM (Windows Shell):

   1. Install [Ubuntu 22.04 from the Microsoft Store](https://apps.microsoft.com/store/detail/ubuntu-2204-lts/9PN20MSR04DW)

   2. Open the Ubuntu 22.04 application

      1. Choose a user name
      2. Choose a password

   3. Execute the following commands in a Powershell session

      ```pwsh
      wsl --setdefault Ubuntu-22.04
      wsl --set-version Ubuntu-22.04 2
      ```

      The second command might fail, if `Ubuntu-22.04` already uses WSL 2. In this case please just ignore the error message.

3. [Create Custom Kernel](https://github.com/dorssel/usbipd-win/wiki/WSL-support#building-your-own-usbip-enabled-wsl-2-kernel)

   Windows Shell:

   **Note:** Please replace `<user>` with your (Linux) username (e.g. `rene`)

   ```pwsh
   cd ~/Documents
   mkdir WSL
   cd WSL
   wsl --export Ubuntu-22.04 CANbuntu.tar
   wsl --import CANbuntu CANbuntu CANbuntu.tar
   wsl --distribution CANbuntu --user <user>
   ```

   Linux Shell:

   ```sh
   sudo apt update
   sudo apt upgrade -y
   sudo apt install -y bc build-essential flex bison libssl-dev libelf-dev \
                       libncurses-dev autoconf libudev-dev libtool dwarves
   cd ~
   git clone https://github.com/microsoft/WSL2-Linux-Kernel.git
   cd WSL2-Linux-Kernel
   uname -r # 5.15.74.2-microsoft-standard-WSL2 → branch …5.15.y
   git checkout linux-msft-wsl-5.15.y
   cat /proc/config.gz | gunzip > .config
   make menuconfig
   ```

   Make sure the following features are enabled:

   - `Device Drivers` → `USB Support`
   - `Device Drivers` → `USB Support` → `USB announce new devices`
   - `Device Drivers` → `USB Support` → `USB Modem (CDC ACM) support`
   - `Device Drivers` → `USB Support` → `USB/IP`
   - `Device Drivers` → `USB Support` → `USB/IP` → `VHCI HCD`
   - `Device Drivers` → `USB Support` → `USB Serial Converter Support`
   - `Device Drivers` → `USB Support` → `USB Serial Converter Support` → `USB FTDI Single port Serial Driver`

   Enable the following features:

   - `Networking support` → `CAN bus subsystem support`
   - `Networking support` → `CAN bus subsystem support` → `Raw CAN Protocol`
   - `Networking support` → `CAN bus subsystem support` → `CAN device drivers` → `Virtual Local CAN Interface`
   - `Networking support` → `CAN bus subsystem support` → `CAN device drivers` → `Serial / USB serial CAN Adaptors (slcan)`
   - `Networking support` → `CAN bus subsystem support` → `CAN device drivers` → → `CAN USB Interfaces` → `PEAK PCAN-USB/USB Pro interfaces for CAN 2.0b/CAN-FD`

   Save the modified kernel configuration.

   Linux Shell:

   ```sh
   touch .scmversion
   make
   sudo make modules_install
   sudo make install
   ```

4. Install `usbipd-win` (Linux Shell):

   ```sh
   cd tools/usb/usbip
   ./autogen.sh
   ./configure
   sudo make install
   sudo cp libsrc/.libs/libusbip.so.0 /lib/libusbip.so.0
   sudo apt-get install -y hwdata
   ```

5. Copy image (Linux Shell):

   **Note:** Please replace `<user>` with your (Windows) username (e.g. `rene`)

   ```sh
   cd ~/WSL2-Linux-Kernel
   cp arch/x86/boot/bzImage /mnt/c/Users/<user>/Documents/WSL/canbuntu-bzImage
   ```

6. Create `.wslconfig` in (root of) Windows user directory and store the following text:

   ```ini
   [wsl2]
   kernel=c:\\users\\<user>\\Documents\\WSL\\canbuntu-bzImage
   ```

   **Note:** Please replace `<user>` with your (Windows) username (e.g. `rene`)

7. Set default distribution (Windows Shell)

   ```sh
   wsl --setdefault CANbuntu
   ```

8. Shutdown and restart WSL (Windows Shell):

   ```pwsh
   wsl --shutdown
   wsl -d CANbuntu --cd "~"
   ```

9. Change default user of WSL distro (Linux Shell):

   ```
   nano /etc/wsl.conf
   ```

   Insert the following text:

   ```
   [user]
   default=<user>
   ```

   **Note:** Please replace `<user>` with your (Windows) username (e.g. `rene`)

   Save the file and exit `nano`:

   1. <kbd>Ctrl</kbd> + <kbd>O</kbd>
   2. <kbd>⏎</kbd>
   3. <kbd>Ctrl</kbd> + <kbd>X</kbd>)

10. Restart WSL: See step `9`

11. Install `usbipd` (Windows Shell):

    ```pwsh
    winget install usbipd
    ```

12. Attach CAN-Adapter to Linux VM (Windows Shell)

    ```pwsh
    usbipd wsl list
    # …
    # 5-3    0c72:0012  PCAN-USB FD                      Not attached
    # …
    usbipd wsl attach -d CANbuntu --busid 5-3
    usbipd wsl list
    # …
    # 5-3    0c72:0012  PCAN-USB FD                      Attached - CANbuntu
    # …
    ```

13. Check for PEAK CAN adapter in Linux (Linux Shell):

    ```sh
    dmesg | grep peak_usb
    # …
    # peak_usb 1-1:1.0: PEAK-System PCAN-USB FD v1 fw v3.2.0 (1 channels)
    # …

    lsusb
    # …
    # Bus 001 Device 002: ID 0c72:0012 PEAK System PCAN-USB FD
    # …
    ```

14. Add virtual link for CAN device (Linux Shell)

    ```sh
    sudo ip link set can0 type can bitrate 1000000
    sudo ip link set can0 up
    ```

15. Install `pip` (Linux Shell):

    ```sh
    sudo apt install -y python3-pip
    ```

16. Install ICOc (Linux Shell)

    ```sh
    cd ~
    mkdir Documents
    cd Documents
    git clone https://github.com/MyTooliT/ICOc.git
    cd ICOc
    python3 -m pip install --prefix=$(python3 -m site --user-base) -e .
    ```

17. Run a script to test that everything works as expected (Linux Shell)

    ```sh
    icon list
    ```

    If the command above fails with the message

    ```
    Command 'icon' not found…
    ```

    then you might have to logout and login into the WSL session again before you execute `icon list` again.

**Note:** You only need to repeat steps

- `12`: attach the CAN adapter to the VM in Windows and
- `14`: create the link for the CAN device in Linux

after you set up everything properly once.

#### Installing/Using Simplicity Commander

1. Download and unpack [Simplicity Commander](https://community.silabs.com/s/article/simplicity-commander?language=en_US) (Linux Shell)

   ```sh
   sudo apt install -y unzip
   mkdir -p ~/Downloads
   cd ~/Downloads
   wget https://www.silabs.com/documents/public/software/SimplicityCommander-Linux.zip
   unzip SimplicityCommander-Linux.zip
   cd SimplicityCommander-Linux
   tar xf Commander_linux_*.tar.bz
   mkdir -p ~/Applications
   mv commander ~/Applications
   ```

2. Add `commander` binary to path (Linux Shell)

   1. Open `~/.profile` in `nano`:

      ```sh
      nano ~/.profile
      ```

   2. Add the following text at the bottom:

      ```sh
      if [ -d "$HOME/Applications/commander" ] ; then
          PATH="$HOME/Applications/commander:$PATH"
      fi
      ```

   3. Save your changes

3. Install JLink (Linux Shell)

   1. Download [JLink](https://www.segger.com/downloads/jlink/) (64-bit DEB Installer) into your Windows user `Downloads` folder

   2. Copy the installer

      ```sh
      mv /mnt/c/Users/<user>/Downloads/*JLink_Linux*.deb ~/Downloads
      ```

      **Note:** Please replace `<user>` with your (Windows) username (e.g. `rene`)

   3. Install JLink package

      ```sh
      cd ~/Downloads
      sudo dpkg -i JLink_Linux_*.deb
      sudo apt-get -fy install # if there were unresolved dependencies
      ```

4. Detach USB connector of programming adapter
5. Attach USB connector of programming adapter

6. [Reload udev rules](https://github.com/dorssel/usbipd-win/issues/96#issuecomment-992804504) (Linux Shell)

   ```sh
   sudo service udev restart
   sudo udevadm control --reload
   ```

7. Connect programming adapter to Linux (Windows Shell)

   ```pwsh
   usbipd wsl list
   # …
   # 5-4    1366:0105  JLink CDC UART Port (COM3), J-Link driver Not attached
   # …
   usbipd wsl attach --busid 5-4
   ```

8. Check if `commander` JLink connection works without using `sudo` (Linux Shell)

   ```sh
   commander adapter dbgmode OUT --serialno <serialnumber>
   # Setting debug mode to OUT...
   # DONE
   ```

   Notes:

   - Please replace `<serialnumber>` with the serial number of your programming board (e.g. `440069950`):

     ```sh
     commander adapter dbgmode OUT --serialno 440069950
     ```

   - If the command above [fails with the error message](https://stackoverflow.com/questions/55313610/importerror-libgl-so-1-cannot-open-shared-object-file-no-such-file-or-directo):

     ```
     error while loading shared libraries: libGL.so.1: cannot open shared object file…
     ```

     then you need to install `libgl1`:

     ```
     sudo apt install -y libgl1
     ```

#### Run Tests in WSL

1. Reload `udev` rules (Linux Shell):

   ```sh
   sudo service udev restart
   sudo udevadm control --reload
   ```

2. Connect programming/CAN adapter to Linux (Windows Shell):

   ```pwsh
   usbipd wsl list
   # …
   # 5-3    0c72:0012  PCAN-USB FD                               Not attached
   # 5-4    1366:0105  JLink CDC UART Port (COM3), J-Link driver Not attached
   # …
   usbipd wsl attach --busid 5-3
   usbipd wsl attach --busid 5-4
   ```

3. Add virtual link for CAN device (Linux Shell):

   ```sh
   sudo ip link set can0 type can bitrate 1000000
   sudo ip link set can0 up
   ```

4. Run tests (Linux Shell):

   ```sh
   make run
   ```

### Docker on Linux

The text below shows how you can use (code of) the new Network class in a Docker container on a **Linux host**. The description on how to move the interface of the Docker container is an adaption of an [article/video from the “Chemnitzer Linux-Tage”](https://chemnitzer.linux-tage.de/2021/de/programm/beitrag/210). Currently we provide two images based on:

- [Alpine](Docker/Alpine) and
- [Ubuntu](Docker/Ubuntu).

#### Build/Pull the Docker Image

You can download a recent version of the image from Docker Hub

- for Alpine:

```
docker image pull mytoolit/icoc-alpine:latest
```

- or Ubuntu:

```
docker image pull mytoolit/icoc-ubuntu:latest
```

Another option is to build the image yourself.

- Alpine Linux:

```sh
docker build -t mytoolit/icoc-alpine -f Docker/Alpine/Dockerfile .
```

- Ubuntu:

```sh
docker build -t mytoolit/icoc-ubuntu -f Docker/Ubuntu/Dockerfile .
```

#### Using ICOc in the Docker Container

1. Run the container **(Terminal 1)**

   1. Open a new terminal window

   2. Depending on the Docker container you want to use please execute one of the following commands:

      - Alpine:

        ```sh
        docker run --rm -it --name icoc mytoolit/icoc-alpine
        ```

      - Ubuntu:

        ```sh
        docker run --rm -it --name icoc mytoolit/icoc-ubuntu
        ```

2. Make sure the CAN interface is available on the Linux host **(Terminal 2)**

   1. Open a new terminal window
   2. Check that the following command:

      ```sh
      networkctl list
      ```

      lists `can0` under the column `LINK`

3. Move the CAN interface into the network space of the Docker container **(Terminal 2)**

   ```sh
   export DOCKERPID="$(docker inspect -f '{{ .State.Pid }}' icoc)"
   sudo ip link set can0 netns "$DOCKERPID"
   sudo nsenter -t "$DOCKERPID" -n ip link set can0 type can bitrate 1000000
   sudo nsenter -t "$DOCKERPID" -n ip link set can0 up
   ```

4. Run a test command in Docker container **(Terminal 1)** e.g.:

   ```sh
   icon list
   ```
