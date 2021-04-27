# STH Renaming

1. Please start ICOc:

   ```sh
   icoc
   ```

2. The text based interface will show you a selection of the available STHs:

   ```
   MyToolIt Terminal

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
   08:6b:d7:01:de:81(Tanja)
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
