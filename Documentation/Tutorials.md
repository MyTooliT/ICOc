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

   Sensors               M1: S1

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
usage: icoc [-h] [-b BLUETOOTH_ADDRESS | -n [NAME]] [-f FILENAME] [-r SECONDS] [-1 [FIRST_CHANNEL]] [-2 [SECOND_CHANNEL]] [-3 [THIRD_CHANNEL]] [-s 2–127] [-a {1,2,3,4,8,16,32,64,128,256}]
            [-o {1,2,4,8,16,32,64,128,256,512,1024,2048,4096}] [-v {1V25,Vfs1V65,Vfs1V8,Vfs2V1,Vfs2V2,2V5,Vfs2V7,VDD,5V,6V6}] [--log {debug,info,warning,error,critical}]

Configure and measure data with the ICOtronic system

options:
  -h, --help            show this help message and exit

Connection:
  -b BLUETOOTH_ADDRESS, --bluetooth-address BLUETOOTH_ADDRESS
                        connect to device with specified Bluetooth address (e.g. “08:6b:d7:01:de:81”)
  -n [NAME], --name [NAME]
                        connect to device with specified name

Measurement:
  -f FILENAME, --filename FILENAME
                        base name of the output file (default: Measurement)
  -r SECONDS, --run-time SECONDS
                        run time in seconds (values equal or below “0” specify infinite runtime) (default: 0)
  -1 [FIRST_CHANNEL], --first-channel [FIRST_CHANNEL]
                        sensor channel number for first measurement channel (1 - 255; 0 to disable) (default: 1)
  -2 [SECOND_CHANNEL], --second-channel [SECOND_CHANNEL]
                        sensor channel number for second measurement channel (1 - 255; 0 to disable) (default: 0)
  -3 [THIRD_CHANNEL], --third-channel [THIRD_CHANNEL]
                        sensor channel number for third measurement channel (1 - 255; 0 to disable) (default: 0)

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
                        Minimum level of messages written to log (default: info)
```

All options below the section “Measurement” and “ADC” in the [help output of ICOc](#tutorials:section:available-options) allow you to change a specific configuration value before you start ICOc.

### Channel Selection

To enable the measurement for the first (“x”) channel and second (“y”) channel of an “older” STH (Firmware `2.x`, `BGM113` chip) you can use the following command:

```sh
icoc -1 1 -2 1 -3 0
```

Here `0` indicates that you want to disable the channel, while a positive number (such as `1`) specifies that the measurement for the channel should take place. Since the default value

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

> **Note:** If you connect to an older STH using the command above, then the command would just enable the measurement for all three measurement channels, but not change the selected hardware channel.

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

for example, would change the runtime to 300 seconds (5 minutes).

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

By default ICOc only writes log messages of level `INFO` or higher. In some situations, for example when ICOc behaves incorrectly, you might want to set a lower level. You can do that using the option `--log`. For example, to activate logging of level `WARNING` and higher when you start ICOc you can use the following command:

```sh
icoc --log warning
```

The different logs for ICOc are stored in the current working directory in the following files:

- `cli.log`: Log messages of ICOc
- `network.log`: Log messages of CAN network class
- `plotter.log`: Log messages of plotter (process for measurement graph)

### Changing the Reference Voltage

For certain sensor devices you have to change the reference voltage to retrieve a proper measurement value. For example, STHs that use a ± 40 g acceleration sensor ([ADXL356](https://www.analog.com/en/products/adxl356.html)) require a reference voltage of 1.8 V instead of the usual supply voltage (`VDD`) of 3.3 V. To select the correct reference voltage for these devices at startup use the option `-v Vfs1V8`:

```sh
icoc -v Vfs1V8
```

### Changing the Sampling Rate

If you want to change the sampling rate you can do that by changing the parameters of the ADC. There are 3 parameters which influence the sampling rate.

- **Prescaler** (Prescaler used by the ADC to get the sample points)
- **Acquisition Time** (Time the ADC holds a value to get a sampling point)
- **Oversampling Rate** (Oversampling rate of the ADC)

The formula which can be used to calculate the sampling rate can be found in the [documentation of the CAN commands](https://mytoolit.github.io/Documentation/#sampling-rate).

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

### Collecting Measurement Data

To collect and store measurement data from an STH you can uses the subcommand `measure`:

```sh
icon measure
```

By default the command will collect streaming data for 10 seconds for the first measurement channel and store the data as `Measurement.hdf5` in the current working directory. You can change the default measurement duration using the option `-t`/`--time`. For example to collect measurement data for 1.5 seconds from the STH with the name `Test-STH` use the command:

```sh
icon measure -t 1.5 -n Test-STH
```

### Renaming a Sensor Device

To change the name of a sensor you can use the subcommand `rename`. For example to change the name of the sensor device with the Bluetooth MAC address `08-6B-D7-01-DE-81` to `Test-STH` use the following command:

```sh
icon rename -m 08-6B-D7-01-DE-81 Test-STH
```

For more information about the command you can use the option `-h`/`--help`:

```sh
icon rename -h
```

<a name=tutorials:section:opening-the-user-configuration></a>

### Opening the User Configuration

To open the user configuration file, you can use the subcommand `config`:

```sh
icon config
```

If the file does not exist yet, then it will be created and filled with the content of the [default user configuration](https://github.com/MyTooliT/ICOc/blob/master/mytoolit/config/user.yaml). For more information on how to change the configuration, please take a look [here](#introduction:section:changing-configuration-values).

### STU Commands

To list all available STU subcommands, please use the option `-h` (or `--help`):

```sh
icon stu -h
```

#### Enable STU OTA Mode

To enable the Bluetooth advertising of the STU and hence the “over the air” firmware update, please run the following command:

```sh
icon stu ota
```

#### Retrieve the Bluetooth STU MAC Address

To retrieve the STU Bluetooth address you can use the following command:

```sh
icon stu mac
```

#### Reset STU

To reset the STU please use the following command:

```sh
icon stu reset
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

1. > **Note:** You can **skip this step, if you do not want to run the flash test**. To skip the flash test, please set `sth` → `status` in the [configuration](#introduction:section:changing-configuration-values) to `Epoxied`.

   Please create a directory called `Firmware` in the current user’s `Documents` (`~`) directory.

   > **Note:** To open the user’s home directory on Windows you can use the following command in (Windows) Terminal:
   >
   > ```sh
   > ii ~/Documents
   > ```

   Then put the [current version of the STH firmware](https://github.com/MyTooliT/STH/releases/download/2.1.10/manufacturingImageSthv2.1.10.hex) into this directory. Afterwards the directory and file structure should look like this:

   ```
   ~
   └── Documents
           └── Firmware
                   └── manufacturingImageSthv2.1.10.hex
   ```

   As alternative to the steps above you can also change the variable `sth` → `firmware` → `location` → `flash` in the [configuration](#introduction:section:changing-configuration-values) to point to the firmware that should be used for the flash test.

2. Make sure that [the configuration values](#introduction:section:changing-configuration-values) are set correctly. You probably need to change at least the following variables:

   - **Name**: Please change the Bluetooth advertisement name (`sth` → `name` ) to the name of the STH you want to test.

   - **Serial Number of Programming Board**: Please make sure, that the variable `sth` → `programming board` → `serial number` contains the serial number of the programming board connected to the STH. This serial number should be displayed on the bottom right of the LCD on the programming board.

3. Please open your favorite Terminal application and execute, the STH test using the command `test-sth`. For more information about this command, please take a look at the section [“General”](#tutorials:section:general) above.

   Please note, that the test will rename the tested STH

   - to a [**Base64 encoded version of the Bluetooth MAC address**](#section:mac-address-conversion), if `sth` → `status` is set to `Bare PCB`, or

   - to the **serial number** (`sth` → `programming board` → `serial number`), if you set the status to `Epoxied`.

### SMH

The preparation steps for the SMH test are very similar to the ones of the [STH test](#tutorials:section:sth).

1. Please make sure that the config value that stores the SMH firmware filepath (`smh` → `firmware` → `location` → `flash`) points to the correct firmware. If you have not downloaded a firmware image for the SMH you can do so [here](https://github.com/MyTooliT/STH/releases).

2. Check that the [configuration values][config] like SMH name (`smh` → `name`) and programming board serial number (`smh` → `programming board` → `serial number`) are set correctly.

3. Please execute the test using the following command:

   ```sh
   test-smh
   ```

### STU

The following description shows you how to run the STU tests.

1. > **Note:** You can **skip this step, if you do not want to run the flash test**.

   Please take a look at step 1 of the description for the [STH test](#tutorials:section:sth) and replace every occurrence of STH (or `sth`) with STU (or `stu`).

   > **Note:** The STU test always uploads the flash file to the board, i.e. the setting `stu` → `status` is **not** read/used by the STU tests.

   In the end of this step the directory structure should look like this:

   ```
   ~
   └── Documents
          └── Firmware
                 └── manufacturingImageStuv2.1.10.hex
   ```

   You can find the current version of the STU firmware [here](https://github.com/MyTooliT/STU/releases).

2. Please take a look at the section [“General”](#tutorials:section:general) to find out how to execute the production tests for the STU. If you want to run the connection and EEPROM test (aka **all tests except the flash test**), then please execute the following command:

   ```sh
   test-stu -k eeprom -k connection
   ```

---

**Note:** For the STU (flash) test to work correctly:

1. Connect the **programming board** to the USB port of the computer and the programming port of the STU **first**.

2. Only after that connect the **power injector to the power adapter**.

If you reverse this order, then the programmer might not work. If you do not connect the power injector, then the STU test might fail because of a CAN bus error:

> Bus error: an error counter reached the 'heavy'/'warning' limit

---

### Firmware Versions

The (non-exhaustive) table below shows the compatible firmware for a certain device. The production tests assume that you use **firmware that includes the bootloader**.

| Device | Hardware Version | Microcontroller | Firmware                                                                                                                                                                 |
| ------ | ---------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| STH    | `1.3`            | BGM113          | • [Version 2.1.10](https://github.com/MyTooliT/STH/releases/tag/2.1.10)                                                                                                  |
| STH    | `2.2`            | BGM123          | • [Aladdin](https://github.com/MyTooliT/STH/releases/tag/Aladdin)                                                                                                        |
| SMH    | `2.1`            | BGM121          | • [Version 3.0.0](https://github.com/MyTooliT/STH/releases/tag/3.0.0) <br/>• [Version E3016 Beta](<https://github.com/MyTooliT/STH/releases/tag/E3016_BETA(11_Sensors)>) |

## Verification Tests

### Preparation

- The tests assume that the name of the STH is stored in `sth` → `name` in the [configuration](#introduction:section:changing-configuration-values).
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

Please note that while most of the tests should run successfully, if you use working hardware and firmware, some of them might fail occasionally. In this case please rerun the specific test using the option `-k` and specifying a text that matches the name of the test. For example, to return the STH test `test0107BlueToothConnectMin` you can use the following command:

```sh
test-sth-verification -v -k test0107
```

> **Note**: If you want to stop the test while it is running, but <kbd>Ctrl</kbd> + <kbd>C</kbd> does not terminate the test as you expected, then you can use the command:
>
> ```sh
> Stop-Process -Name python
> ```
>
> to stop **all running Python interpreters** and hence also the `test-sth-verification` script.

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
