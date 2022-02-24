from asyncio import run
from time import time

from netaddr import EUI

from mytoolit.can import Network


async def test(identifier=EUI("08:6b:d7:01:de:81")):
    async with Network() as network:
        node = 'STH 1'
        start_time = time()

        await network.connect_sensor_device(identifier)
        name = await network.get_name(node)
        print(f"Name of {node}: {name}")

        seconds = 1
        print(f"Read raw x acceleration data for {seconds} s")
        data = await network.read_x_acceleration_raw(seconds)
        print(f"Read Data: {data}")

        print("\nExecution took {:.3} seconds".format(time() - start_time))


if __name__ == '__main__':
    run(test())
