"""Experiment with some functionality of the „new“ Network class"""

# -- Imports ------------------------------------------------------------------

from asyncio import run
from functools import partial

from mytoolit.can import Network
from mytoolit.measurement import convert_raw_to_g


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

        stream_data = await network.read_streaming_data_amount(1000)

        sensor_range = await network.read_acceleration_sensor_range_in_g()
        conversion_to_g = partial(convert_raw_to_g, max_value=sensor_range)
        stream_data.apply(conversion_to_g)

        print(f"\nStream Data:\n{stream_data}")


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    run(test(identifier=0))
