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


async def rename(identifier: Union[int, str, EUI], name) -> None:
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


async def stu(subcommand: str) -> None:
    """Run specific commands regarding stationary transceiver unit

    Parameters
    ----------

    subcommand:
        A command that specifies the specific action regarding the STU

    """

    async with Network() as network:
        if subcommand == 'enable-ota':
            # The coroutine below activates the advertisement required for the
            # Over The Air (OTA) firmware update.
            #
            # - The `deactivate_bluetooth` command called when the execution
            #   leaves the `async with` block seems to not turn off the
            #   advertisement for the STU.
            # - Even a **hard STU reset does not turn off the advertisement**.
            # - One way to turn off the advertisement seems to be to initiate a
            #   connection with a sensor device.
            await network.activate_bluetooth()
        elif subcommand == 'show-mac-address':
            print(await network.get_mac_address('STU 1'))
        else:
            raise ValueError(f"Unknown STU subcommand “{subcommand}”")


def main():
    """ICOtronic command line tool"""

    arguments = parse_arguments()

    try:
        if arguments.subcommand == 'list':
            coroutine = list_sensor_devices()
        elif arguments.subcommand == 'rename':
            coroutine = rename(identifier=arguments.identifier,
                               name=arguments.name)
        elif arguments.subcommand == 'stu':
            coroutine = stu(arguments.stu_command)
        run(coroutine)
    except NetworkError as error:
        print(error)
    except KeyboardInterrupt:
        pass


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    main()
