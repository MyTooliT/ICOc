# Production Tests

This tutorial lists the usual steps to test a sensory holder assembly or a sensory tool holder.

Before you start, please make sure that you installed the hardware and software mentioned under the section “Requirements” in the [main readme](../ReadMe.md).

## STH

1. Please either

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

   - **Name**: Please change the Bluetooth advertisement name (`STH` → `Name` ) to the name of the STH you want to test.

   - **Serial Number of Programming Board**: Please make sure, that the variable `STH` → `Programming Board` → `Serial Number` contains the serial number of the programming board connected to the STH. This serial number should be displayed on the bottom right of the LCD on the programming board.

3. Now please open your favorite Terminal application and execute, the STH test using the command `Test-TH`. For more information about this command, please take a look at the section “Production Tests” in the [main readme file](../../ReadMe.md).

   Please note, that the test will rename the tested STH to a Base64 encoded version of the Bluetooth MAC address. The rationale behind this is that we can use this string to uniquely identify a STH. For more information, please take a look at the [corresponding issue](https://github.com/MyTooliT/ICOc/issues/1).

[config]: ../../Configuration/config.yaml

## STU

1. Please take a look at step 1 for the STH and replace every occurrence of STU with `STU`. In the end of this step the directory structure should look like something like this:

   ```
   .
   ├── ICOc
   └── STU
       └── builds
             └── manufacturingImageStuv2.1.10.hex
   ```

   You can find the current version of the STU firmware [here](https://github.com/MyTooliT/STU/releases).

2. Please take a look at the section “Production Tests” in the [main readme file](../../ReadMe.md) to find out how to execute the production tests for the STU.
