"""Experiment with some functionality of the „new“ Network class"""

# -- Imports ------------------------------------------------------------------

from asyncio import run
from time import time

from mytoolit.can import Network


# -- Functions ----------------------------------------------------------------
async def test(identifier="Test-STH"):
    async with Network() as network:
        node = 'STH 1'
        start_time = time()

        await network.connect_sensor_device(identifier)
        name = await network.get_name(node)
        mac_address = await network.get_mac_address(node)
        print(f"Connected to sensor device “{name}” with MAC "
              f"address “{mac_address}”")

        adc_config = await network.read_adc_configuration()

        print(f"ADC configuration: {adc_config}")

        print("\nExecution took {:.3} seconds".format(time() - start_time))


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    run(test())
