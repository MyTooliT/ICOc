"""Experiment with some functionality of the „new“ Network class"""

# -- Imports ------------------------------------------------------------------

from asyncio import run

from mytoolit.can import Network
from mytoolit.measurement import convert_acceleration_adc_to_g


# -- Functions ----------------------------------------------------------------
async def test(identifier="Test-STH"):
    network = Network()
    node = 'STH 1'

    await network.connect_sensor_device(identifier)
    name = await network.get_name(node)
    mac_address = await network.get_mac_address(node)
    print(f"Connected to sensor device “{name}” with MAC "
          f"address “{mac_address}”\n")

    values_raw = await network.read_x_acceleration_raw(seconds=1)
    max_value = int(
        abs(await network.read_eeprom_x_axis_acceleration_offset()) * 2)
    values_in_g = [
        convert_acceleration_adc_to_g(value, max_value=max_value)
        for value in values_raw
    ]

    print(f"Values: {values_in_g}")

    await network.shutdown()  # Also call this in case of error


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    run(test())
