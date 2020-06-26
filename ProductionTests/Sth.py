import unittest
import os
import sys
sDirName = os.path.dirname('')
sys.path.append(sDirName)
file_path = '../'
sDirName = os.path.dirname(file_path)
sys.path.append(sDirName)
import CanFd
import time
import array
import math
import struct
from datetime import date
from shutil import copyfile
from MyToolItNetworkNumbers import MyToolItNetworkNr
from MyToolItSth import TestConfig, SthErrorWord, fVoltageBattery
from MyToolItStu import StuErrorWord
from SthLimits import SthLimits
from StuLimits import StuLimits
from MyToolItCommands import *
from os.path import abspath, isfile, join
from re import escape, search
from subprocess import run

sVersion = "v2.1.9"
sLogName = 'ProductionTestSth'
sLogLocation = '../../Logs/ProductionTestSth/'
sOtaComPort = 'COM6'
sBuildLocation = "../../STH/builds/"
sSilabsCommanderLocation = "C:/SiliconLabs/SimplicityStudio/v4/developer/adapter_packs/commander/"
sAdapterSerialNo = "440120910"
sBoardType = "BGM113A256V2"
iSensorAxis = 1
uAdc2Acc = 200
iRssiMin = -75
bStuPcbOnly = True

bSkip = False
sHolderNameInput = None
"""
This class supports a production test of the Sensory Tool Holder (STH)
"""


class TestSth(unittest.TestCase):
    def setUp(self):
        global bSkip
        global sHolderNameInput
        self.tSthLimits = SthLimits(iSensorAxis, uAdc2Acc, 20, 35)
        self.tStuLimits = StuLimits(bStuPcbOnly)
        self.sBuildLocation = sBuildLocation + sVersion
        self.sBootloader = sBuildLocation + "BootloaderOtaBgm113.s37"
        self.sAdapterSerialNo = sAdapterSerialNo
        self.sBoardType = sBoardType
        self.sSilabsCommander = sSilabsCommanderLocation + "commander"
        self.sLogLocation = sLogLocation
        self.bError = False
        self.sBuildLocation = sBuildLocation + sVersion
        self.iTestNumber = int(self._testMethodName[4:8])
        self.fileName = self.sLogLocation + self._testMethodName + ".txt"
        self.fileNameError = self.sLogLocation + "Error_" + self._testMethodName + ".txt"
        self.sExcelEepromContentFileName = "Sth" + sVersion + ".xlsx"

        if False != bSkip and "test9999StoreTestResults" != self._testMethodName:
            self.skipTest("At least some previous test failed")
        else:
            self.sDateClock = sDateClock()
            self.Can = CanFd.CanFd(
                CanFd.PCAN_BAUD_1M,
                self.fileName,
                self.fileNameError,
                MyToolItNetworkNr["SPU1"],
                MyToolItNetworkNr["STH1"],
                self.tSthLimits.uSamplingRatePrescalerReset,
                self.tSthLimits.uSamplingRateAcqTimeReset,
                self.tSthLimits.uSamplingRateOverSamplesReset,
                FreshLog=True)
            self.Can.Logger.Info("TestCase: " + str(self._testMethodName))
            self.Can.CanTimeStampStart(
                self._resetStu()["CanTime"])  # This will also reset the STH

            if "test0000FirmwareFlash" != self._testMethodName:
                self.Can.Logger.Info("Connect to STH")
                self.sHolderName = TestConfig["DevName"]
                if None != self.sHolderName:
                    if "test0001OverTheAirUpdate" == self._testMethodName:
                        for _i in range(0, 2):
                            atDevList = self.Can.tDeviceList(
                                MyToolItNetworkNr["STU1"])
                            for tDev in atDevList:
                                if tDev["Name"] == sHolderNameInput:
                                    self.sHolderName = sHolderNameInput
                                    break
                            if self.sHolderName == sHolderNameInput:
                                break
                            time.sleep(2)
                    else:
                        self.sHolderName = sHolderNameInput
                self.Can.bBlueToothConnectPollingName(
                    MyToolItNetworkNr["STU1"], self.sHolderName, log=False)
                time.sleep(2)
                self.sSthAddr = sBlueToothMacAddr(
                    self.Can.BlueToothAddress(MyToolItNetworkNr["STH1"]))
                self.sTestReport = sHolderNameInput + "_" + sLogName
                sStoreFileName = "./ResultsSth/OK_" + self.sTestReport + "_nr0.xlsx"
                if False == os.path.isfile(
                        sStoreFileName
                ) and "test0001OverTheAirUpdate" == self._testMethodName:
                    batchFile = open("BatchNumberSth.txt", "w")
                    iBatchNr = int(self.sBatchNumber)
                    iBatchNr += 1
                    self.sBatchNumber = str(iBatchNr)
                    batchFile.write(self.sBatchNumber)
                    batchFile.close()
                self._statusWords()
                self._iSthAdcTemp()
                self._SthWDog()
                self.Can.Logger.Info("STH BlueTooth Address: " + self.sSthAddr)
            else:
                sHolderNameInput = "Blubb"
                if 8 < len(sHolderNameInput):
                    sHolderNameInput = sHolderName[:8]
            self.sStuAddr = sBlueToothMacAddr(
                self.Can.BlueToothAddress(MyToolItNetworkNr["STU1"]))
            self.Can.Logger.Info("STU BlueTooth Address: " + self.sStuAddr)
            self.Can.Logger.Info(
                "_______________________________________________________________________________________________________________"
            )
            self.Can.Logger.Info("Start")

    def tearDown(self):
        global bSkip
        self.Can.Logger.Info("Fin")
        self.Can.Logger.Info(
            "_______________________________________________________________________________________________________________"
        )
        if "test9999StoreTestResults" != self._testMethodName and "test0000FirmwareFlash" != self._testMethodName:
            self.tWorkbook.save(self.sTestReport + ".xlsx")
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
        if self._outcome.errors[1][1]:
            if False == bSkip:
                print("Error! Please put red point on it(" +
                      self.sBatchNumber + ")")
            bSkip = True
        if False != self.bError:
            if False == bSkip:
                print("Error! Please put red point on it(" +
                      self.sBatchNumber + ")")
            bSkip = True

    def run(self, result=None):
        global bSkip
        batchFile = open("BatchNumberSth.txt")
        sBatchData = batchFile.readlines()
        self.sBatchNumber = sBatchData[0]
        batchFile.close()
        """ Stop after first error """
        if not result.errors:
            super(TestSth, self).run(result)
        else:
            if False == bSkip:
                print("Error! Please put red point on it(" +
                      self.sBatchNumber + ")")
            bSkip = True
            if "test9999StoreTestResults" == self._testMethodName:
                super(TestSth, self).run(result)

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

        identification_arguments = (f"--serialno {self.sAdapterSerialNo} " +
                                    f"-d {self.sBoardType}")

        # Unlock debug access
        unlock_command = (
            f"{self.sSilabsCommander} device unlock {identification_arguments}"
        )
        if os.name == 'nt':
            unlock_command = unlock_command.replace('/', '\\')
        status = run(unlock_command, capture_output=True, text=True)
        self.assertEqual(
            status.returncode, 0,
            f"Unlock command returned non-zero exit code {status.returncode}")
        self.assertRegex(status.stdout, "Chip successfully unlocked",
                         "Unable to unlock debug access of chip")

        # Retrieve device id
        info_command = (
            f"{self.sSilabsCommander} device info {identification_arguments}")
        if os.name == 'nt':
            info_command = info_command.replace('/', '\\')
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
        bootloader_filepath = abspath(
            join(sBuildLocation, sVersion,
                 f"manufacturingImageSth{sVersion}.hex"))
        self.assertTrue(
            isfile(bootloader_filepath),
            f"Bootloader file {bootloader_filepath} does not exist")

        flash_command = (
            f"{self.sSilabsCommander} flash {bootloader_filepath} " +
            f"--address 0x0 {identification_arguments}")
        if os.name == 'nt':
            flash_command = flash_command.replace('/', '\\')
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
    sVersion = sys.argv[1]
    unittest.main(argv=['first-arg-is-ignored'])
