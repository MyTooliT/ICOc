# -- Imports ------------------------------------------------------------------

from enum import Enum
from os import environ, pathsep
from os.path import abspath, dirname, isfile, join
from re import escape
from subprocess import run
from sys import path as module_path
from time import sleep
from types import SimpleNamespace
from unittest import TestCase, TextTestResult, TextTestRunner, main

# Add path for custom libraries
repository_root = dirname(dirname(dirname(dirname(abspath(__file__)))))
module_path.append(repository_root)

from mytoolit.can.identifier import Identifier
from mytoolit.measurement.acceleration import (convert_acceleration_adc_to_g,
                                               ratio_noise_max)
from mytoolit.report.report import Report
from mytoolit.config import settings

from CanFd import CanFd
from MyToolItNetworkNumbers import MyToolItNetworkNr
from MyToolItCommands import (
    ActiveState,
    AdcMax,
    AdcReference,
    CalibMeassurementActionNr,
    CalibMeassurementTypeNr,
    DataSets,
    iMessage2Value,
    MyToolItBlock,
    MyToolItEeprom,
    MyToolItProductData,
    MyToolItStreaming,
    MyToolItSystem,
    NetworkState,
    Node,
    sBlueToothMacAddr,
)
from MyToolItSth import fVoltageBattery
from SthLimits import SthLimits

# -- Classes ------------------------------------------------------------------


class ExtendedTestRunner(TextTestRunner):
    """Extend default test runner to change result class"""

    def __init__(self, *arguments, **keyword_arguments):
        """Initialize the test runner"""

        keyword_arguments['resultclass'] = ExtendedTestResult
        super().__init__(*arguments, **keyword_arguments)


class ExtendedTestResult(TextTestResult):
    """Store data about the result of a test"""

    class TestInformation(object):
        """Store additional data of a test result

        We use this class to store test information in a PDF report.
        """

        class Status(Enum):
            """Store the status of a test"""
            success = 0
            failure = 1
            error = 2

        def __init__(self):
            """Initialize a new test info object"""

            self.status = type(self).Status.success
            self.message = ""

        def set_error(self, message):
            """Set the status of the test to error

            Parameters
            ----------

            message:
                Specifies the error message
            """

            self.status = type(self).Status.error
            self.message = message

        def set_failure(self, message):
            """Set the status of the test to failure

            Parameters
            ----------

            message:
                Specifies the failure message
            """

            self.status = type(self).Status.failure
            self.message = message

        def set_success(self):
            """Set the status of the test to success"""

            self.status = type(self).Status.success
            self.message = ""

        def error(self):
            """Check if there was an error

            Returns
            -------

            True if there was an error, False otherwise
            """

            return self.status == type(self).Status.error

        def failure(self):
            """Check if there test failed

            Returns
            -------

            True if the test failed, False otherwise
            """

            return self.status == type(self).Status.failure

    def __init__(self, *arguments, **keyword_arguments):
        """Initialize the test result"""

        super().__init__(*arguments, **keyword_arguments)

        self.last_test = ExtendedTestResult.TestInformation()

    def addFailure(self, test, error):
        """Add information about the latest failure

        Arguments
        ---------

        test:
            The test case that produced the failure

        error:
            A tuple of the form returned by `sys.exc_info()`:
            (type, value, traceback)
        """

        super().addFailure(test, error)

        # Store message for latest failure
        failure_message = str(error[1])
        # Only store custom message added to assertion, since it should be more
        # readable for a person. If there was no custom message, then the
        # object stores the auto-generated message.
        custom_failure_message = failure_message.split(" : ")[-1]

        self.last_test.set_failure(custom_failure_message)

    def addError(self, test, error):
        """Add information about the latest error

        This should usually not happen unless there are problems with the
        connection or the syntax of the current code base.

        Arguments
        ---------

        test:
            The test case that produced the error

        error:
            A tuple of the form returned by `sys.exc_info()`:
            (type, value, traceback)
        """

        super().addError(test, error)

        self.last_test.set_error(error[1])

    def addSuccess(self, test):
        """Add information about latest successful test

        Arguments
        ---------

        test:
            The successful test
        """

        super().addSuccess(test)

        self.last_test.set_success()


class TestSTH(TestCase):
    """This class contains tests for the Sensory Tool Holder (STH)"""

    @classmethod
    def setUpClass(cls):
        """Set up data for whole test"""

        # Initialize report
        cls.report = Report()

        # We store attributes related to the connection, such as MAC address
        # and RSSI only once. To do that we set `read_attributes` to true after
        # the test class gathered the relevant data.
        cls.read_attributes = False

    @classmethod
    def tearDownClass(cls):
        """Print attributes of tested STH after all successful test cases"""

        # Check available read hardware attributes
        possible_attributes = [
            SimpleNamespace(name='name',
                            description="Name",
                            value="{cls.name}"),
            SimpleNamespace(name='bluetooth_mac',
                            description="Bluetooth Address",
                            value="{cls.bluetooth_mac}"),
            SimpleNamespace(name='bluetooth_rssi',
                            description="RSSI",
                            value="{cls.bluetooth_rssi} dBm"),
            SimpleNamespace(name='firmware_version',
                            description="Firmware Version",
                            value="{cls.firmware_version}"),
            SimpleNamespace(name='ratio_noise_max',
                            description="Ration Noise Maximum",
                            value="{cls.ratio_noise_max:.3f} dB")
        ]

        attributes = [
            attribute for attribute in possible_attributes
            if hasattr(cls, attribute.name)
        ]

        # Only print something, if at least one attribute was read
        if attributes:
            print("\n\nTest Data")
            print("—————————")

            for attribute in attributes:
                description = attribute.description
                value = attribute.value.format(cls=cls)
                print(f"{description}: {value}")
                cls.report.add_attribute(description, value)

            print()

        cls.report.build()

    def setUp(self):
        """Set up hardware before a single test case"""

        # We do not need a CAN connection for the firmware flash test
        if self._testMethodName == 'test__firmware_flash':
            return

        self.__connect()

    def tearDown(self):
        """Clean up after single test case"""

        # The firmware flash test does not require cleanup
        if self._testMethodName == 'test__firmware_flash':
            return

        self.__disconnect()

    def run(self, result=None):
        """Execute a single test

        We override this method to store data about the test outcome.
        """

        super().run(result)
        type(self).report.add_test_result(self.shortDescription(), result)

    def __connect(self):
        """Create a connection to the STH"""

        # Initialize CAN bus
        log_filepath = f"{self._testMethodName}.txt"
        log_filepath_error = f"{self._testMethodName}_Error.txt"

        sth_limits = SthLimits(
            # number of axes
            1,
            # maximum acceleration
            200,
            # minimum temperature
            20,
            # maximum temperature
            35)
        self.can = CanFd(log_filepath,
                         log_filepath_error,
                         MyToolItNetworkNr['SPU1'],
                         MyToolItNetworkNr['STH1'],
                         sth_limits.uSamplingRatePrescalerReset,
                         sth_limits.uSamplingRateAcqTimeReset,
                         sth_limits.uSamplingRateOverSamplesReset,
                         FreshLog=True)

        # Reset STU (and STH)
        self.can.bConnected = False
        return_message = self.can.cmdReset(MyToolItNetworkNr['STU1'])
        self.can.CanTimeStampStart(return_message['CanTime'])

        # Connect to STH
        self.can.bBlueToothConnectPollingName(MyToolItNetworkNr['STU1'],
                                              settings.STH.Name,
                                              log=False)
        sleep(2)
        if not type(self).read_attributes:
            self.__read_data()
            type(self).read_attributes = True

    def __disconnect(self):
        """Tear down connection to STH"""

        self.can.bBlueToothDisconnect(MyToolItNetworkNr['STU1'])
        self.can.__exit__()

    def __read_data(self):
        """Read data from connected STH"""

        cls = type(self)

        cls.bluetooth_mac = sBlueToothMacAddr(
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

    def test__firmware_flash(self):
        """Upload bootloader and application into STH

        Please note the additional underscore in the method name that makes
        sure this test case is executed before all other test cases.
        """

        # Add path to Simplicity Commander
        environ['PATH'] += (pathsep +
                            pathsep.join(settings.Commands.Path.Windows))

        identification_arguments = (
            f"--serialno {settings.STH.Programming_Board.Serial_Number} " +
            f"-d BGM113A256V2")

        # Unlock debug access
        unlock_command = (
            f"commander device unlock {identification_arguments}")
        status = run(unlock_command, capture_output=True, text=True)
        self.assertEqual(
            status.returncode, 0,
            f"Unlock command returned non-zero exit code {status.returncode}")
        self.assertRegex(status.stdout, "Chip successfully unlocked",
                         "Unable to unlock debug access of chip")

        # Upload bootloader and application data
        image_filepath = join(repository_root, settings.STH.Firmware.Location)
        self.assertTrue(isfile(image_filepath),
                        f"Firmware file {image_filepath} does not exist")

        flash_command = (f"commander flash {image_filepath} " +
                         f"--address 0x0 {identification_arguments}")
        status = run(flash_command, capture_output=True, text=True)
        self.assertEqual(
            status.returncode, 0,
            "Flash program command returned non-zero exit code " +
            f"{status.returncode}")
        expected_output = "range 0x0FE04000 - 0x0FE047FF (2 KB)"
        self.assertRegex(
            status.stdout, escape(expected_output),
            f"Flash output did not contain expected output “{expected_output}”"
        )
        expected_output = "DONE"
        self.assertRegex(
            status.stdout, expected_output,
            f"Flash output did not contain expected output “{expected_output}”"
        )

    def test_connection(self):
        """Check connection to STH

        This tests sends a command from the STU (with the identifier of SPU1)
        to the STH and checks if the acknowledgment message from the STH
        contains the same data as the sent message (, except for switched
        sender/receiver and flipped acknowledgment bit).
        """

        # Send message to STH
        command = self.can.CanCmd(MyToolItBlock['System'],
                                  MyToolItSystem['ActiveState'],
                                  request=True)
        expected_data = ActiveState()
        expected_data.asbyte = 0
        expected_data.b.u2NodeState = Node['Application']
        expected_data.b.u3NetworkState = NetworkState['Operating']
        message = self.can.CanMessage20(command, MyToolItNetworkNr['SPU1'],
                                        MyToolItNetworkNr['STH1'],
                                        [expected_data.asbyte])
        self.can.Logger.Info('Write message')
        self.can.WriteFrame(message)
        self.can.Logger.Info('Wait 200ms')
        sleep(0.2)

        # Receive message from STH
        received_message = self.can.getReadMessage(-1)

        # Check for equivalence of message content
        command = self.can.CanCmd(MyToolItBlock['System'],
                                  MyToolItSystem['ActiveState'],
                                  request=False)
        expected_id = (self.can.CanMessage20(command,
                                             MyToolItNetworkNr['STH1'],
                                             MyToolItNetworkNr['SPU1'],
                                             [0])).ID
        received_id = received_message.ID

        self.assertEqual(
            expected_id, received_id,
            f"Expected CAN identifier {Identifier(expected_id)} does not " +
            f"match received CAN identifier {Identifier(received_id)}")

        expected_data_byte = expected_data.asbyte
        received_data_byte = received_message.DATA[0]
        self.assertEqual(
            expected_data_byte, received_data_byte,
            f"Expected data “{expected_data_byte}” does not match " +
            f"received data “{received_data_byte}”")

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
        battery_voltage_raw = iMessage2Value(voltage_bytes)

        expected_voltage = settings.STH.Battery_Voltage.Average
        tolerance_voltage = settings.STH.Battery_Voltage.Tolerance
        expected_minimum_voltage = expected_voltage - tolerance_voltage
        expected_maximum_voltage = expected_voltage + tolerance_voltage

        battery_voltage = fVoltageBattery(battery_voltage_raw)

        self.assertGreaterEqual(
            battery_voltage, expected_minimum_voltage,
            f"STH power source voltage of {battery_voltage:.3f} V is lower " +
            f"than expected minimum voltage of {expected_minimum_voltage} V")
        self.assertLessEqual(
            battery_voltage, expected_maximum_voltage,
            f"STH power source voltage of {battery_voltage:.3f} V is " +
            "greater than expected maximum voltage of " +
            f"{expected_minimum_voltage} V")

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
        acceleration = convert_acceleration_adc_to_g(acceleration_value_raw)

        # We expect a stationary acceleration of the standard gravity
        # (1 g₀ = 9.807 m/s²)
        expected_acceleration = 1
        tolerance_acceleration = (
            settings.STH.Acceleration_Sensor.Acceleration.Tolerance)
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

        maximum_ratio_allowed = (settings.STH.Acceleration_Sensor.Acceleration.
                                 Ratio_Noise_To_Max_Value)
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
            adc_value = iMessage2Value(response[index_result:])
            return 100 * AdcReference['VDD'] * adc_value / AdcMax

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

        voltage_diff_expected = (
            settings.STH.Acceleration_Sensor.Self_Test.Voltage.Difference)
        voltage_diff_tolerance = (
            settings.STH.Acceleration_Sensor.Self_Test.Voltage.Tolerance)

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

        def read_eeprom(address, offset, length):
            """Read EEPROM data at a specific address"""

            read_data = []
            reserved = [0] * 5
            data_start = 4  # Start index of data in response message

            while length > 0:
                # Write at most 4 bytes of data at once
                read_length = 4 if length > 4 else length
                payload = [address, offset, read_length, *reserved]
                index = self.can.cmdSend(MyToolItNetworkNr['STH1'],
                                         MyToolItBlock['Eeprom'],
                                         MyToolItEeprom['Read'],
                                         payload,
                                         log=False)
                response = self.can.getReadMessageData(index)
                data_end = data_start + read_length
                read_data.extend(response[data_start:data_end])
                length -= read_length
                offset += read_length

            return read_data

        def read_eeprom_text(address, offset, length):
            """Read EEPROM data in UTT8 format"""

            data = read_eeprom(address, offset, length)
            return "".join(map(chr, data))

        def write_eeprom(address, offset, data, length=None):
            """Write EEPROM data at the specified address"""

            # Change data, if
            # - only a subset, or
            # - additional data
            # should be written to the EEPROM.
            if length:
                # Cut off additional data bytes
                data = data[:length]
                # Fill up additional data bytes
                data.extend([0] * (length - len(data)))

            while data:
                write_data = data[:4]  # Maximum of 4 bytes per message
                write_length = len(write_data)
                # Use zeroes to fill up missing data bytes
                write_data.extend([0] * (4 - write_length))

                reserved = [0] * 1
                payload = [
                    address, offset, write_length, *reserved, *write_data
                ]
                self.can.cmdSend(MyToolItNetworkNr['STH1'],
                                 MyToolItBlock['Eeprom'],
                                 MyToolItEeprom['Write'],
                                 payload,
                                 log=False)
                data = data[4:]
                offset += write_length

        def write_eeprom_text(address, offset, text, length=None):
            """Write a string at the specified EEPROM address"""

            data = list(map(ord, list(text)))
            write_eeprom(address, offset, data, length)

        def read_name():
            return read_eeprom_text(address=0, offset=1, length=8)

        def write_name(text):
            write_eeprom_text(address=0, offset=1, text=text, length=8)

        cls = type(self)
        name = cls.bluetooth_mac[-8:]  # Use last part of MAC as identifier
        write_name(name)
        read_name = read_name()

        self.assertEqual(
            name, read_name,
            f"Written name “{name}” does not match read name “{read_name}”")


if __name__ == "__main__":
    main(testRunner=ExtendedTestRunner)
