# Version 1.0.13

## Production Test

- The

  - stationary acceleration test (`test_acceleration_single_value`),
  - supply voltage test (`test_battery_voltage`),
  - connection test (`test_connection`), and
  - EEPROM test (`test_eeprom`)

  now use the [new network class](../../mytoolit/can/network.py) instead of the [old network class](../../mytoolit/old/network.py)

## Internal

### Calibration

- Add class `CalibrationMeasurementFormat` to specify the data bytes of a [calibration measurement command](https://mytoolit.github.io/Documentation/#command:Calibration-Measurement).

### Measurement

- Add function `convert_voltage_adc_to_volts` to convert (2 byte) [streaming voltage][streaming] values to a supply voltage in volts

[streaming]: https://mytoolit.github.io/Documentation/#block-streaming

### Message

- The string representation of a message (`repr`) now includes additional information for the [Get/Set State](https://mytoolit.github.io/Documentation/#command:get-set-state) block command

### Network

- Add the coroutine `get_state` to [retrieve information about the current state of a node](https://mytoolit.github.io/Documentation/#command:get-set-state)
- Add the coroutine `read_voltage` to read the supply voltage of a connected STH
- Add the coroutine `read_x_acceleration` to read the x acceleration of a connected STH

### Streaming Format

- New class `StreamingFormat` to specify the format of [streaming data][streaming]
- New class `StreamingFormatVoltage` to specify the format of voltage streaming data
- New class `StreamingFormatAcceleration` to specify the format of acceleration streaming data
