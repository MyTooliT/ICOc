# -- Imports ------------------------------------------------------------------

from datetime import datetime
from os import environ, pathsep
from os.path import abspath, dirname, isfile, join
from re import escape, search
from subprocess import run
from sys import path as module_path
from time import sleep
from types import SimpleNamespace
from unittest import (TestCase, TextTestResult, TextTestRunner, main, skip,
                      skipIf)

# Add path for custom libraries
repository_root = dirname(dirname(dirname(dirname(abspath(__file__)))))
module_path.append(repository_root)

from mytoolit import __version__
from mytoolit.can import Identifier, Node
from mytoolit.eeprom import EEPROMStatus
from mytoolit.measurement.acceleration import (convert_acceleration_adc_to_g,
                                               ratio_noise_max)
from mytoolit.report import Report
from mytoolit.config import settings
from mytoolit.test.production import TestNode
from mytoolit.unittest import ExtendedTestRunner
from mytoolit.utility import convert_mac_base64

from network import Network
from MyToolItCommands import (
    ActiveState,
    AdcMax,
    AdcVRefValuemV,
    AdcOverSamplingRate,
    AdcReference,
    CalibMeassurementActionNr,
    CalibMeassurementTypeNr,
    DataSets,
    byte_list_to_int,
    MyToolItBlock,
    MyToolItEeprom,
    MyToolItProductData,
    MyToolItStreaming,
    MyToolItSystem,
    NetworkState,
    NodeState,
    int_to_mac_address,
)
from MyToolItSth import fVoltageBattery
from SthLimits import SthLimits

# -- Classes ------------------------------------------------------------------


class TestSTH(TestNode):
    """This class contains tests for the Sensory Tool Holder (STH)"""

    @classmethod
    def setUpClass(cls):
        """Set up data for whole test"""

        super().setUpClass()

        # The status attribute (`Epoxied` or `Bare PCB`) only applies to the
        # STH
        cls.status = settings.STH.Status

    def _connect(self):
        """Create a connection to the STH"""

        # Connect to STU
        super()._connect(receiver=Node('STH 1').value)

        # Connect to STH
        self.can.bBlueToothConnectPollingName(Node('STU 1').value,
                                              settings.STH.Name,
                                              log=False)
        sleep(2)

    def _disconnect(self):
        """Tear down connection to STH"""

        # Disconnect from STH
        self.can.bBlueToothDisconnect(Node('STU 1').value)

        # Disconnect from STU
        super()._disconnect()

    def _read_data(self):
        """Read data from connected STH"""

        cls = type(self)

        cls.bluetooth_mac = int_to_mac_address(
            self.can.BlueToothAddress(Node('STH 1').value))
        cls.bluetooth_rssi = self.can.BlueToothRssi(Node('STH 1').value)

        index = self.can.cmdSend(
            Node('STH 1').value, MyToolItBlock['ProductData'],
            MyToolItProductData['FirmwareVersion'], [])
        version = self.can.getReadMessageData(index)[-3:]

        cls.firmware_version = '.'.join(map(str, version))

        # This is more or less placeholder code, until we handle the naming
        # process gracefully. Currently the whole test requires that we know
        # the name of the STH in advance.
        cls.name = settings.STH.Name

    @skipIf(settings.STH.Status == "Epoxied",
            f"Flash test skipped because of status “{settings.STH.Status}”")
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

        self._test_connection()

    def test_battery_voltage(self):
        """Test voltage of STH power source"""

        # Read 2 byte voltage format
        index = self.can.singleValueCollect(
            Node('STH 1').value,
            MyToolItStreaming['Voltage'],
            # Read voltage 1
            1,
            # Do not read voltage 2
            0,
            # Do not read voltage 3
            0,
            log=False)

        message = self.can.getReadMessageData(index)
        self.assertEqual(len(message), 8,
                         "Unable to read battery voltage data")
        voltage_index_start = 2
        voltage_index_end = voltage_index_start + 1
        voltage_bytes = message[voltage_index_start:voltage_index_end + 1]
        battery_voltage_raw = byte_list_to_int(voltage_bytes)

        expected_voltage = settings.STH.Battery_Voltage.Average
        tolerance_voltage = settings.STH.Battery_Voltage.Tolerance
        expected_minimum_voltage = expected_voltage - tolerance_voltage
        expected_maximum_voltage = expected_voltage + tolerance_voltage

        battery_voltage = fVoltageBattery(battery_voltage_raw)

        self.assertGreaterEqual(
            battery_voltage, expected_minimum_voltage,
            f"STH power source voltage of {battery_voltage:.3f} V is lower " +
            "than expected minimum voltage of" +
            "{expected_minimum_voltage:.3f} V")
        self.assertLessEqual(
            battery_voltage, expected_maximum_voltage,
            f"STH power source voltage of {battery_voltage:.3f} V is " +
            "greater than expected maximum voltage of " +
            f"{expected_minimum_voltage:.3f} V")

    def test_acceleration_single_value(self):
        """Test stationary acceleration value"""

        # Read acceleration at x-axis
        index = self.can.singleValueCollect(
            Node('STH 1').value, MyToolItStreaming['Acceleration'], 1, 0, 0)
        acceleration_raw, _, _ = self.can.singleValueArray(
            Node('STH 1').value, MyToolItStreaming['Acceleration'], 1, 0, 0,
            index)
        acceleration_value_raw = acceleration_raw[0]
        sensor = settings.acceleration_sensor()
        acceleration = convert_acceleration_adc_to_g(
            acceleration_value_raw, sensor.Acceleration.Maximum)

        # We expect a stationary acceleration of the standard gravity
        # (1 g₀ = 9.807 m/s²)
        expected_acceleration = 1
        tolerance_acceleration = sensor.Acceleration.Tolerance
        expected_minimum_acceleration = (expected_acceleration -
                                         tolerance_acceleration)
        expected_maximum_acceleration = (expected_acceleration +
                                         tolerance_acceleration)

        self.assertGreaterEqual(
            acceleration, expected_minimum_acceleration,
            f"Measured acceleration {acceleration:.3f} g₀ is lower " +
            "than expected minimum acceleration " +
            f"{expected_minimum_acceleration} g₀")
        self.assertLessEqual(
            acceleration, expected_maximum_acceleration,
            f"Measured acceleration {acceleration:.3f} g₀ is greater " +
            "than expected maximum acceleration " +
            f"{expected_maximum_acceleration} g₀")

    def test_acceleration_noise(self):
        """Test ratio of noise to maximal possible measurement value"""

        # Read x-acceleration values in single data sets for 4
        # seconds
        index_start, index_end = self.can.streamingValueCollect(
            Node("STH 1").value, MyToolItStreaming["Acceleration"],
            DataSets[1], 1, 0, 0, 4000)

        acceleration, _, _ = self.can.streamingValueArray(
            Node("STH 1").value, MyToolItStreaming["Acceleration"],
            DataSets[1], 1, 0, 0, index_start, index_end)

        cls = type(self)
        cls.ratio_noise_max = ratio_noise_max(acceleration)

        sensor = settings.acceleration_sensor()
        maximum_ratio_allowed = sensor.Acceleration.Ratio_Noise_To_Max_Value
        self.assertLessEqual(
            cls.ratio_noise_max, maximum_ratio_allowed,
            "The ratio noise to possible maximum measured value of " +
            f"{cls.ratio_noise_max} dB is higher than the maximum allowed " +
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
            Node('STH 1').value, CalibMeassurementActionNr['Inject'],
            CalibMeassurementTypeNr['Acc'], 1, AdcReference['VDD'])
        sleep(0.1)

        # Turn off self test and wait for deactivation
        voltage_at_test = measure_voltage()
        self.can.calibMeasurement(
            Node('STH 1').value, CalibMeassurementActionNr['Eject'],
            CalibMeassurementTypeNr['Acc'], 1, AdcReference['VDD'])
        sleep(0.1)

        voltage_after_test = measure_voltage()

        voltage_diff = voltage_at_test - voltage_before_test

        sensor = settings.acceleration_sensor()
        voltage_diff_expected = sensor.Self_Test.Voltage.Difference
        voltage_diff_tolerance = sensor.Self_Test.Voltage.Tolerance

        voltage_diff_minimum = voltage_diff_expected - voltage_diff_tolerance
        voltage_diff_maximum = voltage_diff_expected + voltage_diff_tolerance

        self.assertLess(
            voltage_before_test, voltage_at_test,
            f"Self test voltage of {voltage_at_test:.0f} mV was lower " +
            f"than voltage before test {voltage_before_test:.0f} mv")
        self.assertLess(
            voltage_after_test, voltage_at_test,
            f"Self test voltage of {voltage_at_test:.0f} mV was lower " +
            f"than voltage after test {voltage_before_test:.0f} mv")

        self.assertGreaterEqual(
            voltage_diff, voltage_diff_minimum,
            f"Measured voltage difference of {voltage_diff:.0f} mV is lower " +
            "than expected minimum voltage difference of " +
            f"{voltage_diff_minimum:.0f} mV")
        self.assertLessEqual(
            voltage_diff, voltage_diff_maximum,
            f"Measured voltage difference of {voltage_diff:.0f} mV is " +
            "greater than expected minimum voltage difference of " +
            f"{voltage_diff_maximum:.0f} mV")

    def test_eeprom(self):
        """Test if reading and writing the EEPROM works"""

        cls = type(self)

        # ========
        # = Name =
        # ========

        mac = [int(byte, 16) for byte in cls.bluetooth_mac.split(":")]
        name = convert_mac_base64(mac)

        self.can.write_eeprom_name(name)
        read_name = self.can.read_eeprom_name()

        self.assertEqual(
            name, read_name,
            f"Written name “{name}” does not match read name “{read_name}”")

        cls.name = read_name

        # We update the name also with the `System` → `Bluetooth` command.
        # This way the STH takes the name change into account. Otherwise the
        # device would still use the old name, although the name in the EEPROM
        # was already updated.
        #
        # Before this approach we already tried to reset
        # the node after we changed all the values. However, this way the name
        # of the device often was not updated properly. For example, even
        # though the name was written and read as “AAtXb+lp” it showed up as
        # “IItYb+lq” after the test.
        self.can.vBlueToothNameWrite(Node("STH1").value, 0, cls.name)

        # =========================
        # = Sleep & Advertisement =
        # =========================

        def read_write_time(read_function, write_function, variable,
                            description, milliseconds):
            write_function(milliseconds)
            milliseconds_read = read_function()
            setattr(type(self), variable, milliseconds_read)
            self.assertEqual(
                milliseconds_read, milliseconds,
                f"{description} {milliseconds_read} ms does not match " +
                f" written value of {milliseconds} ms")

        read_write_time(read_function=self.can.read_eeprom_sleep_time_1,
                        write_function=self.can.write_eeprom_sleep_time_1,
                        variable='sleep_time_1',
                        description="Sleep Time 1",
                        milliseconds=settings.STH.Bluetooth.Sleep_Time_1)

        read_write_time(
            read_function=self.can.read_eeprom_advertisement_time_1,
            write_function=self.can.write_eeprom_advertisement_time_1,
            variable='advertisement_time_1',
            description="Advertisement Time 1",
            milliseconds=settings.STH.Bluetooth.Advertisement_Time_1)

        read_write_time(read_function=self.can.read_eeprom_sleep_time_2,
                        write_function=self.can.write_eeprom_sleep_time_2,
                        variable='sleep_time_2',
                        description="Sleep Time 2",
                        milliseconds=settings.STH.Bluetooth.Sleep_Time_2)

        read_write_time(
            read_function=self.can.read_eeprom_advertisement_time_2,
            write_function=self.can.write_eeprom_advertisement_time_2,
            variable='advertisement_time_2',
            description="Advertisement Time 2",
            milliseconds=settings.STH.Bluetooth.Advertisement_Time_2)

        # ================
        # = Product Data =
        # ================

        super()._test_eeprom_product_data()

        # ==============
        # = Statistics =
        # ==============

        super()._test_eeprom_statistics()

        # ================
        # = Acceleration =
        # ================

        sensor = settings.acceleration_sensor()
        acceleration_max = sensor.Acceleration.Maximum
        adc_max = 0xffff
        acceleration_slope = acceleration_max / adc_max
        self.can.write_eeprom_x_axis_acceleration_slope(acceleration_slope)
        cls.acceleration_slope = (
            self.can.read_eeprom_x_axis_acceleration_slope())
        self.assertAlmostEqual(
            acceleration_slope,
            cls.acceleration_slope,
            msg=f"Written acceleration slope “{acceleration_slope:.5f}” " +
            "does not match read acceleration slope " +
            f"“{cls.acceleration_slope:.5f}”")

        acceleration_offset = -(acceleration_max / 2)
        self.can.write_eeprom_x_axis_acceleration_offset(acceleration_offset)
        cls.acceleration_offset = (
            self.can.read_eeprom_x_axis_acceleration_offset())
        self.assertAlmostEqual(
            acceleration_offset,
            cls.acceleration_offset,
            msg=f"Written acceleration offset “{acceleration_offset:.3f}” " +
            "does not match read acceleration offset " +
            f"“{cls.acceleration_offset:.3f}”")

        # =================
        # = EEPROM Status =
        # =================

        super()._test_eeprom_status()


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    # Add path to Simplicity Commander (`commander`) — We do this to ensure,
    # that we can call the command directly, without adding the path before
    # the tool’s name.
    environ['PATH'] += (pathsep + pathsep.join(settings.Commands.Path.Windows))

    main(testRunner=ExtendedTestRunner)
