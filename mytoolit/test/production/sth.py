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
from mytoolit.config import settings, acceleration_sensor
from mytoolit.test.production import (TestNode, create_attribute,
                                      filter_undefined_attributes)
from mytoolit.unittest import ExtendedTestRunner
from mytoolit.utility import convert_mac_base64

from network import Network
from MyToolItNetworkNumbers import MyToolItNetworkNr
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
    def _collect_node_data(cls):
        """Collect data about STH

        Returns
        -------

        An iterable of defined STH attributes stored in simple name space
        objects
        """

        possible_attributes = [
            create_attribute("EEPROM Status", "{cls.eeprom_status}",
                             pdf=False),
            create_attribute("Name", "{cls.name}"),
            create_attribute("Status", settings.STH.Status),
            create_attribute("Production Date",
                             "{cls.production_date}",
                             pdf=False),
            create_attribute("GTIN", "{cls.gtin}", pdf=False),
            create_attribute("Product Name", "{cls.product_name}", pdf=False),
            create_attribute("Serial Number", "{cls.serial_number}",
                             pdf=False),
            create_attribute("Batch Number", "{cls.batch_number}", pdf=False),
            create_attribute("Bluetooth Address", "{cls.bluetooth_mac}"),
            create_attribute("RSSI", "{cls.bluetooth_rssi} dBm"),
            create_attribute("Hardware Revision", "{cls.hardware_revision}"),
            create_attribute("Firmware Version", "{cls.firmware_version}"),
            create_attribute("Release Name", "{cls.release_name}", pdf=False),
            create_attribute("Ratio Noise Maximum",
                             "{cls.ratio_noise_max:.3f} dB"),
            create_attribute("Sleep Time 1",
                             "{cls.sleep_time_1} ms",
                             pdf=False),
            create_attribute("Advertisement Time 1",
                             "{cls.advertisement_time_1} ms",
                             pdf=False),
            create_attribute("Sleep Time 2",
                             "{cls.sleep_time_2} ms",
                             pdf=False),
            create_attribute("Advertisement Time 2",
                             "{cls.advertisement_time_2} ms",
                             pdf=False),
            create_attribute("OEM Data", "{cls.oem_data}", pdf=False),
            create_attribute("Power On Cycles",
                             "{cls.power_on_cycles}",
                             pdf=False),
            create_attribute("Power Off Cycles",
                             "{cls.power_off_cycles}",
                             pdf=False),
            create_attribute("Under Voltage Counter",
                             "{cls.under_voltage_counter}",
                             pdf=False),
            create_attribute("Watchdog Reset Counter",
                             "{cls.watchdog_reset_counter}",
                             pdf=False),
            create_attribute("Operating Time",
                             "{cls.operating_time} s",
                             pdf=False),
            create_attribute("Acceleration Slope",
                             "{cls.acceleration_slope:.5f}",
                             pdf=False),
            create_attribute("Acceleration Offset",
                             "{cls.acceleration_offset:.3f}",
                             pdf=False),
        ]

        return filter_undefined_attributes(cls, possible_attributes)

    def _connect(self):
        """Create a connection to the STH"""

        # Connect to STU
        super()._connect(receiver=Node('STH 1').value)

        # Connect to STH
        self.can.bBlueToothConnectPollingName(MyToolItNetworkNr['STU1'],
                                              settings.STH.Name,
                                              log=False)
        sleep(2)

    def _disconnect(self):
        """Tear down connection to STH"""

        # Disconnect from STH
        self.can.bBlueToothDisconnect(MyToolItNetworkNr['STU1'])

        # Disconnect from STU
        super()._disconnect()

    def _read_data(self):
        """Read data from connected STH"""

        cls = type(self)

        cls.bluetooth_mac = int_to_mac_address(
            self.can.BlueToothAddress(MyToolItNetworkNr['STH1']))
        cls.bluetooth_rssi = self.can.BlueToothRssi(MyToolItNetworkNr['STH1'])

        index = self.can.cmdSend(MyToolItNetworkNr['STH1'],
                                 MyToolItBlock['ProductData'],
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

        self._test_firmware_flash('STH')

    def test_connection(self):
        """Check connection to STH

        This tests sends a command from the STU (with the identifier of SPU1)
        to the STH and checks if the acknowledgment message from the STH
        contains the same data as the sent message (, except for switched
        sender/receiver and flipped acknowledgment bit).
        """

        self._test_connection('STH')

    def test_battery_voltage(self):
        """Test voltage of STH power source"""

        # Read 2 byte voltage format
        index = self.can.singleValueCollect(
            MyToolItNetworkNr['STH1'],
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
        index = self.can.singleValueCollect(MyToolItNetworkNr['STH1'],
                                            MyToolItStreaming['Acceleration'],
                                            1, 0, 0)
        acceleration_raw, _, _ = self.can.singleValueArray(
            MyToolItNetworkNr['STH1'], MyToolItStreaming['Acceleration'], 1, 0,
            0, index)
        acceleration_value_raw = acceleration_raw[0]
        sensor = acceleration_sensor()
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
            MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"],
            DataSets[1], 1, 0, 0, 4000)

        acceleration, _, _ = self.can.streamingValueArray(
            MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"],
            DataSets[1], 1, 0, 0, index_start, index_end)

        cls = type(self)
        cls.ratio_noise_max = ratio_noise_max(acceleration)

        sensor = acceleration_sensor()
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
                MyToolItNetworkNr['STH1'],
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
        self.can.calibMeasurement(MyToolItNetworkNr['STH1'],
                                  CalibMeassurementActionNr['Inject'],
                                  CalibMeassurementTypeNr['Acc'], 1,
                                  AdcReference['VDD'])
        sleep(0.1)

        # Turn off self test and wait for deactivation
        voltage_at_test = measure_voltage()
        self.can.calibMeasurement(MyToolItNetworkNr['STH1'],
                                  CalibMeassurementActionNr['Eject'],
                                  CalibMeassurementTypeNr['Acc'], 1,
                                  AdcReference['VDD'])
        sleep(0.1)

        voltage_after_test = measure_voltage()

        voltage_diff = voltage_at_test - voltage_before_test

        sensor = acceleration_sensor()
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

        def read_write_time(read_function, write_function, variable,
                            description, milliseconds):
            write_function(milliseconds)
            milliseconds_read = read_function()
            setattr(type(self), variable, milliseconds_read)
            self.assertEqual(
                milliseconds_read, milliseconds,
                f"{description} {milliseconds_read} ms does not match " +
                f" written value of {milliseconds} ms")

        def read_production_date():
            date = self.can.read_eeprom_text(address=5, offset=20, length=8)
            year = date[0:4]
            month = date[4:6]
            day = date[6:8]
            return f"{year}-{month}-{day}"

        def read_power_off_cycles():
            return self.can.read_eeprom_unsigned(address=5, offset=4, length=4)

        def read_operating_time():
            return self.can.read_eeprom_unsigned(address=5, offset=8, length=4)

        def write_operating_time(seconds):
            self.can.write_eeprom_unsigned(address=5,
                                           offset=8,
                                           length=4,
                                           value=seconds)

        def read_under_voltage_counter():
            return self.can.read_eeprom_unsigned(address=5,
                                                 offset=12,
                                                 length=4)

        def write_under_voltage_counter(times):
            self.can.write_eeprom_unsigned(address=5,
                                           offset=12,
                                           length=4,
                                           value=times)

        def read_watchdog_reset_counter():
            return self.can.read_eeprom_unsigned(address=5,
                                                 offset=16,
                                                 length=4)

        def write_watchdog_reset_counter(times):
            self.can.write_eeprom_unsigned(address=5,
                                           offset=16,
                                           length=4,
                                           value=times)

        def write_production_date(date="1970-12-31"):
            date = date.replace("-", "")
            self.can.write_eeprom_text(address=5,
                                       offset=20,
                                       length=8,
                                       text=date)

        def read_batch_number():
            return self.can.read_eeprom_unsigned(address=5,
                                                 offset=28,
                                                 length=4)

        def write_batch_number(value):
            self.can.write_eeprom_unsigned(address=5,
                                           offset=28,
                                           length=4,
                                           value=value)

        def read_acceleration_slope():
            return self.can.read_eeprom_float(address=8, offset=0)

        def write_acceleration_slope(slope):
            self.can.write_eeprom_float(address=8, offset=0, value=slope)

        def read_acceleration_offset():
            return self.can.read_eeprom_float(address=8, offset=4)

        def write_acceleration_offset(offset):
            self.can.write_eeprom_float(address=8, offset=4, value=offset)

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
        self.can.vBlueToothNameWrite(MyToolItNetworkNr["STH1"], 0, cls.name)

        # =========================
        # = Sleep & Advertisement =
        # =========================

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

        # ========
        # = GTIN =
        # ========

        gtin = settings.STH.GTIN
        self.can.write_eeprom_gtin(gtin)
        cls.gtin = self.can.read_eeprom_gtin()
        self.assertEqual(
            gtin, cls.gtin,
            f"Written GTIN “{gtin}” does not match read GTIN “{cls.gtin}”")

        # ============
        # = Hardware =
        # ============

        hardware_revision = settings.STH.Hardware_Revision
        self.can.write_eeprom_hardware_revision(hardware_revision)
        cls.hardware_revision = self.can.read_eeprom_hardware_revision()
        self.assertEqual(
            hardware_revision, f"{cls.hardware_revision}",
            f"Written hardware revision “{hardware_revision}” does not " +
            f"match read hardware revision “{cls.hardware_revision}”")

        # ============
        # = Firmware =
        # ============

        # The STH seems to define two different firmware version numbers. We
        # overwrite the version stored in the EEPROM with the one read, when
        # the test connected to the STH.
        self.can.write_eeprom_firmware_version(cls.firmware_version)
        firmware_version = self.can.read_eeprom_firmware_version()
        self.assertEqual(
            cls.firmware_version, f"{firmware_version}",
            f"Written firmware version “{cls.firmware_version}” does not " +
            f"match read firmware version “{firmware_version}”")

        # ================
        # = Release Name =
        # ================

        # Originally we assumed that this value would be set by the firmware
        # itself. However, according to tests with SHAs with an empty EEPROM
        # this is not the case.
        release_name = settings.STH.Firmware.Release_Name
        self.can.write_eeprom_release_name(release_name)
        cls.release_name = self.can.read_eeprom_release_name()
        self.assertEqual(
            release_name, cls.release_name,
            f"Written firmware release name “{release_name}” does not " +
            f"match read firmware release name “{cls.release_name}”")

        # =================
        # = Serial Number =
        # =================

        serial_number = str(settings.STH.Serial_Number)
        self.can.write_eeprom_serial_number(serial_number)
        cls.serial_number = self.can.read_eeprom_serial_number()
        self.assertEqual(
            serial_number, cls.serial_number,
            f"Written serial number “{serial_number}” does not " +
            f"match read serial number “{cls.serial_number}”")

        # ================
        # = Product Name =
        # ================

        product_name = str(settings.STH.Product_Name)
        self.can.write_eeprom_product_name(product_name)
        cls.product_name = self.can.read_eeprom_product_name()
        self.assertEqual(
            product_name, cls.product_name,
            f"Written product name “{product_name}” does not " +
            f"match read product name “{cls.product_name}”")

        # ============
        # = OEM Data =
        # ============

        oem_data = settings.STH.OEM_Data
        self.can.write_eeprom_oem_data(oem_data)
        cls.oem_data = self.can.read_eeprom_oem_data()
        self.assertListEqual(
            oem_data, cls.oem_data,
            f"Written OEM data “{oem_data}” does not " +
            f"match read OEM data “{cls.oem_data}”")
        # We currently store the data in text format, to improve the
        # readability of null bytes in the shell. Please notice, that this will
        # not always work (depending on the binary data stored in EEPROM
        # region).
        cls.oem_data = ''.join(map(chr, cls.oem_data)).replace('\x00', '')

        # =======================
        # = Power On/Off Cycles =
        # =======================

        power_on_cycles = 0
        self.can.write_eeprom_power_on_cycles(power_on_cycles)
        cls.power_on_cycles = self.can.read_eeprom_power_on_cycles()
        self.assertEqual(
            power_on_cycles, cls.power_on_cycles,
            f"Written power on cycle value “{power_on_cycles}” " +
            "does not match read power on cycle value " +
            f"“{cls.power_on_cycles}”")

        power_off_cycles = 0
        self.can.write_eeprom_power_off_cycles(power_off_cycles)
        cls.power_off_cycles = read_power_off_cycles()
        self.assertEqual(
            power_off_cycles, cls.power_off_cycles,
            f"Written power off cycle value “{power_off_cycles}” " +
            "does not match read power off cycle value " +
            f"“{cls.power_off_cycles}”")

        # ==================
        # = Operating Time =
        # ==================

        operating_time = 0
        write_operating_time(operating_time)
        cls.operating_time = read_operating_time()
        self.assertEqual(
            operating_time, cls.operating_time,
            f"Written operating time “{operating_time}” " +
            "does not match read operating time “{cls.operating_time}”")

        # =========================
        # = Under Voltage Counter =
        # =========================

        under_voltage_counter = 0
        write_under_voltage_counter(under_voltage_counter)
        cls.under_voltage_counter = read_under_voltage_counter()
        self.assertEqual(
            under_voltage_counter, cls.under_voltage_counter,
            f"Written under voltage counter value “{under_voltage_counter}” " +
            "does not match read under voltage counter value " +
            f"“{cls.under_voltage_counter}”")

        # ==========================
        # = Watchdog Reset Counter =
        # ==========================

        watchdog_reset_counter = 0
        write_watchdog_reset_counter(watchdog_reset_counter)
        cls.watchdog_reset_counter = read_watchdog_reset_counter()
        self.assertEqual(
            watchdog_reset_counter, cls.watchdog_reset_counter,
            f"Written watchdog reset counter value " +
            f"“{watchdog_reset_counter} does not match read watchdog reset " +
            f"counter value “{cls.watchdog_reset_counter}”")

        # ===================
        # = Production Date =
        # ===================

        production_date = str(settings.STH.Production_Date)
        write_production_date(production_date)
        cls.production_date = read_production_date()
        self.assertEqual(
            production_date, cls.production_date,
            f"Written production date “{production_date}” does not match " +
            f"read production date “{cls.production_date}”")

        # ================
        # = Batch Number =
        # ================

        batch_number = settings.STH.Batch_Number
        write_batch_number(batch_number)
        cls.batch_number = read_batch_number()
        self.assertEqual(
            batch_number, cls.batch_number,
            f"Written batch “{batch_number}” does not match " +
            f"read batch number “{cls.batch_number}”")

        # ================
        # = Acceleration =
        # ================

        sensor = acceleration_sensor()
        acceleration_max = sensor.Acceleration.Maximum
        adc_max = 0xffff
        acceleration_slope = acceleration_max / adc_max
        write_acceleration_slope(acceleration_slope)
        cls.acceleration_slope = read_acceleration_slope()
        self.assertAlmostEqual(
            acceleration_slope,
            cls.acceleration_slope,
            msg=f"Written acceleration slope “{acceleration_slope:.5f}” " +
            "does not match read acceleration slope " +
            f"“{cls.acceleration_slope:.5f}”")

        acceleration_offset = -(acceleration_max / 2)
        write_acceleration_offset(acceleration_offset)
        cls.acceleration_offset = read_acceleration_offset()
        self.assertAlmostEqual(
            acceleration_offset,
            cls.acceleration_offset,
            msg=f"Written acceleration offset “{acceleration_offset:.3f}” " +
            "does not match read acceleration offset " +
            f"“{cls.acceleration_offset:.3f}”")

        # =================
        # = EEPROM Status =
        # =================

        self.can.write_eeprom_status('Initialized')
        cls.eeprom_status = self.can.read_eeprom_status()
        self.assertTrue(
            cls.eeprom_status.is_initialized(),
            f"Setting EEPROM status to “Initialized” failed. "
            "EEPROM status byte currently stores the value "
            f"“{cls.eeprom_status}”")


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    # Add path to Simplicity Commander (`commander`) — We do this to ensure,
    # that we can call the command directly, without adding the path before
    # the tool’s name.
    environ['PATH'] += (pathsep + pathsep.join(settings.Commands.Path.Windows))

    main(testRunner=ExtendedTestRunner)
