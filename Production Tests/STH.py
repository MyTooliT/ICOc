from os import environ, pathsep
from os.path import abspath, dirname, isfile, join
from re import escape
from subprocess import run
from sys import path as module_path
from unittest import TestCase, main

# Add path for custom libraries
repository_root = dirname(dirname(abspath(__file__)))
module_path.append(repository_root)
module_path.append(join(repository_root, "Configuration"))

from config import settings

from CanFd import CanFd, PCAN_BAUD_1M
from MyToolItNetworkNumbers import MyToolItNetworkNr
from SthLimits import SthLimits


class TestSth(TestCase):
    """This class contains tests for the Sensory Tool Holder (STH)"""


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


if __name__ == "__main__":
    main(failfast=True)
