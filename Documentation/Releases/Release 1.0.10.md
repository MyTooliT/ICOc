# Version 1.0.10

## Checks

- We also check the code base with the static type checker [Mypy](https://mypy.readthedocs.io)

## GitHub Actions

- We now also test ICOc on Ubuntu Linux

## Package

- We now use the version number specified in the [init file of the package](../../mytoolit/__init__.py) for the package version number.
- You can now also install the Package on Linux (and macOS)

## Requirements

- The package now uses the `EUI` (Extended Unique Identifier) class of the [`netaddr`](https://netaddr.readthedocs.io) package to handle MAC addresses

## Scripts

- We added a script that removes log and PDF files from the repository root. For more information please take a look at the section “Remove Log and PDF Files” of the [script documentation](../Scripts.md).

### STH Test

- The report of the STH test now also contains information about the used acceleration sensor (±100 g or ± 50 g)
- Removed extra space before and after headers in PDF report
- The PDF report now contains a list of tables with checkboxes for manual checks

## Internal

### Checkbox

- New `Flowable` class that can be used to add a checkbox to a PDF report

### Command

- Add method `is_error` to check if the current command represents an error
- Add method `set_error` to set or unset the error bit

### Identifier

- Add method `acknowledge` to retrieve expected acknowledgment identifier for id
- Add method `is_error` to check if the current identifier represents an error message
- Add method `set_error` to set or unset the error bit
- Support comparison with other identifiers (`==`)

### Message

- The class now uses the class `Message` of python-can to store data instead of the class `TPCANMsg` of the PCAN-Basic API
- Add method `identifier` to receive an identifier object for the current message
- Add accessor to set and retrieve message data (`.data`)
- The method `acknowledge` now stores the data of the message in the acknowledgment message
- Fix conversion into `python-can` message for non-empty data field
- Add explanation to string representation for Bluetooth “Activate” and “Get number of available devices” [subcommand](https://mytoolit.github.io/Documentation/#value:bluetooth-subcommand)

### Network (New)

- Add coroutine (`reset_node`) to reset a node in the network
- Add coroutine (`activate_bluetooth`) to activate Bluetooth on a node in the network
- Add coroutine (`get_available_devices_bluetooth`) to retrieve the number of available Bluetooth devices
- Add coroutine (`get_device_name_bluetooth`) to retrieve the Bluetooth advertisement name of a device
- Add coroutine (`connect_device_number_bluetooth`) to connect to a Bluetooth device using the device number
- Add coroutine (`deactivate_bluetooth`) to deactivate the Bluetooth connection of a node
- Add coroutine (`check_connection_device_bluetooth`) to check if a Bluetooth device is connected to a node
- Add coroutine (`get_mac_address_bluetooth`) to retrieve the MAC address of a connected Bluetooth device
- Implement context manager interface (`with … as`)
- The code now checks part of the acknowledgement data for the Bluetooth and reset commands of the `System` block

### Report

- Add method `add_checkbox_list` to add a list of checkboxes at the end of the PDF report

### Utility

- Add function `bytearray_to_text` to convert byte data to a string
