"""Experiment with some functionality of the „new“ Network class"""

# -- Imports ------------------------------------------------------------------

from asyncio import run
from sys import stderr

from mytoolit.can import Network
from mytoolit.can.error import UnsupportedFeatureException


# -- Functions ----------------------------------------------------------------
async def test(identifier):
    async with Network() as network:
        node = 'STH 1'

        await network.connect_sensor_device(identifier)
        name = await network.get_name(node)
        mac_address = await network.get_mac_address(node)
        print(f"Connected to sensor device “{name}” with MAC "
              f"address “{mac_address}”")

        try:
            await network.write_sensor_configuration(3, 2, 1)
            sensor_config = await network.read_sensor_configuration()
            print(f"Sensor Configuration: {sensor_config}")
        except UnsupportedFeatureException as error:
            print(error, file=stderr)


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    run(test(identifier=0))
