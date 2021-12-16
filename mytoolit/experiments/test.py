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

        voltage = await network.read_acceleration_voltage()
        print(f"Acceleration Voltage Before: {voltage} V")

        print("Activate self test")
        await network.activate_acceleration_self_test()

        voltage = await network.read_acceleration_voltage()
        print(f"Acceleration Voltage Between: {voltage} V")

        print("Deactivate self test")
        await network.deactivate_acceleration_self_test()

        voltage = await network.read_acceleration_voltage()
        print(f"Acceleration Voltage After: {voltage} V")

        print("\nExecution took {:.3} seconds".format(time() - start_time))


if __name__ == '__main__':
    run(test())
