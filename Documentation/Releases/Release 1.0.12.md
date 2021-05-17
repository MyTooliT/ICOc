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
  - `read_eeprom_batch_number`,
  - `read_eeprom_firmware_version`,
  - `read_eeprom_gtin`,
  - `read_eeprom_hardware_version`,
  - `read_eeprom_oem_data`,
  - `read_eeprom_operating_time`,
  - `read_eeprom_power_off_cycles`,
  - `read_eeprom_power_on_cycles`,
  - `read_eeprom_product_name`,
  - `read_eeprom_production_date`,
  - `read_eeprom_release_name`,
  - `read_eeprom_serial_number`,
  - `read_eeprom_sleep_time_2`,
  - `read_eeprom_under_voltage_counter`,
  - `read_eeprom_watchdog_reset_counter`,
  - `read_eeprom_x_axis_acceleration_offset`, and
  - `read_eeprom_x_axis_acceleration_slope`

  to read specific values of the EEPROM

- Add the coroutines

  - `write_eeprom_advertisement_time_2`,
  - `write_eeprom_batch_number`,
  - `write_eeprom_firmware_version`,
  - `write_eeprom_gtin`,
  - `write_eeprom_hardware_version`,
  - `write_eeprom_oem_data`,
  - `write_eeprom_operating_time`,
  - `write_eeprom_power_off_cycles`,
  - `write_eeprom_power_on_cycles`,
  - `write_eeprom_product_name`,
  - `write_eeprom_production_date`,
  - `write_eeprom_release_name`,
  - `write_eeprom_serial_number`,
  - `write_eeprom_sleep_time_2`,
  - `write_eeprom_under_voltage_counter`,
  - `write_eeprom_watchdog_reset_counter`,
  - `write_eeprom_x_axis_acceleration_offset`, and
  - `write_eeprom_x_axis_acceleration_slope`

  to change specific values in the EEPROM

- Add the following coroutines to read product data:

  | Name                        | Data Item                                 |
  | --------------------------- | ----------------------------------------- |
  | `get_gtin`                  | GTIN (Global Trade Identification Number) |
  | `get_hardware_version`      | Hardware Version Number                   |
  | `get_firmware_version`      | Firmware Version Number                   |
  | `get_firmware_release_name` | Firmware Release Name                     |
  | `get_serial_number`         | Serial Number                             |
