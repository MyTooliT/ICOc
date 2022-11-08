# -- Imports ------------------------------------------------------------------

from statistics import mean
from unittest import main as unittest_main

from mytoolit.can.node import Node
from mytoolit.cmdline.commander import Commander
from mytoolit.config import settings
from mytoolit.measurement import ADC_MAX_VALUE
from mytoolit.measurement.sensor import guess_sensor_type
from mytoolit.report import Report
from mytoolit.test.production import TestSensorNode
from mytoolit.test.unit import ExtendedTestRunner

# -- Class --------------------------------------------------------------------


class TestSMH(TestSensorNode):
    """This class contains tests for the milling head sensor (PCB)"""

    @classmethod
    def setUpClass(cls):
        """Set up data for whole test"""

        super().setUpClass()
        cls.report = Report(node='SMH')

    def _connect(self):
        """Create a connection to the SMH"""

        super()._connect_device(settings.smh.name)

    def _read_data(self):
        """Read data from connected SMH"""

        super()._read_data()

        cls = type(self)
        cls.name = settings.smh.name

    def test__firmware_flash_disconnected(self):
        """Upload bootloader and application into SMH

        Please note the additional underscore in the method name that makes
        sure this test case is executed before all other test cases.

        The text `disconnected` in the method name make sure that the test
        framework does not initialize a connection.

        """

        self._test_firmware_flash(
            node='SMH',
            flash_location=settings.smh.firmware.location.flash,
            programmmer_serial_number=settings.smh.programming_board.
            serial_number,
            chip='BGM121A256V2')

    def test_connection(self):
        """Check connection to SMH"""

        super()._test_connection_device()

    def test_eeprom(self):
        """Test if reading and writing the EEPROM works"""

        async def test_eeprom():
            """Test the EERPOM of the SMH"""

            cls = type(self)
            receiver = Node('STH 1')

            # ========
            # = Name =
            # ========

            name = settings.smh.name

            await self.can.write_eeprom_name(name, receiver)
            read_name = await self.can.read_eeprom_name(receiver)

            self.assertEqual(
                name, read_name,
                f"Written name “{name}” does not match read name “{read_name}”"
            )

            cls.name = read_name

            # =========================
            # = Sleep & Advertisement =
            # =========================

            await self._test_eeprom_sleep_advertisement_times()

            # ================
            # = Product Data =
            # ================

            await self._test_eeprom_product_data(receiver, settings.smh)

            # ==============
            # = Statistics =
            # ==============

            await self._test_eeprom_statistics(receiver,
                                               settings.smh.production_date,
                                               settings.smh.batch_number)

        self.loop.run_until_complete(test_eeprom())

    def test_adc_values(self):
        """Test raw ADC sensor values"""

        async def test_adc_values():

            def check_value(value,
                            channel,
                            expected_value,
                            tolerance=round(ADC_MAX_VALUE * 0.1)):
                """Check if an ADC value is roughly equal to another value"""

                expected_minimum_value = expected_value - tolerance
                expected_maximum_value = expected_value + tolerance

                self.assertGreaterEqual(
                    value, expected_minimum_value,
                    f"Measured ADC value for channel {channel} “{value}” is "
                    "lower than expected minimum value "
                    f"“{expected_minimum_value}”")
                self.assertLessEqual(
                    value, expected_maximum_value,
                    f"Measured ADC value for channel {channel} “{value}” is "
                    "higher than expected maximum value "
                    f"“{expected_maximum_value}”")

            # The values below represent roughly the read values from a
            # working SMH
            expected_value_piezo = 38300
            expected_value_thermistor = 10780

            data = await self.can.read_streaming_data_single()
            values = (channel.pop().value for channel in data)
            expected_values = (expected_value_piezo, expected_value_piezo,
                               expected_value_thermistor)

            for channel, (value,
                          expected) in enumerate(zip(values, expected_values),
                                                 start=1):
                check_value(value, channel, expected)

        self.loop.run_until_complete(test_adc_values())

    def test_sensors(self):
        """Test available sensor channels"""

        async def test_sensors():

            for test_channel in range(1, settings.smh.channels + 1):
                await self.can.write_sensor_configuration(first=test_channel)
                config = await self.can.read_sensor_configuration()
                self.assertEqual(
                    config.first, test_channel,
                    f"Read sensor channel number “{config.first}” does "
                    f"not match expected channel number “{test_channel}”")
                stream_data = await self.can.read_streaming_data_amount(
                    1000, first=True, second=False, third=False)
                values = [
                    timestamped.value for timestamped in stream_data.first
                ]
                sensor_type = guess_sensor_type(values)
                print(f"Sensor Channel {test_channel}: {sensor_type}")

                self.assertNotRegex(
                    sensor_type, "[Bb]roken",
                    f"The sensor on measurement channel {test_channel} seems "
                    "to not work correctly. Mean of measured sensor values: "
                    f"{mean(values)}")

        self.loop.run_until_complete(test_sensors())

    def test_power_usage_disconnected(self) -> None:
        """Check power usage in disconnected state"""

        commander = Commander(
            serial_number=settings.smh.programming_board.serial_number,
            chip='BGM121A256V2')

        commander.enable_debug_mode()
        power_usage_mw = commander.read_power_usage()

        expected_maxmimum_usage_mw = 10
        self.assertLess(
            power_usage_mw, expected_maxmimum_usage_mw,
            f"Measured power usage of {power_usage_mw} mW is "
            "higher than expected maximum value "
            f"{expected_maxmimum_usage_mw} mW")


# -- Main ---------------------------------------------------------------------


def main():
    unittest_main(testRunner=ExtendedTestRunner,
                  module="mytoolit.test.production.smh")


if __name__ == "__main__":
    main()
