"""Read some acceleration data of STH with device name Test-STH"""

# -- Imports ------------------------------------------------------------------

from asyncio import run

from mytoolit.can import Network
from mytoolit.can.streaming import StreamingConfiguration

# -- Functions ----------------------------------------------------------------


async def read_streaming_data(identifier):
    async with Network() as network:
        await network.connect_sensor_device(identifier)

        # Read data of first channel
        async with network.open_data_stream(
            StreamingConfiguration(first=True)
        ) as stream:
            messages = 5
            async for data, _ in stream:
                print(f"Read data values: {data}")
                messages -= 1
                if messages <= 0:
                    break


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    run(read_streaming_data(identifier="Test-STH"))
