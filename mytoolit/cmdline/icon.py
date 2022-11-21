# -- Imports ------------------------------------------------------------------

from argparse import ArgumentParser, Namespace
from asyncio import run, sleep
from time import time
from typing import Union

from netaddr import EUI

from mytoolit.can import Network
from mytoolit.can.network import NetworkError
from mytoolit.cmdline.parse import mac_address

# -- Functions ----------------------------------------------------------------


def parse_arguments() -> Namespace:
    """Parse command line arguments

    Returns
    -------

    A namespace object that represents the given command line arguments

    """

    parser = ArgumentParser(description="ICOtronic CLI tool")

    subparsers = parser.add_subparsers(required=True,
                                       title="Subcommands",
                                       dest="subcommand")

    subparsers.add_parser('list', help='List sensor devices')

    rename_parser = subparsers.add_parser('rename',
                                          help='Rename a sensor device')

    identifier_group = rename_parser.add_mutually_exclusive_group(
        required=True)
    identifier_group.add_argument('-n',
                                  '--name',
                                  dest='identifier',
                                  metavar='NAME',
                                  help="Name of sensor device",
                                  default='Test-STH')
    identifier_group.add_argument(
        '-m',
        '--mac-address',
        dest='identifier',
        metavar='MAC_ADRESS',
        help="Bluetooth MAC address of sensor device",
        type=mac_address)
    identifier_group.add_argument(
        '-d',
        '--device-number',
        dest='identifier_blubb',
        metavar='DEVICE_NUMBER',
        help="Bluetooth device number of sensor device")

    rename_parser.add_argument('name',
                               type=str,
                               help='New name of STH',
                               nargs='?',
                               default='Test-STH')

    return parser.parse_args()


async def list_sensor_devices() -> None:
    """Print a list of available sensor devices"""

    async with Network() as network:
        # - First request for sensor devices will produce empty list
        # - Subsequent retries should provide all available sensor devices
        timeout = time() + 5
        sensor_devices = []
        while len(sensor_devices) <= 0 and time() < timeout:
            sensor_devices = await network.get_sensor_devices()
            await sleep(0.5)

        for device in sensor_devices:
            print(device)


async def set_name(identifier: Union[int, str, EUI], name) -> None:
    """Rename a sensor device

    Parameters
    ----------

    identifier:
        The identifier of the sensor device (e.g. the current name)

    name:
        The new name of the sensor device

    """

    async with Network() as network:
        node = 'STH 1'

        await network.connect_sensor_device(identifier)
        old_name = await network.get_name(node)
        mac_address = await network.get_mac_address(node)

        await network.set_name(name, node)
        name = await network.get_name(node)
        print(f"Renamed sensor device “{old_name}” with MAC "
              f"address “{mac_address}” to “{name}”")


def main():
    """ICOtronic command line tool"""

    arguments = parse_arguments()

    try:
        coroutine = set_name(
            identifier=arguments.identifier, name=arguments.name
        ) if arguments.subcommand == 'rename' else list_sensor_devices()
        run(coroutine)
    except NetworkError as error:
        print(error)


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    main()
