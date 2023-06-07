# -- Imports ------------------------------------------------------------------

from argparse import Namespace
from asyncio import run, sleep
from functools import partial
from logging import basicConfig, getLogger
from pathlib import Path
from sys import stderr
from time import time
from typing import List

from can.interfaces.pcan import PcanError
from tqdm import tqdm

from mytoolit.can import Network
from mytoolit.can.adc import ADCConfiguration
from mytoolit.can.network import STHDeviceInfo, NetworkError
from mytoolit.cmdline.parse import parse_arguments
from mytoolit.config import ConfigurationUtility
from mytoolit.measurement import convert_raw_to_g, Storage


# -- Functions ----------------------------------------------------------------


def config(arguments: Namespace) -> None:
    """Open configuration file"""

    ConfigurationUtility.open_user_config()


async def dataloss(arguments: Namespace) -> None:
    """Check data loss at different sample rates"""

    identifier = arguments.identifier
    logger = getLogger(__name__)

    async with Network() as network:
        logger.info(f"Connecting to “{identifier}”")
        await network.connect_sensor_device(identifier)
        logger.info(f"Connected to “{identifier}”")

        sensor_range = await network.read_acceleration_sensor_range_in_g()
        conversion_to_g = partial(convert_raw_to_g, max_value=sensor_range)

        measurement_time_s = 10

        for oversampling_rate in (2**exponent for exponent in range(6, 10)):
            logger.info(f"Oversampling rate: {oversampling_rate}")
            config = ADCConfiguration(
                prescaler=2,
                acquisition_time=8,
                oversampling_rate=oversampling_rate,
            )
            await network.write_adc_configuration(**config)
            sample_rate = config.sample_rate()
            logger.info(f"Sample rate: {sample_rate} Hz")

            filepath = Path(f"Measurement {sample_rate} Hz.hdf5")
            with Storage(filepath.resolve()) as storage:
                progress = tqdm(
                    total=int(sample_rate * measurement_time_s),
                    desc="Read sensor data",
                    unit=" values",
                    leave=False,
                    disable=None,
                )

                start_time = time()
                try:
                    async with network.open_data_stream(first=True) as stream:
                        async for data in stream:
                            data.apply(conversion_to_g)
                            storage.add_streaming_data(data)
                            progress.update(3)
                            if time() - start_time >= measurement_time_s:
                                break
                except PcanError as error:
                    print(
                        f"Unable to collect streaming data: {error}",
                        file=stderr,
                    )

                storage.add_acceleration_meta(
                    "Sensor_Range", f"± {sensor_range/2} g₀"
                )

                progress.close()
            print(f"Stored measurement data in “{filepath}”")


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
    measurement_time_s = arguments.time

    async with Network() as network:
        await network.connect_sensor_device(identifier)

        # Reduce sample rate to decrease CPU usage
        # See: https://github.com/MyTooliT/ICOc/issues/40
        adc_config = ADCConfiguration(
            reference_voltage=3.3,
            prescaler=2,
            acquisition_time=8,
            oversampling_rate=512,
        )
        await network.write_adc_configuration(**adc_config)

        sensor_range = await network.read_acceleration_sensor_range_in_g()
        conversion_to_g = partial(convert_raw_to_g, max_value=sensor_range)

        filepath = Path("Measurement.hdf5")

        with Storage(filepath.resolve()) as storage:
            sample_rate = (
                await network.read_adc_configuration()
            ).sample_rate()
            progress = tqdm(
                total=int(sample_rate * measurement_time_s),
                desc="Read sensor data",
                unit=" values",
                leave=False,
                disable=None,
            )

            async with network.open_data_stream(first=True) as stream:
                start_time = time()
                async for data in stream:
                    data.apply(conversion_to_g)
                    storage.add_streaming_data(data)
                    progress.update(3)  # 3 values per message

                    if time() - start_time >= measurement_time_s:
                        break
            storage.add_acceleration_meta(
                "Sensor_Range", f"± {sensor_range/2} g₀"
            )

            progress.close()


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
        elif subcommand == "reset":
            await network.reset_node("STU 1")
        else:
            raise ValueError(f"Unknown STU subcommand “{subcommand}”")


def main():
    """ICOtronic command line tool"""

    arguments = parse_arguments()
    basicConfig(
        level=arguments.log.upper(),
        style="{",
        format="{asctime} {levelname:7} {message}",
    )

    if arguments.subcommand == "config":
        config(arguments.subcommand)
    else:
        command_to_coroutine = {
            "config": config,
            "dataloss": dataloss,
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
