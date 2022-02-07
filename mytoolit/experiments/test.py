from asyncio import run
from time import time

from netaddr import EUI

from mytoolit.can.network import Network, Times


async def test(identifier=EUI("08:6b:d7:01:de:81")):
    async with Network() as network:
        node = 'STH 1'
        start_time = time()

        await network.connect_sth(identifier)
        name = await network.get_name(node)
        print(f"Name of {node}: {name}\n")

        times = Times(
            sleep=300000,
            advertisement=1250,
        )
        print(f"Set time values for reduced energy mode to “{times}”")

        await network.write_energy_mode_reduced(node=node, times=times)

        times = await network.read_energy_mode_reduced(node)
        print(f"Advertisement Time: {times.advertisement} ms")
        print(f"Sleep Time:         {times.sleep} ms")

        print("\nExecution took {:.3} seconds".format(time() - start_time))


if __name__ == '__main__':
    run(test())
