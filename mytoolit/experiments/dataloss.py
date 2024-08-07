"""Calculate streaming dataloss over a certain time period"""

# -- Imports ------------------------------------------------------------------

from asyncio import run
from time import time

from mytoolit.can import Network

# -- Functions ----------------------------------------------------------------


async def iterate_streaming_data(network, messages):
    offset_start = -1
    offset_end = -1
    async with network.open_data_stream(first=True) as stream:
        async for data, messages_lost in stream:
            if offset_start < 0:
                offset_start = time() - data.timestamp
            messages -= 1 + messages_lost
            if messages_lost > 0:
                print(f"Lost {messages_lost} messages")
            if messages <= 0:
                offset_end = time() - data.timestamp
                break
        messages_lost_overall = stream.lost_messages

    return messages_lost_overall, offset_end - offset_start


async def read_streaming_data(identifier):
    async with Network() as network:
        await network.connect_sensor_device(identifier)
        adc_config = await network.read_adc_configuration()
        time_s = 10
        messages = int(adc_config.sample_rate() * time_s / 3)
        messages_lost, delay = await iterate_streaming_data(network, messages)

    data_loss = messages_lost / messages
    print(f"Measurement Time: {time_s} s")
    print(f"Messages:         {messages}")
    print(f"Messages Lost:    {messages_lost}")
    print(f"Data Loss:        {data_loss:0.2f}")
    print(f"Delay:            {delay:0.2f} s")


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    run(read_streaming_data(identifier="Test-STH"))
