from os import environ, pathsep
from os.path import abspath, dirname, isfile, join, sep
from re import escape
from subprocess import run
from sys import argv
from sys import path as module_path
from unittest import TestCase, main

# Add path for custom libraries
repository_root = dirname(dirname(abspath(__file__)))
module_path.append(repository_root)

from config import settings

from CanFd import CanFd, PCAN_BAUD_1M
from MyToolItNetworkNumbers import MyToolItNetworkNr
from SthLimits import SthLimits


class TestSth(TestCase):
    """This class contains tests for the Sensory Tool Holder (STH)"""

    @classmethod
    def setUpClass(cls):
        """Initialize data for whole test"""

        build_location = join(dirname(repository_root),
                              f"STH/builds/{version}")
        cls.complete_image_filepath = abspath(
            join(build_location, f"manufacturingImageSth{version}.hex"))
        cls.board_type = "BGM113A256V2"
        commander_path = sep.join([
            'C:', 'SiliconLabs', 'SimplicityStudio', 'v4', 'developer',
            'adapter_packs', 'commander'
        ])
        environ["PATH"] += pathsep + commander_path

    def setUp(self):
        """Set up hardware before a single test case"""

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
        self.Can.Logger.Info("TestCase: " + str(self._testMethodName))
        self.Can.CanTimeStampStart(
            self.__reset_stu()["CanTime"])  # This will also reset the STH

    def tearDown(self):
        """Clean up after single test case"""

        self.Can.Logger.Info("> Tear Down")
        self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])
        self.Can.__exit__()

    def __reset_stu(self):
        """Reset STU"""

        self.Can.bConnected = False
        return self.Can.cmdReset(MyToolItNetworkNr["STU1"])

    def test0000FirmwareFlash(self):
        """Upload bootloader and application into STH"""

        identification_arguments = (
            f"--serialno {settings.STH.Programming_Board.Serial_Number} " +
            f"-d {type(self).board_type}")

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
        image_filepath = type(self).complete_image_filepath
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
    version = argv[1] if len(argv) > 1 else 'v2.1.10'
    main(argv=['first-arg-is-ignored'], failfast=True)
