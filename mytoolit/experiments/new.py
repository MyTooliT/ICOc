"""Experiment with some functionality of the „new“ Network class"""

# -- Imports ------------------------------------------------------------------

from asyncio import run
from datetime import datetime

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

        sensor_range = await network.read_acceleration_sensor_range_in_g()
        print(f"Sensor Range: {sensor_range/2} g")

        data = await network.read_streaming_data_single()
        timestamp = data.first.pop().timestamp
        timestamp_utc = datetime.utcfromtimestamp(timestamp)
        timestamp_local = datetime.fromtimestamp(timestamp)

        print(f"Timestamp:     {timestamp}")
        print(f"Timestamp UTC: {timestamp_utc.timestamp()}")
        print(f"Local Time:    {timestamp_local.isoformat()}")
        print(f"UTC Time:      {timestamp_utc.isoformat()}")


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    run(test(identifier=0))
