from unittest import TestCase, main
from os import environ, pathsep
from os.path import abspath, dirname, isfile, join, sep
from re import escape, search
from subprocess import run
from sys import argv
from sys import path as module_path

# Add path for custom libraries
module_path.insert(1, dirname(dirname(abspath(__file__))))
import CanFd
from MyToolItNetworkNumbers import MyToolItNetworkNr
from MyToolItSth import SthErrorWord
from MyToolItStu import StuErrorWord
from SthLimits import SthLimits
from MyToolItCommands import *


class TestSth(TestCase):
    """Production test for the Sensory Tool Holder (STH)"""
    @classmethod
    def setUpClass(cls):
        "Initialize data for whole test"
        build_location = f"../../STH/builds/{version}"
        cls.bootloader_filepath = abspath(
            join(build_location, f"manufacturingImageSth{version}.hex"))
        cls.board_type = "BGM113A256V2"
        cls.adapter_serial_number = "440120910"
        commander_path = sep.join([
            'C:', 'SiliconLabs', 'SimplicityStudio', 'v4', 'developer',
            'adapter_packs', 'commander'
        ])
        environ["PATH"] += pathsep + commander_path

    def setUp(self):
        self.bError = False
        log_filepath = f"{self._testMethodName}.txt"
        log_filepath_error = f"{self._testMethodName}_Error.txt"

        uAdc2Acc = 200
        sth_limits = SthLimits(1, uAdc2Acc, 20, 35)
        self.Can = CanFd.CanFd(CanFd.PCAN_BAUD_1M,
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
            self._resetStu()["CanTime"])  # This will also reset the STH

    def tearDown(self):
        self.Can.Logger.Info("> Tear Down")
        if "test0000FirmwareFlash" != self._testMethodName and "test9999StoreTestResults" != self._testMethodName:
            self.Can.streamingStop(MyToolItNetworkNr["STH1"],
                                   MyToolItStreaming["Acceleration"])
            self.Can.streamingStop(MyToolItNetworkNr["STH1"],
                                   MyToolItStreaming["Voltage"])
            self._statusWords()
            self._iSthAdcTemp()
            self.Can.Logger.Info("Test Time End Time Stamp")
        self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])
        self.Can.__exit__()

    """
    Reset STU
    """

    def _resetStu(self, retries=5, log=True):
        self.Can.bConnected = False
        return self.Can.cmdReset(MyToolItNetworkNr["STU1"],
                                 retries=retries,
                                 log=log)

    """
    Get internal BGM113 Chip Temperature in °C of STH
    """

    def _iSthAdcTemp(self):
        ret = self.Can.calibMeasurement(MyToolItNetworkNr["STH1"],
                                        CalibMeassurementActionNr["Measure"],
                                        CalibMeassurementTypeNr["Temp"],
                                        1,
                                        AdcReference["1V25"],
                                        log=False)
        result = float(iMessage2Value(ret[4:]))
        result /= 1000
        self.Can.Logger.Info("Temperature(Chip): " + str(result) + "°C")
        self.Can.calibMeasurement(MyToolItNetworkNr["STH1"],
                                  CalibMeassurementActionNr["None"],
                                  CalibMeassurementTypeNr["Temp"],
                                  1,
                                  AdcReference["VDD"],
                                  log=False,
                                  bReset=True)
        return result

    """
    Get all status words of STH and STU
    """

    def _statusWords(self):
        ErrorWordSth = SthErrorWord()
        ErrorWordStu = StuErrorWord()
        psw0 = self.Can.statusWord0(MyToolItNetworkNr["STH1"])
        self.Can.Logger.Info("STH Status Word: " + hex(psw0))
        psw0 = self.Can.statusWord0(MyToolItNetworkNr["STU1"])
        self.Can.Logger.Info("STU Status Word: " + hex(psw0))
        ErrorWordSth.asword = self.Can.statusWord1(MyToolItNetworkNr["STH1"])
        if True == ErrorWordSth.b.bAdcOverRun:
            self.bError = True
        self.Can.Logger.Info("STH Error Word: " + hex(ErrorWordSth.asword))
        ErrorWordStu.asword = self.Can.statusWord1(MyToolItNetworkNr["STU1"])
        self.Can.Logger.Info("STU Error Word: " + hex(ErrorWordStu.asword))

    """
    Retrieve STH Watchdog counter
    """

    def _SthWDog(self):
        WdogCounter = iMessage2Value(
            self.Can.statisticalData(MyToolItNetworkNr["STH1"],
                                     MyToolItStatData["Wdog"])[:4])
        self.Can.Logger.Info("WatchDog Counter: " + str(WdogCounter))
        return WdogCounter

    def test0000FirmwareFlash(self):
        """Upload bootloader into STH"""

        identification_arguments = (
            f"--serialno {type(self).adapter_serial_number} " +
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

        # Retrieve device id
        info_command = (f"commander device info {identification_arguments}")
        status = run(info_command, capture_output=True, text=True)
        self.assertEqual(
            status.returncode, 0,
            "Device information command returned non-zero exit code " +
            f"{status.returncode}")
        id_match = search("Unique ID\s*:\s*(?P<id>[0-9A-Fa-f]+)",
                          status.stdout)
        self.assertIsNotNone(id_match, "Unable to determine unique ID of chip")
        unique_id = id_match['id']

        # Upload bootloader data
        bootloader_filepath = type(self).bootloader_filepath
        self.assertTrue(
            isfile(bootloader_filepath),
            f"Bootloader file {bootloader_filepath} does not exist")

        flash_command = (f"commander flash {bootloader_filepath} " +
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
