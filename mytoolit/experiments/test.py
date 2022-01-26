from asyncio import run
from time import time

from netaddr import EUI

from mytoolit.can import Network


async def test(identifier):
    async with Network() as network:
        node = 'STH 1'
        start_time = time()

        await network.connect_sth(identifier)
        name = await network.get_name(node)
        print(f"Name of {node}: {name}\n")

        values = await network.read_sensor_values()
        print(f"Sensor Values: {values}")

        print(f"\nExecution took {time() - start_time:.3f} seconds")


if __name__ == '__main__':
    sth_mac = EUI("08:6b:d7:01:de:81")
    smh_mac = EUI("94-DE-B8-ED-70-37")

    run(test(identifier=smh_mac))
