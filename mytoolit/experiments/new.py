"""Experiment with some functionality of the „new“ Network class"""

# -- Imports ------------------------------------------------------------------

from asyncio import run
from time import time

from mytoolit.can import Network
from mytoolit.measurement import ratio_noise_max


# -- Functions ----------------------------------------------------------------
async def test(identifier="Test-STH"):
    async with Network() as network:

        async def read_snr(voltage):
            await network.write_adc_configuration(prescaler=2,
                                                  acquisition_time=8,
                                                  oversampling_rate=64,
                                                  reference_voltage=voltage)

            data = await network.read_x_acceleration_raw(1)
            return ratio_noise_max(data)

        node = 'STH 1'
        start_time = time()

        await network.connect_sensor_device(identifier)
        name = await network.get_name(node)
        mac_address = await network.get_mac_address(node)
        print(f"Connected to sensor device “{name}” with MAC "
              f"address “{mac_address}”\n")

        for voltage in (1.8, 3.3):
            snr = await read_snr(voltage)
            print(f"SNR ({voltage} V): {snr}")

        print("\nExecution took {:.3} seconds".format(time() - start_time))


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    run(test())
