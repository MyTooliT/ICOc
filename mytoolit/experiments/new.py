"""Experiment with some functionality of the „new“ Network class"""

# -- Imports ------------------------------------------------------------------

from asyncio import run

from mytoolit.can import Network


# -- Functions ----------------------------------------------------------------
async def test(identifier):
    async with Network() as network:
        node = 'STH 1'

        await network.connect_sensor_device(identifier)
        name = await network.get_name(node)
        mac_address = await network.get_mac_address(node)
        print(f"Connected to sensor device “{name}” with MAC "
              f"address “{mac_address}”")

        offset = 10.4
        print(f"Store offset value y-axis: {offset}")
        await network.write_eeprom_y_axis_acceleration_offset(offset)
        offset = await network.read_eeprom_y_axis_acceleration_offset()
        print(f"Slope y-axis: {offset}")


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    run(test("Test-STH"))
