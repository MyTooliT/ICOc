# Version 1.0.12

## Config

- We now use the common term “version” instead of “revision” to specify the current state of the hardware. We therefore renamed

  - `STH` → `HARDWARE REVISION` to
  - `STH` → `HARDWARE VERSION`

  in the [configuration file](../../mytoolit/config/config.yaml).

## ICOc

- The menu for a connected STH now displays the correct STH name instead of the text “Tanja”.
- The main menu now uses “ICOc” instead of “MyToolIt Terminal” as title

## Internal

### Network

- Add the coroutines

  - `read_eeprom_advertisement_time_2`,
  - `read_eeprom_firmware_version`,
  - `read_eeprom_gtin`,
  - `read_eeprom_hardware_version`,
  - `read_eeprom_product_name`,
  - `read_eeprom_release_name`,
  - `read_eeprom_serial_number`, and
  - `read_eeprom_sleep_time_2`,

  to read specific values of the EEPROM

- Add the coroutines

  - `write_eeprom_advertisement_time_2`,
  - `write_eeprom_firmware_version`,
  - `write_eeprom_gtin`,
  - `write_eeprom_hardware_version`,
  - `write_eeprom_release_name`,
  - `write_eeprom_serial_number`, and
  - `write_eeprom_sleep_time_2`

  to change specific values in the EEPROM