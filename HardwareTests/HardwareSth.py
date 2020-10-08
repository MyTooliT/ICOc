import unittest
import sys
import os
import random
from datetime import date
from numpy.core.arrayprint import array2string

# Required to add peakcan
sDirName = os.path.dirname('')
sys.path.append(sDirName)
file_path = '../'
sDirName = os.path.dirname(file_path)
sys.path.append(sDirName)

import CanFd
import math
from MyToolItNetworkNumbers import MyToolItNetworkNr
import time
from MyToolItSth import TestConfig, SthModule, SleepTime, SthErrorWord, SthStateWord, fVoltageBattery, fAdcRawDat
from MyToolItCommands import *
from SthLimits import SthLimits
from testSignal import *

sVersion = TestConfig["Version"]
sLogLocation = '../../Logs/Hardware/'
sHomeLocation = "../../SimplicityStudio/v4_workspace/STH/"
sSilabsCommanderLocation = "../../SimplicityStudio/SimplicityCommander/"
sAdapterSerialNo = "440115849"
sBoardType = "BGM113A256V2"
iSensorAxis = 1
bBatteryExternalDcDc = True
uAdc2Acc = 100
iRssiMin = -75
bStuPcbOnly = True
"""
This class is used for automated internal verification of the sensory tool holder
"""


class TestSth(unittest.TestCase):
    def setUp(self):
        self.tSthLimits = SthLimits()
        SthLimits(iSensorAxis, bBatteryExternalDcDc, uAdc2Acc, iRssiMin, 20,
                  35)
        self.sHomeLocation = sHomeLocation
        self.sBuildLocation = sHomeLocation + "builds/" + sVersion
        self.sBootloader = sHomeLocation + "builds/" + "BootloaderOtaBgm113.s37"
        self.sAdapterSerialNo = sAdapterSerialNo
        self.sBoardType = sBoardType
        self.sSilabsCommander = sSilabsCommanderLocation + "commander"
        self.bError = False
        self.fileName = sLogLocation + self._testMethodName + ".txt"
        self.fileNameError = sLogLocation + "Error_" + self._testMethodName + ".txt"
        self.Can = CanFd.CanFd(self.fileName,
                               self.fileNameError,
                               MyToolItNetworkNr["SPU1"],
                               MyToolItNetworkNr["STH1"],
                               self.tSthLimits.uSamplingRatePrescalerReset,
                               self.tSthLimits.uSamplingRateAcqTimeReset,
                               self.tSthLimits.uSamplingRateOverSamplesReset,
                               FreshLog=True)
        self.Can.Logger.Info("TestCase: " + str(self._testMethodName))
        self.vSilabsAdapterReset()
        self.Can.CanTimeStampStart(
            self._resetStu()["CanTime"])  # This will also reset to STH
        self.Can.Logger.Info("Connect to STH")
        self.Can.bBlueToothConnectPollingName(MyToolItNetworkNr["STU1"],
                                              TestConfig["DevName"])
        self.sStuAddr = sBlueToothMacAddr(
            self.Can.BlueToothAddress(MyToolItNetworkNr["STU1"]))
        self.sSthAddr = sBlueToothMacAddr(
            self.Can.BlueToothAddress(MyToolItNetworkNr["STH1"]))
        self.Can.Logger.Info("STU BlueTooth Address: " + self.sStuAddr)
        self.Can.Logger.Info("STH BlueTooth Address: " + self.sSthAddr)
        self.Can.u32EepromWriteRequestCounter(MyToolItNetworkNr["STH1"])
        iOperatingSeconds = self.Can.statisticalData(
            MyToolItNetworkNr["STU1"], MyToolItStatData["OperatingTime"])[4:]
        iOperatingSeconds = iMessage2Value(iOperatingSeconds)
        self.Can.Logger.Info("STU Operating Seconds: " +
                             str(iOperatingSeconds))
        iOperatingSeconds = self.Can.statisticalData(
            MyToolItNetworkNr["STH1"], MyToolItStatData["OperatingTime"])[4:]
        iOperatingSeconds = iMessage2Value(iOperatingSeconds)
        self.Can.Logger.Info("STH Operating Seconds: " +
                             str(iOperatingSeconds))
        self._statusWords()
        temp = self._SthAdcTemp()
        self.assertGreaterEqual(self.tSthLimits.iTemperatureInternalMax, temp)
        self.assertLessEqual(self.tSthLimits.iTemperatureInternalMin, temp)
        self._SthWDog()

        self.Can.Logger.Info(
            "_______________________________________________________________________________________________________________"
        )
        self.Can.Logger.Info("Start")

    def tearDown(self):
        self.Can.Logger.Info("Fin")
        self.Can.Logger.Info(
            "_______________________________________________________________________________________________________________"
        )
        if False == self.Can.bError:
            self._streamingStop()
            self._BlueToothStatistics()
            ReceiveFailCounter = self._RoutingInformation()
            iOperatingSeconds = self.Can.statisticalData(
                MyToolItNetworkNr["STU1"],
                MyToolItStatData["OperatingTime"])[4:]
            iOperatingSeconds = iMessage2Value(iOperatingSeconds)
            self.Can.Logger.Info("STU Operating Seconds: " +
                                 str(iOperatingSeconds))
            iOperatingSeconds = self.Can.statisticalData(
                MyToolItNetworkNr["STH1"],
                MyToolItStatData["OperatingTime"])[4:]
            iOperatingSeconds = iMessage2Value(iOperatingSeconds)
            self.Can.Logger.Info("STH Operating Seconds: " +
                                 str(iOperatingSeconds))
            self._statusWords()
            temp = self._SthAdcTemp()
            self.assertGreaterEqual(self.tSthLimits.iTemperatureInternalMax,
                                    temp)
            self.assertLessEqual(self.tSthLimits.iTemperatureInternalMin, temp)
            self.Can.u32EepromWriteRequestCounter(MyToolItNetworkNr["STH1"])
            self.Can.Logger.Info("Test Time End Time Stamp")
            self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])
        else:
            ReceiveFailCounter = 0
        if (0 < ReceiveFailCounter):
            self.bError = True
        if False != self.Can.bError:
            self.bError = True
        self.Can.__exit__()
        if self._test_has_failed():
            if os.path.isfile(self.fileNameError) and os.path.isfile(
                    self.fileName):
                os.remove(self.fileNameError)
            if os.path.isfile(self.fileName):
                os.rename(self.fileName, self.fileNameError)

    """
    Checks if test has failed
    """

    def _test_has_failed(self):
        for _method, error in self._outcome.errors:
            if error:
                return True
        if True == self.bError:
            return True
        return False

    """
    Reset STU
    """

    def _resetStu(self, retries=5, log=True):
        self.Can.bConnected = False
        return self.Can.reset_node("STU1", retries=retries, log=log)

    """
    Reset STH
    """

    def _resetSth(self, retries=5, log=True):
        self.Can.bConnected = False
        return self.Can.reset_node("STH1",
                                   retries=retries,
                                   log=log)

    """
    Retrieve BGM113 internal Chip Temperature from the STH
    """

    def _SthAdcTemp(self):
        au8TempReturn = self.Can.calibMeasurement(
            MyToolItNetworkNr["STH1"],
            CalibMeassurementActionNr["Measure"],
            CalibMeassurementTypeNr["Temp"],
            1,
            AdcReference["1V25"],
            log=False)
        iTemperature = float(iMessage2Value(au8TempReturn[4:]))
        iTemperature /= 1000
        self.Can.Logger.Info("Temperature(Chip): " + str(iTemperature) + "°C")
        self.Can.calibMeasurement(MyToolItNetworkNr["STH1"],
                                  CalibMeassurementActionNr["None"],
                                  CalibMeassurementTypeNr["Temp"],
                                  1,
                                  AdcReference["VDD"],
                                  log=False,
                                  bReset=True)
        return iTemperature

    """
    Retrieve Watch Dog Counter
    """

    def _SthWDog(self):
        WdogCounter = iMessage2Value(
            self.Can.statisticalData(MyToolItNetworkNr["STH1"],
                                     MyToolItStatData["Wdog"])[:4])
        self.Can.Logger.Info("WatchDog Counter: " + str(WdogCounter))
        return WdogCounter

    """
    Get all Status Words from STH and STU
    """

    def _statusWords(self):
        ErrorWord = SthErrorWord()

        self.Can.Logger.Info("STH Status Word: {}".format(
            self.Can.node_status(MyToolItNetworkNr["STH1"])))
        self.Can.Logger.Info("STU Status Word: {}".format(
            self.Can.node_status(MyToolItNetworkNr["STU1"])))

        status = self.Can.error_status(MyToolItNetworkNr["STH1"])
        if status.adc_overrun():
            self.bError = True
        self.Can.Logger.Info(f"STH Error Word: {status}")

        self.Can.Logger.Info("STU Error Word: {}".format(
            self.Can.error_status(MyToolItNetworkNr["STU1"])))

    """
    Stop any streaming
    """

    def _streamingStop(self):
        self.Can.streamingStop(MyToolItNetworkNr["STH1"],
                               MyToolItStreaming["Acceleration"])
        self.Can.streamingStop(MyToolItNetworkNr["STH1"],
                               MyToolItStreaming["Voltage"])

    """
    Get RSSI, receive and send message counters of Bluetooth
    """

    def _BlueToothStatistics(self):
        SendCounter = self.Can.BlueToothCmd(
            MyToolItNetworkNr["STH1"], SystemCommandBlueTooth["SendCounter"])
        self.Can.Logger.Info("BlueTooth Send Counter(STH1): " +
                             str(SendCounter))
        ReceiveCounter = self.Can.BlueToothCmd(
            MyToolItNetworkNr["STH1"],
            SystemCommandBlueTooth["ReceiveCounter"])
        self.Can.Logger.Info("BlueTooth Receive Counter(STU1): " +
                             str(ReceiveCounter))
        Rssi = self.Can.BlueToothRssi(MyToolItNetworkNr["STH1"])
        self.Can.Logger.Info("BlueTooth Rssi(STH1): " + str(Rssi) + "dBm")
        SendCounter = self.Can.BlueToothCmd(
            MyToolItNetworkNr["STU1"], SystemCommandBlueTooth["SendCounter"])
        self.Can.Logger.Info("BlueTooth Send Counter(STU1): " +
                             str(SendCounter))
        ReceiveCounter = self.Can.BlueToothCmd(
            MyToolItNetworkNr["STU1"],
            SystemCommandBlueTooth["ReceiveCounter"])
        self.Can.Logger.Info("BlueTooth Receive Counter(STU1): " +
                             str(ReceiveCounter))
        Rssi = self.Can.BlueToothRssi(MyToolItNetworkNr["STU1"])
        self.Can.Logger.Info("BlueTooth Rssi(STU1): " + str(Rssi) + "dBm")

    """
    Routing information of STH send ports
    """

    def _RoutingInformationSthSend(self):
        SendCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STH1"], SystemCommandRouting["SendCounter"],
            MyToolItNetworkNr["STU1"])
        self.Can.Logger.Info("STH1 - Send Counter(Port STU1): " +
                             str(SendCounter))
        SendCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STH1"], SystemCommandRouting["SendFailCounter"],
            MyToolItNetworkNr["STU1"])
        self.Can.Logger.Info("STH1 - Send Fail Counter(Port STU1): " +
                             str(SendCounter))
        SendCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STH1"],
            SystemCommandRouting["SendLowLevelByteCounter"],
            MyToolItNetworkNr["STU1"])
        self.Can.Logger.Info("STH1 - Send Byte Counter(Port STU1): " +
                             str(SendCounter))

    """
    Routing information of STU send ports
    """

    def _RoutingInformationSthReceive(self):
        ReceiveCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STH1"], SystemCommandRouting["ReceiveCounter"],
            MyToolItNetworkNr["STU1"])
        self.Can.Logger.Info("STH1 - Receive Counter(Port STU1): " +
                             str(ReceiveCounter))
        ReceiveFailCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STH1"],
            SystemCommandRouting["ReceiveFailCounter"],
            MyToolItNetworkNr["STU1"])
        self.Can.Logger.Info("STH1 - Receive Fail Counter(Port STU1): " +
                             str(ReceiveFailCounter))
        ReceiveCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STH1"],
            SystemCommandRouting["ReceiveLowLevelByteCounter"],
            MyToolItNetworkNr["STU1"])
        self.Can.Logger.Info("STH1 - Receive Byte Counter(Port STU1): " +
                             str(ReceiveCounter))
        return ReceiveFailCounter

    """
    Routing information of STH
    """

    def _RoutingInformationSth(self):
        self._RoutingInformationSthSend()
        ReceiveFailCounter = self._RoutingInformationSthReceive()
        return ReceiveFailCounter

    """
    Routing information of STU send port SPU
    """

    def _RoutingInformationStuPortSpuSend(self):
        SendCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"], SystemCommandRouting["SendCounter"],
            MyToolItNetworkNr["SPU1"])
        self.Can.Logger.Info("STU1 - Send Counter(Port SPU1): " +
                             str(SendCounter))
        SendCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"], SystemCommandRouting["SendFailCounter"],
            MyToolItNetworkNr["SPU1"])
        self.Can.Logger.Info("STU1 - Send Fail Counter(Port SPU1): " +
                             str(SendCounter))
        SendCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"],
            SystemCommandRouting["SendLowLevelByteCounter"],
            MyToolItNetworkNr["SPU1"])
        self.Can.Logger.Info("STU1 - Send Byte Counter(Port SPU1): " +
                             str(SendCounter))

    """
    Routing information of STU receive port SPU
    """

    def _RoutingInformationStuPortSpuReceive(self):
        ReceiveCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"], SystemCommandRouting["ReceiveCounter"],
            MyToolItNetworkNr["SPU1"])
        self.Can.Logger.Info("STU1 - Receive Counter(Port SPU1): " +
                             str(ReceiveCounter))
        ReceiveFailCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"],
            SystemCommandRouting["ReceiveFailCounter"],
            MyToolItNetworkNr["SPU1"])
        self.Can.Logger.Info("STU1 - Receive Fail Counter(Port SPU1): " +
                             str(ReceiveFailCounter))
        ReceiveCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"],
            SystemCommandRouting["ReceiveLowLevelByteCounter"],
            MyToolItNetworkNr["SPU1"])
        self.Can.Logger.Info("STU1 - Receive Byte Counter(Port SPU1): " +
                             str(ReceiveCounter))
        return ReceiveFailCounter

    """
    Routing information of STU port SPU
    """

    def _RoutingInformationStuPortSpu(self):
        self._RoutingInformationStuPortSpuSend()
        ReceiveFailCounter = self._RoutingInformationStuPortSpuReceive()
        return ReceiveFailCounter

    """
    Routing information of STU send port STH
    """

    def _RoutingInformationStuPortSthSend(self):
        SendCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"], SystemCommandRouting["SendCounter"],
            MyToolItNetworkNr["STH1"])
        self.Can.Logger.Info("STU1 - Send Counter(Port STH1): " +
                             str(SendCounter))
        SendCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"], SystemCommandRouting["SendFailCounter"],
            MyToolItNetworkNr["STH1"])
        self.Can.Logger.Info("STU1 - Send Fail Counter(Port STH1): " +
                             str(SendCounter))
        SendCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"],
            SystemCommandRouting["SendLowLevelByteCounter"],
            MyToolItNetworkNr["STH1"])
        self.Can.Logger.Info("STU1 - Send Byte Counter(Port STH1): " +
                             str(SendCounter))

    """
    Routing information of STU receive port STH
    """

    def _RoutingInformationStuPortSthReceive(self):
        ReceiveCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"], SystemCommandRouting["ReceiveCounter"],
            MyToolItNetworkNr["STH1"])
        self.Can.Logger.Info("STU1 - Receive Counter(Port STH1): " +
                             str(ReceiveCounter))
        ReceiveFailCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"],
            SystemCommandRouting["ReceiveFailCounter"],
            MyToolItNetworkNr["STH1"])
        self.Can.Logger.Info("STU1 - Receive Fail Counter(Port STH1): " +
                             str(ReceiveFailCounter))
        ReceiveCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"],
            SystemCommandRouting["ReceiveLowLevelByteCounter"],
            MyToolItNetworkNr["STH1"])
        self.Can.Logger.Info("STU1 - Receive Byte Counter(Port STH1): " +
                             str(ReceiveCounter))
        return ReceiveFailCounter

    """
    Routing information of STU port STH
    """

    def _RoutingInformationStuPortSth(self):
        self._RoutingInformationStuPortSthSend()
        ReceiveFailCounter = self._RoutingInformationStuPortSthReceive()
        return ReceiveFailCounter

    """
    Routing information of system
    """

    def _RoutingInformation(self):
        ReceiveFailCounter = self._RoutingInformationSth()
        ReceiveFailCounter += self._RoutingInformationStuPortSth()
        ReceiveFailCounter += self._RoutingInformationStuPortSpu()
        return ReceiveFailCounter

    """
    Test single point in a three dimensional tube
    """

    def singleValueCompare(self, array1, array2, array3, middle1, tolerance1,
                           middle2, tolerance2, middle3, tolerance3,
                           fCbfRecalc):
        if 0 < len(array1):
            self.assertGreaterEqual(middle1 + tolerance1,
                                    fCbfRecalc(array1[0]))
            self.assertLessEqual(middle1 - tolerance1, fCbfRecalc(array1[0]))
        if 0 < len(array2):
            self.assertGreaterEqual(middle2 + tolerance2,
                                    fCbfRecalc(array2[0]))
            self.assertLessEqual(middle2 - tolerance2, fCbfRecalc(array2[0]))
        if 0 < len(array3):
            self.assertGreaterEqual(middle3 + tolerance3,
                                    fCbfRecalc(array3[0]))
            self.assertLessEqual(middle3 - tolerance3, fCbfRecalc(array3[0]))

    """
    Config ADC and determine correct sampling rate
    """

    def SamplingRate(self,
                     prescaler,
                     acquisitionTime,
                     overSamplingRate,
                     adcRef,
                     b1=1,
                     b2=0,
                     b3=0,
                     runTime=None,
                     compare=True,
                     compareRate=True,
                     log=True,
                     startupTime=None):
        if None == runTime:
            runTime = self.tSthLimits.uStandardTestTimeMs

        if None == startupTime:
            startupTime = self.tSthLimits.uStartupTimeMs

        Settings = self.Can.ConfigAdc(MyToolItNetworkNr["STH1"],
                                      prescaler,
                                      acquisitionTime,
                                      overSamplingRate,
                                      adcRef,
                                      log=log)[1:]
        self.assertEqual(prescaler, Settings[0])
        self.assertEqual(acquisitionTime, Settings[1])
        self.assertEqual(overSamplingRate, Settings[2])
        self.assertEqual(adcRef, Settings[3])
        calcRate = calcSamplingRate(prescaler, acquisitionTime,
                                    overSamplingRate)
        if False != log:
            self.Can.Logger.Info("Start sending package")
        dataSets = self.Can.Can20DataSet(b1, b2, b3)
        [indexStart, indexEnd
         ] = self.Can.streamingValueCollect(MyToolItNetworkNr["STH1"],
                                            MyToolItStreaming["Acceleration"],
                                            dataSets,
                                            b1,
                                            b2,
                                            b3,
                                            runTime,
                                            log=log,
                                            StartupTimeMs=startupTime)
        [array1, array2, array3] = self.Can.streamingValueArray(
            MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"],
            dataSets, b1, b2, b3, indexStart, indexEnd)
        self.Can.ReadThreadReset()
        samplingPoints = self.Can.samplingPoints(array1, array2, array3)
        if False != log:
            samplingPoints = self.Can.samplingPoints(array1, array2, array3)
            self.Can.Logger.Info("Running Time: " + str(runTime) + "ms")
            if False != startupTime:
                self.Can.Logger.Info("Startup Time: " + str(startupTime) +
                                     "ms")
            self.Can.Logger.Info("Assumed Sampling Points/s: " + str(calcRate))
            samplingRateDet = 1000 * samplingPoints / (runTime)
            self.Can.Logger.Info("Determined Sampling Points/s: " +
                                 str(samplingRateDet))
            self.Can.Logger.Info("Difference to Assumed Sampling Points: " +
                                 str((100 * samplingRateDet - calcRate) /
                                     calcRate) + "%")
            self.Can.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "")
        ratM = AdcVRefValuemV[AdcReference["VDD"]] / AdcVRefValuemV[adcRef]
        ratT = 1
        if adcRef != AdcReference["VDD"]:
            ratT = self.tSthLimits.Vfs
        if False != compare:
            if (1 != ratM):
                self.Can.Logger.Info(
                    "Compare Ration to compensate not AVDD: " + str(ratM))
            adcXMiddle = ratM * self.tSthLimits.iAdcAccXRawMiddle
            adcYMiddle = ratM * self.tSthLimits.iAdcAccYRawMiddle
            adcZMiddle = ratM * self.tSthLimits.iAdcAccZRawMiddle
            adcXTol = self.tSthLimits.iAdcAccXRawTolerance * ratT
            adcYTol = self.tSthLimits.iAdcAccYRawTolerance * ratT
            adcZTol = self.tSthLimits.iAdcAccZRawTolerance * ratT
            if (16 > AdcOverSamplingRateReverse[overSamplingRate]):
                self.Can.Logger.Info("Maximum ADC Value: " + str(AdcMax / 2**(
                    5 - AdcOverSamplingRateReverse[overSamplingRate])))
                adcXMiddle = adcXMiddle / 2**(
                    5 - AdcOverSamplingRateReverse[overSamplingRate])
                adcYMiddle = adcYMiddle / 2**(
                    5 - AdcOverSamplingRateReverse[overSamplingRate])
                adcZMiddle = adcZMiddle / 2**(
                    5 - AdcOverSamplingRateReverse[overSamplingRate])
            else:
                self.Can.Logger.Info("Maximum ADC Value: " + str(AdcMax))
            self.streamingValueCompare(array1, array2, array3, adcXMiddle,
                                       adcXTol, adcYMiddle, adcYTol,
                                       adcZMiddle, adcZTol, fAdcRawDat)
        if False != compareRate:
            self.assertLess(
                runTime / 1000 * calcRate *
                self.tSthLimits.uSamplingToleranceLow, samplingPoints)
            self.assertGreater(
                runTime / 1000 * calcRate *
                self.tSthLimits.uSamplingToleranceHigh, samplingPoints)
        result = {
            "SamplingRate": calcRate,
            "Value1": array1,
            "Value2": array2,
            "Value3": array3
        }
        return result

    """
    Turn off STH LED
    """

    def TurnOffLed(self):
        self.Can.Logger.Info("Turn Off LED")
        cmd = self.Can.CanCmd(MyToolItBlock["Configuration"],
                              MyToolItConfiguration["Hmi"], 1, 0)
        message = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                        MyToolItNetworkNr["STH1"],
                                        [129, 1, 2, 0, 0, 0, 0, 0])
        self.Can.tWriteFrameWaitAckRetries(message)

    """
    Turn on STH LED
    """

    def TurnOnLed(self):
        self.Can.Logger.Info("Turn On LED")
        cmd = self.Can.CanCmd(MyToolItBlock["Configuration"],
                              MyToolItConfiguration["Hmi"], 1, 0)
        message = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                        MyToolItNetworkNr["STH1"],
                                        [129, 1, 1, 0, 0, 0, 0, 0])
        self.Can.tWriteFrameWaitAckRetries(message)

    """
    Get streaming Data and collect them
    """

    def streamingTestSignalCollect(self,
                                   sender,
                                   receiver,
                                   subCmd,
                                   testSignal,
                                   testModule,
                                   value,
                                   dataSets,
                                   b1,
                                   b2,
                                   b3,
                                   testTimeMs,
                                   log=True):
        self.Can.Logger.Info("Request Test Signal: " + str(testSignal))
        self.Can.Logger.Info("Test Module: " + str(testModule))
        self.Can.Logger.Info("Test Value: " + str(testModule))
        accFormat = AtvcFormat()
        accFormat.asbyte = 0
        accFormat.b.bStreaming = 1
        accFormat.b.bNumber1 = b1
        accFormat.b.bNumber2 = b2
        accFormat.b.bNumber3 = b3
        accFormat.b.u3DataSets = dataSets
        cmd = self.Can.CanCmd(MyToolItBlock["Streaming"], subCmd, 1, 0)
        message = self.Can.CanMessage20(cmd, sender, receiver,
                                        [accFormat.asbyte])
        if False != log:
            self.Can.Logger.Info("Start sending package")
        self.Can.tWriteFrameWaitAckRetries(message, retries=1)
        cmd = self.Can.CanCmd(MyToolItBlock["Test"], MyToolItTest["Signal"], 1,
                              0)
        message = self.Can.CanMessage20(cmd, sender, receiver, [
            testSignal, testModule, 0, 0, 0, 0, 0xFF & value, 0xFF &
            (value >> 8)
        ])
        if False != log:
            self.Can.Logger.Info("Start sending test signal")
        self.Can.WriteFrame(message)
        time.sleep(0.5)
        indexStart = self.Can.GetReadArrayIndex()
        timeEnd = self.Can.getTimeMs() + testTimeMs
        if False != log:
            self.Can.Logger.Info("indexStart: " + str(indexStart))
        while self.Can.getTimeMs() < timeEnd:
            pass
        self.Can.streamingStop(MyToolItNetworkNr["STH1"], subCmd)
        time.sleep(0.2)  # synch to read thread
        indexEnd = self.Can.GetReadArrayIndex(
        ) - 40  # do not catch stop command
        if False != log:
            self.Can.Logger.Info("indexEnd: " + str(indexEnd))
        return [indexStart, indexEnd]

    """
    Compare collected streaming data with 3dimensional tube
    """

    def streamingValueCompare(self, array1, array2, array3, middle1,
                              tolerance1, middle2, tolerance2, middle3,
                              tolerance3, fCbfRecalc):
        samplingPoints1 = len(array1)
        samplingPoints2 = len(array2)
        samplingPoints3 = len(array3)
        samplingPoints = samplingPoints1
        if (samplingPoints2 > samplingPoints):
            samplingPoints = samplingPoints2
        if (samplingPoints3 > samplingPoints):
            samplingPoints = samplingPoints3
        self.Can.Logger.Info("Received Sampling Points: " +
                             str(samplingPoints))
        self.assertGreater(samplingPoints, 0)
        for i in range(0, samplingPoints):
            if 0 != samplingPoints1:
                self.assertGreaterEqual(middle1 + tolerance1,
                                        fCbfRecalc(array1[i]))
                self.assertLessEqual(middle1 - tolerance1,
                                     fCbfRecalc(array1[i]))
            if 0 != samplingPoints2:
                self.assertGreaterEqual(middle2 + tolerance2,
                                        fCbfRecalc(array2[i]))
                self.assertLessEqual(middle2 - tolerance2,
                                     fCbfRecalc(array2[i]))
            if 0 != samplingPoints3:
                self.assertGreaterEqual(middle3 + tolerance3,
                                        fCbfRecalc(array3[i]))
                self.assertLessEqual(middle3 - tolerance3,
                                     fCbfRecalc(array3[i]))

    """
    Compare collected streaming data with 1dimensional tube
    """

    def streamingValueCompareSignal(self, array, testSignal):
        self.Can.Logger.Info(
            "Comparing to Test Signal(Test Signal/Received Signal)")
        for i in range(0, len(testSignal)):
            self.Can.Logger.Info("Point " + str(i) + ": " +
                                 str(testSignal[i]) + "/" + str(array[i]))
        self.assertEqual(len(array), len(testSignal))
        for i in range(0, len(testSignal)):
            self.assertEqual(array[i], testSignal[i])

    """
    Compare calculated signal indicators of collected data e.g. Signal to noice ratio (SNR)
    """

    def siginalIndicatorCheck(self, name, statistic, quantil1, quantil25,
                              medianL, medianH, quantil75, quantil99, variance,
                              skewness, SNR):
        self.Can.Logger.Info(
            "____________________________________________________")
        self.Can.Logger.Info("Singal Indicator Check: " + name)
        self.Can.Logger.Info(
            "Quantil1%, quantil25%, Median Low, Median High, Quantil75%, Quantil99%, Variance, Skewness, SNR"
        )
        self.Can.Logger.Info("Limit - Quantil 1%: " + str(quantil1))
        self.Can.Logger.Info("Limit - Quantil 25%: " + str(quantil25))
        self.Can.Logger.Info("Limit - Median Low: " + str(medianL))
        self.Can.Logger.Info("Limit - Median High: " + str(medianH))
        self.Can.Logger.Info("Limit - Quantil 75%: " + str(quantil75))
        self.Can.Logger.Info("Limit - Quantil 99%: " + str(quantil99))
        self.Can.Logger.Info("Limit - Variance: " + str(variance))
        self.Can.Logger.Info("Limit - Skewness: " + str(skewness))
        self.Can.Logger.Info("Limit - SNR: " + str(SNR))
        self.assertGreaterEqual(statistic["Quantil1"], quantil1)
        self.assertGreaterEqual(statistic["Quantil25"], quantil25)
        self.assertGreaterEqual(statistic["Median"], medianL)
        self.assertLessEqual(statistic["Median"], medianH)
        self.assertLessEqual(statistic["Quantil75"], quantil75)
        self.assertLessEqual(statistic["Quantil99"], quantil99)
        self.assertLessEqual(statistic["Variance"], variance)
        self.assertLessEqual(abs(statistic["Skewness"]), abs(skewness))
        SignalSNR = 20 * math.log(
            (statistic["StandardDeviation"] / AdcMax), 10)
        self.assertGreaterEqual(abs(SignalSNR), abs(SNR))
        self.Can.Logger.Info(
            "____________________________________________________")

    """
    Write Page by value
    """

    def vEepromWritePage(self, iPage, value):
        au8Content = [value] * 4
        timeStamp = self.Can.getTimeMs()
        for offset in range(0, 256, 4):
            au8Payload = [iPage, 0xFF & offset, 4, 0] + au8Content
            self.Can.cmdSend(MyToolItNetworkNr["STH1"],
                             MyToolItBlock["EEPROM"], MyToolItEeprom["Write"],
                             au8Payload)
        self.Can.Logger.Info("Page Write Time: " +
                             str(self.Can.getTimeMs() - timeStamp) + "ms")

    """
    Read page and check content
    """

    def vEepromReadPage(self, iPage, value):
        timeStamp = self.Can.getTimeMs()
        for offset in range(0, 256, 4):
            au8Payload = [iPage, 0xFF & offset, 4, 0, 0, 0, 0, 0]
            index = self.Can.cmdSend(MyToolItNetworkNr["STH1"],
                                     MyToolItBlock["EEPROM"],
                                     MyToolItEeprom["Read"], au8Payload)
            dataReadBack = self.Can.getReadMessageData(index)
            for dataByte in dataReadBack[4:]:
                self.assertEqual(dataByte, value)
        self.Can.Logger.Info("Page Read Time: " +
                             str(self.Can.getTimeMs() - timeStamp) + "ms")

    """
    Reset the Silicion Laps Adapter
    """

    def vSilabsAdapterReset(self):
        self.Can.Logger.Info("Reset Adapter " + self.sAdapterSerialNo)
        sSystemCall = self.sSilabsCommander + " adapter reset "
        sSystemCall += "--serialno " + self.sAdapterSerialNo
        sSystemCall += (">>" + sLogLocation + "AdapterReset.txt")
        if os.name == 'nt':
            sSystemCall = sSystemCall.replace("/", "\\")
            os.system(sSystemCall)
        # for mac and linux(here, os.name is 'posix')
        else:
            os.system(sSystemCall)
        time.sleep(4)

    """
    Duration Test of Tripple Axis Sensor: Multiple "Turn On -> Meassure -> Off"
    """

    def test0100TrippleAxisSensorOnOff(self):
        uLoopRuns = 10
        for _i in range(0, uLoopRuns):
            index = self.Can.singleValueCollect(
                MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"],
                1, 1, 1)
            [val1, val2, val3
             ] = self.Can.singleValueArray(MyToolItNetworkNr["STH1"],
                                           MyToolItStreaming["Acceleration"],
                                           1, 1, 1, index)
            self.Can.ValueLog(val1, val2, val3, self.tSthLimits.fAcceleration,
                              "Acc", "g")

            self.singleValueCompare(val1, val2, val3,
                                    self.tSthLimits.iAdcAccXMiddle,
                                    self.tSthLimits.iAdcAccXTolerance,
                                    self.tSthLimits.iAdcAccYMiddle,
                                    self.tSthLimits.iAdcAccYTolerance,
                                    self.tSthLimits.iAdcAccZMiddle,
                                    self.tSthLimits.iAdcAccZTolerance,
                                    self.tSthLimits.fAcceleration)


if __name__ == "__main__":
    sLogLocation = sys.argv[1]
    sLogFile = sys.argv[2]
    sVersion = sys.argv[3]
    if '/' != sLogLocation[-1]:
        sLogLocation += '/'
    sLogFileLocation = sLogLocation + sLogFile
    sDirName = os.path.dirname(sLogFileLocation)
    sys.path.append(sDirName)

    if not os.path.exists(sDirName):
        os.makedirs(sDirName)
    with open(sLogFileLocation, "w") as f:
        runner = unittest.TextTestRunner(f)
        unittest.main(argv=['first-arg-is-ignored'], testRunner=runner)
