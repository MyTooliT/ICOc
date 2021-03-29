from asyncio import run, sleep

from netaddr import EUI

from mytoolit.can import Network


async def test(identifier=EUI("08:6b:d7:01:de:81")):
    with Network() as network:
        print("Reset STU 1")
        await network.reset_node('STU 1')  # Reset STU (and STH)

        wait_time = 1
        print(f"Wait {wait_time} second{'' if wait_time == 1 else 's'} "
              "for STU 1 reset")
        await sleep(wait_time)

        print(f"Connect to device “{identifier}”")
        await network.connect_sth(identifier)

        print("Deactivate Bluetooth of STU 1")
        await network.deactivate_bluetooth()


if __name__ == '__main__':
    run(test("Serial"))
    run(test(0))
    run(test())
