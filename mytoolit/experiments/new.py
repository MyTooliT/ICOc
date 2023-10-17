"""Experiment with some functionality of the „new“ Network class"""

# -- Imports ------------------------------------------------------------------

from asyncio import run
from time import time

from mytoolit.can import Network


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

        async with network.open_data_stream(first=True) as stream:
            async for data in stream:
                utc_timestamp = time()
                message_timestamp = data.first.pop().timestamp
                offset = abs(message_timestamp - utc_timestamp)
                print(f"UTC timestamp:     {utc_timestamp}")
                print(f"Message timestamp: {message_timestamp}")
                print(f"Offset: {offset} ({offset / 60:.3f} minutes)")
                break


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    run(test(identifier=0))
