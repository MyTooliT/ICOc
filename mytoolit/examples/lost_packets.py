"""Read acceleration data and calculate packet loss of STH"""

# -- Imports ------------------------------------------------------------------

from asyncio import run
from argparse import ArgumentParser, Namespace
from time import sleep, time

from mytoolit.can import Network
from mytoolit.cmdline.parse import add_identifier_arguments

# -- Functions ----------------------------------------------------------------


def parse_arguments() -> Namespace:
    """Parse command line arguments

    Returns
    -------

    A namespace object that represents the given command line arguments

    """

    parser = ArgumentParser(
        description="Measure signal and determine data loss"
    )

    add_identifier_arguments(parser)

    parser.add_argument(
        "-t",
        "--time",
        type=float,
        help="measurement time in seconds",
        default=3,
    )

    return parser.parse_args()


# -- Coroutines ---------------------------------------------------------------


async def calculate_loss(identifier, duration):
    """Connect to sensor device and measure data loss

    Parameters
    ----------

    identifier:
        Identifier of the sensor device we want to connect to

    duration:
        Amount of seconds streaming data should be measured

    """

    async with Network() as network:
        await network.reset_node("STU 1")

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

                sleep(1)  # Wait to fill CAN message buffer

                counter = timestamped_value.counter

                messages += 1
                lost_messages += (counter - last_counter) % 256 - 1

                last_counter = counter

                if time() - start_time >= duration:
                    break

            print("Stop streaming of data")
            await network.stop_streaming_data()

            print("Count messages in buffer")
            lost_messages_buffer = 0

            while not stream.queue.empty():
                await stream.queue.get()
                lost_messages_buffer += 1

                if time() - start_time > 10:
                    print("Stopping after 10 seconds")
                    break

        print(f"Lost {lost_messages} of {messages} messages")
        print(f"{lost_messages_buffer} messages in buffer")


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    args = parse_arguments()

    run(calculate_loss(identifier=args.identifier, duration=args.time))
