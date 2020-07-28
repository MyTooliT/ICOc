# -- Imports ------------------------------------------------------------------

from datetime import datetime
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

from mytoolit import __version__
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

# -- Functions ----------------------------------------------------------------


def create_attribute(description, value, pdf=True):
    """Create a simple object that stores test attributes


    Parameters
    ----------

    description:
        The description (name) of the attribute

    value:
        The value of the attribute

    pdf:
        True if the attribute should be added to the PDF report


    Returns
    -------

    A simple namespace object that stores the specified data
    """

    return SimpleNamespace(description=description, value=str(value), pdf=pdf)


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

        cls.__output_general_data()
        cls.__output_sth_data()
        cls.report.build()

    @classmethod
    def __output_general_data(cls):
        """Print general information and add it to PDF report"""

        now = datetime.now()
        date = now.strftime('%Y-%m-%d')
        time = now.strftime("%H:%M:%S")

        operator = settings.Operator.Name

        attributes = [
            create_attribute("ICOc Version", __version__),
            create_attribute("Date", date),
            create_attribute("Time", time),
            create_attribute("Operator", operator),
        ]

        cls.__output_data(attributes, sth_data=False)

    @classmethod
    def __output_sth_data(cls):
        """Print STH information and add it to PDF report"""

        attributes = cls.__collect_sth_data()
        cls.__output_data(attributes)

    @classmethod
    def __collect_sth_data(cls):
        """Collect data about STH


        Returns
        -------

        An iterable of defined STH attributes stored in simple name space
        objects
        """

        possible_attributes = [
            create_attribute("EEPROM Init", "{cls.init}", pdf=False),
            create_attribute("Name", "{cls.name}"),
            create_attribute("Status", settings.STH.Status),
            create_attribute("Production Date",
                             "{cls.production_date}",
                             pdf=False),
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
        ]

        # Check available read hardware attributes
        attributes = []
        for attribute in possible_attributes:
            try:
                attribute.value = str(attribute.value).format(cls=cls)
                attributes.append(attribute)
            except AttributeError:
                pass

        return attributes

    @classmethod
    def __output_data(cls, attributes, sth_data=True):
        """Output data to standard output and PDF report

        Parameters
        ----------

        attributes:
            An iterable that stores simple name space objects created via
            ``create_attribute``

        sth_data:
            Specifies if this method outputs STH or general data
        """

        # Only output something, if there is at least one attribute
        if not attributes:
            return

        max_length_description = max(
            [len(attribute.description) for attribute in attributes])
        max_length_value = max(
            [len(attribute.value) for attribute in attributes])

        # Print attributes to standard output
        print("\n")
        header = "Attributes" if sth_data else "General"
        print(header)
        print("—" * len(header))

        for attribute in attributes:
            print(f"{attribute.description:{max_length_description}} " +
                  f"{attribute.value:>{max_length_value}}")

        # Add attributes to PDF
        attributes_pdf = [
            attribute for attribute in attributes if attribute.pdf
        ]
        for attribute in attributes_pdf:
            cls.report.add_attribute(attribute.description, attribute.value,
                                     sth_data)

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
            data_without_null = []
            for byte in data:
                if byte == 0:
                    break
                data_without_null.append(byte)

            return "".join(map(chr, data_without_null))

        def read_eeprom_unsigned(address, offset, length):
            """Read EEPROM data in unsigned format"""

            return iMessage2Value(read_eeprom(address, offset, length))

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

        def write_eeprom_unsigned(address, offset, value, length):
            """Write an unsigned integer at the specified EEPROM address"""

            data = list(value.to_bytes(length, byteorder='little'))
            write_eeprom(address, offset, data)

        def read_init():
            return read_eeprom(address=0, offset=0, length=1).pop()

        def read_name():
            return read_eeprom_text(address=0, offset=1, length=8)

        def write_name(text):
            write_eeprom_text(address=0, offset=1, text=text, length=8)

        def read_write_time(read_function, write_function, name, description,
                            miliseconds):
            write_function(miliseconds)
            miliseconds_read = read_function()
            cls = type(self)
            setattr(cls, name, miliseconds_read)
            self.assertEqual(
                miliseconds_read, miliseconds,
                f"{description} {miliseconds_read} ms does not match " +
                f" written value of {miliseconds} ms")

        def read_sleep_time_1():
            return read_eeprom_unsigned(address=0, offset=9, length=4)

        def write_sleep_time_1(miliseconds):
            write_eeprom_unsigned(address=0,
                                  offset=9,
                                  value=miliseconds,
                                  length=4)

        def read_advertisement_time_1():
            return read_eeprom_unsigned(address=0, offset=13, length=2)

        def write_advertisement_time_1(miliseconds):
            write_eeprom_unsigned(address=0,
                                  offset=13,
                                  value=miliseconds,
                                  length=2)

        def read_sleep_time_2():
            return read_eeprom_unsigned(address=0, offset=15, length=4)

        def write_sleep_time_2(miliseconds):
            write_eeprom_unsigned(address=0,
                                  offset=15,
                                  value=miliseconds,
                                  length=4)

        def read_advertisement_time_2():
            return read_eeprom_unsigned(address=0, offset=19, length=2)

        def write_advertisement_time_2(miliseconds):
            write_eeprom_unsigned(address=0,
                                  offset=19,
                                  value=miliseconds,
                                  length=2)

        def read_hardware_revision():
            major, minor, build = read_eeprom(address=4, offset=13, length=3)
            return f"{major}.{minor}.{build}"

        def write_hardware_revision(major, minor, build):
            write_eeprom(address=4,
                         offset=13,
                         length=3,
                         data=[major, minor, build])

        def read_firmware_version():
            major, minor, build = read_eeprom(address=4, offset=21, length=3)
            return f"{major}.{minor}.{build}"

        def write_firmware_version(major, minor, build):
            write_eeprom(address=4,
                         offset=21,
                         length=3,
                         data=[major, minor, build])

        def read_release_name():
            return read_eeprom_text(address=4, offset=24, length=8)

        def read_serial_number():
            serial_number = read_eeprom_text(address=4, offset=32, length=32)
            return serial_number

        def read_product_name():
            return read_eeprom_text(address=4, offset=64, length=128)

        def read_production_date():
            return read_eeprom_text(address=5, offset=20, length=8)

        def write_production_date(date="19701231"):
            write_eeprom_text(address=5, offset=20, length=8, text=date)

        def read_batch_number():
            return read_eeprom_unsigned(address=5, offset=28, length=4)

        cls = type(self)

        # ========
        # = Init =
        # ========

        init = read_init()
        initialized = 0xac
        locked = 0xca
        cls.init = "Initialized" if init == initialized else (
            "Locked" if init == locked else f"Undefined ({hex(init)})")

        # ========
        # = Name =
        # ========

        name = cls.bluetooth_mac[-8:]  # Use last part of MAC as identifier
        write_name(name)
        read_name = read_name()

        self.assertEqual(
            name, read_name,
            f"Written name “{name}” does not match read name “{read_name}”")

        # =========================
        # = Sleep & Advertisement =
        # =========================

        read_write_time(read_function=read_sleep_time_1,
                        write_function=write_sleep_time_1,
                        name='sleep_time_1',
                        description="Sleep Time 1",
                        miliseconds=settings.STH.Bluetooth.Sleep_Time_1)

        read_write_time(
            read_function=read_advertisement_time_1,
            write_function=write_advertisement_time_1,
            name='advertisement_time_1',
            description="Advertisement Time 1",
            miliseconds=settings.STH.Bluetooth.Advertisement_Time_1)

        read_write_time(read_function=read_sleep_time_2,
                        write_function=write_sleep_time_2,
                        name='sleep_time_2',
                        description="Sleep Time 2",
                        miliseconds=settings.STH.Bluetooth.Sleep_Time_2)

        read_write_time(
            read_function=read_advertisement_time_2,
            write_function=write_advertisement_time_2,
            name='advertisement_time_2',
            description="Advertisement Time 2",
            miliseconds=settings.STH.Bluetooth.Advertisement_Time_2)

        # ============
        # = Firmware =
        # ============

        # The STH seems to define two different firmware version numbers. We
        # overwrite the version stored in the EEPROM with the one read, when
        # the test connected to the STH.
        major, minor, build = map(int, cls.firmware_version.split('.'))
        write_firmware_version(major, minor, build)
        firmware_version = read_firmware_version()
        self.assertEqual(
            cls.firmware_version, firmware_version,
            f"Written firmware version “{cls.firmware_version}” does not " +
            f"match read firmware version “{firmware_version}”")

        # ============
        # = Hardware =
        # ============

        hardware_revision = settings.STH.Hardware_Revision
        major, minor, build = map(int, hardware_revision.split('.'))
        write_hardware_revision(major, minor, build)
        cls.hardware_revision = read_hardware_revision()
        self.assertEqual(
            hardware_revision, cls.hardware_revision,
            f"Written hardware revision “{hardware_revision}” does not " +
            f"match read hardware revision “{cls.hardware_revision}”")

        cls.release_name = read_release_name()
        cls.serial_number = read_serial_number()
        cls.product_name = read_product_name()

        production_date = str(settings.STH.Production_Date)
        write_production_date(production_date)
        cls.production_date = read_production_date()
        self.assertEqual(
            production_date, cls.production_date,
            f"Written production date “{production_date}” does not match " +
            f"read production date “{cls.production_date}”")

        cls.batch_number = read_batch_number()


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    main(testRunner=ExtendedTestRunner)
