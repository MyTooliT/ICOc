"""Experiment with some functionality of the „new“ Network class"""

# -- Imports ------------------------------------------------------------------

from asyncio import run

from mytoolit.can import Network


# -- Functions ----------------------------------------------------------------
async def test(identifier):
    async with Network() as network:
        node = 'STH 1'

        await network.connect_sensor_device(identifier)
        name = await network.get_name(node)
        mac_address = await network.get_mac_address(node)
        print(f"Connected to sensor device “{name}” with MAC "
              f"address “{mac_address}”")

        for reference_voltage in (1.8, 3.3):
            await network.write_adc_configuration(
                reference_voltage=reference_voltage)
            adc_config = await network.read_adc_configuration()
            reference_voltage = adc_config.reference_voltage()
            print(f"\nReference Voltage: {reference_voltage} V")

            for dimension in list("xyz"):

                acceleration_voltage_before = (
                    await network.read_acceleration_voltage(
                        dimension=dimension,
                        reference_voltage=reference_voltage))

                await network.activate_acceleration_self_test()

                acceleration_voltage = await network.read_acceleration_voltage(
                    dimension=dimension, reference_voltage=reference_voltage)

                await network.deactivate_acceleration_self_test()

                difference_voltage = (acceleration_voltage -
                                      acceleration_voltage_before)
                difference_voltage_mv = round(difference_voltage * 1000)

                print(f"{dimension.upper()} Difference: "
                      f"{difference_voltage_mv} mV")


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    new_sth = ""
    old_sth = "Test-STH"

    run(test(new_sth))
