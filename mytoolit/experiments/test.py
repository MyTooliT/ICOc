from asyncio import run

from mytoolit.can import Network


async def test():
    async with Network() as network:
        node = 'STU 1'
        hardware_version = await network.get_hardware_version(node)
        print(f"Hardware version of “{node}”: “{hardware_version}”")


if __name__ == '__main__':
    run(test())
