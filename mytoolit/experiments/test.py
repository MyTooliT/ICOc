from asyncio import run

from netaddr import EUI

from mytoolit.can import Network


async def test(identifier=EUI("08:6b:d7:01:de:81")):
    with Network() as network:
        await network.connect_sth(identifier)
        slope = await network.read_eeprom_float(address=8,
                                                offset=0,
                                                node='STH 1')
        print(f"Slope: {slope}")
        await network.deactivate_bluetooth('STU 1')


if __name__ == '__main__':
    run(test())
