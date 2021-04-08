# Version 1.0.11

### STH Test

- The test now uses the serial number (`STH` → `SERIAL NUMBER`) as new name, if you set the status (`STH` → `STATUS`) to `Epoxied` in the [configuration](../../mytoolit/config/config.yaml). If you use use a different status, then the test will still use the [Base64 encoded MAC address](https://github.com/MyTooliT/ICOc/issues/1) as new (Bluetooth advertisement) name.
- Remove wait time (of 2 seconds) after Bluetooth connection was established. In theory this should make the test execution quite a bit faster, without any adverse effects.

## Internal

### Message

- The string representation of a message (`repr`) now includes additional information for:

  - [EEPROM commands](https://mytoolit.github.io/Documentation/#block-eeprom), and
  - the [Bluetooth commands](https://mytoolit.github.io/Documentation/#command:bluetooth):
    - [to request a connection](https://mytoolit.github.io/Documentation/#command:bluetooth:7),
    - [to check the connection status](https://mytoolit.github.io/Documentation/#command:bluetooth:8),
    - [to retrieve the RSSI](https://mytoolit.github.io/Documentation/#command:bluetooth:12), and
    - [to retrieve the MAC address](https://mytoolit.github.io/Documentation/#command:bluetooth:17)

### Network (Old)

- Improve error message for disconnected CAN adapter

### Network (New)

- The class now sends requests multiple times, if it does not receive an answer in a certain amount of time
- Improve error message for disconnected CAN adapter
- Renamed the following coroutines:

  | Old Name                            | New Name                     |
  | ----------------------------------- | ---------------------------- |
  | `get_available_devices_bluetooth`   | `get_available_devices`      |
  | `get_device_name_bluetooth`         | `get_name`                   |
  | `get_mac_address_bluetooth`         | `get_mac_address`            |
  | `connect_device_number_bluetooth`   | `connect_with_device_number` |
  | `check_connection_device_bluetooth` | `is_connected`               |

- Add the following coroutines

  | Name                       | Description                                                                                       |
  | -------------------------- | ------------------------------------------------------------------------------------------------- |
  | `connect_with_mac_address` | Connect to a device using its MAC address                                                         |
  | `get_rssi`                 | Retrieve the RSSI (Received Signal Strength Indication) of a device                               |
  | `get_sths`                 | Retrieve a list of available STHs                                                                 |
  | `connect_sth`              | Directly connect to an STH using its<br/>• MAC address,<br/> • device number, or<br/> • name<br/> |
  | `set_name`                 | Set the (Bluetooth advertisement) name of an STU or STH                                           |

- Add coroutines:

  - `read_eeprom`,
  - `read_eeprom_float`,
  - `read_eeprom_int`, and
  - `read_eeprom_text`

  to read EEPROM data

- Add coroutines

  - `write_eeprom`,
  - `write_eeprom_float`,
  - `write_eeprom_int`, and
  - `write_eeprom_text`,

  to write EEPROM data

- Add the coroutines:

  - `read_eeprom_advertisement_time_1`,
  - `read_eeprom_name`,
  - `read_eeprom_sleep_time_1`, and
  - `read_eeprom_status`

  to read specific parts of the EEPROM

- Add the coroutines:

  - `write_eeprom_advertisement_time_1`,
  - `write_eeprom_name`,
  - `write_eeprom_sleep_time_1`, and
  - `write_eeprom_status`

  to write specific parts of the EEPROM
