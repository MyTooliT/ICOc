from asyncio import run
from time import time

from netaddr import EUI

from mytoolit.can import Network


async def test(identifier=EUI("08:6b:d7:01:de:81")):
    async with Network() as network:
        node = 'STH 1'
        start_time = time()

        await network.connect_sth(identifier)
        name = await network.get_name(node)
        print(f"Name of {node}: {name}")
        supply_voltage = await network.read_voltage()
        print(f"Supply voltage of {node}: {supply_voltage:.3} V")

        print("\nExecution took {:.3} seconds".format(time() - start_time))


if __name__ == '__main__':
    run(test())
