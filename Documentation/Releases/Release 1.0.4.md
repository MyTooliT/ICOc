# Version 1.0.4

## Documentation

- We moved the release notes from the init code of the [`mytoolit` package](../mytoolit) into this file.
- We added an [FAQ](FAQ.md) text that should answer questions not covered by the main readme.
- We rewrote the main readme file. The document should now contain more information that is relevant for the typical user of ICOc. Before this update the text contained more technical information that is only interesting for developers of the ICOc application, such as ADC settings and hardware configuration steps.
- We added a [tutorial](../Documentation/Tutorials/Testing.md) that shows you how to test an STH (or SHA).
- The documentation now includes a description of [manual tests for the software](Guidelines/Test.md).
- We added a document that describes the [style guidelines](Guidelines/Style.md) for the code base.

## Install

- We forgot to add the [requirements file](../requirements.txt) for pip in the last release. This problem should now be fixed.
- We now use the [Python CAN package](https://python-can.readthedocs.io) to access the PCAN-Basic API instead of including a copy of the Python API file in the repository.

## Scripts

- Add a simple wrapper script for the STH test. If you add its parent folder to your path you will be able to execute the test regardless of your current path. For more information, please take a look at the [readme](../ReadMe.md).
- We added a simple wrapper script for [`mwt.py`](../mwt.py). For more information, please take a look [here](../Scripts/ReadMe.md).
- The new scripts [`Convert-MAC-Base64`](../Scripts/ReadMe.md) and [`Convert-Base64-MAC`](../Scripts/ReadMe.md) convert a MAC address (e.g. `08:6b:d7:01:de:81`) into a Base64 encoded (8 character long) text (e.g. `CGvXAd6B`) and back. We use the Base64 encoded MAC address as Bluetooth advertisement name to uniquely identify a STH (or SHA).

## Style

- We formatted the code base with [YAPF](https://github.com/google/yapf).

## STH Test

- We added a test that checks, if updating the over the air update via the [ota-dfu](https://www.silabs.com/documents/public/application-notes/an1086-gecko-bootloader-bluetooth.pdf) command line application works correctly. Currently this test is not activated by default, since it requires that the operator compiles the `ota-dfu` application.
- The test now uses the Base64 encoded version of the MAC address as default name. The rationale behind this update was that the name we used until now was not unique for a certain STH (or SHA). For more information, please take a look [here](https://github.com/MyTooliT/ICOc/issues/1).
- The EEPROM test now resets the STH at the end. This way the STH will already use the Base64 encoded MAC address as name after the test was executed. Before this update we had to do a manual reset for the name change to take place.
