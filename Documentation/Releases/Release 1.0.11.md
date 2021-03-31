# Version 1.0.11

### STH Test

- The test now uses the serial number (`STH` → `SERIAL NUMBER`) as new name, if you set the status (`STH` → `STATUS`) to `Epoxied` in the [configuration](../../mytoolit/config/config.yaml). If you use use a different status, then the test will still use the [Base64 encoded MAC address](https://github.com/MyTooliT/ICOc/issues/1) as new (Bluetooth advertisement) name.

## Internal

### Message

- The string representation of a message (`repr`) now includes additional information for [EEPROM commands](https://mytoolit.github.io/Documentation/#block-eeprom)

### Network (New)

- Add coroutine (`connect_mac_address_bluetooth`) to connect to a device using its MAC address
- Add coroutine (`get_rssi_bluetooth`) to retrieve the RSSI (Received Signal Strength Indication) of a device
- Add coroutine (`connect_sth`) to directly connect to an STH using its
  - MAC address,
  - device number, or
  - name
- Add coroutine (`get_sths`) to retrieve a list of available STHs
- Renamed the coroutine to retrieve a Bluetooth device name to `get_name_bluetooth`
- The class now sends requests multiple times, if it does not receive an answer in a certain amount of time
- Improve error message for disconnected CAN adapter
- Add coroutines:

  - `read_eeprom`, and
  - `read_eeprom_text`

  to read EEPROM data
