"""Read and store some acceleration data of STH with device name Test-STH"""

# -- Imports ------------------------------------------------------------------

from asyncio import run
from functools import partial
from pathlib import Path
from time import time

from mytoolit.can import Network
from mytoolit.can.streaming import StreamingConfiguration
from mytoolit.measurement import convert_raw_to_g, Storage

# -- Functions ----------------------------------------------------------------


async def store_streaming_data(identifier):
    async with Network() as network:
        await network.connect_sensor_device(identifier)

        sensor_range = await network.read_acceleration_sensor_range_in_g()
        conversion_to_g = partial(convert_raw_to_g, max_value=sensor_range)

        # Read data for five seconds
        start = time()
        end = start + 5
        filepath = Path("test.hdf5")
        stream_first = StreamingConfiguration(first=True)

        with Storage(filepath, channels=stream_first) as storage:
            # Store acceleration range as metadata
            storage.add_acceleration_meta(
                "Sensor_Range", f"± {sensor_range / 2} g₀"
            )
            async with network.open_data_stream(stream_first) as stream:
                async for data, _ in stream:
                    # Convert from ADC bit value into multiples of g
                    data.apply(conversion_to_g)
                    # Store in data file
                    storage.add_streaming_data(data)
                    if time() > end:
                        break


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    run(store_streaming_data(identifier="Test-STH"))
