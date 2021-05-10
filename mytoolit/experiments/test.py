from asyncio import run

from mytoolit.can import Network


async def test():
    async with Network() as network:
        node = 'STU 1'
        gtin = await network.get_gtin(node)
        print(f"GTIN of “{node}”: “{gtin}”")


if __name__ == '__main__':
    run(test())
