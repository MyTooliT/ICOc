"""Experiment with some functionality of the „new“ Network class"""

# -- Imports ------------------------------------------------------------------

from argparse import ArgumentParser
from asyncio import run

from mytoolit.can import Network


# -- Functions ----------------------------------------------------------------
async def set_name(identifier, name):
    async with Network() as network:
        node = 'STH 1'

        await network.connect_sensor_device(identifier)
        current_name = await network.get_name(node)
        mac_address = await network.get_mac_address(node)
        print(f"Connected to sensor device “{current_name}” with MAC "
              f"address “{mac_address}”")

        await network.set_name(name, node)
        name = await network.get_name(node)
        print(f"New name of sensor device: {name}")


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    parser = ArgumentParser(description='STH Renaming Tool')
    parser.add_argument('name',
                        type=str,
                        help='new name of STH',
                        nargs='?',
                        default='Test-STH')

    arguments = parser.parse_args()

    run(set_name(identifier=0, name=arguments.name))
