# -- Imports ------------------------------------------------------------------

from typing import List
from unittest import main as unittest_main, skipIf

from mytoolit.can import Node
from mytoolit.measurement import ratio_noise_max
from mytoolit.config import settings
from mytoolit.report import Report
from mytoolit.test.production import TestSensorNode
from mytoolit.test.unit import ExtendedTestRunner
from mytoolit.utility import (add_commander_path_to_environment,
                              convert_mac_base64)

# -- Classes ------------------------------------------------------------------


class TestSTH(TestSensorNode):
    """This class contains tests for the Sensory Tool Holder (STH)"""

    @classmethod
    def setUpClass(cls):
        """Set up data for whole test"""

        super().setUpClass()

        cls.add_attribute("Holder Type", "{cls.holder_type}", pdf=True)
        cls.add_attribute("Acceleration Sensor",
                          "{cls.acceleration_sensor}",
                          pdf=True)
        cls.add_attribute("Acceleration Slope",
                          "{cls.acceleration_slope:.5f}",
                          pdf=False)
        cls.add_attribute("Acceleration Offset",
                          "{cls.acceleration_offset:.3f}",
                          pdf=False)

        cls.report = Report(node='STH')

        # Add data that only applies to the STH
        cls.holder_type = settings.sth.holder_type
        cls.status = settings.sth.status

        sensor_name = settings.sth.acceleration_sensor.sensor
        maximum_acceleration = settings.acceleration_sensor(
        ).acceleration.maximum
        cls.acceleration_sensor = (
            f"±{maximum_acceleration//2} g Sensor ({sensor_name})")

        # Manual checks
        cls.report.add_checkbox_list(title="Metal Blank",
                                     boxes=[
                                         "Okay", "Cylindrical thread defect",
                                         "Dent", "Oil spillage", "Shavings",
                                         "Milling errors"
                                     ],
                                     text_fields=1)

        cls.report.add_checkbox_list(title="PCB",
                                     boxes=["Optical inspection: no defects"],
                                     text_fields=1)

        cls.report.add_checkbox_list(
            title="Before Resin Cast",
            boxes=[
                "Battery test successful",
                "Charge in charging station was successful"
            ],
            text_fields=2)

        cls.report.add_checkbox_list(
            title="Final Checks",
            boxes=[
                "Resin cast contains no bubbles",
                "Resin cast hardened completely",
                "No resin residue outside of pocket",
                "Pocket is completely filled with resin",
                "No oil spillage in vacuum chamber",
                "Charge in charging station was successful"
            ],
            text_fields=2)

    def _connect(self):
        """Create a connection to the STH"""

        super()._connect_device(settings.sth_name())

    def _read_data(self):
        """Read data from connected STH"""

        super()._read_data()

        cls = type(self)
        cls.name = settings.sth_name()

    @skipIf(settings.sth.status == "Epoxied",
            f"Flash test skipped because of status “{settings.sth.status}”")
    def test__firmware_flash_disconnected(self):
        """Upload bootloader and application into STH

        Please note the additional underscore in the method name that makes
        sure this test case is executed before all other test cases.

        The text `disconnected` in the method name make sure that the test
        framework does not initialize a connection.

        """

        self._test_firmware_flash(
            node='STH',
            flash_location=settings.sth.firmware.location.flash,
            programmmer_serial_number=settings.sth.programming_board.
            serial_number,
            chip='BGM113A256V2')

    def test_connection(self):
        """Check connection to STH"""

        super()._test_connection_device()

    def test_battery_voltage(self):
        """Test voltage of STH power source"""

        async def test_supply_voltage():
            """Check the supply voltage of the STH"""

            supply_voltage = await self.can.read_supply_voltage()

            expected_voltage = settings.sth.battery_voltage.average
            tolerance_voltage = settings.sth.battery_voltage.tolerance
            expected_minimum_voltage = expected_voltage - tolerance_voltage
            expected_maximum_voltage = expected_voltage + tolerance_voltage

            self.assertGreaterEqual(
                supply_voltage, expected_minimum_voltage,
                f"STH supply voltage of {supply_voltage:.3f} V is lower "
                "than expected minimum voltage of "
                f"{expected_minimum_voltage:.3f} V")
            self.assertLessEqual(
                supply_voltage, expected_maximum_voltage,
                f"STH supply voltage of {supply_voltage:.3f} V is "
                "greater than expected maximum voltage of "
                f"{expected_minimum_voltage:.3f} V")

        self.loop.run_until_complete(test_supply_voltage())

    def test_acceleration_single_value(self):
        """Test stationary acceleration value"""

        async def test_acceleration_single():
            """Test stationary x acceleration value"""

            sensor = settings.acceleration_sensor()
            acceleration = await self.can.read_x_acceleration(
                sensor.acceleration.maximum)

            # We expect a stationary acceleration of the standard gravity
            # (1 g₀ = 9.807 m/s²)
            expected_acceleration = 1
            tolerance_acceleration = sensor.acceleration.tolerance
            expected_minimum_acceleration = (expected_acceleration -
                                             tolerance_acceleration)
            expected_maximum_acceleration = (expected_acceleration +
                                             tolerance_acceleration)

            self.assertGreaterEqual(
                acceleration, expected_minimum_acceleration,
                f"Measured acceleration {acceleration:.3f} g is lower "
                "than expected minimum acceleration "
                f"{expected_minimum_acceleration} g")
            self.assertLessEqual(
                acceleration, expected_maximum_acceleration,
                f"Measured acceleration {acceleration:.3f} g is greater "
                "than expected maximum acceleration "
                f"{expected_maximum_acceleration} g")

        self.loop.run_until_complete(test_acceleration_single())

    def test_acceleration_noise(self):
        """Test ratio of noise to maximal possible measurement value"""

        acceleration = self.loop.run_until_complete(
            self.can.read_x_acceleration_raw(seconds=4))

        cls = type(self)
        cls.ratio_noise_max = ratio_noise_max(acceleration)

        sensor = settings.acceleration_sensor()
        maximum_ratio_allowed = sensor.acceleration.ratio_noise_to_max_value
        self.assertLessEqual(
            cls.ratio_noise_max, maximum_ratio_allowed,
            "The ratio noise to possible maximum measured value of "
            f"{cls.ratio_noise_max} dB is higher than the maximum allowed "
            f"level of {maximum_ratio_allowed} dB")

    def test_acceleration_self_test(self):
        """Execute self test of accelerometer"""

        async def read_voltages(dimension, reference_voltage) -> List[int]:
            """Read acceleration voltages in millivolts"""

            before = await self.can.read_acceleration_voltage(
                dimension, reference_voltage)

            await self.can.activate_acceleration_self_test(dimension)
            between = await self.can.read_acceleration_voltage(
                dimension, reference_voltage)

            await self.can.deactivate_acceleration_self_test(dimension)
            after = await self.can.read_acceleration_voltage(
                dimension, reference_voltage)

            return [round(value * 1000) for value in (before, between, after)]

        sensor = settings.acceleration_sensor()

        voltage_before_test, voltage_at_test, voltage_after_test = (
            self.loop.run_until_complete(
                read_voltages(sensor.self_test.dimension,
                              sensor.reference_voltage)))

        voltage_diff = voltage_at_test - voltage_before_test

        voltage_diff_expected = sensor.self_test.voltage.difference
        voltage_diff_tolerance = sensor.self_test.voltage.tolerance

        voltage_diff_minimum = voltage_diff_expected - voltage_diff_tolerance
        voltage_diff_maximum = voltage_diff_expected + voltage_diff_tolerance

        self.assertLess(
            voltage_before_test, voltage_at_test,
            f"Self test voltage of {voltage_at_test:.0f} mV was lower "
            f"than voltage before test {voltage_before_test:.0f} mV")
        self.assertLess(
            voltage_after_test, voltage_at_test,
            f"Self test voltage of {voltage_at_test:.0f} mV was lower "
            f"than voltage after test {voltage_before_test:.0f} mV")

        possible_failure_reason = (
            "\n\nPossible Reason:\n\n• Acceleration sensor config value "
            f"“{settings.sth.acceleration_sensor.sensor}” is incorrect")

        self.assertGreaterEqual(
            voltage_diff, voltage_diff_minimum,
            f"Measured voltage difference of {voltage_diff:.0f} mV is lower "
            "than expected minimum voltage difference of "
            f"{voltage_diff_minimum:.0f} mV{possible_failure_reason}")
        self.assertLessEqual(
            voltage_diff, voltage_diff_maximum,
            f"Measured voltage difference of {voltage_diff:.0f} mV is "
            "greater than expected minimum voltage difference of "
            f"{voltage_diff_maximum:.0f} mV{possible_failure_reason}")

    def test_eeprom(self):
        """Test if reading and writing the EEPROM works"""

        async def test_eeprom():
            """Test the EERPOM of the STH"""

            cls = type(self)
            receiver = 'STH 1'

            # ========
            # = Name =
            # ========

            name = (str(settings.sth.serial_number) if settings.sth.status
                    == "Epoxied" else convert_mac_base64(cls.bluetooth_mac))

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

            await self._test_eeprom_product_data(Node(receiver), settings.sth)

            # ==============
            # = Statistics =
            # ==============

            await self._test_eeprom_statistics(Node(receiver),
                                               settings.sth.production_date,
                                               settings.sth.batch_number)

            # ================
            # = Acceleration =
            # ================

            sensor = settings.acceleration_sensor()
            acceleration_max = sensor.acceleration.maximum
            adc_max = 0xffff
            acceleration_slope = acceleration_max / adc_max
            await self.can.write_eeprom_x_axis_acceleration_slope(
                acceleration_slope)
            cls.acceleration_slope = (
                await self.can.read_eeprom_x_axis_acceleration_slope())
            self.assertAlmostEqual(
                acceleration_slope,
                cls.acceleration_slope,
                msg=f"Written acceleration slope “{acceleration_slope:.5f}” "
                "does not match read acceleration slope "
                f"“{cls.acceleration_slope:.5f}”")

            acceleration_offset = -(acceleration_max / 2)
            await self.can.write_eeprom_x_axis_acceleration_offset(
                acceleration_offset)
            cls.acceleration_offset = (
                await self.can.read_eeprom_x_axis_acceleration_offset())
            self.assertAlmostEqual(
                acceleration_offset,
                cls.acceleration_offset,
                msg=f"Written acceleration offset “{acceleration_offset:.3f}” "
                "does not match read acceleration offset "
                f"“{cls.acceleration_offset:.3f}”")

            # =================
            # = EEPROM Status =
            # =================

            await self._test_eeprom_status(Node(receiver))

            # =========
            # = Reset =
            # =========

            # We reset the STH and STU to make sure
            # - the name change takes place and we can connect to the STH
            #   using the new name
            # - the STH also takes the other changed EEPROM values (such as
            #   the changed advertisement times) into account.
            await self.can.reset_node('STH 1')
            await self.can.reset_node('STU 1')

            try:
                await self.can.connect_sensor_device(cls.name
                                                     )  # Reconnect to STH
            except TimeoutError:
                self.fail("Unable to reconnect to STH using updated name "
                          f"“{cls.name}”")

        self.loop.run_until_complete(test_eeprom())


def main():
    add_commander_path_to_environment()
    unittest_main(testRunner=ExtendedTestRunner,
                  module="mytoolit.test.production.sth")


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    main()
