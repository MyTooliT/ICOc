from asyncio import run

from netaddr import EUI

from mytoolit.can import Network


async def test(identifier=EUI("08:6b:d7:01:de:81")):
    with Network() as network:
        await network.connect_sth(identifier)

        text = "something"
        length = len(text)
        print(f"Write text: {text}")
        await network.write_eeprom_text(address=10,
                                        offset=0,
                                        text=text,
                                        length=length,
                                        node='STH 1')
        read_text = await network.read_eeprom_text(address=10,
                                                   offset=0,
                                                   length=length,
                                                   node='STH 1')
        print(f"Read text: {read_text}")


if __name__ == '__main__':
    run(test())
