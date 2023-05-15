# -- Imports ------------------------------------------------------------------

from argparse import Namespace
from asyncio import run, sleep
from functools import partial
from time import time
from typing import List

from mytoolit.can import Network
from mytoolit.can.network import STHDeviceInfo, NetworkError
from mytoolit.cmdline.parse import parse_arguments
from mytoolit.measurement import convert_raw_to_g


# -- Functions ----------------------------------------------------------------


async def list_sensor_devices(arguments: Namespace) -> None:
    """Print a list of available sensor devices

    Parameters
    ----------

    arguments:
        The given command line arguments

    """

    async with Network() as network:
        timeout = time() + 5
        sensor_devices: List[STHDeviceInfo] = []
        sensor_devices_before: List[STHDeviceInfo] = []

        # - First request for sensor devices will produce empty list
        # - Subsequent retries should provide all available sensor devices
        # - We wait until the number of sensor devices is larger than 1 and
        #   has not changed between one iteration or the timeout is reached
        while (
            len(sensor_devices) <= 0
            and time() < timeout
            or len(sensor_devices) != len(sensor_devices_before)
        ):
            sensor_devices_before = list(sensor_devices)
            sensor_devices = await network.get_sensor_devices()
            await sleep(0.5)

        for device in sensor_devices:
            print(device)


async def measure(arguments: Namespace) -> None:
    """Open measurement stream and store data

    Parameters
    ----------

    arguments:
        The given command line arguments

    """

    identifier = arguments.identifier

    async with Network() as network:
        await network.connect_sensor_device(identifier)

        stream_data = await network.read_streaming_data_seconds(arguments.time)

        sensor_range = await network.read_acceleration_sensor_range_in_g()
        conversion_to_g = partial(convert_raw_to_g, max_value=sensor_range)
        stream_data.apply(conversion_to_g)

        print(f"\nStream Data:\n{stream_data}")


async def rename(arguments: Namespace) -> None:
    """Rename a sensor device

    Parameters
    ----------

    arguments:
        The given command line arguments

    """

    identifier = arguments.identifier
    name = arguments.name

    async with Network() as network:
        node = "STH 1"

        await network.connect_sensor_device(identifier)
        old_name = await network.get_name(node)
        mac_address = await network.get_mac_address(node)

        await network.set_name(name, node)
        name = await network.get_name(node)
        print(
            f"Renamed sensor device “{old_name}” with MAC "
            f"address “{mac_address}” to “{name}”"
        )


async def stu(arguments: Namespace) -> None:
    """Run specific commands regarding stationary transceiver unit

    Parameters
    ----------

    arguments:
        The given command line arguments

    """

    subcommand = arguments.stu_subcommand

    async with Network() as network:
        if subcommand == "ota":
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
        elif subcommand == "mac":
            print(await network.get_mac_address("STU 1"))
        else:
            raise ValueError(f"Unknown STU subcommand “{subcommand}”")


def main():
    """ICOtronic command line tool"""

    arguments = parse_arguments()
    command_to_coroutine = {
        "list": list_sensor_devices,
        "measure": measure,
        "rename": rename,
        "stu": stu,
    }

    try:
        run(command_to_coroutine[arguments.subcommand](arguments))
    except NetworkError as error:
        print(error)
    except KeyboardInterrupt:
        pass


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    main()
