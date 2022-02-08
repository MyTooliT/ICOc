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
        node = 'STU 1'
        device_number = 0xff
        print(f"Set time values for “{node}” (device number: {device_number}) "
              f" to “{times}”\n")
        await network.write_energy_mode_reduced(node=node, times=times)

        times = await network.read_energy_mode_reduced(
            node=node, device_number=device_number)
        print(f"{node}\n{'—' * len(node)}")
        print(f"Advertisement Time: {times.advertisement} ms")
        print(f"Sleep Time:         {times.sleep} ms")

        print("\nExecution took {:.3} seconds".format(time() - start_time))


if __name__ == '__main__':
    run(test())
