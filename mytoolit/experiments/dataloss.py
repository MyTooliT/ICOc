"""Calculate streaming dataloss over a certain time period"""

# -- Imports ------------------------------------------------------------------

from asyncio import run

from mytoolit.can import Network

# -- Functions ----------------------------------------------------------------


async def iterate_streaming_data(network, messages):
    messages_lost = 0
    async with network.open_data_stream(first=True) as stream:
        async for data, messages_lost in stream:
            messages -= 1 + messages_lost
            messages_lost += messages_lost
            if messages <= 0:
                break
    return messages_lost


async def read_streaming_data(identifier):
    async with Network() as network:
        await network.connect_sensor_device(identifier)
        adc_config = await network.read_adc_configuration()
        time_s = 10
        messages = int(adc_config.sample_rate() * time_s / 3)
        messages_lost = await iterate_streaming_data(network, messages)

    data_loss = messages_lost / messages
    print(f"Measurement Time: {time_s} s")
    print(f"Messages:         {messages}")
    print(f"Messages Lost:    {messages_lost}")
    print(f"Data Loss:        {data_loss:0.2f}")


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    run(read_streaming_data(identifier="Test-STH"))
