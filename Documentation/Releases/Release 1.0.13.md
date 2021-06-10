# Version 1.0.13

## Production Test

- The

  - connection test (`test_connection`) and
  - EEPROM test (`test_eeprom`)

  now use the [new network class](../../mytoolit/can/network.py) instead of the [old network class](../../mytoolit/old/network.py)

## Internal

### Measurement

- Add function `convert_voltage_adc_to_volts` to convert (2 byte) [streaming voltage][streaming] values to a supply voltage in volts

[streaming]: https://mytoolit.github.io/Documentation/#block-streaming

### Message

- The string representation of a message (`repr`) now includes additional information for the [Get/Set State](https://mytoolit.github.io/Documentation/#command:get-set-state) block command

### Network

- Add the coroutine `get_state` to [retrieve information about the current state of a node](https://mytoolit.github.io/Documentation/#command:get-set-state)
