from os import environ, pathsep
from os.path import abspath, dirname, isfile, join
from re import escape
from subprocess import run
from sys import path as module_path
from time import sleep
from unittest import TestCase, main

# Add path for custom libraries
repository_root = dirname(dirname(abspath(__file__)))
module_path.append(repository_root)
module_path.append(join(repository_root, "Configuration"))

from config import settings

from CanFd import CanFd, PCAN_BAUD_1M
from MyToolItNetworkNumbers import MyToolItNetworkNr
from MyToolItCommands import (ActiveState, MyToolItBlock, MyToolItSystem, Node,
                              NetworkState)
from SthLimits import SthLimits


class TestSth(TestCase):
    """This class contains tests for the Sensory Tool Holder (STH)"""

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

    def __connect(self):
        """Create a connection to the STH"""

        # Initialize CAN bus
        log_filepath = f"{self._testMethodName}.txt"
        log_filepath_error = f"{self._testMethodName}_Error.txt"

        sth_limits = SthLimits(1, 200, 20, 35)
        self.Can = CanFd(PCAN_BAUD_1M,
                         log_filepath,
                         log_filepath_error,
                         MyToolItNetworkNr["SPU1"],
                         MyToolItNetworkNr["STH1"],
                         sth_limits.uSamplingRatePrescalerReset,
                         sth_limits.uSamplingRateAcqTimeReset,
                         sth_limits.uSamplingRateOverSamplesReset,
                         FreshLog=True)

        # Reset STU (and STH)
        self.Can.bConnected = False
        return_message = self.Can.cmdReset(MyToolItNetworkNr["STU1"])
        self.Can.CanTimeStampStart(return_message["CanTime"])

        # Connect to STH
        self.Can.bBlueToothConnectPollingName(MyToolItNetworkNr["STU1"],
                                              settings.STH.Name,
                                              log=False)
        sleep(2)

    def __disconnect(self):
        """Tear down connection to STH"""

        self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])
        self.Can.__exit__()

    def test__firmware_flash(self):
        """Upload bootloader and application into STH.

        Please note the additional underscore in the method name that makes
        sure this test case is executed before all other test cases.
        """

        # Add path to Simplicity Commander
        environ["PATH"] += (pathsep +
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
        command = self.Can.CanCmd(MyToolItBlock['System'],
                                  MyToolItSystem['ActiveState'],
                                  request=True)
        expected_data = ActiveState()
        expected_data.asbyte = 0
        expected_data.b.u2NodeState = Node['Application']
        expected_data.b.u3NetworkState = NetworkState['Operating']
        message = self.Can.CanMessage20(command, MyToolItNetworkNr['SPU1'],
                                        MyToolItNetworkNr['STH1'],
                                        [expected_data.asbyte])
        self.Can.Logger.Info('Write message')
        self.Can.WriteFrame(message)
        self.Can.Logger.Info('Wait 200ms')
        sleep(0.2)

        # Receive message from STH
        command = self.Can.CanCmd(MyToolItBlock['System'],
                                  MyToolItSystem['ActiveState'],
                                  request=False)
        expected_message = self.Can.CanMessage20(command,
                                                 MyToolItNetworkNr['STH1'],
                                                 MyToolItNetworkNr['SPU1'],
                                                 [0])
        received_message = self.Can.getReadMessage(-1)

        # Check for equivalence of message content
        expected_id = hex(expected_message.ID)
        received_id = hex(received_message.ID)
        self.assertEqual(
            expected_id, received_id,
            f"Expected ID “{expected_id}” does not match " +
            f"received ID “{received_id}”")

        expected_data_byte = expected_data.asbyte
        received_data_byte = received_message.DATA[0]
        self.assertEqual(
            expected_data_byte, received_data_byte,
            f"Expected data “{expected_data_byte}” does not match " +
            f"received data “{received_data_byte}”")


if __name__ == "__main__":
    main(failfast=True)
