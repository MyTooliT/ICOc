# -- Imports ------------------------------------------------------------------

from argparse import ArgumentParser
from asyncio import run

from mytoolit.can import Network
from mytoolit.can.network import NetworkError
from mytoolit.cmdline.parse import mac_address


# -- Functions ----------------------------------------------------------------
async def set_name(identifier, name):
    async with Network() as network:
        node = 'STH 1'

        await network.connect_sensor_device(identifier)
        old_name = await network.get_name(node)
        mac_address = await network.get_mac_address(node)

        await network.set_name(name, node)
        name = await network.get_name(node)
        print(f"Renamed sensor device “{old_name}” with MAC "
              f"address “{mac_address}” to “{name}”")


def parse_arguments():
    parser = ArgumentParser(description='STH Renaming Tool')

    subparsers = parser.add_subparsers(required=True,
                                       title="Subcommands",
                                       dest="subcommand")

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


def main():
    """ICOtronic command line tool"""

    arguments = parse_arguments()

    try:
        run(set_name(identifier=arguments.identifier, name=arguments.name))
    except NetworkError as error:
        print(error)


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    main()
