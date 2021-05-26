from asyncio import run
from time import time

from mytoolit.can import Network


async def test():
    async with Network() as network:
        node = 'STU 1'
        print(f"{node}\n{'=' * len(node)}\n")
        start_time = time()
        print(f"State: “{await network.get_state(node)}”")
        print(f"RSSI: “{await network.get_mac_address(node)}”")
        print(f"Firmware: “{await network.get_firmware_release_name(node)}”")
        print("\nExecution took {} seconds".format(time() - start_time))


if __name__ == '__main__':
    run(test())
