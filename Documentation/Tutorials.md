# Tutorials

<a name="tutorials:section:sth-renaming"></a>

## STH Renaming

1. Please start ICOc:

   ```sh
   icoc
   ```

2. The text based interface will show you a selection of the available STHs:

   ```
   ICOc

   1: 08:6b:d7:01:de:81(Serial)@-54dBm

   q: Quit program
   1-9: Connect to STH number (ENTER at input end)
   E: EEPROM (Permanent Storage)
   l: Log File Name
   n: Change Device Name
   t: Test Menu
   u: Update Menu
   x: Xml Data Base
   ```

   Choose the STH you want to rename by entering the number to the left of the STH (here `1`). To confirm your selection press the return key <kbd>⮐</kbd>.

3. Now the menu should look like this:

   ```
   08:6b:d7:01:de:81(Serial)
   Global Trade Identification Number (GTIN): 0
   Hardware Version(Major.Minor.Build): 1.4.0
   Firmware Version(Major.Minor.Build): 2.1.10
   Firmware Release Name: Tanja
   Serial: -

   Battery Voltage: 3.15V
   Internal Chip Temperature: 22.3°C

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

   Press the button `n` to change the name.

4. Enter the new device name.

   ```
   New Device Name (max. 8 characters): Blubb
   ```

   Confirm the name with the return key <kbd>⮐</kbd>.

5. The interface should now show you the menu of step 3. To disconnect from the holder press <kbd>e</kbd>.

6. Now you see the main menu of ICOc. The STH will show up under the name you used in step 4.

7. To exit ICOc, please use the key <kbd>q</kbd>.

## Production Tests

This tutorial lists the usual steps to test a sensory holder assembly or a sensory tool holder.

<a name=tutorials:section:general></a>

### General

To run the production tests for the STH, please execute the following command

```sh
test-sth
```

To run the tests for the STU, please use the command:

```
test-stu
```

instead.

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
   test-stu -k eeprom -k connect
   ```

## Verification Tests

### Preparation

The tests assume that the STH is called `Tanja`. Please rename the STH accordingly. To do that you can use the steps described [here](#tutorials:section:sth-renaming).

### Execution

To run the verification tests, please enter the following command in the **root of the repository**:

```sh
test-sth-verification
```

While you should be able to start the command in another directory, it will currently **write log files in the current working directory**. This is probably not something that you want.
