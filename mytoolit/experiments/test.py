from asyncio import run
from time import time

from netaddr import EUI

from mytoolit.can import Network, NetworkError


async def test(identifier=EUI("08:6b:d7:01:de:81")):
    async with Network() as network:
        start_time = time()

        print("Try to read supply voltage")

        await network.connect_sth(identifier)

        try:
            supply_voltage = await network.read_supply_voltage()
            print(f"Supply voltage: {supply_voltage:.3f}")
        except NetworkError:
            error = "Unable to read supply voltage"
            if not await network.is_connected():
                print(f"{error} because of disconnect")
            else:
                print(f"{error} due to unknown reason")

        print("Execution took {:.3} seconds\n".format(time() - start_time))


if __name__ == '__main__':
    run(test())
