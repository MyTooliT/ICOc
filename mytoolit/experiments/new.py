"""Experiment with some functionality of the „new“ Network class"""

# -- Imports ------------------------------------------------------------------

from asyncio import run
from time import time

from mytoolit.can import Network


# -- Functions ----------------------------------------------------------------
async def test(identifier="Test-STH"):
    async with Network() as network:

        async def read_supply_voltage(reference_voltage: float):
            await network.write_adc_configuration(
                prescaler=2,
                acquisition_time=8,
                oversampling_rate=64,
                reference_voltage=reference_voltage)

            adc_config = await network.read_adc_configuration()
            reference_voltage_read = adc_config.reference_voltage()

            if reference_voltage_read != reference_voltage:
                raise Exception(
                    f"Written reference voltage {reference_voltage} V "
                    f"and read reference voltage {reference_voltage_read} V "
                    "are different")

            return await network.read_supply_voltage()

        node = 'STH 1'
        start_time = time()

        await network.connect_sensor_device(identifier)
        name = await network.get_name(node)
        mac_address = await network.get_mac_address(node)
        print(f"Connected to sensor device “{name}” with MAC "
              f"address “{mac_address}”\n")

        for reference_voltage in (1.8, 3.3):
            supply_voltage = await read_supply_voltage(reference_voltage)
            print(f"Supply Voltage (Reference: {reference_voltage} V):",
                  f"{supply_voltage} V")

        print("\nExecution took {:.3} seconds".format(time() - start_time))


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    run(test())
