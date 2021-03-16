# Version 1.0.11

## Internal

### Network (New)

- Add coroutine (`connect_mac_address_bluetooth`) to connect to a device using its MAC address
- Add coroutine (`get_rssi_bluetooth`) to retrieve the RSSI (Received Signal Strength Indication) of a device
- Add coroutine (`connect_sth`) to directly connect to an STH using its MAC address
- Renamed the coroutine to retrieve a Bluetooth device name to `get_name_bluetooth`
