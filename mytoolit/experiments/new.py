"""Experiment with some functionality of the „new“ Network class"""

# -- Imports ------------------------------------------------------------------

from asyncio import run
from time import time

from mytoolit.can import Network


# -- Functions ----------------------------------------------------------------
async def test(identifier="Test-STH"):
    async with Network() as network:

        async def read_acceleration_voltage(dimension: str = 'x',
                                            self_test=False):
            voltage = await network.read_acceleration_voltage(dimension, 1.8)
            print(f"\nAcceleration Voltage: {voltage} V "
                  "(1.8 V Reference Voltage)")
            if self_test:
                await network.activate_acceleration_self_test(dimension)
            voltage = await network.read_acceleration_voltage(dimension)
            print(f"Acceleration Voltage: {voltage} V "
                  "(Default Reference Voltage)")

        node = 'STH 1'
        start_time = time()

        await network.connect_sensor_device(identifier)
        name = await network.get_name(node)
        mac_address = await network.get_mac_address(node)
        print(f"Connected to sensor device “{name}” with MAC "
              f"address “{mac_address}”")

        for dimension in "xyz":

            print(f"\n=====\n= {dimension} =\n=====")

            print("\nBefore Self Test:")
            await read_acceleration_voltage(dimension)

            print("\nSelf Test:")
            await network.activate_acceleration_self_test(dimension)
            await read_acceleration_voltage(dimension, self_test=True)
            await network.deactivate_acceleration_self_test(dimension)

            print("\nAfter Self Test:")
            await read_acceleration_voltage(dimension)

        print("\nExecution took {:.3} seconds".format(time() - start_time))


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    run(test())
