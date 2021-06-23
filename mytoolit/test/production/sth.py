# -- Imports ------------------------------------------------------------------

from asyncio import TimeoutError
from os import environ, pathsep
from time import sleep
from unittest import main as unittest_main, skipIf

from mytoolit.can import Node
from mytoolit.measurement import ratio_noise_max
from mytoolit.config import settings
from mytoolit.test.production import TestNode
from mytoolit.test.unit import ExtendedTestRunner
from mytoolit.utility import convert_mac_base64

from mytoolit.old.MyToolItCommands import (
    AdcMax,
    AdcVRefValuemV,
    AdcReference,
    CalibMeassurementActionNr,
    CalibMeassurementTypeNr,
    DataSets,
    byte_list_to_int,
    MyToolItBlock,
    MyToolItProductData,
    MyToolItStreaming,
    int_to_mac_address,
)

# -- Classes ------------------------------------------------------------------


class TestSTH(TestNode):
    """This class contains tests for the Sensory Tool Holder (STH)"""

    @classmethod
    def setUpClass(cls):
        """Set up data for whole test"""

        super().setUpClass()

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

        # Connect to STU
        super()._connect()
        # Connect to STH
        new_network = hasattr(self.can, 'bus')
        self.loop.run_until_complete(self.can.connect_sth(
            settings.sth_name())) if new_network else (
                self.can.bBlueToothConnectPollingName(
                    Node('STU 1').value, settings.sth_name(), log=False))

    def _disconnect(self):
        """Tear down connection to STH"""

        # Disconnect from STU
        super()._disconnect()

    def _read_data(self):
        """Read data from connected STH"""

        def read_data_old():
            """Read data using the old network class"""

            cls.bluetooth_mac = int_to_mac_address(
                self.can.BlueToothAddress(Node('STH 1').value))
            cls.bluetooth_rssi = self.can.BlueToothRssi(Node('STH 1').value)

            index = self.can.cmdSend(
                Node('STH 1').value, MyToolItBlock['Product Data'],
                MyToolItProductData['Firmware Version'], [])
            version = self.can.getReadMessageData(index)[-3:]

            cls.firmware_version = '.'.join(map(str, version))

        async def read_data_new():
            """Read data using the old network class"""

            node = 'STH 1'
            cls.bluetooth_mac = await self.can.get_mac_address(node)
            cls.bluetooth_rssi = await self.can.get_rssi(node)
            cls.firmware_version = await self.can.get_firmware_version(node)

        cls = type(self)
        # This is more or less placeholder code, until we handle the naming
        # process gracefully. Currently the whole test requires that we know
        # the name of the STH in advance.
        cls.name = settings.sth_name()

        new_network = hasattr(self.can, 'bus')
        self.loop.run_until_complete(
            read_data_new()) if new_network else read_data_old()

    @skipIf(settings.sth.status == "Epoxied",
            f"Flash test skipped because of status “{settings.sth.status}”")
    def test__firmware_flash(self):
        """Upload bootloader and application into STH

        Please note the additional underscore in the method name that makes
        sure this test case is executed before all other test cases.
        """

        self._test_firmware_flash()

    def test_connection(self):
        """Check connection to STH

        This tests sends a command from the STU (with the identifier of SPU1)
        to the STH and checks if the acknowledgment message from the STH
        contains the same data as the sent message (, except for switched
        sender/receiver and flipped acknowledgment bit).
        """

        self.loop.run_until_complete(self._test_connection())

    def test_battery_voltage(self):
        """Test voltage of STH power source"""

        async def test_supply_voltage():
            """Check the supply voltage of the STH"""

            supply_voltage = await self.can.read_voltage()

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

        # Read x-acceleration values in single data sets for 4 seconds
        streaming_arguments = (Node("STH 1").value,
                               MyToolItStreaming["Acceleration"], DataSets[1],
                               1, 0, 0)
        index_start, index_end = self.can.streamingValueCollect(
            *streaming_arguments, 4000)
        acceleration, _, _ = self.can.streamingValueArray(
            *streaming_arguments, index_start, index_end)

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

        def measure_voltage():
            """Measure the accelerometer voltage in mV"""
            response = self.can.calibMeasurement(
                Node('STH 1').value,
                CalibMeassurementActionNr['Measure'],
                CalibMeassurementTypeNr['Acc'],
                # Measure x-dimension
                1,
                AdcReference['VDD'])
            index_result = 4
            adc_value = byte_list_to_int(response[index_result:])
            return AdcVRefValuemV[AdcReference["VDD"]] * adc_value / AdcMax

        voltage_before_test = measure_voltage()

        # Turn on self test and wait for activation
        self.can.calibMeasurement(
            Node('STH 1').value, CalibMeassurementActionNr['Activate'],
            CalibMeassurementTypeNr['Acc'], 1, AdcReference['VDD'])
        sleep(0.1)

        # Turn off self test and wait for deactivation
        voltage_at_test = measure_voltage()
        self.can.calibMeasurement(
            Node('STH 1').value, CalibMeassurementActionNr['Deactivate'],
            CalibMeassurementTypeNr['Acc'], 1, AdcReference['VDD'])
        sleep(0.1)

        voltage_after_test = measure_voltage()

        voltage_diff = voltage_at_test - voltage_before_test

        sensor = settings.acceleration_sensor()
        voltage_diff_expected = sensor.self_test.voltage.difference
        voltage_diff_tolerance = sensor.self_test.voltage.tolerance

        voltage_diff_minimum = voltage_diff_expected - voltage_diff_tolerance
        voltage_diff_maximum = voltage_diff_expected + voltage_diff_tolerance

        self.assertLess(
            voltage_before_test, voltage_at_test,
            f"Self test voltage of {voltage_at_test:.0f} mV was lower "
            f"than voltage before test {voltage_before_test:.0f} mv")
        self.assertLess(
            voltage_after_test, voltage_at_test,
            f"Self test voltage of {voltage_at_test:.0f} mV was lower "
            f"than voltage after test {voltage_before_test:.0f} mv")

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

            name = (settings.sth.serial_number if settings.sth.status
                    == "Epoxied" else convert_mac_base64(cls.bluetooth_mac))

            await self.can.write_eeprom_name(name, receiver)
            read_name = await self.can.read_eeprom_name(receiver)

            self.assertEqual(
                name, read_name,
                f"Written name “{name}” does not match read name “{read_name}”"
            )

            cls.name = read_name

            # We reset the STH and STU to make sure the name change takes place
            # and we can connect to the STH using the new name
            await self.can.reset_node('STH 1')
            await self.can.reset_node('STU 1')

            try:
                await self.can.connect_sth(cls.name)  # Reconnect to STH
            except TimeoutError:
                self.fail("Unable to reconnect to STH using updated name "
                          f"“{cls.name}”")

            # =========================
            # = Sleep & Advertisement =
            # =========================
            async def read_write_time(read_function, write_function, variable,
                                      description, milliseconds):
                await write_function(milliseconds)
                milliseconds_read = await read_function()
                setattr(type(self), variable, milliseconds_read)
                self.assertEqual(
                    milliseconds_read, milliseconds,
                    f"{description} {milliseconds_read} ms does not match "
                    f" written value of {milliseconds} ms")

            await read_write_time(
                read_function=self.can.read_eeprom_sleep_time_1,
                write_function=self.can.write_eeprom_sleep_time_1,
                variable='sleep_time_1',
                description="Sleep Time 1",
                milliseconds=settings.sth.bluetooth.sleep_time_1)

            await read_write_time(
                read_function=self.can.read_eeprom_advertisement_time_1,
                write_function=self.can.write_eeprom_advertisement_time_1,
                variable='advertisement_time_1',
                description="Advertisement Time 1",
                milliseconds=settings.sth.bluetooth.advertisement_time_1)

            await read_write_time(
                read_function=self.can.read_eeprom_sleep_time_2,
                write_function=self.can.write_eeprom_sleep_time_2,
                variable='sleep_time_2',
                description="Sleep Time 2",
                milliseconds=settings.sth.bluetooth.sleep_time_2)

            await read_write_time(
                read_function=self.can.read_eeprom_advertisement_time_2,
                write_function=self.can.write_eeprom_advertisement_time_2,
                variable='advertisement_time_2',
                description="Advertisement Time 2",
                milliseconds=settings.sth.bluetooth.advertisement_time_2)

            # ================
            # = Product Data =
            # ================

            super_class = super(TestSTH, self)

            await super_class._test_eeprom_product_data()

            # ==============
            # = Statistics =
            # ==============

            await super_class._test_eeprom_statistics()

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

            await super_class._test_eeprom_status()

        self.loop.run_until_complete(test_eeprom())


def main():
    # Add path to Simplicity Commander (`commander`) — We do this to ensure,
    # that we can call the command directly, without adding the path before
    # the tool’s name.
    environ['PATH'] += (pathsep + pathsep.join(settings.commands.path.windows))

    unittest_main(testRunner=ExtendedTestRunner,
                  module="mytoolit.test.production.sth")


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    main()
