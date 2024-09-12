"""ICOn command line tool

See: https://mytoolit.github.io/ICOc/#icon-cli-tool

for more information
"""

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
from mytoolit.can.error import UnsupportedFeatureException
from mytoolit.can.network import STHDeviceInfo, NetworkError
from mytoolit.can.streaming import StreamingTimeoutError
from mytoolit.cmdline.parse import create_icon_parser
from mytoolit.config import ConfigurationUtility, settings
from mytoolit.measurement import convert_raw_to_g, Storage
from mytoolit.measurement.sensor import SensorConfiguration


# -- Functions ----------------------------------------------------------------


async def read_acceleration_sensor_range_in_g(network: Network) -> float:
    """Read sensor range of acceleration sensor

    Precondition
    ------------

    The Network object given as parameter needs to be connected to a sensor
    device before you call this coroutine

    Parameters
    ----------

    network:
        The network class used to read the sensor range

    Returns
    -------

    The sensor range of the acceleration sensor, or the default range of 200
    (± 100 g) sensor, if there was a problem reading the sensor range

    """

    sensor_range = 200

    try:
        sensor_range = await network.read_acceleration_sensor_range_in_g()
        if sensor_range < 1:
            print(
                f"Warning: Sensor range “{sensor_range}” below 1 g — Using "
                "range 200 instead (± 100 g sensor)",
                file=stderr,
            )
            sensor_range = 200
    except ValueError:
        print(
            "Warning: Unable to determine sensor range from "
            "EEPROM value — Assuming ± 100 g sensor",
            file=stderr,
        )

    return sensor_range


def config(arguments: Namespace) -> None:  # pylint: disable=unused-argument
    """Open configuration file"""

    ConfigurationUtility.open_user_config()


# pylint: disable=too-many-locals


async def dataloss(arguments: Namespace) -> None:
    """Check data loss at different sample rates"""

    identifier = arguments.identifier
    logger = getLogger(__name__)

    async with Network() as network:
        logger.info("Connecting to “%s”", identifier)
        await network.connect_sensor_device(identifier)
        logger.info("Connected to “%s”", identifier)

        sensor_range = await read_acceleration_sensor_range_in_g(network)
        conversion_to_g = partial(convert_raw_to_g, max_value=sensor_range)

        measurement_time_s = 10

        sensor_config = SensorConfiguration(first=1)

        for oversampling_rate in (2**exponent for exponent in range(6, 10)):
            logger.info("Oversampling rate: %s", oversampling_rate)
            adc_config = ADCConfiguration(
                prescaler=2,
                acquisition_time=8,
                oversampling_rate=oversampling_rate,
            )
            await network.write_adc_configuration(**adc_config)
            sample_rate = adc_config.sample_rate()
            logger.info("Sample rate: %s Hz", sample_rate)

            filepath = Path(f"Measurement {sample_rate} Hz.hdf5")
            with Storage(
                filepath.resolve(), sensor_config.streaming_configuration()
            ) as storage:
                storage.add_acceleration_meta(
                    "Sensor_Range", f"± {sensor_range / 2} g₀"
                )

                progress = tqdm(
                    total=int(sample_rate * measurement_time_s),
                    desc="Read sensor data",
                    unit=" values",
                    leave=False,
                    disable=None,
                )

                start_time = time()
                try:
                    async with network.open_data_stream(
                        sensor_config.streaming_configuration()
                    ) as stream:
                        async for data, _ in stream:
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

                progress.close()
            print(f"Stored measurement data in “{filepath}”")


# pylint: enable=too-many-locals


async def list_sensor_devices(
    arguments: Namespace,  # pylint: disable=unused-argument
) -> None:
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

    logger = getLogger(__name__)

    identifier = arguments.identifier
    measurement_time_s = arguments.time

    async with Network() as network:
        await network.connect_sensor_device(identifier)

        adc_config = ADCConfiguration(
            reference_voltage=arguments.voltage_reference,
            prescaler=arguments.prescaler,
            acquisition_time=arguments.acquisition,
            oversampling_rate=arguments.oversampling,
        )
        await network.write_adc_configuration(**adc_config)
        print(f"Sample Rate: {adc_config.sample_rate()} Hz")

        user_sensor_config = SensorConfiguration(
            first=arguments.first_channel,
            second=arguments.second_channel,
            third=arguments.third_channel,
        )

        if user_sensor_config.requires_channel_configuration_support():
            try:
                await network.write_sensor_configuration(user_sensor_config)
            except UnsupportedFeatureException as exception:
                raise UnsupportedFeatureException(
                    f"Sensor channel configuration “{user_sensor_config}” is "
                    f"not supported by the sensor node “{identifier}”"
                ) from exception

        sensor_range = await read_acceleration_sensor_range_in_g(network)
        conversion_to_g = partial(convert_raw_to_g, max_value=sensor_range)

        with Storage(
            settings.get_output_filepath(),
            user_sensor_config.streaming_configuration(),
        ) as storage:
            storage.add_acceleration_meta(
                "Sensor_Range", f"± {sensor_range / 2} g₀"
            )

            sample_rate = (
                await network.read_adc_configuration()
            ).sample_rate()
            streaming_config = user_sensor_config.streaming_configuration()
            logger.info("Streaming Configuration: %s", streaming_config)
            values_per_message = streaming_config.data_length()

            progress = tqdm(
                total=round(sample_rate * measurement_time_s, 0),
                desc="Read sensor data",
                unit=" values",
                leave=False,
                disable=None,
            )

            try:
                async with network.open_data_stream(
                    streaming_config
                ) as stream:
                    start_time = time()
                    async for data, _ in stream:
                        data.apply(conversion_to_g)
                        storage.add_streaming_data(data)
                        progress.update(values_per_message)

                        if time() - start_time >= measurement_time_s:
                            break
            except KeyboardInterrupt:
                pass
            finally:
                progress.close()
                print(f"Data Loss: {storage.dataloss()}")


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

    parser = create_icon_parser()
    arguments = parser.parse_args()
    try:
        if arguments.subcommand == "measure":
            SensorConfiguration(
                first=arguments.first_channel,
                second=arguments.second_channel,
                third=arguments.third_channel,
            ).check()
    except ValueError as error:
        parser.prog = f"{parser.prog} {arguments.subcommand}"
        parser.error(str(error))

    basicConfig(
        level=arguments.log.upper(),
        style="{",
        format="{asctime} {levelname:7} {message}",
    )

    logger = getLogger(__name__)
    logger.info("CLI Arguments: %s", arguments)

    if arguments.subcommand == "config":
        config(arguments.subcommand)
    else:
        command_to_coroutine = {
            "dataloss": dataloss,
            "list": list_sensor_devices,
            "measure": measure,
            "rename": rename,
            "stu": stu,
        }

        try:
            run(command_to_coroutine[arguments.subcommand](arguments))
        except (
            NetworkError,
            TimeoutError,
            UnsupportedFeatureException,
        ) as error:
            print(error, file=stderr)
        except StreamingTimeoutError as error:
            print(f"Quitting Measurement: {error}")
        except KeyboardInterrupt:
            pass


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    main()
