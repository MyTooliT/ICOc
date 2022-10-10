"""Experiment with some functionality of the „new“ Network class"""

# -- Imports ------------------------------------------------------------------

from asyncio import run

from mytoolit.can import Network
from mytoolit.can.streaming import StreamingData


# -- Functions ----------------------------------------------------------------
async def test(identifier):
    async with Network() as network:
        node = 'STH 1'

        await network.connect_sensor_device(identifier)
        name = await network.get_name(node)
        mac_address = await network.get_mac_address(node)
        print(f"Connected to sensor device “{name}” with MAC "
              f"address “{mac_address}”")

        values_to_read = 5
        async with network.open_data_stream(first=True) as stream:
            stream_data = StreamingData()
            async for data in stream:
                stream_data.extend(data)
                if len(stream_data.first) >= values_to_read:
                    break

        print(f"\nStream Data:\n{stream_data}")


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    run(test(identifier=0))
