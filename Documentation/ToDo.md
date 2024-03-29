# ToDo

## General

- The [CAN communication class](../Network.py) should support different CAN controllers. For that to work we should use the general purpose interface of the [Python CAN library](https://python-can.readthedocs.io/).
- Add GUI for data collection

## Style

- Use [Restyled](https://restyled.io) to keep the style of the code base intact.

## STH Test

- Add power usage test for different phases of STH:
  - Sleep Mode 1
  - Sleep Mode 2
  - Active
  - Streaming
- Add instructions for operator to test output
  - Write down MAC address on PCB
- Add STU version to PDF report
- Fix premature termination (`SIGKILL`)
  - Clean up resources (read thread) automatically
