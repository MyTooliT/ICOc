from asyncio import run

from netaddr import EUI

from mytoolit.can import Network


async def test(identifier=EUI("08:6b:d7:01:de:81")):
    with Network() as network:
        await network.connect_sth(identifier)

        number = 1337
        length = 4
        print(f"Write number: {number}")
        await network.write_eeprom_int(address=10,
                                       offset=0,
                                       value=number,
                                       length=length,
                                       node='STH 1')
        read_number = await network.read_eeprom_int(address=10,
                                                    offset=0,
                                                    length=length,
                                                    node='STH 1')
        print(f"Read number: {read_number}")


if __name__ == '__main__':
    run(test())
