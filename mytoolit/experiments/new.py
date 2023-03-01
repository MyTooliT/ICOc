"""Experiment with some functionality of the „new“ Network class"""

# -- Imports ------------------------------------------------------------------

from asyncio import run
from functools import partial
from pathlib import Path
from time import time

from mytoolit.can import Network
from mytoolit.measurement import convert_raw_to_g, Storage


# -- Functions ----------------------------------------------------------------
async def test(identifier):
    async with Network() as network:
        node = "STH 1"

        await network.connect_sensor_device(identifier)
        name = await network.get_name(node)
        mac_address = await network.get_mac_address(node)
        print(
            f"Connected to sensor device “{name}” with MAC "
            f"address “{mac_address}”"
        )

        sensor_range = await network.read_acceleration_sensor_range_in_g()
        print(f"Sensor Range: {sensor_range/2} g")

        conversion_to_g = partial(convert_raw_to_g, max_value=sensor_range)

        measurement_time_s = 5 * 60

        print(f"Measure acceleration values for {measurement_time_s} seconds…")
        filepath = Path(__file__).parent.parent.parent / "experiment.hdf5"
        with Storage(filepath) as storage:
            start_time = time()
            async with network.open_data_stream(first=True) as stream:
                async for data in stream:
                    data.apply(conversion_to_g)
                    x_acceleration_values = data.first
                    for timestamped in x_acceleration_values:
                        storage.add_acceleration(
                            values={"x": timestamped.value.magnitude},
                            counter=timestamped.counter,
                            timestamp=timestamped.timestamp,
                        )

                    if time() - start_time >= measurement_time_s:
                        break
                storage.add_acceleration_meta(
                    "Sensor_Range", f"± {sensor_range} g₀"
                )


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    run(test(identifier=0))
