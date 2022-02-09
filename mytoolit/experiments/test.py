from asyncio import run
from time import time

from netaddr import EUI

from mytoolit.can.network import Network


async def test(identifier=EUI("08:6b:d7:01:de:81")):
    async with Network() as network:
        node = 'STH 1'
        start_time = time()

        await network.connect_sth(identifier)
        name = await network.get_name(node)
        print(f"Name of {node}: {name}\n")

        times = await network.read_energy_mode_lowest()
        print(f"Advertisement Time: {times.advertisement} ms")
        print(f"Sleep Time:         {times.sleep} ms")

        print("\nExecution took {:.3} seconds".format(time() - start_time))


if __name__ == '__main__':
    run(test())
