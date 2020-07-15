from os import environ, pathsep
from os.path import abspath, dirname, isfile, join
from re import escape
from subprocess import run
from sys import path as module_path
from time import sleep
from unittest import TestCase, main

# Add path for custom libraries
repository_root = dirname(dirname(dirname(dirname(abspath(__file__)))))
module_path.append(repository_root)

from mytoolit.can.identifier import Identifier
from mytoolit.measurement.acceleration import (convert_acceleration_adc_to_g,
                                               signal_noise_ratio)
from mytoolit.report.report import Report
from mytoolit.config import settings

from CanFd import CanFd
from MyToolItNetworkNumbers import MyToolItNetworkNr
from MyToolItCommands import (ActiveState, DataSets, MyToolItBlock,
                              MyToolItSystem, Node, iMessage2Value,
                              NetworkState, sBlueToothMacAddr,
                              MyToolItProductData, MyToolItStreaming)
from MyToolItSth import fVoltageBattery
from SthLimits import SthLimits


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

        if cls.read_attributes:
            # Do not print anything, if MAC address is undefined
            print("\n\nTest Data")
            print("—————————")

            attributes = [["Bluetooth Address", cls.bluetooth_mac],
                          ["RSSI", f"{cls.bluetooth_rssi} dBm"],
                          ["Firmware Version", cls.firmware_version]]

            if hasattr(cls, 'snr'):
                attributes.append(
                    ["Signal to Noise Ratio", f"{cls.snr:.3f} dB"])

            for description, value in attributes:
                print(f"{description}: {value}")
                cls.report.add_attribute(description, value)

            print()

        cls.report.__exit__()

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
        image_filepath = settings.STH.Firmware.Location
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

    def test_acceleration(self):
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
            settings.STH.Acceleration_Sensor.Acceleration_Tolerance)
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

    def test_acceleration_snr(self):
        """Test signal to noise ratio of sensor"""

        # Read x-acceleration values in single data sets for 4
        # seconds
        index_start, index_end = self.can.streamingValueCollect(
            MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"],
            DataSets[1], 1, 0, 0, 4000)

        [array1, array2, array3] = self.can.streamingValueArray(
            MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"],
            DataSets[1], 1, 0, 0, index_start, index_end)

        # We expect an acceleration of zero (half of the 16 Bit maximum ADC
        # value)
        expected_acceleration_adc = 2**15
        cls = type(self)
        cls.snr = signal_noise_ratio(expected_acceleration_adc, array1)

        expected_minimum_snr = settings.STH.Acceleration_Sensor.Minimum_SNR
        self.assertGreaterEqual(
            cls.snr, expected_minimum_snr,
            f"Measured signal to noise ratio {cls.snr} dB is lower " +
            "than expected minimum signal to noise ratio " +
            f"{expected_minimum_snr} dB")


if __name__ == "__main__":
    main(failfast=True)
