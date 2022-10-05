"""Experiment with some functionality of the „new“ Network class"""

# -- Imports ------------------------------------------------------------------

from asyncio import run

from mytoolit.can import Network
from mytoolit.config import settings
from mytoolit.measurement import convert_raw_to_g


# -- Functions ----------------------------------------------------------------
async def test(identifier):
    async with Network() as network:
        node = 'STH 1'

        await network.connect_sensor_device(identifier)
        name = await network.get_name(node)
        mac_address = await network.get_mac_address(node)
        print(f"Connected to sensor device “{name}” with MAC "
              f"address “{mac_address}”")

        sensor = settings.acceleration_sensor()
        stream_data = await network.read_streaming_data_single()
        acceleration = convert_raw_to_g(stream_data.first.pop().value,
                                        sensor.acceleration.maximum)

        print(f"Acceleration in x direction: {acceleration}")


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    run(test(identifier=0))
