# -- Imports ------------------------------------------------------------------

from asyncio import run, sleep
from time import time
from typing import List, Union

from netaddr import EUI

from mytoolit.can import Network
from mytoolit.can.network import STHDeviceInfo, NetworkError
from mytoolit.cmdline.parse import parse_arguments

# -- Functions ----------------------------------------------------------------

async def list_sensor_devices() -> None:
    """Print a list of available sensor devices"""

    async with Network() as network:
        timeout = time() + 5
        sensor_devices: List[STHDeviceInfo] = []
        sensor_devices_before: List[STHDeviceInfo] = []

        # - First request for sensor devices will produce empty list
        # - Subsequent retries should provide all available sensor devices
        # - We wait until the number of sensor devices is larger than 1 and
        #   has not changed between one iteration or the timeout is reached
        while (len(sensor_devices) <= 0 and time() < timeout
               or len(sensor_devices) != len(sensor_devices_before)):
            sensor_devices_before = list(sensor_devices)
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
