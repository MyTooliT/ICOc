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
        reader = await network.start_streaming_data(first=True)
        network.notifier.add_listener(reader)

        stream_data = StreamingData()
        async for streaming_data in reader:
            stream_data.extend(streaming_data)
            if len(stream_data.first) >= values_to_read:
                break

        network.notifier.remove_listener(reader)
        await network.stop_streaming_data()

        print(f"\nStream Data:\n{stream_data}")


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    run(test(identifier=0))
