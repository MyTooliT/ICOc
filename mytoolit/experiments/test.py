from asyncio import run, sleep

from mytoolit.can import Network


async def create_connection_network():
    with Network() as network:
        print("Reset STU 1")
        await network.reset_node('STU 1')  # Reset STU (and STH)

        wait_time = 1
        print(f"Wait {wait_time} second{'' if wait_time == 1 else 's'} "
              "for STU 1 reset")
        await sleep(wait_time)

        print("Scan for available STHs")
        devices = []
        while not devices:
            devices = await network.get_sths()
            await sleep(0.1)
        device = devices[0]

        print(f"Connect to device “{device.name}”")
        await network.connect_sth(device.mac_address)

        print("Deactivate Bluetooth of STU 1")
        await network.deactivate_bluetooth()


if __name__ == '__main__':
    run(create_connection_network())
