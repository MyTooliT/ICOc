from asyncio import run

from netaddr import EUI

from mytoolit.can import Network


async def test(identifier=EUI("08:6b:d7:01:de:81")):
    with Network() as network:
        await network.connect_sth(identifier)
        data = [1, 3, 3, 7, 5, 6, 7, 8]

        await network.write_eeprom(address=1,
                                   offset=0,
                                   data=data,
                                   node='STH 1')
        read_data = await network.read_eeprom(address=1,
                                              offset=0,
                                              length=len(data),
                                              node='STH 1')
        print(f"Read data: {read_data}")
        await network.deactivate_bluetooth('STU 1')


if __name__ == '__main__':
    run(test())
