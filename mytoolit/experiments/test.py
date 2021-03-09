from asyncio import run, sleep

from netaddr import EUI

from mytoolit.can import Network


async def create_connection_network():
    with Network() as network:
        print("Reset STU 1")
        await network.reset_node('STU 1')  # Reset STU (and STH)

        wait_time = 1
        print(f"Wait {wait_time} second{'' if wait_time == 1 else 's'} "
              "for STU 1 reset")
        await sleep(wait_time)

        print("Activate Bluetooth of STU 1")
        await network.activate_bluetooth('STU 1')

        available_devices = 0
        print("Get available Bluetooth devices for STU 1")
        while available_devices <= 0:
            available_devices = await network.get_available_devices_bluetooth(
                'STU 1')
            await sleep(0.1)

        mac_address = EUI('08:6b:d7:01:de:81')
        print(f"Connect to device with MAC address {mac_address}")
        await network.connect_mac_address_bluetooth(mac_address)

        while not await network.check_connection_device_bluetooth():
            await sleep(0.1)

        print("Connection to Bluetooth device established")

        mac_address = await network.get_mac_address_bluetooth()
        print(f"MAC address of STH 1: {mac_address}")

        print("Deactivate Bluetooth of STU 1")
        await network.deactivate_bluetooth()


if __name__ == '__main__':
    run(create_connection_network())
