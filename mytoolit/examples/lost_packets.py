"""Read acceleration data and calculate packet loss of STH"""

# -- Imports ------------------------------------------------------------------

from asyncio import run
from time import time

from mytoolit.can import Network

# -- Functions ----------------------------------------------------------------


async def calculate_loss(identifier, duration=5):
    """Connect to sensor device and measure data loss

    Parameters
    ----------

    identifier:
        Identifier of the sensor device we want to connect to

    duration:
        Amount of seconds streaming data should be measured

    """

    async with Network() as network:
        await network.connect_sensor_device(identifier)

        print(f"Measure data for {duration} seconds")
        # Read data of first channel
        async with network.open_data_stream(first=True) as stream:
            start_time = time()
            last_counter = -1
            messages = 0
            lost_messages = 0

            async for data in stream:
                timestamped_value = data.first.pop()
                last_counter = timestamped_value.counter
                messages = 1
                break

            async for data in stream:
                timestamped_value = data.first.pop()

                counter = timestamped_value.counter

                messages += 1
                lost_messages += (counter - last_counter) % 256 - 1

                last_counter = counter

                if time() - start_time >= duration:
                    break

        print(f"Lost {lost_messages} of {messages} messages")


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    run(calculate_loss(identifier="Test-STH"))
