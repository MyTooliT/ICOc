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
usage: icoc [-h] [-b BLUETOOTH_ADDRESS | -n NAME] [-f FILENAME] [-p XYZ] [-r SECONDS] [-s 2–127]
            [-a {1,2,3,4,8,16,32,64,128,256}] [-o {1,2,4,8,16,32,64,128,256,512,1024,2048,4096}]
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
  -p XYZ, --points XYZ  specify the sensor number (1 – 8) for each axis; use 0 to disable the
                        measurement for an axis (e.g. “104” to use sensor 1 for the x-axis and sensor
                        4 for the z-axis) (default: 100)
  -r SECONDS, --run-time SECONDS
                        run time in seconds (values equal or below “0” specify infinite runtime)
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

To enable the measurement for the “x” channel and “y” channel of an “older” STH (Firmware `2.x`, `BGM113` chip) you can use the following command:

```sh
icoc -p 110
```

Here `0` indicates that you want to disable the channel while a positive number (such as `1`) specifies that the measurement for the channel should take place.

> **Note:** Due to a problem in the current firmware the amount of **paket loss is much higher**, if you
>
> - use the standard ADC configuration values, and
> - enable data transmission for **exactly 2 (channels)**.
>
> We strongly recommend you **use either one or three channels**.

For newer STH versions (Firmware `3.x`, `BGM121` chip) or SMHs (Sensory Milling Heads) you can also change the hardware channel for the “x”, “y” or “z” measurement channel. For example, to select

- hardware channel 8 for the “x” measurement channel
- hardware channel 1 for the “y” measurement channel, and
- hardware channel 3 for the “z” measurement channel

you can use the following command:

```sh
icoc -p 813
```

**Note:** If you connect to an older STH using the command above, then the command would just enable the measurement for “x”, “y” and “z”, but not change the selected hardware channel.

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

   - to a [**Base64 encoded version of the Bluetooth MAC address**](#section:mac-address-conversion), if `STH` → `STATUS` is set to `Epoxied`, or

   - to the **serial number** (`STH` → `PROGRAMMING BOARD` → `SERIAL NUMBER`), if you set the status to `Bare PCB`.

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
