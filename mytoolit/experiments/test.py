from asyncio import run

from netaddr import EUI

from mytoolit.can import Network


async def test(identifier=EUI("08:6b:d7:01:de:81")):
        await network.connect_sth(identifier)

        node = 'STU 1'
        mac_address = await network.get_mac_address(node)
        print(f"MAC address of {node}: {mac_address}")
    async with Network() as network:


if __name__ == '__main__':
    run(test())
