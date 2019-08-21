import unittest
import sys
import os

# Required to add peakcan
dir_name = os.path.dirname('')
sys.path.append(dir_name)
file_path = '../'
dir_name = os.path.dirname(file_path)
sys.path.append(dir_name)

import PeakCanFd
import math
from MyToolItNetworkNumbers import MyToolItNetworkNr
import time
from MyToolItSth import TestConfig, SthModule, SleepTime, SthErrorWord, SthStateWord
from MyToolItCommands import *
from SthLimits import *
from testSignal import *

log_file = 'TestStu.txt'
log_location = '../../Logs/STH/'


def fVoltageBattery(x):
    if(0 < x):
        voltage = ((10.5 * 3300) / (16 * 4096 * 1000 * x))
    else:
        voltage = 0
    return voltage


def fAdcRawDat(x):
    return x


def fAcceleration(x):
    return ((x / AdcMax - 1 / 2) * AccelerationToAccGravitity)


def fAccelerationSingle(x):
    return (100 * (x / 4096 - 1 / 2))


def fCheckFunctionNone(statistics):
    pass


class TestSth(unittest.TestCase):

    def setUp(self):
        print("TestCase: ", self._testMethodName)
        self.fileName = log_location + self._testMethodName + ".txt"
        self.fileNameError = log_location + "Error_" + self._testMethodName + ".txt"
        self.PeakCan = PeakCanFd.PeakCanFd(PeakCanFd.PCAN_BAUD_1M, self.fileName, self.fileNameError, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], AdcPrescalerReset, AdcAcquisitionTimeReset, AdcAcquisitionOverSamplingRateReset)
        self.PeakCan.Logger.Info("TestCase: " + str(self._testMethodName))
        self.PeakCan.CanTimeStampStart(self._resetStu()["CanTime"])
        self.PeakCan.Logger.Info("Connect to STH")
        self.PeakCan.BlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])
        self._resetSth()
        self.PeakCan.Logger.Info("Connect to STH")
        self.PeakCan.BlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])
        self.bError = False
        self.PeakCan.Logger.Info("STU BlueTooth Address: " + hex(self.PeakCan.BlueToothAddress(MyToolItNetworkNr["STU1"])))
        self.PeakCan.Logger.Info("STH BlueTooth Address: " + hex(self.PeakCan.BlueToothAddress(MyToolItNetworkNr["STH1"])))
        self._statusWords()
        temp = self._SthAdcTemp()
        self.assertGreaterEqual(TempInternalMax, temp)
        self.assertLessEqual(TempInternalMin, temp)
        self._SthWDog()
        print("Start")
        self.PeakCan.Logger.Info("_______________________________________________________________________________________________________________")
        self.PeakCan.Logger.Info("Start")

    def tearDown(self):
        self.PeakCan.Logger.Info("Fin")
        self.PeakCan.Logger.Info("_______________________________________________________________________________________________________________")
        if False == self.PeakCan.bError:
            self._streamingStop()
            self._BlueToothStatistics()
            ReceiveFailCounter = self._RoutingInformation()
            self._statusWords()
            temp = self._SthAdcTemp()
            self.assertGreaterEqual(TempInternalMax, temp)
            self.assertLessEqual(TempInternalMin, temp)
            self.PeakCan.Logger.Info("Test Time End Time Stamp")
            self.PeakCan.BlueToothDisconnect(MyToolItNetworkNr["STU1"])
        else:
            ReceiveFailCounter = 0
        if(0 < ReceiveFailCounter):
            self.bError = True
        if False != self.PeakCan.bError:
            self.bError = True
        self.PeakCan.__exit__()
        if self._test_has_failed():
            if os.path.isfile(self.fileNameError) and os.path.isfile(self.fileName):
                os.remove(self.fileNameError)
            if os.path.isfile(self.fileName):
                os.rename(self.fileName, self.fileNameError)

    def _test_has_failed(self):
        for _method, error in self._outcome.errors:
            if error:
                return True
        if True == self.bError:
            return True
        return False

    def _resetStu(self, retries=5, log=True):
        return self.PeakCan.cmdReset(MyToolItNetworkNr["STU1"], retries=retries, log=log)

    def _resetSth(self, retries=5, log=True):
        return self.PeakCan.cmdReset(MyToolItNetworkNr["STH1"], retries=retries, log=log)
        
    def _SthAdcTemp(self):
        ret = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["Temp"], 1, AdcReference["1V25"], log=False)
        result = float(messageWordGet(ret[4:]))
        result /= 1000
        self.PeakCan.Logger.Info("Temperature(Chip): " + str(result) + "°C") 
        self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["None"], CalibMeassurementTypeNr["Temp"], 1, AdcReference["VDD"], log=False, bReset=True)
        return result
    
    def _SthWDog(self):
        WdogCounter = messageWordGet(self.PeakCan.statisticalData(MyToolItNetworkNr["STH1"], MyToolItStatData["Wdog"])[:4])
        self.PeakCan.Logger.Info("WatchDog Counter: " + str(WdogCounter))
        return WdogCounter 
        
    def _statusWords(self):
        ErrorWord = SthErrorWord()
        psw0 = self.PeakCan.statusWord0(MyToolItNetworkNr["STH1"])
        self.PeakCan.Logger.Info("STH Status Word: " + hex(psw0))
        psw0 = self.PeakCan.statusWord0(MyToolItNetworkNr["STU1"])
        self.PeakCan.Logger.Info("STU Status Word: " + hex(psw0))
        ErrorWord.asword = self.PeakCan.statusWord1(MyToolItNetworkNr["STH1"])
        if True == ErrorWord.b.bAdcOverRun:
            self.bError = True
        self.PeakCan.Logger.Info("STH bError Word: " + hex(ErrorWord.asword))
        ErrorWord.asword = self.PeakCan.statusWord1(MyToolItNetworkNr["STU1"])
        self.PeakCan.Logger.Info("STU bError Word: " + hex(ErrorWord.asword))

    def _streamingStop(self):
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"])

    def _BlueToothStatistics(self):
        SendCounter = self.PeakCan.BlueToothCmd(MyToolItNetworkNr["STH1"], SystemCommandBlueTooth["SendCounter"])
        self.PeakCan.Logger.Info("BlueTooth Send Counter(STH1): " + str(SendCounter))
        Rssi = self.PeakCan.BlueToothRssi(MyToolItNetworkNr["STH1"])
        self.PeakCan.Logger.Info("BlueTooth Rssi(STH1): " + str(Rssi) + "dBm")
        SendCounter = self.PeakCan.BlueToothCmd(MyToolItNetworkNr["STU1"], SystemCommandBlueTooth["SendCounter"])
        self.PeakCan.Logger.Info("BlueTooth Send Counter(STU1): " + str(SendCounter))
        ReceiveCounter = self.PeakCan.BlueToothCmd(MyToolItNetworkNr["STU1"], SystemCommandBlueTooth["ReceiveCounter"])
        self.PeakCan.Logger.Info("BlueTooth Receive Counter(STU1): " + str(ReceiveCounter))
        Rssi = self.PeakCan.BlueToothRssi(MyToolItNetworkNr["STU1"])
        self.PeakCan.Logger.Info("BlueTooth Rssi(STU1): " + str(Rssi) + "dBm")

    def _RoutingInformationSthSend(self):
        SendCounter = self.PeakCan.RoutingInformationCmd(MyToolItNetworkNr["STH1"], SystemCommandRouting["SendCounter"], MyToolItNetworkNr["STU1"])
        self.PeakCan.Logger.Info("STH1 - Send Counter(Port STU1): " + str(SendCounter))
        SendCounter = self.PeakCan.RoutingInformationCmd(MyToolItNetworkNr["STH1"], SystemCommandRouting["SendFailCounter"], MyToolItNetworkNr["STU1"])
        self.PeakCan.Logger.Info("STH1 - Send Fail Counter(Port STU1): " + str(SendCounter))
        SendCounter = self.PeakCan.RoutingInformationCmd(MyToolItNetworkNr["STH1"], SystemCommandRouting["SendLowLevelByteCounter"], MyToolItNetworkNr["STU1"])
        self.PeakCan.Logger.Info("STH1 - Send Byte Counter(Port STU1): " + str(SendCounter))

    def _RoutingInformationSthReceive(self):
        ReceiveCounter = self.PeakCan.RoutingInformationCmd(MyToolItNetworkNr["STH1"], SystemCommandRouting["ReceiveCounter"], MyToolItNetworkNr["STU1"])
        self.PeakCan.Logger.Info("STH1 - Receive Counter(Port STU1): " + str(ReceiveCounter))
        ReceiveFailCounter = self.PeakCan.RoutingInformationCmd(MyToolItNetworkNr["STH1"], SystemCommandRouting["ReceiveFailCounter"], MyToolItNetworkNr["STU1"])
        self.PeakCan.Logger.Info("STH1 - Receive Fail Counter(Port STU1): " + str(ReceiveFailCounter))
        ReceiveCounter = self.PeakCan.RoutingInformationCmd(MyToolItNetworkNr["STH1"], SystemCommandRouting["ReceiveLowLevelByteCounter"], MyToolItNetworkNr["STU1"])
        self.PeakCan.Logger.Info("STH1 - Receive Byte Counter(Port STU1): " + str(ReceiveCounter))
        return ReceiveFailCounter

    def _RoutingInformationSth(self):
        self._RoutingInformationSthSend()
        ReceiveFailCounter = self._RoutingInformationSthReceive()
        return ReceiveFailCounter

    def _RoutingInformationStuPortSpuSend(self):
        SendCounter = self.PeakCan.RoutingInformationCmd(MyToolItNetworkNr["STU1"], SystemCommandRouting["SendCounter"], MyToolItNetworkNr["SPU1"])
        self.PeakCan.Logger.Info("STU1 - Send Counter(Port SPU1): " + str(SendCounter))
        SendCounter = self.PeakCan.RoutingInformationCmd(MyToolItNetworkNr["STU1"], SystemCommandRouting["SendFailCounter"], MyToolItNetworkNr["SPU1"])
        self.PeakCan.Logger.Info("STU1 - Send Fail Counter(Port SPU1): " + str(SendCounter))
        SendCounter = self.PeakCan.RoutingInformationCmd(MyToolItNetworkNr["STU1"], SystemCommandRouting["SendLowLevelByteCounter"], MyToolItNetworkNr["SPU1"])
        self.PeakCan.Logger.Info("STU1 - Send Byte Counter(Port SPU1): " + str(SendCounter))

    def _RoutingInformationStuPortSpuReceive(self):
        ReceiveCounter = self.PeakCan.RoutingInformationCmd(MyToolItNetworkNr["STU1"], SystemCommandRouting["ReceiveCounter"], MyToolItNetworkNr["SPU1"])
        self.PeakCan.Logger.Info("STU1 - Receive Counter(Port SPU1): " + str(ReceiveCounter))
        ReceiveFailCounter = self.PeakCan.RoutingInformationCmd(MyToolItNetworkNr["STU1"], SystemCommandRouting["ReceiveFailCounter"], MyToolItNetworkNr["SPU1"])
        self.PeakCan.Logger.Info("STU1 - Receive Fail Counter(Port SPU1): " + str(ReceiveFailCounter))
        ReceiveCounter = self.PeakCan.RoutingInformationCmd(MyToolItNetworkNr["STU1"], SystemCommandRouting["ReceiveLowLevelByteCounter"], MyToolItNetworkNr["SPU1"])
        self.PeakCan.Logger.Info("STU1 - Receive Byte Counter(Port SPU1): " + str(ReceiveCounter))
        return ReceiveFailCounter

    def _RoutingInformationStuPortSpu(self):
        self._RoutingInformationStuPortSpuSend()
        ReceiveFailCounter = self._RoutingInformationStuPortSpuReceive()
        return ReceiveFailCounter

    def _RoutingInformationStuPortSthSend(self):
        SendCounter = self.PeakCan.RoutingInformationCmd(MyToolItNetworkNr["STU1"], SystemCommandRouting["SendCounter"], MyToolItNetworkNr["STH1"])
        self.PeakCan.Logger.Info("STU1 - Send Counter(Port STH1): " + str(SendCounter))
        SendCounter = self.PeakCan.RoutingInformationCmd(MyToolItNetworkNr["STU1"], SystemCommandRouting["SendFailCounter"], MyToolItNetworkNr["STH1"])
        self.PeakCan.Logger.Info("STU1 - Send Fail Counter(Port STH1): " + str(SendCounter))
        SendCounter = self.PeakCan.RoutingInformationCmd(MyToolItNetworkNr["STU1"], SystemCommandRouting["SendLowLevelByteCounter"], MyToolItNetworkNr["STH1"])
        self.PeakCan.Logger.Info("STU1 - Send Byte Counter(Port STH1): " + str(SendCounter))

    def _RoutingInformationStuPortSthReceive(self):
        ReceiveCounter = self.PeakCan.RoutingInformationCmd(MyToolItNetworkNr["STU1"], SystemCommandRouting["ReceiveCounter"], MyToolItNetworkNr["STH1"])
        self.PeakCan.Logger.Info("STU1 - Receive Counter(Port STH1): " + str(ReceiveCounter))
        ReceiveFailCounter = self.PeakCan.RoutingInformationCmd(MyToolItNetworkNr["STU1"], SystemCommandRouting["ReceiveFailCounter"], MyToolItNetworkNr["STH1"])
        self.PeakCan.Logger.Info("STU1 - Receive Fail Counter(Port STH1): " + str(ReceiveFailCounter))
        ReceiveCounter = self.PeakCan.RoutingInformationCmd(MyToolItNetworkNr["STU1"], SystemCommandRouting["ReceiveLowLevelByteCounter"], MyToolItNetworkNr["STH1"])
        self.PeakCan.Logger.Info("STU1 - Receive Byte Counter(Port STH1): " + str(ReceiveCounter))
        return ReceiveFailCounter

    def _RoutingInformationStuPortSth(self):
        self._RoutingInformationStuPortSthSend()
        ReceiveFailCounter = self._RoutingInformationStuPortSthReceive()
        return ReceiveFailCounter

    def _RoutingInformation(self):
        ReceiveFailCounter = self._RoutingInformationSth()
        ReceiveFailCounter += self._RoutingInformationStuPortSth()
        ReceiveFailCounter += self._RoutingInformationStuPortSpu()
        return ReceiveFailCounter

    def singleValueCompare(self, array1, array2, array3, middle1, tolerance1, middle2, tolerance2, middle3, tolerance3, fCbfRecalc):
        if 0 < len(array1):
            self.assertGreaterEqual(middle1 + tolerance1, fCbfRecalc(array1[0]))
            self.assertLessEqual(middle1 - tolerance1, fCbfRecalc(array1[0]))
        if 0 < len(array2):
            self.assertGreaterEqual(middle2 + tolerance2, fCbfRecalc(array2[0]))
            self.assertLessEqual(middle2 - tolerance2, fCbfRecalc(array2[0]))
        if 0 < len(array3):
            self.assertGreaterEqual(middle3 + tolerance3, fCbfRecalc(array3[0]))
            self.assertLessEqual(middle3 - tolerance3, fCbfRecalc(array3[0]))  
        
    """
    Config ADC and determine correct sampling rate
    """

    def SamplingRate(self, prescaler, acquisitionTime, overSamplingRate, adcRef, b1=1, b2=0, b3=0, runTime=StreamingStandardTestTimeMs, compare=True, compareRate=True, log=True, startupTime=StreamingStartupTimeMs):
        Settings = self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], prescaler, acquisitionTime, overSamplingRate, adcRef, log=log)[1:]
        self.assertEqual(prescaler, Settings[0])
        self.assertEqual(acquisitionTime, Settings[1])
        self.assertEqual(overSamplingRate, Settings[2])
        self.assertEqual(adcRef, Settings[3])
        calcRate = calcSamplingRate(prescaler, acquisitionTime, overSamplingRate)
        if False != log:
            self.PeakCan.Logger.Info("Start sending package")
        dataSets = self.PeakCan.Can20DataSet(b1, b2, b3)
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], dataSets, b1, b2, b3, runTime, log=log, StartupTimeMs=startupTime)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], dataSets, b1, b2, b3, indexStart, indexEnd)
        self.PeakCan.ReadThreadReset()
        samplingPoints = self.PeakCan.samplingPoints(array1, array2, array3)
        if False != log:
            samplingPoints = self.PeakCan.samplingPoints(array1, array2, array3)
            self.PeakCan.Logger.Info("Running Time: " + str(runTime) + "ms")
            if False != startupTime:
                self.PeakCan.Logger.Info("Startup Time: " + str(startupTime) + "ms")
            self.PeakCan.Logger.Info("Assumed Sampling Points/s: " + str(calcRate))
            samplingRateDet = 1000 * samplingPoints / (runTime)
            self.PeakCan.Logger.Info("Determined Sampling Points/s: " + str(samplingRateDet))
            self.PeakCan.Logger.Info("Difference to Assumed Sampling Points: " + str((100 * samplingRateDet - calcRate) / calcRate) + "%")
            self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "")
        ratM = AdcVRefValuemV[AdcReference["VDD"]] / AdcVRefValuemV[adcRef]
        ratT = 1
        if adcRef != AdcReference["VDD"]:
            ratT = SamplingRateVfsToleranceRation
        if False != compare:
            if(1 != ratM):
                self.PeakCan.Logger.Info("Compare Ration to compensate not AVDD: " + str(ratM))
            adcXMiddle = ratM * AdcRawMiddleX
            adcYMiddle = ratM * AdcRawMiddleY
            adcZMiddle = ratM * AdcRawMiddleZ
            adcXTol = AdcRawToleranceX * ratT
            adcYTol = AdcRawToleranceY * ratT
            adcZTol = AdcRawToleranceZ * ratT
            if(16 > AdcOverSamplingRateReverse[overSamplingRate]):
                self.PeakCan.Logger.Info("Maximum ADC Value: " + str(AdcMax / 2 ** (5 - AdcOverSamplingRateReverse[overSamplingRate])))
                adcXMiddle = adcXMiddle / 2 ** (5 - AdcOverSamplingRateReverse[overSamplingRate])
                adcYMiddle = adcYMiddle / 2 ** (5 - AdcOverSamplingRateReverse[overSamplingRate])
                adcZMiddle = adcZMiddle / 2 ** (5 - AdcOverSamplingRateReverse[overSamplingRate])
            else:
                self.PeakCan.Logger.Info("Maximum ADC Value: " + str(AdcMax))
            self.streamingValueCompare(array1, array2, array3, adcXMiddle, adcXTol, adcYMiddle, adcYTol, adcZMiddle, adcZTol, fAdcRawDat)
        if False != compareRate:
            self.assertLess(runTime / 1000 * calcRate * SamplingToleranceLow, samplingPoints)
            self.assertGreater(runTime / 1000 * calcRate * SamplingToleranceHigh, samplingPoints)
        result = {"SamplingRate" : calcRate, "Value1" : array1, "Value2" : array2, "Value3" : array3}
        return result

    def TurnOffLed(self):
        self.PeakCan.Logger.Info("Turn Off LED")
        cmd = self.PeakCan.CanCmd(MyToolItBlock["Configuration"], MyToolItConfiguration["Hmi"], 1, 0)
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [129, 1, 2, 0, 0, 0, 0, 0])
        self.PeakCan.WriteFrameWaitAckRetries(message)

    def TurnOnLed(self):
        self.PeakCan.Logger.Info("Turn On LED")
        cmd = self.PeakCan.CanCmd(MyToolItBlock["Configuration"], MyToolItConfiguration["Hmi"], 1, 0)
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [129, 1, 1, 0, 0, 0, 0, 0])
        self.PeakCan.WriteFrameWaitAckRetries(message)  
        
    """
    Test single battery/Acc meassurement
    """

    """
    Test Signal
    """

    def streamingTestSignalCollect(self, sender, receiver, subCmd, testSignal, testModule, value, dataSets, b1, b2, b3, testTimeMs, log=True):
        self.PeakCan.Logger.Info("Request Test Signal: " + str(testSignal))
        self.PeakCan.Logger.Info("Test Module: " + str(testModule))
        self.PeakCan.Logger.Info("Test Value: " + str(testModule))
        accFormat = AtvcFormat()
        accFormat.asbyte = 0
        accFormat.b.bStreaming = 1
        accFormat.b.bNumber1 = b1
        accFormat.b.bNumber2 = b2
        accFormat.b.bNumber3 = b3
        accFormat.b.u3DataSets = dataSets
        cmd = self.PeakCan.CanCmd(MyToolItBlock["Streaming"], subCmd, 1, 0)
        message = self.PeakCan.CanMessage20(cmd, sender, receiver, [accFormat.asbyte])
        if False != log:
            self.PeakCan.Logger.Info("Start sending package")
        self.PeakCan.WriteFrameWaitAckRetries(message, retries=1)
        cmd = self.PeakCan.CanCmd(MyToolItBlock["Test"], MyToolItTest["Signal"], 1, 0)
        message = self.PeakCan.CanMessage20(cmd, sender, receiver, [testSignal, testModule, 0, 0, 0 , 0, 0xFF & value, 0xFF & (value >> 8)])
        if False != log:
            self.PeakCan.Logger.Info("Start sending test signal")
        self.PeakCan.WriteFrame(message)
        time.sleep(0.5)
        indexStart = self.PeakCan.GetReadArrayIndex()
        timeEnd = self.PeakCan.getTimeMs() + testTimeMs
        if False != log:
            self.PeakCan.Logger.Info("indexStart: " + str(indexStart))
        while self.PeakCan.getTimeMs() < timeEnd:
            pass
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], subCmd)
        time.sleep(0.2)  # synch to read thread
        indexEnd = self.PeakCan.GetReadArrayIndex() - 40  # do not catch stop command
        if False != log:
            self.PeakCan.Logger.Info("indexEnd: " + str(indexEnd))
        return[indexStart, indexEnd]

    def streamingValueCompare(self, array1, array2, array3, middle1, tolerance1, middle2, tolerance2, middle3, tolerance3, fCbfRecalc):
        samplingPoints1 = len(array1)
        samplingPoints2 = len(array2)
        samplingPoints3 = len(array3)
        samplingPoints = samplingPoints1
        if(samplingPoints2 > samplingPoints):
            samplingPoints = samplingPoints2
        if(samplingPoints3 > samplingPoints):
            samplingPoints = samplingPoints3
        self.PeakCan.Logger.Info("Received Sampling Points: " + str(samplingPoints))
        for i in range(0, samplingPoints):
            if 0 != samplingPoints1:
                self.assertGreaterEqual(middle1 + tolerance1, fCbfRecalc(array1[i]))
                self.assertLessEqual(middle1 - tolerance1, fCbfRecalc(array1[i]))
            if 0 != samplingPoints2:
                self.assertGreaterEqual(middle2 + tolerance2, fCbfRecalc(array2[i]))
                self.assertLessEqual(middle2 - tolerance2, fCbfRecalc(array2[i]))
            if 0 != samplingPoints3:
                self.assertGreaterEqual(middle3 + tolerance3, fCbfRecalc(array3[i]))
                self.assertLessEqual(middle3 - tolerance3, fCbfRecalc(array3[i]))

    def streamingValueCompareSignal(self, array, testSignal):
        self.PeakCan.Logger.Info("Comparing to Test Signal(Test Signal/Received Signal)")
        for i in range(0, len(testSignal)):
            self.PeakCan.Logger.Info("Point " + str(i) + ": " + str(testSignal[i]) + "/" + str(array[i]))
        self.assertEqual(len(array), len(testSignal))
        for i in range(0, len(testSignal)):
            self.assertEqual(array[i], testSignal[i])

    def streamingValueStatisticsArithmeticAverage(self, sortArray):
        arithmeticAverage = 0
        if None != arithmeticAverage:
            for Value in sortArray:
                arithmeticAverage += Value
            arithmeticAverage /= len(sortArray)
        return arithmeticAverage

    def streamingValueStatisticsSort(self, sortArray):
        if None != sortArray:
            sortArray.sort()
        return sortArray

    def streamingValueStatisticsQuantile(self, sortArray, quantil):
        if None != sortArray:
            sortArray.sort()
            samplingPoints = len(sortArray)
            if(samplingPoints % 2 == 0):
                quantilSet = sortArray[int(samplingPoints * quantil)]
                quantilSet += sortArray[int(samplingPoints * quantil - 1)]
                quantilSet /= 2
            else:
                quantilSet = sortArray[int(quantil * samplingPoints)]
        else:
            quantilSet = None
        return quantilSet

    def streamingValueStatisticsVariance(self, sortArray):
        variance = 0
        arithmeticAverage = self.streamingValueStatisticsArithmeticAverage(sortArray)
        if None != sortArray:
            for Value in sortArray:
                Value = (Value - arithmeticAverage) ** 2
                variance += Value
            variance /= len(sortArray)
        return variance

    def streamingValueStatisticsMomentOrder(self, sortArray, order):
        momentOrder = 0
        arithmeticAverage = self.streamingValueStatisticsArithmeticAverage(sortArray)
        standardDeviation = self.streamingValueStatisticsVariance(sortArray) ** 0.5
        if None != sortArray:
            for Value in sortArray:
                Value = (Value - arithmeticAverage) / standardDeviation
                Value = Value ** order
                momentOrder += Value
            momentOrder /= len(sortArray)
        return momentOrder

    def streamingValueStatisticsValue(self, sortArray):
        statistics = {}
        statistics["Minimum"] = sortArray[0]
        statistics["Quantil1"] = self.streamingValueStatisticsQuantile(sortArray, 0.01)
        statistics["Quantil5"] = self.streamingValueStatisticsQuantile(sortArray, 0.05)
        statistics["Quantil25"] = self.streamingValueStatisticsQuantile(sortArray, 0.25)
        statistics["Median"] = self.streamingValueStatisticsQuantile(sortArray, 0.5)
        statistics["Quantil75"] = self.streamingValueStatisticsQuantile(sortArray, 0.75)
        statistics["Quantil95"] = self.streamingValueStatisticsQuantile(sortArray, 0.95)
        statistics["Quantil99"] = self.streamingValueStatisticsQuantile(sortArray, 0.99)
        statistics["Maximum"] = sortArray[-1]
        statistics["ArithmeticAverage"] = self.streamingValueStatisticsArithmeticAverage(sortArray)
        statistics["StandardDeviation"] = self.streamingValueStatisticsVariance(sortArray) ** 0.5
        statistics["Variance"] = self.streamingValueStatisticsVariance(sortArray)
        statistics["Skewness"] = self.streamingValueStatisticsMomentOrder(sortArray, 3)
        statistics["Kurtosis"] = self.streamingValueStatisticsMomentOrder(sortArray, 4)
        statistics["Data"] = sortArray
        statistics["InterQuartialRange"] = statistics["Quantil75"] - statistics["Quantil25"]
        statistics["90PRange"] = statistics["Quantil95"] - statistics["Quantil5"]
        statistics["98PRange"] = statistics["Quantil99"] - statistics["Quantil1"]
        statistics["TotalRange"] = sortArray[-1] - sortArray[0]        
        return statistics
    
    def streamingValueStatistics(self, Array1, Array2, Array3):
        sortArray1 = Array1.copy()
        sortArray2 = Array2.copy()
        sortArray3 = Array3.copy()
        sortArray1 = self.streamingValueStatisticsSort(sortArray1)
        sortArray2 = self.streamingValueStatisticsSort(sortArray2)
        sortArray3 = self.streamingValueStatisticsSort(sortArray3)

        statistics = {"Value1" : None, "Value2" : None, "Value3" : None}
        if 0 < len(sortArray1):
            statistics["Value1"] = self.streamingValueStatisticsValue(sortArray1)
        if 0 < len(sortArray2):
            statistics["Value2"] = self.streamingValueStatisticsValue(sortArray2)
        if 0 < len(sortArray3):
            statistics["Value3"] = self.streamingValueStatisticsValue(sortArray3)
        return statistics

    def signalIndicators(self, array1, array2, array3):
        statistics = self.streamingValueStatistics(array1, array2, array3)
        for key, stat in statistics.items():
            if None != stat:
                self.PeakCan.Logger.Info("____________________________________________________")
                self.PeakCan.Logger.Info(key)
                self.PeakCan.Logger.Info("Minimum: " + str(stat["Minimum"]))
                self.PeakCan.Logger.Info("Quantil 1%: " + str(stat["Quantil1"]))
                self.PeakCan.Logger.Info("Quantil 5%: " + str(stat["Quantil5"]))
                self.PeakCan.Logger.Info("Quantil 25%: " + str(stat["Quantil25"]))
                self.PeakCan.Logger.Info("Median: " + str(stat["Median"]))
                self.PeakCan.Logger.Info("Quantil 75%: " + str(stat["Quantil75"]))
                self.PeakCan.Logger.Info("Quantil 95%: " + str(stat["Quantil95"]))
                self.PeakCan.Logger.Info("Quantil 99%: " + str(stat["Quantil99"]))
                self.PeakCan.Logger.Info("Maximum: " + str(stat["Maximum"]))
                self.PeakCan.Logger.Info("Arithmetic Average: " + str(stat["ArithmeticAverage"]))
                self.PeakCan.Logger.Info("Standard Deviation: " + str(stat["StandardDeviation"]))
                self.PeakCan.Logger.Info("Variance: " + str(stat["Variance"]))
                self.PeakCan.Logger.Info("Skewness: " + str(stat["Skewness"]))
                self.PeakCan.Logger.Info("Kurtosis: " + str(stat["Kurtosis"]))
                self.PeakCan.Logger.Info("Inter Quartial Range: " + str(stat["InterQuartialRange"]))
                self.PeakCan.Logger.Info("90%-Range: " + str(stat["90PRange"]))
                self.PeakCan.Logger.Info("98%-Range: " + str(stat["98PRange"]))
                self.PeakCan.Logger.Info("Total Range: " + str(stat["TotalRange"]))
                SNR = 20 * math.log((stat["StandardDeviation"] / AdcMax), 10)
                self.PeakCan.Logger.Info("SNR: " + str(SNR))
                self.PeakCan.Logger.Info("____________________________________________________")
        return statistics

    def siginalIndicatorCheck(self, name, statistic, quantil1, quantil25, medianL, medianH, quantil75, quantil99, variance, skewness, SNR):
        self.PeakCan.Logger.Info("____________________________________________________")
        self.PeakCan.Logger.Info("Singal Indicator Check: " + name)
        self.PeakCan.Logger.Info("Quantil1%, quantil25%, Median Low, Median High, Quantil75%, Quantil99%, Variance, Skewness, SNR")
        self.PeakCan.Logger.Info("Limit - Quantil 1%: " + str(quantil1))
        self.PeakCan.Logger.Info("Limit - Quantil 25%: " + str(quantil25))
        self.PeakCan.Logger.Info("Limit - Median Low: " + str(medianL))
        self.PeakCan.Logger.Info("Limit - Median High: " + str(medianH))
        self.PeakCan.Logger.Info("Limit - Quantil 75%: " + str(quantil75))
        self.PeakCan.Logger.Info("Limit - Quantil 99%: " + str(quantil99))
        self.PeakCan.Logger.Info("Limit - Variance: " + str(variance))
        self.PeakCan.Logger.Info("Limit - Skewness: " + str(skewness))
        self.PeakCan.Logger.Info("Limit - SNR: " + str(SNR))
        self.assertGreaterEqual(statistic["Quantil1"], quantil1)
        self.assertGreaterEqual(statistic["Quantil25"], quantil25)
        self.assertGreaterEqual(statistic["Median"], medianL)
        self.assertLessEqual(statistic["Median"], medianH)
        self.assertLessEqual(statistic["Quantil75"], quantil75)
        self.assertLessEqual(statistic["Quantil99"], quantil99)
        self.assertLessEqual(statistic["Variance"], variance)
        self.assertLessEqual(abs(statistic["Skewness"]), abs(skewness))
        SignalSNR = 20 * math.log((statistic["StandardDeviation"] / AdcMax), 10)
        self.assertGreaterEqual(abs(SignalSNR), abs(SNR))
        self.PeakCan.Logger.Info("____________________________________________________")

    """
    Test Acknowledgement from STH. Write message and check identifier to be ack (No bError)
    """

    def test0001Ack(self):
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 1, 0)
        expectedData = ActiveState()
        expectedData.asbyte = 0
        expectedData.b.u2NodeState = Node["Application"]
        expectedData.b.u3NetworkState = NetworkState["Operating"]
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [expectedData.asbyte])
        self.PeakCan.Logger.Info("Write Message")
        self.PeakCan.WriteFrame(msg)
        self.PeakCan.Logger.Info("Wait 200ms")
        time.sleep(0.2)
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 0, 0)
        msgAckExpected = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["STH1"], MyToolItNetworkNr["SPU1"], [0])
        self.PeakCan.Logger.Info("Send ID: " + hex(msg.ID) + "; Expected ID: " + hex(msgAckExpected.ID) + "; Received ID: " + hex(self.PeakCan.getReadMessage(-1).ID))
        self.PeakCan.Logger.Info("Send Data: " + hex(0) + "; Expected Data: " + hex(expectedData.asbyte) + "; Received Data: " + hex(self.PeakCan.getReadMessage(-1).DATA[0]))
        self.assertEqual(hex(msgAckExpected.ID), hex(self.PeakCan.getReadMessage(-1).ID))
        self.assertEqual(expectedData.asbyte, self.PeakCan.getReadMessage(-1).DATA[0])

    """
    Test Energy Mode 1 - If you like to evaluate power consumption: Please do it manually
    """

    def test0011EnergySaveMode1(self):
        self.PeakCan.Logger.Info("Read out parameters from EEPORM")
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode([SystemCommandBlueTooth["EnergyModeReducedRead"], self.PeakCan.DeviceNr, 0, 0, 0, 0, 0, 0])
        self.PeakCan.Logger.Info("First Read Time Sleep Time1: " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("First Read Time Advertisement Time 1: " + str(timeAdvertisement) + " ms")
        S1B0 = SleepTime["Min"] & 0xFF
        S1B1 = (SleepTime["Min"] >> 8) & 0xFF
        S1B2 = (SleepTime["Min"] >> 16) & 0xFF
        S1B3 = (SleepTime["Min"] >> 24) & 0xFF
        A1B0 = 1000 & 0xFF
        A1B1 = (1000 >> 8) & 0xFF
        Payload = [SystemCommandBlueTooth["EnergyModeReducedWrite"], self.PeakCan.DeviceNr, S1B0, S1B1, S1B2, S1B3, A1B0, A1B1]
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode(Payload)
        self.PeakCan.Logger.Info("First Write Time Sleep Time1(ACK): " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("First Write Time Advertisement Time 1(ACK): " + str(timeAdvertisement) + " ms")
        self.assertEqual(timeReset, SleepTime["Min"])
        self.assertEqual(timeAdvertisement, 1000)
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode([SystemCommandBlueTooth["EnergyModeReducedRead"], self.PeakCan.DeviceNr, 0, 0, 0, 0, 0, 0])
        self.PeakCan.Logger.Info("Read Time Sleep Time1: " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("Read Time Advertisement Time 1: " + str(timeAdvertisement) + " ms")
        self.assertEqual(timeReset, SleepTime["Min"])
        self.assertEqual(timeAdvertisement, 1000)
        self._resetSth()
        self.PeakCan.BlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode([SystemCommandBlueTooth["EnergyModeReducedRead"], self.PeakCan.DeviceNr, 0, 0, 0, 0, 0, 0])
        self.PeakCan.Logger.Info("Read Time Sleep Time1: " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("Read Time Advertisement Time 1: " + str(timeAdvertisement) + " ms")
        self.assertEqual(timeReset, SleepTime["Min"])
        self.assertEqual(timeAdvertisement, 1000)
        # Reset to default values
        self.PeakCan.Logger.Info("Write Time Sleep Time1: " + str(SleepTime["Reset1"]) + " ms")
        self.PeakCan.Logger.Info("Write Time Advertisement Time 1: " + str(SleepTime["AdvertisementReset1"]) + " ms")
        S1B0 = SleepTime["Reset1"] & 0xFF
        S1B1 = (SleepTime["Reset1"] >> 8) & 0xFF
        S1B2 = (SleepTime["Reset1"] >> 16) & 0xFF
        S1B3 = (SleepTime["Reset1"] >> 24) & 0xFF
        A1B0 = SleepTime["AdvertisementReset1"] & 0xFF
        A1B1 = (SleepTime["AdvertisementReset1"] >> 8) & 0xFF
        Payload = [SystemCommandBlueTooth["EnergyModeReducedWrite"], self.PeakCan.DeviceNr, S1B0, S1B1, S1B2, S1B3, A1B0, A1B1]
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode(Payload)
        self.PeakCan.Logger.Info("Write Time Sleep Time1(ACK): " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("Write Time Advertisement Time 1(ACK): " + str(timeAdvertisement) + " ms")
        self.assertEqual(timeReset, SleepTime["Reset1"])
        self.assertEqual(timeAdvertisement, SleepTime["AdvertisementReset1"])
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode([SystemCommandBlueTooth["EnergyModeReducedRead"], self.PeakCan.DeviceNr, 0, 0, 0, 0, 0, 0])
        self.PeakCan.Logger.Info("Read Time Sleep Time1: " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("Read Time Advertisement Time 1: " + str(timeAdvertisement) + " ms")
        self.assertEqual(timeReset, SleepTime["Reset1"])
        self.assertEqual(timeAdvertisement, SleepTime["AdvertisementReset1"])
        self._resetSth()
        self.PeakCan.BlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode([SystemCommandBlueTooth["EnergyModeReducedRead"], self.PeakCan.DeviceNr, 0, 0, 0, 0, 0, 0])
        self.PeakCan.Logger.Info("Read Time Sleep Time1: " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("Read Time Advertisement Time 1: " + str(timeAdvertisement) + " ms")
        self.assertEqual(timeReset, SleepTime["Reset1"])
        self.assertEqual(timeAdvertisement, SleepTime["AdvertisementReset1"])

    """
    Test Energy Mode 2 - If you like to evaluate power consumption: Please do it manually
    """

    def test0012EnergySaveMode2(self):
        self.PeakCan.Logger.Info("Set Energy Mode1 parameters")
        self.PeakCan.Logger.Info("Write EM1 parameters to EEPORM")
        S1B0 = SleepTime["Min"] & 0xFF
        S1B1 = (SleepTime["Min"] >> 8) & 0xFF
        S1B2 = (SleepTime["Min"] >> 16) & 0xFF
        S1B3 = (SleepTime["Min"] >> 24) & 0xFF
        A1B0 = 2000 & 0xFF
        A1B1 = (2000 >> 8) & 0xFF
        Payload = [SystemCommandBlueTooth["EnergyModeLowestWrite"], self.PeakCan.DeviceNr, S1B0, S1B1, S1B2, S1B3, A1B0, A1B1]
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode(Payload)
        self.PeakCan.Logger.Info("First Write Time Sleep Time1(ACK): " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("First Write Time Advertisement Time 1(ACK): " + str(timeAdvertisement) + " ms")
        self.PeakCan.Logger.Info("Doing Energy Mode2 stuff")
        self.PeakCan.Logger.Info("Read out EM2 parameters from EEPORM")
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode([SystemCommandBlueTooth["EnergyModeLowestRead"], self.PeakCan.DeviceNr, 0, 0, 0, 0, 0, 0])
        self.PeakCan.Logger.Info("First Read Time Sleep Time1: " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("First Read Time Advertisement Time 1: " + str(timeAdvertisement) + " ms")
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode(Payload)
        self.PeakCan.Logger.Info("First Write Time Sleep Time1(ACK): " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("First Write Time Advertisement Time 1(ACK): " + str(timeAdvertisement) + " ms")
        self.assertEqual(timeReset, SleepTime["Min"])
        self.assertEqual(timeAdvertisement, 2000)
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode([SystemCommandBlueTooth["EnergyModeLowestRead"], self.PeakCan.DeviceNr, 0, 0, 0, 0, 0, 0])
        self.PeakCan.Logger.Info("Read Time Sleep Time1: " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("Read Time Advertisement Time 1: " + str(timeAdvertisement) + " ms")
        self.assertEqual(timeReset, SleepTime["Min"])
        self.assertEqual(timeAdvertisement, 2000)
        self._resetSth()
        self.PeakCan.BlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode([SystemCommandBlueTooth["EnergyModeLowestRead"], self.PeakCan.DeviceNr, 0, 0, 0, 0, 0, 0])
        self.PeakCan.Logger.Info("Read Time Sleep Time1: " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("Read Time Advertisement Time 1: " + str(timeAdvertisement) + " ms")
        self.assertEqual(timeReset, SleepTime["Min"])
        self.assertEqual(timeAdvertisement, 2000)
        # Reset to default values
        self.PeakCan.Logger.Info("Write Time Sleep Time1: " + str(SleepTime["Reset2"]) + " ms")
        self.PeakCan.Logger.Info("Write Time Advertisement Time 1: " + str(SleepTime["AdvertisementReset2"]) + " ms")
        S1B0 = SleepTime["Reset2"] & 0xFF
        S1B1 = (SleepTime["Reset2"] >> 8) & 0xFF
        S1B2 = (SleepTime["Reset2"] >> 16) & 0xFF
        S1B3 = (SleepTime["Reset2"] >> 24) & 0xFF
        A1B0 = SleepTime["AdvertisementReset2"] & 0xFF
        A1B1 = (SleepTime["AdvertisementReset2"] >> 8) & 0xFF
        Payload = [SystemCommandBlueTooth["EnergyModeLowestWrite"], self.PeakCan.DeviceNr, S1B0, S1B1, S1B2, S1B3, A1B0, A1B1]
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode(Payload)
        self.PeakCan.Logger.Info("Write Time Sleep Time1(ACK): " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("Write Time Advertisement Time 1(ACK): " + str(timeAdvertisement) + " ms")
        self.assertEqual(timeReset, SleepTime["Reset2"])
        self.assertEqual(timeAdvertisement, SleepTime["AdvertisementReset2"])
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode([SystemCommandBlueTooth["EnergyModeLowestRead"], self.PeakCan.DeviceNr, 0, 0, 0, 0, 0, 0])
        self.PeakCan.Logger.Info("Read Time Sleep Time1: " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("Read Time Advertisement Time 1: " + str(timeAdvertisement) + " ms")
        self.assertEqual(timeReset, SleepTime["Reset2"])
        self.assertEqual(timeAdvertisement, SleepTime["AdvertisementReset2"])
        self._resetSth()
        self.PeakCan.BlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode([SystemCommandBlueTooth["EnergyModeLowestRead"], self.PeakCan.DeviceNr, 0, 0, 0, 0, 0, 0])
        self.PeakCan.Logger.Info("Read Time Sleep Time1: " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("Read Time Advertisement Time 1: " + str(timeAdvertisement) + " ms")
        self.assertEqual(timeReset, SleepTime["Reset2"])
        self.assertEqual(timeAdvertisement, SleepTime["AdvertisementReset2"])
        self.PeakCan.Logger.Info("Reset via test0011EnergySaveMode1 EM1 parameters")
        self.test0011EnergySaveMode1()
    
    """
    Test HMI
    """

    def test0020HmiLedGeckoModule(self):
        self.PeakCan.Logger.Info("Get LED state")
        cmd = self.PeakCan.CanCmd(MyToolItBlock["Configuration"], MyToolItConfiguration["Hmi"], 1, 0)
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [1, 1, 0, 0, 0, 0, 0, 0])
        LedState = self.PeakCan.WriteFrameWaitAckRetries(message)["Payload"]
        LedType = LedState[0]
        LedNumber = LedState[1]
        LedState = LedState[2]
        self.PeakCan.Logger.Info("HMI Type(1=LED): " + str(LedType))
        self.PeakCan.Logger.Info("LED number: " + str(LedNumber))
        self.PeakCan.Logger.Info("LED State(1=On,2=Off): " + str(LedState))
        self.assertEqual(1, LedType)
        self.assertEqual(1, LedNumber)
        self.assertEqual(1, LedState)
        self.PeakCan.Logger.Info("Turn Off LED")
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [129, 1, 2, 0, 0, 0, 0, 0])
        LedState = self.PeakCan.WriteFrameWaitAckRetries(message)["Payload"]
        LedType = LedState[0] & 0x7F
        LedNumber = LedState[1]
        LedState = LedState[2]
        self.PeakCan.Logger.Info("HMI Type(1=LED): " + str(LedType))
        self.PeakCan.Logger.Info("LED number: " + str(LedNumber))
        self.PeakCan.Logger.Info("LED State(1=On,2=Off): " + str(LedState))
        self.assertEqual(1, LedType)
        self.assertEqual(1, LedNumber)
        self.assertEqual(2, LedState)
        self.PeakCan.Logger.Info("Sleep 5s")
        time.sleep(5)
        self.PeakCan.Logger.Info("Get LED state")
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [1, 1, 0, 0, 0, 0, 0, 0])
        LedState = self.PeakCan.WriteFrameWaitAckRetries(message)["Payload"]
        LedType = LedState[0]
        LedNumber = LedState[1]
        LedState = LedState[2]
        self.assertEqual(1, LedType)
        self.assertEqual(1, LedNumber)
        self.assertEqual(2, LedState)
        self.PeakCan.Logger.Info("HMI Type(1=LED): " + str(LedType))
        self.PeakCan.Logger.Info("LED number: " + str(LedNumber))
        self.PeakCan.Logger.Info("LED State(1=On,2=Off): " + str(LedState))
        self.PeakCan.Logger.Info("Turn On LED")
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [129, 1, 1, 0, 0, 0, 0, 0])
        LedState = self.PeakCan.WriteFrameWaitAckRetries(message)["Payload"]
        LedType = LedState[0] & 0x7F
        LedNumber = LedState[1]
        LedState = LedState[2]
        self.PeakCan.Logger.Info("HMI Type(1=LED): " + str(LedType))
        self.PeakCan.Logger.Info("LED number: " + str(LedNumber))
        self.PeakCan.Logger.Info("LED State(1=On,2=Off): " + str(LedState))
        self.PeakCan.Logger.Info("Sleep 5s")
        self.assertEqual(1, LedType)
        self.assertEqual(1, LedNumber)
        self.assertEqual(1, LedState)
        time.sleep(5)
        self.PeakCan.Logger.Info("Get LED state")
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [1, 1, 0, 0, 0, 0, 0, 0])
        LedState = self.PeakCan.WriteFrameWaitAckRetries(message)["Payload"]
        LedType = LedState[0]
        LedNumber = LedState[1]
        LedState = LedState[2]
        self.PeakCan.Logger.Info("HMI Type(1=LED): " + str(LedType))
        self.PeakCan.Logger.Info("LED number: " + str(LedNumber))
        self.PeakCan.Logger.Info("LED State(1=On,2=Off): " + str(LedState))
        self.assertEqual(1, LedType)
        self.assertEqual(1, LedNumber)
        self.assertEqual(1, LedState)

    """
    Write each calibration factor k entry
    """

    def test0030CalibrationFactorsKSingle(self):
        for _keyK, valueK in CalibrationFactor.items():
            b0 = 2
            b1 = 8
            b2 = 32
            b3 = 128
            for i in range(1, 4):
                writePayload = [valueK, i, (1 << 7), 0, b0, b1, b2, b3]
                self.PeakCan.cmdSend(MyToolItNetworkNr["STH1"], MyToolItBlock["Configuration"], MyToolItConfiguration["CalibrationFactorK"], writePayload)
                readPayload = [valueK, i, 0, 0, 0, 0, 0, 0]
                readKIndex = self.PeakCan.cmdSend(MyToolItNetworkNr["STH1"], MyToolItBlock["Configuration"], MyToolItConfiguration["CalibrationFactorK"], readPayload)
                readK = self.PeakCan.getReadMessageData(readKIndex)
                self.PeakCan.Logger.Info("Write Payload: " + payload2Hex(writePayload))
                self.PeakCan.Logger.Info("Request Payload: " + payload2Hex(readPayload))
                self.PeakCan.Logger.Info("Read Payload: " + payload2Hex(readK))
                self.assertEqual(readK[0], valueK)
                self.assertEqual(readK[1], i)
                self.assertEqual(readK[2], 0)
                self.assertEqual(readK[3], 0)
                self.assertEqual(readK[4], b0)
                self.assertEqual(readK[5], b1)
                self.assertEqual(readK[6], b2)
                self.assertEqual(readK[7], b3)
                writePayload = [valueK, i, (1 << 7), 0, 0, 0, 0, 0]
                self.PeakCan.cmdSend(MyToolItNetworkNr["STH1"], MyToolItBlock["Configuration"], MyToolItConfiguration["CalibrationFactorK"], writePayload)       
                readPayload = [valueK, i, 0, 0, 0, 0, 0, 0]
                readKIndex = self.PeakCan.cmdSend(MyToolItNetworkNr["STH1"], MyToolItBlock["Configuration"], MyToolItConfiguration["CalibrationFactorK"], readPayload)
                readK = self.PeakCan.getReadMessageData(readKIndex)
                self.PeakCan.Logger.Info("Write Payload: " + payload2Hex(writePayload))
                self.PeakCan.Logger.Info("Request Payload: " + payload2Hex(readPayload))
                self.PeakCan.Logger.Info("Read Payload: " + payload2Hex(readK))
                self.assertEqual(readK[0], valueK)
                self.assertEqual(readK[1], i)
                self.assertEqual(readK[2], 0)
                self.assertEqual(readK[3], 0)
                self.assertEqual(readK[4], 0)
                self.assertEqual(readK[5], 0)
                self.assertEqual(readK[6], 0)
                self.assertEqual(readK[7], 0)
 
    """
    Write each calibration factor D entry
    """

    def test0031CalibrationFactorsDSingle(self):
        for _keyD, valueD in CalibrationFactor.items():
            b0 = 2
            b1 = 8
            b2 = 32
            b3 = 128
            for i in range(1, 4):
                writePayload = [valueD, i, (1 << 7), 0, b0, b1, b2, b3]
                self.PeakCan.cmdSend(MyToolItNetworkNr["STH1"], MyToolItBlock["Configuration"], MyToolItConfiguration["CalibrationFactorD"], writePayload)
                readPayload = [valueD, i, 0, 0, 0, 0, 0, 0]
                readDIndex = self.PeakCan.cmdSend(MyToolItNetworkNr["STH1"], MyToolItBlock["Configuration"], MyToolItConfiguration["CalibrationFactorD"], readPayload)
                readD = self.PeakCan.getReadMessageData(readDIndex)
                self.PeakCan.Logger.Info("Write Payload: " + payload2Hex(writePayload))
                self.PeakCan.Logger.Info("Request Payload: " + payload2Hex(readPayload))
                self.PeakCan.Logger.Info("Read Payload: " + payload2Hex(readD))
                self.assertEqual(readD[0], valueD)
                self.assertEqual(readD[1], i)
                self.assertEqual(readD[2], 0)
                self.assertEqual(readD[3], 0)
                self.assertEqual(readD[4], b0)
                self.assertEqual(readD[5], b1)
                self.assertEqual(readD[6], b2)
                self.assertEqual(readD[7], b3)
                writePayload = [valueD, i, (1 << 7), 0, 0, 0, 0, 0]
                self.PeakCan.cmdSend(MyToolItNetworkNr["STH1"], MyToolItBlock["Configuration"], MyToolItConfiguration["CalibrationFactorD"], writePayload)       
                readPayload = [valueD, i, 0, 0, 0, 0, 0, 0]
                readDIndex = self.PeakCan.cmdSend(MyToolItNetworkNr["STH1"], MyToolItBlock["Configuration"], MyToolItConfiguration["CalibrationFactorD"], readPayload)
                readD = self.PeakCan.getReadMessageData(readDIndex)
                self.PeakCan.Logger.Info("Write Payload: " + payload2Hex(writePayload))
                self.PeakCan.Logger.Info("Request Payload: " + payload2Hex(readPayload))
                self.PeakCan.Logger.Info("Read Payload: " + payload2Hex(readD))
                self.assertEqual(readD[0], valueD)
                self.assertEqual(readD[1], i)
                self.assertEqual(readD[2], 0)
                self.assertEqual(readD[3], 0)
                self.assertEqual(readD[4], 0)
                self.assertEqual(readD[5], 0)
                self.assertEqual(readD[6], 0)
                self.assertEqual(readD[7], 0)

    """
    Write all calibraton factors and read them afterwards
    """

    def test0032CalibrationFactorsKDWriteThenRead(self):
        b0 = 2 - 1
        b1 = 8 - 1
        b2 = 32 - 1
        b3 = 128 - 1
        for _keyKD, valueKD in CalibrationFactor.items():
            for i in range(1, 4):
                b0 += 1
                b1 += 1
                b2 += 1
                b3 += 1
                writePayload = [valueKD, i, (1 << 7), 0, b0, b1, b2, b3]
                self.PeakCan.cmdSend(MyToolItNetworkNr["STH1"], MyToolItBlock["Configuration"], MyToolItConfiguration["CalibrationFactorK"], writePayload)
                self.PeakCan.cmdSend(MyToolItNetworkNr["STH1"], MyToolItBlock["Configuration"], MyToolItConfiguration["CalibrationFactorD"], writePayload)
        b0 = 2 - 1
        b1 = 8 - 1
        b2 = 32 - 1
        b3 = 128 - 1                                      
        for _keyKD, valueKD in CalibrationFactor.items():
            for i in range(1, 4):
                b0 += 1
                b1 += 1
                b2 += 1
                b3 += 1
                readPayload = [valueKD, i, 0, 0, 0, 0, 0, 0]
                readKIndex = self.PeakCan.cmdSend(MyToolItNetworkNr["STH1"], MyToolItBlock["Configuration"], MyToolItConfiguration["CalibrationFactorK"], readPayload)
                readDIndex = self.PeakCan.cmdSend(MyToolItNetworkNr["STH1"], MyToolItBlock["Configuration"], MyToolItConfiguration["CalibrationFactorD"], readPayload)
                readK = self.PeakCan.getReadMessageData(readKIndex)
                readD = self.PeakCan.getReadMessageData(readDIndex)
                self.PeakCan.Logger.Info("Read Payload K: " + payload2Hex(readD))
                self.PeakCan.Logger.Info("Read Payload D: " + payload2Hex(readD))
                self.assertEqual(readK[0], valueKD)
                self.assertEqual(readD[0], valueKD)
                self.assertEqual(readK[1], i)
                self.assertEqual(readD[1], i)
                self.assertEqual(readK[2], 0)
                self.assertEqual(readD[2], 0) 
                self.assertEqual(readK[3], 0)
                self.assertEqual(readD[3], 0) 
                self.assertEqual(readK[4], b0)
                self.assertEqual(readD[4], b0)                 
                self.assertEqual(readK[5], b1)
                self.assertEqual(readD[5], b1) 
                self.assertEqual(readK[6], b2)
                self.assertEqual(readD[6], b2) 
                self.assertEqual(readK[7], b3)
                self.assertEqual(readD[7], b3)                 
        for _keyK, valueK in CalibrationFactor.items():
            for i in range(1, 4):
                writePayload = [valueK, i, (1 << 7), 0, 0, 0, 0, 0]
                self.PeakCan.cmdSend(MyToolItNetworkNr["STH1"], MyToolItBlock["Configuration"], MyToolItConfiguration["CalibrationFactorK"], writePayload)
                self.PeakCan.cmdSend(MyToolItNetworkNr["STH1"], MyToolItBlock["Configuration"], MyToolItConfiguration["CalibrationFactorD"], writePayload)             

        for _keyK, valueK in CalibrationFactor.items():
            for i in range(1, 4):
                readPayload = [valueK, i, 0, 0, 0, 0, 0, 0]
                readKIndex = self.PeakCan.cmdSend(MyToolItNetworkNr["STH1"], MyToolItBlock["Configuration"], MyToolItConfiguration["CalibrationFactorK"], readPayload)
                readDIndex = self.PeakCan.cmdSend(MyToolItNetworkNr["STH1"], MyToolItBlock["Configuration"], MyToolItConfiguration["CalibrationFactorD"], readPayload)
                readK = self.PeakCan.getReadMessageData(readKIndex)
                readD = self.PeakCan.getReadMessageData(readDIndex)
                self.PeakCan.Logger.Info("Read Payload K: " + payload2Hex(readD))
                self.PeakCan.Logger.Info("Read Payload D: " + payload2Hex(readD))
                self.assertEqual(readK[0], valueK)
                self.assertEqual(readK[1], i)
                for j in range(2, 8):
                    self.assertEqual(readK[j], 0)
                    self.assertEqual(readD[j], 0) 
                                    
    """
    Write name and get name (bluetooth command)
    """

    def test0103BlueToothName(self):
        self.PeakCan.Logger.Info("Bluetooth name command")
        self.PeakCan.Logger.Info("Write Walther0")
        self.PeakCan.BlueToothNameWrite(0, "Walther0")
        self.PeakCan.Logger.Info("Check Walther0")
        Name = self.PeakCan.BlueToothNameGet(MyToolItNetworkNr["STH1"], 0)[0:8]
        self.PeakCan.Logger.Info("Received: " + Name)
        self.assertEqual("Walther0", Name)
        self.PeakCan.Logger.Info("Write " + TestConfig["DevName"])
        self.PeakCan.BlueToothNameWrite(0, TestConfig["DevName"])
        self.PeakCan.Logger.Info("Check " + TestConfig["DevName"])
        Name = self.PeakCan.BlueToothNameGet(MyToolItNetworkNr["STH1"], 0)[0:8]
        self.PeakCan.Logger.Info("Received: " + Name)
        self.assertEqual(TestConfig["DevName"], Name)
        print("Last Set Name: " + Name)
        
    """
    Bluetooth Address
    """

    def test0104BlueToothAddress(self):
        self.PeakCan.Logger.Info("Get Bluetooth Address")
        iAddress = int(self.PeakCan.BlueToothAddress(MyToolItNetworkNr["STH1"]))
        self.assertGreater(iAddress, 0)
        self.PeakCan.Logger.Info("BlueTooth Address: " + hex(iAddress))

    """
    Check Bluetooth connectablity for standard settings with minimimum sleep time
    """

    def test0105BlueToothConnectStandard(self):
        self.PeakCan.BlueToothEnergyModeNr(SleepTime["Min"], SleepTime["AdvertisementReset1"], 1)
        self.PeakCan.BlueToothEnergyModeNr(SleepTime["Min"], SleepTime["AdvertisementReset2"], 2)  
        timeAverageSleep2 = 0
        self.PeakCan.Logger.Info("Test Sleep Mode 2 with Adverteisement Time: " + str(SleepTime["AdvertisementReset2"]) + "ms") 
        for _i in range(0, 10):      
            self.PeakCan.BlueToothDisconnect(MyToolItNetworkNr["STU1"])
            time.sleep(2 * SleepTime["Min"] / 1000)
            timeStampDisconnected = self.PeakCan.Logger.getTimeStamp()
            self.PeakCan.BlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])
            timeStampConnected = self.PeakCan.Logger.getTimeStamp()
            timeConnect = timeStampConnected - timeStampDisconnected
            timeAverageSleep2 += timeConnect
            self.PeakCan.Logger.Info("TimeStamp before connecting start : " + str(timeStampDisconnected) + "ms")
            self.PeakCan.Logger.Info("TimeStamp after reconnected : " + str(timeStampConnected) + "ms")
            self.PeakCan.Logger.Info("Connecting Time : " + str(timeConnect) + "ms")
        timeAverageSleep2 /= 10
        self.PeakCan.Logger.Info("Average Connecting Time for Sleep Mode 2 : " + str(timeAverageSleep2) + "ms")
        self.PeakCan.BlueToothEnergyModeNr(SleepTime["Min"], SleepTime["AdvertisementReset1"], 1)
        self.PeakCan.BlueToothEnergyModeNr(SleepTime["Reset2"], SleepTime["AdvertisementReset2"], 2)  
        timeAverageSleep1 = 0
        self.PeakCan.Logger.Info("Test Sleep Mode 1 with Adverteisement Time: " + str(SleepTime["AdvertisementReset1"]) + "ms") 
        for _i in range(0, 10):      
            self.PeakCan.BlueToothDisconnect(MyToolItNetworkNr["STU1"])
            time.sleep(SleepTime["Min"] / 1000)
            timeStampDisconnected = self.PeakCan.Logger.getTimeStamp()
            self.PeakCan.BlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])     
            timeStampConnected = self.PeakCan.Logger.getTimeStamp()
            timeConnect = timeStampConnected - timeStampDisconnected
            timeAverageSleep1 += timeConnect
            self.PeakCan.Logger.Info("TimeStamp before connecting start : " + str(timeStampDisconnected) + "ms")
            self.PeakCan.Logger.Info("TimeStamp after reconnected : " + str(timeStampConnected) + "ms")
            self.PeakCan.Logger.Info("Connecting Time : " + str(timeConnect) + "ms")  
        timeAverageSleep1 /= 10        
        self.PeakCan.Logger.Info("Average Connecting Time for Sleep Mode 1 : " + str(timeAverageSleep1) + "ms")
        self.PeakCan.BlueToothEnergyModeNr(SleepTime["Reset1"], SleepTime["AdvertisementReset1"], 1)
        self.PeakCan.BlueToothEnergyModeNr(SleepTime["Reset2"], SleepTime["AdvertisementReset2"], 2)  
        self.assertLess(timeAverageSleep1, TestConfig["ConTimeSleep1MaxMs"])
        self.assertLess(timeAverageSleep2, TestConfig["ConTimeSleep2MaxMs"])

    """
    Check Bluetooth connectablity for maximum values
    """

    def test0106BlueToothConnectMax(self):
        self.PeakCan.BlueToothEnergyModeNr(SleepTime["Min"], SleepTime["AdvertisementMax"], 1)
        self.PeakCan.BlueToothEnergyModeNr(SleepTime["Min"], SleepTime["AdvertisementMax"], 2)  
        timeAverageSleep2 = 0
        self.PeakCan.Logger.Info("Test Sleep Mode 2 with Advertisement Time: " + str(SleepTime["AdvertisementReset2"]) + "ms") 
        for _i in range(0, 10):      
            self.PeakCan.BlueToothDisconnect(MyToolItNetworkNr["STU1"])
            time.sleep(2 * SleepTime["Min"] / 1000)
            timeStampDisconnected = self.PeakCan.Logger.getTimeStamp()
            self.PeakCan.BlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])
            timeStampConnected = self.PeakCan.Logger.getTimeStamp()
            timeConnect = timeStampConnected - timeStampDisconnected
            timeAverageSleep2 += timeConnect
            self.PeakCan.Logger.Info("TimeStamp before connecting start : " + str(timeStampDisconnected) + "ms")
            self.PeakCan.Logger.Info("TimeStamp after reconnected : " + str(timeStampConnected) + "ms")
            self.PeakCan.Logger.Info("Connecting Time : " + str(timeConnect) + "ms")
        timeAverageSleep2 /= 10
        self.PeakCan.Logger.Info("Average Connecting Time: " + str(timeAverageSleep2) + "ms")
        self.PeakCan.BlueToothEnergyModeNr(SleepTime["Reset1"], SleepTime["AdvertisementReset1"], 1)
        self.PeakCan.BlueToothEnergyModeNr(SleepTime["Reset2"], SleepTime["AdvertisementReset2"], 2)
        self.assertLess(timeAverageSleep2, TestConfig["ConTimeMaximumMs"])
        
    """
    Check Bluetooth connectablity for Minimum values (Standard Setting at start, not configuratble, 50ms atm)
    """

    def test0107BlueToothConnectMin(self): 
        self.PeakCan.BlueToothEnergyModeNr(SleepTime["Reset1"], SleepTime["AdvertisementReset1"], 1)
        self.PeakCan.BlueToothEnergyModeNr(SleepTime["Reset2"], SleepTime["AdvertisementReset2"], 2)
        timeAverage = 0
        self.PeakCan.Logger.Info("Test Normal Connection Time") 
        for _i in range(0, 10):      
            self.PeakCan.BlueToothDisconnect(MyToolItNetworkNr["STU1"])
            timeStampDisconnected = self.PeakCan.Logger.getTimeStamp()
            self.PeakCan.BlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])
            timeStampConnected = self.PeakCan.Logger.getTimeStamp()
            timeConnect = timeStampConnected - timeStampDisconnected
            timeAverage += timeConnect
            self.PeakCan.Logger.Info("TimeStamp before connecting start : " + str(timeStampDisconnected) + "ms")
            self.PeakCan.Logger.Info("TimeStamp after reconnected : " + str(timeStampConnected) + "ms")
            self.PeakCan.Logger.Info("Connecting Time : " + str(timeConnect) + "ms")
        timeAverage /= 10       
        self.PeakCan.Logger.Info("Average Connecting Time: " + str(timeAverage) + "ms")
        self.assertLess(timeAverage, TestConfig["ConTimeNormalMaxMs"])

    """
    Check Minimum Sleeping Time
    """

    def test0108BlueToothConnectWrongValues(self): 
        # Do not take Time (Note that maximum is 2^32-1... Not testable due to 4Bytes Only
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyModeNr(SleepTime["Min"] - 1, SleepTime["AdvertisementReset1"], 1)
        if 0 == timeReset and 0 == timeAdvertisement:
            self.PeakCan.Logger.Info("Sleep Time1 was not taken: " + str(SleepTime["Min"] - 1) + "ms")
        else:
            self.PeakCan.Logger.bError("Sleep Time1 was taken: " + str(SleepTime["Min"] - 1) + "ms")
            self.PeakCan.__exitError()
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyModeNr(SleepTime["Min"] - 1, SleepTime["AdvertisementReset2"], 2)
        if 0 == timeReset and 0 == timeAdvertisement:
            self.PeakCan.Logger.Info("Sleep Time2 was not taken: " + str(SleepTime["Min"] - 1) + "ms")
        else:
            self.PeakCan.Logger.bError("Sleep Time2 was taken: " + str(SleepTime["Min"] - 1) + "ms")
            self.PeakCan.__exitError()
            
        # Do not take Advertisement Time - Min
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyModeNr(SleepTime["Reset1"], SleepTime["AdvertisementMin"] - 1, 1)
        if 0 == timeReset and 0 == timeAdvertisement:
            self.PeakCan.Logger.Info("Advertisement Time1 was not taken: " + str(SleepTime["AdvertisementMin"] - 1) + "ms")
        else:
            self.PeakCan.Logger.bError("Advertisement Time1 was taken: " + str(SleepTime["AdvertisementMin"] - 1) + "ms")
            self.PeakCan.__exitError()
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyModeNr(SleepTime["Reset2"], SleepTime["AdvertisementMin"] - 1, 2)
        if 0 == timeReset and 0 == timeAdvertisement:
            self.PeakCan.Logger.Info("Advertisement Time2 was not taken: " + str(SleepTime["AdvertisementMin"] - 1) + "ms")
        else:
            self.PeakCan.Logger.bError("Advertisement Time2 was taken: " + str(SleepTime["AdvertisementMin"] - 1) + "ms")
            self.PeakCan.__exitError()
        # Do not take Advertisement Time - Max
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyModeNr(SleepTime["Reset1"], SleepTime["AdvertisementMax"] + 1, 1)
        if 0 == timeReset and 0 == timeAdvertisement:
            self.PeakCan.Logger.Info("Advertisement Time1 was not taken: " + str(SleepTime["AdvertisementMax"] + 1) + "ms")
        else:
            self.PeakCan.Logger.bError("Advertisement Time1 was taken: " + str(SleepTime["AdvertisementMax"] + 1) + "ms")
            self.PeakCan.__exitError()
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyModeNr(SleepTime["Reset2"], SleepTime["AdvertisementMax"] + 1, 2)
        if 0 == timeReset and 0 == timeAdvertisement:
            self.PeakCan.Logger.Info("Advertisement Time2 was not taken: " + str(SleepTime["AdvertisementMax"] + 1) + "ms")
        else:
            self.PeakCan.Logger.bError("Advertisement Time2 was taken: " + str(SleepTime["AdvertisementMax"] + 1) + "ms")
            self.PeakCan.__exitError()

        self.PeakCan.BlueToothEnergyModeNr(SleepTime["Reset1"], SleepTime["AdvertisementReset1"], 1)
        self.PeakCan.BlueToothEnergyModeNr(SleepTime["Reset2"], SleepTime["AdvertisementReset2"], 2)           
        
    """
    Bluetooth Address
    """

    def test0109BlueToothRssi(self):
        self.PeakCan.Logger.Info("Get Bluetooth Address")
        iRssi = int(self.PeakCan.BlueToothRssi(MyToolItNetworkNr["STH1"]))
        self.assertGreater(iRssi, -80)
        self.assertLess(iRssi, 20)
        self.PeakCan.Logger.Info("BlueTooth RSSI: " + hex(iRssi))   
        
    """
    Get Battery Voltage via single command
    """

    def test0300GetSingleVoltageBattery(self):
        index = self.PeakCan.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], 1, 0, 0)
        [val1, val2, val3] = self.PeakCan.singleValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], 1, 0, 0, index)
        self.PeakCan.ValueLog(val1, val2, val3, fVoltageBattery, "Battery Voltage", "V")
        self.singleValueCompare(val1, val2, val3, VoltMiddleBat, VoltToleranceBat, 0, 0, 0, 0, fVoltageBattery)

    """
    Test multi single battery meassurement
    """

    def test0301GetSingleVoltageBatteryMultipleTimes(self):
        for _i in range(0, 10):
            index = self.PeakCan.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], 1, 0, 0)
            [val1, val2, val3] = self.PeakCan.singleValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], 1, 0, 0, index)
            self.PeakCan.ValueLog(val1, val2, val3, fVoltageBattery, "Battery Voltage", "V")
            self.singleValueCompare(val1, val2, val3, VoltMiddleBat, VoltToleranceBat, 0, 0, 0, 0, fVoltageBattery)

    """
    Test single battery Acceleration X-Axis meassurement
    """

    def test0302GetSingleAccX(self):
        index = self.PeakCan.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 1, 0, 0)
        [val1, val2, val3] = self.PeakCan.singleValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 1, 0, 0, index)
        self.PeakCan.ValueLog(val1, val2, val3, fAcceleration, "Acc", "g")
        self.singleValueCompare(val1, val2, val3, AdcMiddleX, AdcToleranceX, 0, 0, 0, 0, fAcceleration)

    """
    Test single battery Acceleration Y-Axis meassurement
    """

    def test0303GetSingleAccY(self):
        index = self.PeakCan.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 0, 1, 0)
        [val1, val2, val3] = self.PeakCan.singleValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 0, 1, 0, index)
        self.PeakCan.ValueLog(val1, val2, val3, fAcceleration, "Acc", "g")
        self.singleValueCompare(val1, val2, val3, 0, 0, AdcMiddleY, AdcToleranceY, 0, 0, fAcceleration)

    """
    Test single battery Acceleration Z-Axis meassurement
    """

    def test0304GetSingleAccZ(self):
        index = self.PeakCan.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 0, 0, 1)
        [val1, val2, val3] = self.PeakCan.singleValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 0, 0, 1, index)
        self.PeakCan.ValueLog(val1, val2, val3, fAcceleration, "Acc", "g")
        self.singleValueCompare(val1, val2, val3, 0, 0, 0, 0, AdcMiddleZ, AdcToleranceZ, fAcceleration)

    """
    Test multi single X Acc meassurement
    """

    def test0305GetSingleSingleAccXMultipleTimes(self):
        for _i in range(0, 10):
            index = self.PeakCan.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 1, 0, 0)
            [val1, val2, val3] = self.PeakCan.singleValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 1, 0, 0, index)
            self.PeakCan.ValueLog(val1, val2, val3, fAcceleration, "Acc", "g")
            self.singleValueCompare(val1, val2, val3, AdcMiddleX, AdcToleranceX, 0, 0, 0, 0, fAcceleration)

    """
    Test multi single Y Acc meassurement
    """

    def test0306GetSingleSingleAccYMultipleTimes(self):
        for _i in range(0, 10):
            index = self.PeakCan.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 0, 1, 0)
            [val1, val2, val3] = self.PeakCan.singleValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 0, 1, 0, index)
            self.PeakCan.ValueLog(val1, val2, val3, fAcceleration, "Acc", "g")
            self.singleValueCompare(val1, val2, val3, 0, 0, AdcMiddleY, AdcToleranceY, 0, 0, fAcceleration)

    """
    Test multi single Z Acc meassurement
    """

    def test0307GetSingleSingleAccZMultipleTimes(self):
        for _i in range(0, 10):
            index = self.PeakCan.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 0, 0, 1)
            [val1, val2, val3] = self.PeakCan.singleValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 0, 0, 1, index)
            self.PeakCan.ValueLog(val1, val2, val3, fAcceleration, "Acc", "g")
            self.singleValueCompare(val1, val2, val3, 0, 0, 0, 0, AdcMiddleZ, AdcToleranceZ, fAcceleration)
            
    """
    Test single XY-Axis meassurement
    """

    def test0308GetSingleAccXY(self):
        index = self.PeakCan.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 1, 1, 0)
        [val1, val2, val3] = self.PeakCan.singleValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 1, 1, 0, index)
        self.PeakCan.ValueLog(val1, val2, val3, fAcceleration, "Acc", "g")
        self.singleValueCompare(val1, val2, val3, AdcMiddleX, AdcToleranceX, AdcMiddleY, AdcToleranceY, 0, 0, fAcceleration)

    """
    Test single XZ-Axis meassurement
    """

    def test0309GetSingleAccXZ(self):
        index = self.PeakCan.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 1, 0, 1)
        [val1, val2, val3] = self.PeakCan.singleValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 1, 0, 1, index)
        self.PeakCan.ValueLog(val1, val2, val3, fAcceleration, "Acc", "g")
        self.singleValueCompare(val1, val2, val3, AdcMiddleX, AdcToleranceX, 0, 0, AdcMiddleZ, AdcToleranceZ, fAcceleration)

    """
    Test single XYZ-Axis meassurement
    """

    def test0310GetSingleAccXYZ(self):
        index = self.PeakCan.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 1, 1, 1)
        [val1, val2, val3] = self.PeakCan.singleValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 1, 1, 1, index)
        self.PeakCan.ValueLog(val1, val2, val3, fAcceleration, "Acc", "g")
        self.singleValueCompare(val1, val2, val3, AdcMiddleX, AdcToleranceX, AdcMiddleY, AdcToleranceY, AdcMiddleZ, AdcToleranceZ, fAcceleration)
         
    """
    Test single YZ-Axis meassurement
    """

    def test0310GetSingleAccYZ(self):
        index = self.PeakCan.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 0, 1, 1)
        [val1, val2, val3] = self.PeakCan.singleValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 0, 1, 1, index)
        self.PeakCan.ValueLog(val1, val2, val3, fAcceleration, "Acc", "g")
        self.singleValueCompare(val1, val2, val3, 0, 0, AdcMiddleY, AdcToleranceY, AdcMiddleZ, AdcToleranceZ, fAcceleration)
                       
    """
    Test streaming battery meassurement
    """

    def test0320GetStreamingVoltageBattery(self):
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, StreamingStandardTestTimeMs)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fVoltageBattery, "Voltage", "V",)
        self.streamingValueCompare(array1, array2, array3, VoltMiddleBat, VoltToleranceBat, 0, 0, 0, 0, fVoltageBattery)

    """
    Test streaming x-Axis meassurement
    """

    def test0321GetStreamingAccX(self):
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0, StreamingStandardTestTimeMs)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAcceleration, "Acc", "g",)
        self.streamingValueCompare(array1, array2, array3, AdcMiddleX, AdcToleranceX, 0, 2 ** 32, 0, 2 ** 32, fAcceleration)

    """
    Test streaming y-Axis meassurement
    """

    def test0322GetStreamingAccY(self):
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 1, 0, StreamingStandardTestTimeMs)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 1, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAcceleration, "Acc", "g",)
        self.streamingValueCompare(array1, array2, array3, 0, 2 ** 32, AdcMiddleY, AdcToleranceY, 0, 2 ** 32, fAcceleration)

    """
    Test streaming z-Axis meassurement
    """

    def test0323GetStreamingAccZ(self):
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 0, 1, StreamingStandardTestTimeMs)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 0, 1, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAcceleration, "Acc", "g",)
        self.streamingValueCompare(array1, array2, array3, 0, 2 ** 32, 0, 2 ** 32, AdcMiddleZ, AdcToleranceZ, fAcceleration)

    """
    Test streaming xyz-Axis meassurement
    """

    def test0324GetStreamingAccXYZ(self):
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 1, StreamingStandardTestTimeMs)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 1, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "",)
        self.streamingValueCompare(array1, array2, array3, AdcMiddleX, AdcToleranceX, AdcMiddleY, AdcToleranceY, AdcMiddleZ, AdcToleranceZ, fAcceleration)

    """
    Test streaming Double-Axis meassurement
    """

    def test0325GetStreamingAccDouble(self):
        self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], SamplingRateDoubleMaxPrescaler, SamplingRateDoubleMaxAcqTime, SamplingRateDoubleMaxOverSamples, AdcReference["VDD"])
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 0, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "",)
        self.streamingValueCompare(array1, array2, array3, AdcMiddleX, AdcToleranceX, AdcMiddleY, AdcToleranceY, AdcMiddleZ, AdcToleranceZ, fAcceleration)
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 0, 1, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 0, 1, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "",)
        self.streamingValueCompare(array1, array2, array3, AdcMiddleX, AdcToleranceX, AdcMiddleY, AdcToleranceY, AdcMiddleZ, AdcToleranceZ, fAcceleration)
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 0, 1, 1, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 0, 1, 1, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "",)
        self.streamingValueCompare(array1, array2, array3, AdcMiddleX, AdcToleranceX, AdcMiddleY, AdcToleranceY, AdcMiddleZ, AdcToleranceZ, fAcceleration)

    """
    Test Signal-to-Noise Ration - x
    """

    def test0326SignalIndicatorsAccX(self):
        self.TurnOffLed()
        self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], SamplingRateSingleMaxPrescaler, SamplingRateSingleMaxAcqTime, SamplingRateSingleMaxOverSamples, AdcReference["VDD"])
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0, StreamingStandardTestTimeMs)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        statistics = self.signalIndicators(array1, array2, array3)
        self.siginalIndicatorCheck("ADC X", statistics["Value1"], SigIndAccXQ1, SigIndAccXQ25, SigIndAccXMedL, SigIndAccXMedH, SigIndAccXQ75, SigIndAccXQ99, SigIndAccXVar, SigIndAccXSkewness, SigIndAccXSNR)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "")
        
    """
    Test Signal-to-Noise Ration - Y
    """

    def test0327SignalIndicatorsAccY(self):
        self.TurnOffLed()
        self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], SamplingRateSingleMaxPrescaler, SamplingRateSingleMaxAcqTime, SamplingRateSingleMaxOverSamples, AdcReference["VDD"])
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 1, 0, StreamingStandardTestTimeMs)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 1, 0, indexStart, indexEnd)
        statistics = self.signalIndicators(array1, array2, array3)
        self.siginalIndicatorCheck("ADC Y", statistics["Value2"], SigIndAccYQ1, SigIndAccYQ25, SigIndAccYMedL, SigIndAccYMedH, SigIndAccYQ75, SigIndAccYQ99, SigIndAccYVar, SigIndAccYSkewness, SigIndAccYSNR)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "")

    """
    Test Signal-to-Noise Ration - Z
    """

    def test0328SignalIndicatorsAccZ(self):
        self.TurnOffLed()
        self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], SamplingRateSingleMaxPrescaler, SamplingRateSingleMaxAcqTime, SamplingRateSingleMaxOverSamples, AdcReference["VDD"])
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 0, 1, StreamingStandardTestTimeMs)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 0, 1, indexStart, indexEnd)
        statistics = self.signalIndicators(array1, array2, array3)
        self.siginalIndicatorCheck("ADC Z", statistics["Value3"], SigIndAccZQ1, SigIndAccZQ25, SigIndAccZMedL, SigIndAccZMedH, SigIndAccZQ75, SigIndAccZQ99, SigIndAccZVar, SigIndAccZSkewness, SigIndAccZSNR)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "")

    """
    Test Signal-to-Noise Ration - Z
    """

    def test0329SignalIndicatorsBattery(self):
        self.TurnOffLed()
        self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], SamplingRateSingleMaxPrescaler, SamplingRateSingleMaxAcqTime, SamplingRateSingleMaxOverSamples, AdcReference["VDD"])
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, StreamingStandardTestTimeMs)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        statistics = self.signalIndicators(array1, array2, array3)
        self.siginalIndicatorCheck("Battery", statistics["Value1"], SigIndBatteryQ1, SigIndBatteryQ25, SigIndBatteryMedL, SigIndBatteryMedH, SigIndBatteryQ75, SigIndBatteryQ99, SigIndBatteryVar, SigIndBatterySkewness, SigIndBatterySNR)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Voltage", "")

    """
    Test Signal-to-Noise Ration - Acc Multi
    """

    def test0330SignalIndicatorsMulti(self):
        self.TurnOffLed()
        self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], SamplingRateDoubleMaxPrescaler, SamplingRateDoubleMaxAcqTime, SamplingRateDoubleMaxOverSamples, AdcReference["VDD"])
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 0, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 0, indexStart, indexEnd)
        statistics = self.signalIndicators(array1, array2, array3)
        self.siginalIndicatorCheck("ADC X", statistics["Value1"], SigIndAccXQ1, SigIndAccXQ25, SigIndAccXMedL, SigIndAccXMedH, SigIndAccXQ75, SigIndAccXQ99, SigIndAccXVar, SigIndAccXSkewness, SigIndAccXSNR)
        self.siginalIndicatorCheck("ADC Y", statistics["Value2"], SigIndAccYQ1, SigIndAccYQ25, SigIndAccYMedL, SigIndAccYMedH, SigIndAccYQ75, SigIndAccYQ99, SigIndAccYVar, SigIndAccYSkewness, SigIndAccYSNR)
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 0, 1, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 0, 1, indexStart, indexEnd)
        statistics = self.signalIndicators(array1, array2, array3)
        self.siginalIndicatorCheck("ADC X", statistics["Value1"], SigIndAccXQ1, SigIndAccXQ25, SigIndAccXMedL, SigIndAccXMedH, SigIndAccXQ75, SigIndAccXQ99, SigIndAccXVar, SigIndAccXSkewness, SigIndAccXSNR)
        self.siginalIndicatorCheck("ADC Z", statistics["Value3"], SigIndAccZQ1, SigIndAccZQ25, SigIndAccZMedL, SigIndAccZMedH, SigIndAccZQ75, SigIndAccZQ99, SigIndAccZVar, SigIndAccZSkewness, SigIndAccZSNR)
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 0, 1, 1, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 0, 1, 1, indexStart, indexEnd)
        statistics = self.signalIndicators(array1, array2, array3)
        self.siginalIndicatorCheck("ADC Y", statistics["Value2"], SigIndAccYQ1, SigIndAccYQ25, SigIndAccYMedL, SigIndAccYMedH, SigIndAccYQ75, SigIndAccYQ99, SigIndAccYVar, SigIndAccYSkewness, SigIndAccYSNR)
        self.siginalIndicatorCheck("ADC Z", statistics["Value3"], SigIndAccZQ1, SigIndAccZQ25, SigIndAccZMedL, SigIndAccZMedH, SigIndAccZQ75, SigIndAccZQ99, SigIndAccZVar, SigIndAccZSkewness, SigIndAccZSNR)
        self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], SamplingRateTrippleMaxPrescaler, SamplingRateTrippleMaxAcqTime, SamplingRateTrippleMaxOverSamples, AdcReference["VDD"])
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 1, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 1, indexStart, indexEnd)
        statistics = self.signalIndicators(array1, array2, array3)
        self.siginalIndicatorCheck("ADC X", statistics["Value1"], SigIndAccXQ1, SigIndAccXQ25, SigIndAccXMedL, SigIndAccXMedH, SigIndAccXQ75, SigIndAccXQ99, SigIndAccXVar, SigIndAccXSkewness, SigIndAccXSNR)
        self.siginalIndicatorCheck("ADC Y", statistics["Value2"], SigIndAccYQ1, SigIndAccYQ25, SigIndAccYMedL, SigIndAccYMedH, SigIndAccYQ75, SigIndAccYQ99, SigIndAccYVar, SigIndAccYSkewness, SigIndAccYSNR)
        self.siginalIndicatorCheck("ADC Z", statistics["Value3"], SigIndAccZQ1, SigIndAccZQ25, SigIndAccZMedL, SigIndAccZMedH, SigIndAccZQ75, SigIndAccZQ99, SigIndAccZVar, SigIndAccZSkewness, SigIndAccZSNR)

    """
    Test Streaming multiple Times
    """

    def test0331GetStreamingMultipleTimes(self):
        for _i in range(0, 3):
            [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, 1000)
            [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
            self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Voltage", "")
            self.streamingValueCompare(array1, array2, array3, VoltMiddleBat, VoltToleranceBat, 0, 0, 0, 0, fVoltageBattery)
        for _i in range(0, 3):
            [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0, 1000)
            [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
            self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "")
            self.streamingValueCompare(array1, array2, array3, AdcMiddleX, AdcToleranceX, AdcMiddleY, AdcToleranceY, AdcMiddleZ, AdcToleranceZ, fAcceleration)
        for _i in range(0, 3):
            [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 1, 0, 1000)
            [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 1, 0, indexStart, indexEnd)
            self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "")
            self.streamingValueCompare(array1, array2, array3, AdcMiddleX, AdcToleranceX, AdcMiddleY, AdcToleranceY, AdcMiddleZ, AdcToleranceZ, fAcceleration)
        for _i in range(0, 3):
            [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 0, 1, 1000)
            [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 0, 1, indexStart, indexEnd)
            self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "")
            self.streamingValueCompare(array1, array2, array3, AdcMiddleX, AdcToleranceX, AdcMiddleY, AdcToleranceY, AdcMiddleZ, AdcToleranceZ, fAcceleration)

    """
    Test multiple config battery, x, y, z
    """

    def test0332StreamingMultiConfigBatAccXAccYAccZ(self):
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Voltage", "")
        self.streamingValueCompare(array1, array2, array3, VoltMiddleBat, VoltToleranceBat, 0, 0, 0, 0, fVoltageBattery)
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "")
        self.streamingValueCompare(array1, array2, array3, AdcMiddleX, AdcToleranceX, AdcMiddleY, AdcToleranceY, AdcMiddleZ, AdcToleranceZ, fAcceleration)
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 1, 0, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 1, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "")
        self.streamingValueCompare(array1, array2, array3, AdcMiddleX, AdcToleranceX, AdcMiddleY, AdcToleranceY, AdcMiddleZ, AdcToleranceZ, fAcceleration)
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 0, 1, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 0, 1, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "")
        self.streamingValueCompare(array1, array2, array3, AdcMiddleX, AdcToleranceX, AdcMiddleY, AdcToleranceY, AdcMiddleZ, AdcToleranceZ, fAcceleration)

    """
    Test multiple config x-xyz-x
    """

    def test0333StreamingMultiConfig(self):
        self.PeakCan.Logger.Info("Streaming AccX starts")
        self.test0321GetStreamingAccX()
        self.PeakCan.ReadThreadReset()
        self.PeakCan.Logger.Info("Streaming AccXYZ starts")
        self.test0324GetStreamingAccXYZ()
        self.PeakCan.ReadThreadReset()
        self.PeakCan.Logger.Info("Streaming AccX starts")
        self.test0321GetStreamingAccX()
        self.PeakCan.ReadThreadReset()
        
    """
    Test long usage of data acquiring
    """        

    def test0334StreamingHeavyDuty(self):
        self.SamplingRate(SamplingRateSingleMaxPrescaler, SamplingRateSingleMaxAcqTime, SamplingRateSingleMaxOverSamples, AdcReference["VDD"], runTime=1200000)
 
    """
    Mixed Streaming - AccX + VoltageBattery
    """        

    def test0335MixedStreamingAccXVoltBat(self):
        self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0)
        indexStart = self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0)
        time.sleep(StreamingStandardTestTimeMs / 1000)
        indexEnd = self.PeakCan.GetReadArrayIndex() - 1
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"])   
        time.sleep(1)    
        countDel = 0
        while StreamingStandardTestTimeMs < self.PeakCan.getReadMessageTimeMs(indexStart, indexEnd) - 0.5:
            countDel += 1
            indexEnd -= 1
        self.PeakCan.Logger.Info("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))
        self.PeakCan.Logger.Info("indexStart: " + str(indexStart))
        self.PeakCan.Logger.Info("indexEnd: " + str(indexEnd))
        if 0.2 * (indexEnd - indexStart) < countDel:
            self.PeakCan.Logger.Warning("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))        
        [arrayBat, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.assertEqual(0, len(array2))
        self.assertEqual(0, len(array3))
        [arrayAccX, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.assertEqual(0, len(array2))
        self.assertEqual(0, len(array3))
        self.PeakCan.Logger.Info("Voltage Sampling Points: " + str(len(arrayBat)))
        self.PeakCan.Logger.Info("Acceleration Sampling Points: " + str(len(arrayAccX)))
        self.PeakCan.ValueLog(arrayBat, array2, array3, fAdcRawDat, "Voltage", "")
        self.PeakCan.ValueLog(arrayAccX, array2, array3, fAdcRawDat, "Acc", "")
        self.streamingValueCompare(arrayBat, array2, array3, VoltMiddleBat, VoltToleranceBat, 0, 0, 0, 0, fVoltageBattery)   
        self.streamingValueCompare(arrayAccX, array2, array3, AdcMiddleX, AdcToleranceX, 0, 0, 0, 0, fAcceleration)    

    """
    Mixed Streaming - AccX + VoltageBattery; Requesting Reverse
    """        

    def test0336MixedStreamingAccXVoltBatInverse(self):
        self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0)
        indexStart = self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0)
        time.sleep(StreamingStandardTestTimeMs / 1000)
        indexEnd = self.PeakCan.GetReadArrayIndex() - 1
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"])   
        time.sleep(1)    
        countDel = 0
        while StreamingStandardTestTimeMs < self.PeakCan.getReadMessageTimeMs(indexStart, indexEnd) - 0.5:
            countDel += 1
            indexEnd -= 1
        self.PeakCan.Logger.Info("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))
        self.PeakCan.Logger.Info("indexStart: " + str(indexStart))
        self.PeakCan.Logger.Info("indexEnd: " + str(indexEnd))
        if 0.2 * (indexEnd - indexStart) < countDel:
            self.PeakCan.Logger.Warning("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))        
        [arrayBat, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.assertEqual(0, len(array2))
        self.assertEqual(0, len(array3))
        [arrayAccX, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.assertEqual(0, len(array2))
        self.assertEqual(0, len(array3))
        self.PeakCan.Logger.Info("Voltage Sampling Points: " + str(len(arrayBat)))
        self.PeakCan.Logger.Info("Acceleration Sampling Points: " + str(len(arrayAccX)))
        self.PeakCan.ValueLog(arrayBat, array2, array3, fAdcRawDat, "Voltage", "")
        self.PeakCan.ValueLog(arrayAccX, array2, array3, fAdcRawDat, "Acc", "")
        self.streamingValueCompare(arrayBat, array2, array3, VoltMiddleBat, VoltToleranceBat, 0, 0, 0, 0, fVoltageBattery)   
        self.streamingValueCompare(arrayAccX, array2, array3, AdcMiddleX, AdcToleranceX, 0, 0, 0, 0, fAcceleration)    
        
    """
    Mixed Streaming - AccY + VoltageBattery
    """        

    def test0337MixedStreamingAccYVoltBat(self):
        self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0)
        indexStart = self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 1, 0)
        time.sleep(StreamingStandardTestTimeMs / 1000)
        indexEnd = self.PeakCan.GetReadArrayIndex() - 1
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"])   
        time.sleep(1)    
        countDel = 0
        while StreamingStandardTestTimeMs < self.PeakCan.getReadMessageTimeMs(indexStart, indexEnd) - 0.5:
            countDel += 1
            indexEnd -= 1
        self.PeakCan.Logger.Info("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))
        self.PeakCan.Logger.Info("indexStart: " + str(indexStart))
        self.PeakCan.Logger.Info("indexEnd: " + str(indexEnd))
        if 0.2 * (indexEnd - indexStart) < countDel:
            self.PeakCan.Logger.Warning("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))        
        [arrayBat, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.assertEqual(0, len(array2))
        self.assertEqual(0, len(array3))
        [array1, arrayAccY, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 1, 0, indexStart, indexEnd)
        self.assertEqual(0, len(array1))
        self.assertEqual(0, len(array3))
        self.PeakCan.Logger.Info("Voltage Sampling Points: " + str(len(arrayBat)))
        self.PeakCan.Logger.Info("Acceleration Sampling Points: " + str(len(arrayAccY)))
        self.PeakCan.ValueLog(arrayBat, array2, array3, fAdcRawDat, "Voltage", "")
        self.PeakCan.ValueLog(array1, arrayAccY, array3, fAdcRawDat, "Acc", "")
        self.streamingValueCompare(arrayBat, array2, array3, VoltMiddleBat, VoltToleranceBat, 0, 0, 0, 0, fVoltageBattery)   
        self.streamingValueCompare(array1, arrayAccY, array3, 0, 0, AdcMiddleY, AdcToleranceY, 0, 0, fAcceleration)    

    """
    Mixed Streaming - AccZ + VoltageBattery
    """        

    def test0338MixedStreamingAccZVoltBat(self):
        self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0)
        indexStart = self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 0, 1)
        time.sleep(StreamingStandardTestTimeMs / 1000)
        indexEnd = self.PeakCan.GetReadArrayIndex() - 1
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"])   
        time.sleep(1)    
        countDel = 0
        while StreamingStandardTestTimeMs < self.PeakCan.getReadMessageTimeMs(indexStart, indexEnd) - 0.5:
            countDel += 1
            indexEnd -= 1
        self.PeakCan.Logger.Info("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))
        self.PeakCan.Logger.Info("indexStart: " + str(indexStart))
        self.PeakCan.Logger.Info("indexEnd: " + str(indexEnd))
        if 0.2 * (indexEnd - indexStart) < countDel:
            self.PeakCan.Logger.Warning("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))        
        [arrayBat, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.assertEqual(0, len(array2))
        self.assertEqual(0, len(array3))
        [array1, array2, arrayAccZ] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 0, 1, indexStart, indexEnd)
        self.assertEqual(0, len(array1))
        self.assertEqual(0, len(array2))
        self.PeakCan.Logger.Info("Voltage Sampling Points: " + str(len(arrayBat)))
        self.PeakCan.Logger.Info("Acceleration Sampling Points: " + str(len(arrayAccZ)))
        self.PeakCan.ValueLog(arrayBat, array2, array3, fAdcRawDat, "Voltage", "")
        self.PeakCan.ValueLog(array1, array2, arrayAccZ, fAdcRawDat, "Acc", "")
        self.streamingValueCompare(arrayBat, array2, array3, VoltMiddleBat, VoltToleranceBat, 0, 0, 0, 0, fVoltageBattery)   
        self.streamingValueCompare(array1, array2, arrayAccZ, 0, 0, 0, 0, AdcMiddleZ, AdcToleranceZ, fAcceleration)    
 
    """
    Mixed Streaming - AccX + AccZ + VoltageBattery
    """        

    def test0339MixedStreamingAccXZVoltBat(self):
        self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0)
        indexStart = self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 0, 1)
        time.sleep(StreamingStandardTestTimeMs / 1000)
        indexEnd = self.PeakCan.GetReadArrayIndex() - 1
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"])   
        time.sleep(1)    
        countDel = 0
        while StreamingStandardTestTimeMs < self.PeakCan.getReadMessageTimeMs(indexStart, indexEnd) - 0.5:
            countDel += 1
            indexEnd -= 1
        self.PeakCan.Logger.Info("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))
        self.PeakCan.Logger.Info("indexStart: " + str(indexStart))
        self.PeakCan.Logger.Info("indexEnd: " + str(indexEnd))
        if 0.2 * (indexEnd - indexStart) < countDel:
            self.PeakCan.Logger.Warning("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))        
        [arrayBat, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.assertEqual(0, len(array2))
        self.assertEqual(0, len(array3))
        [arrayAccX, array2, arrayAccZ] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 0, 1, indexStart, indexEnd)
        self.assertEqual(0, len(array2))
        self.PeakCan.Logger.Info("Voltage Sampling Points: " + str(len(arrayBat)))
        self.PeakCan.Logger.Info("Acceleration Sampling Points: " + str(len(arrayAccZ)))
        self.PeakCan.ValueLog(arrayBat, array2, array3, fAdcRawDat, "Voltage", "")
        self.PeakCan.ValueLog(arrayAccX, array2, arrayAccZ, fAdcRawDat, "Acc", "")
        self.streamingValueCompare(arrayBat, array2, array3, VoltMiddleBat, VoltToleranceBat, 0, 0, 0, 0, fVoltageBattery)   
        self.streamingValueCompare(arrayAccX, array2, arrayAccZ, AdcMiddleX, AdcToleranceX, 0, 0, AdcMiddleZ, AdcToleranceZ, fAcceleration)    

    """
    Mixed Streaming - AccX + AccY + VoltageBattery
    """        

    def test0340MixedStreamingAccXYVoltBat(self):
        self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0)
        indexStart = self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 0)
        time.sleep(StreamingStandardTestTimeMs / 1000)
        indexEnd = self.PeakCan.GetReadArrayIndex() - 1
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"])   
        time.sleep(1)    
        countDel = 0
        while StreamingStandardTestTimeMs < self.PeakCan.getReadMessageTimeMs(indexStart, indexEnd) - 0.5:
            countDel += 1
            indexEnd -= 1
        self.PeakCan.Logger.Info("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))
        self.PeakCan.Logger.Info("indexStart: " + str(indexStart))
        self.PeakCan.Logger.Info("indexEnd: " + str(indexEnd))
        if 0.2 * (indexEnd - indexStart) < countDel:
            self.PeakCan.Logger.Warning("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))        
        [arrayBat, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.assertEqual(0, len(array2))
        self.assertEqual(0, len(array3))
        [arrayAccX, arrayAccY, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 0, indexStart, indexEnd)
        self.assertEqual(0, len(array3))
        self.PeakCan.Logger.Info("Voltage Sampling Points: " + str(len(arrayBat)))
        self.PeakCan.Logger.Info("Acceleration Sampling Points: " + str(len(arrayAccY)))
        self.PeakCan.ValueLog(arrayBat, array2, array3, fAdcRawDat, "Voltage", "")
        self.PeakCan.ValueLog(arrayAccX, arrayAccY, array3, fAdcRawDat, "Acc", "")
        self.streamingValueCompare(arrayBat, array2, array3, VoltMiddleBat, VoltToleranceBat, 0, 0, 0, 0, fVoltageBattery)   
        self.streamingValueCompare(arrayAccX, arrayAccY, array3, AdcMiddleX, AdcToleranceX, AdcMiddleY, AdcToleranceY, 0, 0, fAcceleration)  
        
    """
    Mixed Streaming - AccY + AccZ + VoltageBattery
    """        

    def test0341MixedStreamingAccYZVoltBat(self):
        self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0)
        indexStart = self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 0, 1, 1)
        time.sleep(StreamingStandardTestTimeMs / 1000)
        indexEnd = self.PeakCan.GetReadArrayIndex() - 1
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"])   
        time.sleep(1)    
        countDel = 0
        while StreamingStandardTestTimeMs < self.PeakCan.getReadMessageTimeMs(indexStart, indexEnd) - 0.5:
            countDel += 1
            indexEnd -= 1
        self.PeakCan.Logger.Info("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))
        self.PeakCan.Logger.Info("indexStart: " + str(indexStart))
        self.PeakCan.Logger.Info("indexEnd: " + str(indexEnd))
        if 0.2 * (indexEnd - indexStart) < countDel:
            self.PeakCan.Logger.Warning("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))        
        [arrayBat, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.assertEqual(0, len(array2))
        self.assertEqual(0, len(array3))
        [array1, arrayAccY, arrayAccZ] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 0, 1, 1, indexStart, indexEnd)
        self.assertEqual(0, len(array1))
        self.PeakCan.Logger.Info("Voltage Sampling Points: " + str(len(arrayBat)))
        self.PeakCan.Logger.Info("Acceleration Sampling Points: " + str(len(arrayAccY)))
        self.PeakCan.ValueLog(arrayBat, array2, array3, fAdcRawDat, "Voltage", "")
        self.PeakCan.ValueLog(array1, arrayAccY, arrayAccZ, fAdcRawDat, "Acc", "")
        self.streamingValueCompare(arrayBat, array2, array3, VoltMiddleBat, VoltToleranceBat, 0, 0, 0, 0, fVoltageBattery)   
        self.streamingValueCompare(array1, arrayAccY, arrayAccZ, 0, 0, AdcMiddleY, AdcToleranceY, AdcMiddleZ, AdcToleranceZ, fAcceleration)  
        
    """
    Mixed Streaming - AccX + AccY + AccZ + VoltageBattery
    """        

    def test0342MixedStreamingAccXYZVoltBat(self):
        self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0)
        indexStart = self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 1)
        time.sleep(StreamingStandardTestTimeMs / 1000)
        indexEnd = self.PeakCan.GetReadArrayIndex() - 1
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"])   
        time.sleep(1)    
        countDel = 0
        while StreamingStandardTestTimeMs < self.PeakCan.getReadMessageTimeMs(indexStart, indexEnd) - 0.5:
            countDel += 1
            indexEnd -= 1
        self.PeakCan.Logger.Info("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))
        self.PeakCan.Logger.Info("indexStart: " + str(indexStart))
        self.PeakCan.Logger.Info("indexEnd: " + str(indexEnd))
        if 0.2 * (indexEnd - indexStart) < countDel:
            self.PeakCan.Logger.Warning("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))        
        [arrayBat, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.assertEqual(0, len(array2))
        self.assertEqual(0, len(array3))
        [arrayAccX, arrayAccY, arrayAccZ] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 1, indexStart, indexEnd)
        self.PeakCan.Logger.Info("Voltage Sampling Points: " + str(len(arrayBat)))
        self.PeakCan.Logger.Info("Acceleration Sampling Points: " + str(len(arrayAccZ)))
        self.PeakCan.ValueLog(arrayBat, array2, array3, fAdcRawDat, "Voltage", "")
        self.PeakCan.ValueLog(arrayAccX, arrayAccY, arrayAccZ, fAdcRawDat, "Acc", "")
        self.streamingValueCompare(arrayBat, array2, array3, VoltMiddleBat, VoltToleranceBat, 0, 0, 0, 0, fVoltageBattery)   
        self.streamingValueCompare(arrayAccX, array2, arrayAccZ, AdcMiddleX, AdcToleranceX, AdcMiddleY, AdcToleranceY, AdcMiddleZ, AdcToleranceZ, fAcceleration)      
    
    """
    Stream Acceleration(X) and receive single sampling point for Battery
    """         

    def test0343StreamingAccXSingleBattery(self):
        indexStart = self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0)
        time.sleep(1.025)
        self.PeakCan.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], 1, 0, 0)
        time.sleep(9)
        indexEnd = self.PeakCan.GetReadArrayIndex()
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])
        [AccArray1, AccArray2, AccArray3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        [voltage1Array, voltage2Array, voltage3Array] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[1], 1, 0, 0, indexStart, indexEnd)
        self.assertEqual(0, len(AccArray2))
        self.assertEqual(0, len(AccArray3))
        self.assertEqual(1, len(voltage1Array))
        self.assertEqual(0, len(voltage2Array))
        self.assertEqual(0, len(voltage3Array))
        samplingPointsAccX = len(AccArray1) / 10
        self.PeakCan.Logger.Info("Battery Voltage Raw: " + str(voltage1Array[0]))
        self.singleValueCompare(voltage1Array, voltage2Array, voltage3Array, VoltMiddleBat, VoltToleranceBat, 0, 0, 0, 0, fVoltageBattery)
        self.PeakCan.Logger.Info("Accleration X Sampling Points per seconds: " + str(samplingPointsAccX))     
        calcRate = calcSamplingRate(AdcPrescalerReset, AdcAcquisitionTimeReset, AdcAcquisitionOverSamplingRateReset) 
        self.PeakCan.Logger.Info("Calculated Sampling Points per seconds: " + str(calcRate))   
        self.assertLess(calcRate * SamplingToleranceLow, samplingPointsAccX)
        self.assertGreater(calcRate * SamplingToleranceHigh, samplingPointsAccX)       
        
    """
    Stream Acceleration(Y) and receive single sampling point for Battery
    """         

    def test0344StreamingAccYSingleBattery(self):
        indexStart = self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 1, 0)
        time.sleep(1.025)
        self.PeakCan.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], 1, 0, 0)
        time.sleep(9)
        indexEnd = self.PeakCan.GetReadArrayIndex()
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])
        [AccArray1, AccArray2, AccArray3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 1, 0, indexStart, indexEnd)
        [voltage1Array, voltage2Array, voltage3Array] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[1], 1, 0, 0, indexStart, indexEnd)
        self.assertEqual(0, len(AccArray1))
        self.assertEqual(0, len(AccArray3))
        self.assertEqual(1, len(voltage1Array))
        self.assertEqual(0, len(voltage2Array))
        self.assertEqual(0, len(voltage3Array))
        samplingPointsAccY = len(AccArray2) / 10
        self.PeakCan.Logger.Info("Battery Voltage Raw: " + str(voltage1Array[0]))
        self.singleValueCompare(voltage1Array, voltage2Array, voltage3Array, VoltMiddleBat, VoltToleranceBat, 0, 0, 0, 0, fVoltageBattery)
        self.PeakCan.Logger.Info("Accleration Y Sampling Points per seconds: " + str(samplingPointsAccY))     
        calcRate = calcSamplingRate(AdcPrescalerReset, AdcAcquisitionTimeReset, AdcAcquisitionOverSamplingRateReset) 
        self.PeakCan.Logger.Info("Calculated Sampling Points per seconds: " + str(calcRate))   
        self.assertLess(calcRate * SamplingToleranceLow, samplingPointsAccY)
        self.assertGreater(calcRate * SamplingToleranceHigh, samplingPointsAccY)        

    """
    Stream Acceleration(Z) and receive single sampling point for Battery
    """         

    def test0345StreamingAccZSingleBattery(self):
        indexStart = self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 0, 1)
        time.sleep(1.025)
        self.PeakCan.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], 1, 0, 0)
        time.sleep(9)
        indexEnd = self.PeakCan.GetReadArrayIndex()
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])
        [AccArray1, AccArray2, AccArray3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 0, 1, indexStart, indexEnd)
        [voltage1Array, voltage2Array, voltage3Array] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[1], 1, 0, 0, indexStart, indexEnd)
        self.assertEqual(0, len(AccArray1))
        self.assertEqual(0, len(AccArray2))
        self.assertEqual(1, len(voltage1Array))
        self.assertEqual(0, len(voltage2Array))
        self.assertEqual(0, len(voltage3Array))
        samplingPointsAccZ = len(AccArray3) / 10
        self.PeakCan.Logger.Info("Battery Voltage Raw: " + str(voltage1Array[0]))
        self.singleValueCompare(voltage1Array, voltage2Array, voltage3Array, VoltMiddleBat, VoltToleranceBat, 0, 0, 0, 0, fVoltageBattery)
        self.PeakCan.Logger.Info("Accleration Z Sampling Points per seconds: " + str(samplingPointsAccZ))     
        calcRate = calcSamplingRate(AdcPrescalerReset, AdcAcquisitionTimeReset, AdcAcquisitionOverSamplingRateReset) 
        self.PeakCan.Logger.Info("Calculated Sampling Points per seconds: " + str(calcRate))   
        self.assertLess(calcRate * SamplingToleranceLow, samplingPointsAccZ)
        self.assertGreater(calcRate * SamplingToleranceHigh, samplingPointsAccZ)   
                       
    """
    Stream Battery and receive single sampling point for AccX
    """         

    def test0346StreamingBatterySingleAccX(self):
        indexStart = self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0)
        time.sleep(1.025)
        self.PeakCan.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 1, 0, 0)
        time.sleep(9)
        indexEnd = self.PeakCan.GetReadArrayIndex()
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"])
        [voltage1Array, voltage2Array, voltage3Array] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        [AccArray1, AccArray2, AccArray3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 0, 0, indexStart, indexEnd)
        self.assertEqual(0, len(AccArray2))
        self.assertEqual(0, len(AccArray3))
        self.assertEqual(1, len(AccArray1))
        self.assertEqual(0, len(voltage2Array))
        self.assertEqual(0, len(voltage3Array))
        samplingPointsBattery = len(voltage1Array) / 10
        self.PeakCan.Logger.Info("AccX Raw: " + str(AccArray1[0]))
        self.singleValueCompare(AccArray1, AccArray2, AccArray3, AdcRawMiddleX, AdcRawToleranceX, AdcRawMiddleY, AdcRawToleranceY, AdcRawMiddleZ, AdcRawToleranceZ, fAdcRawDat)
        self.PeakCan.Logger.Info("Battery Sampling Points per seconds: " + str(samplingPointsBattery))     
        calcRate = calcSamplingRate(AdcPrescalerReset, AdcAcquisitionTimeReset, AdcAcquisitionOverSamplingRateReset) 
        self.PeakCan.Logger.Info("Calculated Sampling Points per seconds: " + str(calcRate))   
        self.assertLess(calcRate * SamplingToleranceLow, samplingPointsBattery)
        self.assertGreater(calcRate * SamplingToleranceHigh, samplingPointsBattery)     
  
    """
    Stream Battery and receive single sampling point for AccY
    """         

    def test0347StreamingBatterySingleAccY(self):
        indexStart = self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0)
        time.sleep(1.025)
        self.PeakCan.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 0, 1, 0)
        time.sleep(9)
        indexEnd = self.PeakCan.GetReadArrayIndex()
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"])
        [voltage1Array, voltage2Array, voltage3Array] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        [AccArray1, AccArray2, AccArray3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 0, 1, 0, indexStart, indexEnd)
        self.assertEqual(0, len(AccArray1))
        self.assertEqual(0, len(AccArray3))
        self.assertEqual(1, len(AccArray2))
        self.assertEqual(0, len(voltage2Array))
        self.assertEqual(0, len(voltage3Array))
        samplingPointsBattery = len(voltage1Array) / 10
        self.PeakCan.Logger.Info("AccY Raw: " + str(AccArray2[0]))
        self.singleValueCompare(AccArray1, AccArray2, AccArray3, AdcRawMiddleX, AdcRawToleranceX, AdcRawMiddleY, AdcRawToleranceY, AdcRawMiddleZ, AdcRawToleranceZ, fAdcRawDat)
        self.PeakCan.Logger.Info("Battery Sampling Points per seconds: " + str(samplingPointsBattery))     
        calcRate = calcSamplingRate(AdcPrescalerReset, AdcAcquisitionTimeReset, AdcAcquisitionOverSamplingRateReset) 
        self.PeakCan.Logger.Info("Calculated Sampling Points per seconds: " + str(calcRate))   
        self.assertLess(calcRate * SamplingToleranceLow, samplingPointsBattery)
        self.assertGreater(calcRate * SamplingToleranceHigh, samplingPointsBattery) 

    """
    Stream Battery and receive single sampling point for AccZ
    """         

    def test0348StreamingBatterySingleAccZ(self):
        indexStart = self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0)
        time.sleep(1.025)
        self.PeakCan.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 0, 0, 1)
        time.sleep(9)
        indexEnd = self.PeakCan.GetReadArrayIndex()
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"])
        [voltage1Array, voltage2Array, voltage3Array] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        [AccArray1, AccArray2, AccArray3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 0, 0, 1, indexStart, indexEnd)
        self.assertEqual(0, len(AccArray1))
        self.assertEqual(0, len(AccArray2))
        self.assertEqual(1, len(AccArray3))
        self.assertEqual(0, len(voltage2Array))
        self.assertEqual(0, len(voltage3Array))
        samplingPointsBattery = len(voltage1Array) / 10
        self.PeakCan.Logger.Info("AccZ Raw: " + str(AccArray3[0]))
        self.singleValueCompare(AccArray1, AccArray2, AccArray3, AdcRawMiddleX, AdcRawToleranceX, AdcRawMiddleY, AdcRawToleranceY, AdcRawMiddleZ, AdcRawToleranceZ, fAdcRawDat)
        self.PeakCan.Logger.Info("Battery Sampling Points per seconds: " + str(samplingPointsBattery))     
        calcRate = calcSamplingRate(AdcPrescalerReset, AdcAcquisitionTimeReset, AdcAcquisitionOverSamplingRateReset) 
        self.PeakCan.Logger.Info("Calculated Sampling Points per seconds: " + str(calcRate))   
        self.assertLess(calcRate * SamplingToleranceLow, samplingPointsBattery)
        self.assertGreater(calcRate * SamplingToleranceHigh, samplingPointsBattery)        

    """
    Stream Battery and receive single sampling point for AccYZ
    """         

    def test0349StreamingBatterySingleAccYZ(self):
        indexStart = self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0)
        time.sleep(1.025)
        self.PeakCan.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 0, 1, 1)
        time.sleep(9)
        indexEnd = self.PeakCan.GetReadArrayIndex()
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"])
        [voltage1Array, voltage2Array, voltage3Array] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        [AccArray1, AccArray2, AccArray3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 0, 1, 1, indexStart, indexEnd)
        self.assertEqual(0, len(AccArray1))
        self.assertEqual(1, len(AccArray2))
        self.assertEqual(1, len(AccArray3))
        self.assertEqual(0, len(voltage2Array))
        self.assertEqual(0, len(voltage3Array))
        samplingPointsBattery = len(voltage1Array) / 10
        self.PeakCan.Logger.Info("AccY Raw: " + str(AccArray2[0]))
        self.PeakCan.Logger.Info("AccZ Raw: " + str(AccArray3[0]))
        self.singleValueCompare(AccArray1, AccArray2, AccArray3, AdcRawMiddleX, AdcRawToleranceX, AdcRawMiddleY, AdcRawToleranceY, AdcRawMiddleZ, AdcRawToleranceZ, fAdcRawDat)
        self.PeakCan.Logger.Info("Battery Sampling Points per seconds: " + str(samplingPointsBattery))     
        calcRate = calcSamplingRate(AdcPrescalerReset, AdcAcquisitionTimeReset, AdcAcquisitionOverSamplingRateReset) 
        self.PeakCan.Logger.Info("Calculated Sampling Points per seconds: " + str(calcRate))   
        self.assertLess(calcRate * SamplingToleranceLow, samplingPointsBattery)
        self.assertGreater(calcRate * SamplingToleranceHigh, samplingPointsBattery) 

    """
    Stream Battery and receive single sampling point for AccXZ
    """         

    def test0350StreamingBatterySingleAccXZ(self):
        indexStart = self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0)
        time.sleep(1.025)
        self.PeakCan.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 1, 0, 1)
        time.sleep(9)
        indexEnd = self.PeakCan.GetReadArrayIndex()
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"])
        [voltage1Array, voltage2Array, voltage3Array] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        [AccArray1, AccArray2, AccArray3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 0, 1, indexStart, indexEnd)
        self.assertEqual(1, len(AccArray1))
        self.assertEqual(0, len(AccArray2))
        self.assertEqual(1, len(AccArray3))
        self.assertEqual(0, len(voltage2Array))
        self.assertEqual(0, len(voltage3Array))
        samplingPointsBattery = len(voltage1Array) / 10
        self.PeakCan.Logger.Info("AccX Raw: " + str(AccArray1[0]))
        self.PeakCan.Logger.Info("AccZ Raw: " + str(AccArray3[0]))
        self.singleValueCompare(AccArray1, AccArray2, AccArray3, AdcRawMiddleX, AdcRawToleranceX, AdcRawMiddleY, AdcRawToleranceY, AdcRawMiddleZ, AdcRawToleranceZ, fAdcRawDat)
        self.PeakCan.Logger.Info("Battery Sampling Points per seconds: " + str(samplingPointsBattery))     
        calcRate = calcSamplingRate(AdcPrescalerReset, AdcAcquisitionTimeReset, AdcAcquisitionOverSamplingRateReset) 
        self.PeakCan.Logger.Info("Calculated Sampling Points per seconds: " + str(calcRate))   
        self.assertLess(calcRate * SamplingToleranceLow, samplingPointsBattery)
        self.assertGreater(calcRate * SamplingToleranceHigh, samplingPointsBattery)        

    """
    Stream Battery and receive single sampling point for AccXY
    """         

    def test0351StreamingBatterySingleAccXY(self):
        indexStart = self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0)
        time.sleep(1.025)
        self.PeakCan.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 1, 1, 0)
        time.sleep(9)
        indexEnd = self.PeakCan.GetReadArrayIndex()
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"])
        [voltage1Array, voltage2Array, voltage3Array] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        [AccArray1, AccArray2, AccArray3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 0, indexStart, indexEnd)
        self.assertEqual(1, len(AccArray1))
        self.assertEqual(1, len(AccArray2))
        self.assertEqual(0, len(AccArray3))
        self.assertEqual(0, len(voltage2Array))
        self.assertEqual(0, len(voltage3Array))
        samplingPointsBattery = len(voltage1Array) / 10
        self.PeakCan.Logger.Info("AccX Raw: " + str(AccArray1[0]))
        self.PeakCan.Logger.Info("AccY Raw: " + str(AccArray2[0]))
        self.singleValueCompare(AccArray1, AccArray2, AccArray3, AdcRawMiddleX, AdcRawToleranceX, AdcRawMiddleY, AdcRawToleranceY, AdcRawMiddleZ, AdcRawToleranceZ, fAdcRawDat)
        self.PeakCan.Logger.Info("Battery Sampling Points per seconds: " + str(samplingPointsBattery))     
        calcRate = calcSamplingRate(AdcPrescalerReset, AdcAcquisitionTimeReset, AdcAcquisitionOverSamplingRateReset) 
        self.PeakCan.Logger.Info("Calculated Sampling Points per seconds: " + str(calcRate))   
        self.assertLess(calcRate * SamplingToleranceLow, samplingPointsBattery)
        self.assertGreater(calcRate * SamplingToleranceHigh, samplingPointsBattery)

    """
    Stream Battery and receive single sampling point for AccXYZ
    """         

    def test0352StreamingBatterySingleAccXYZ(self):
        indexStart = self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0)
        time.sleep(1.025)
        self.PeakCan.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 1, 1, 1)
        time.sleep(9)
        indexEnd = self.PeakCan.GetReadArrayIndex()
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"])
        [voltage1Array, voltage2Array, voltage3Array] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        [AccArray1, AccArray2, AccArray3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 1, indexStart, indexEnd)
        self.assertEqual(1, len(AccArray1))
        self.assertEqual(1, len(AccArray2))
        self.assertEqual(1, len(AccArray3))
        self.assertEqual(0, len(voltage2Array))
        self.assertEqual(0, len(voltage3Array))
        samplingPointsBattery = len(voltage1Array) / 10
        self.PeakCan.Logger.Info("AccX Raw: " + str(AccArray1[0]))
        self.PeakCan.Logger.Info("AccY Raw: " + str(AccArray2[0]))
        self.PeakCan.Logger.Info("AccZ Raw: " + str(AccArray2[0]))
        self.singleValueCompare(AccArray1, AccArray2, AccArray3, AdcRawMiddleX, AdcRawToleranceX, AdcRawMiddleY, AdcRawToleranceY, AdcRawMiddleZ, AdcRawToleranceZ, fAdcRawDat)
        self.PeakCan.Logger.Info("Battery Sampling Points per seconds: " + str(samplingPointsBattery))     
        calcRate = calcSamplingRate(AdcPrescalerReset, AdcAcquisitionTimeReset, AdcAcquisitionOverSamplingRateReset) 
        self.PeakCan.Logger.Info("Calculated Sampling Points per seconds: " + str(calcRate))   
        self.assertLess(calcRate * SamplingToleranceLow, samplingPointsBattery)
        self.assertGreater(calcRate * SamplingToleranceHigh, samplingPointsBattery)        
   
    """
    Stream AccXY and receive single sampling point for Battery
    """         

    def test0353StreamingAccXYSingleBattery(self):
        prescaler = SamplingRateDoubleMaxPrescaler
        acqTime = SamplingRateDoubleMaxAcqTime
        overSamples = SamplingRateDoubleMaxOverSamples + 1
        self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], prescaler, acqTime, overSamples, AdcReference["VDD"])
        self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 0)
        time.sleep(1.025)
        indexStart = self.PeakCan.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], 1, 0, 0)
        time.sleep(10)
        indexEnd = self.PeakCan.GetReadArrayIndex()
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])
        [AccArray1, AccArray2, AccArray3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 0, indexStart, indexEnd)
        [voltage1Array, voltage2Array, voltage3Array] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[1], 1, 0, 0, indexStart, indexEnd)
        self.assertEqual(0, len(AccArray3))
        self.assertEqual(1, len(voltage1Array))
        self.assertEqual(0, len(voltage2Array))
        self.assertEqual(0, len(voltage3Array))
        samplingPointsAccX = len(AccArray1) / 10
        samplingPointsAccY = len(AccArray2) / 10
        self.PeakCan.Logger.Info("Battery Voltage Raw: " + str(voltage1Array[0]))
        self.singleValueCompare(voltage1Array, voltage2Array, voltage3Array, VoltMiddleBat, VoltToleranceBat, 0, 0, 0, 0, fVoltageBattery)
        self.PeakCan.Logger.Info("Accleration XY Sampling Points per seconds: " + str(samplingPointsAccX))     
        calcRate = calcSamplingRate(prescaler, acqTime, overSamples) 
        calcRate /= 2
        calcRate *= 1.1
        self.PeakCan.Logger.Info("Calculated Sampling Points per seconds: " + str(calcRate))   
        self.assertLess(calcRate * SamplingToleranceLow, samplingPointsAccX)
        self.assertGreater(calcRate * SamplingToleranceHigh, samplingPointsAccX)  
        self.assertEqual(samplingPointsAccX, samplingPointsAccY)
        
    """
    Stream AccXZ and receive single sampling point for Battery
    """         

    def test0354StreamingAccXZSingleBattery(self):
        prescaler = SamplingRateDoubleMaxPrescaler
        acqTime = SamplingRateDoubleMaxAcqTime
        overSamples = SamplingRateDoubleMaxOverSamples + 1
        self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], prescaler, acqTime, overSamples, AdcReference["VDD"])
        self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 0, 1)
        time.sleep(1.025)
        indexStart = self.PeakCan.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], 1, 0, 0, DataSets[1])
        time.sleep(10)
        indexEnd = self.PeakCan.GetReadArrayIndex()
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])
        [AccArray1, AccArray2, AccArray3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 0, 1, indexStart, indexEnd)
        [voltage1Array, voltage2Array, voltage3Array] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[1], 1, 0, 0, indexStart, indexEnd)
        self.assertEqual(0, len(AccArray2))
        self.assertEqual(1, len(voltage1Array))
        self.assertEqual(0, len(voltage2Array))
        self.assertEqual(0, len(voltage3Array))
        samplingPointsAccX = len(AccArray1) / 10
        samplingPointsAccZ = len(AccArray3) / 10
        self.PeakCan.Logger.Info("Battery Voltage Raw: " + str(voltage1Array[0]))
        self.singleValueCompare(voltage1Array, voltage2Array, voltage3Array, VoltMiddleBat, VoltToleranceBat, 0, 0, 0, 0, fVoltageBattery)
        self.PeakCan.Logger.Info("Accleration XZ Sampling Points per seconds: " + str(samplingPointsAccX))     
        calcRate = calcSamplingRate(prescaler, acqTime, overSamples) 
        calcRate /= 2
        calcRate *= 1.1
        self.PeakCan.Logger.Info("Calculated Sampling Points per seconds: " + str(calcRate))   
        self.assertLess(calcRate * SamplingToleranceLow, samplingPointsAccX)
        self.assertGreater(calcRate * SamplingToleranceHigh, samplingPointsAccX)  
        self.assertEqual(samplingPointsAccX, samplingPointsAccZ)

    """
    Stream AccYZ and receive single sampling point for Battery
    """         

    def test0355StreamingAccYZSingleBattery(self):
        prescaler = SamplingRateDoubleMaxPrescaler
        acqTime = SamplingRateDoubleMaxAcqTime
        overSamples = SamplingRateDoubleMaxOverSamples + 1
        self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], prescaler, acqTime, overSamples, AdcReference["VDD"])
        self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 0, 1, 1)
        time.sleep(1.025)
        indexStart = self.PeakCan.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], 1, 0, 0)
        time.sleep(10)
        indexEnd = self.PeakCan.GetReadArrayIndex()
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])
        [AccArray1, AccArray2, AccArray3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 0, 1, 1, indexStart, indexEnd)
        [voltage1Array, voltage2Array, voltage3Array] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[1], 1, 0, 0, indexStart, indexEnd)
        self.assertEqual(0, len(AccArray1))
        self.assertEqual(1, len(voltage1Array))
        self.assertEqual(0, len(voltage2Array))
        self.assertEqual(0, len(voltage3Array))
        samplingPointsAccY = len(AccArray2) / 10
        samplingPointsAccZ = len(AccArray3) / 10
        self.PeakCan.Logger.Info("Battery Voltage Raw: " + str(voltage1Array[0]))
        self.singleValueCompare(voltage1Array, voltage2Array, voltage3Array, VoltMiddleBat, VoltToleranceBat, 0, 0, 0, 0, fVoltageBattery)
        self.PeakCan.Logger.Info("Accleration YZ Sampling Points per seconds: " + str(samplingPointsAccY))     
        calcRate = calcSamplingRate(prescaler, acqTime, overSamples) 
        calcRate /= 2
        calcRate *= 1.1
        self.PeakCan.Logger.Info("Calculated Sampling Points per seconds: " + str(calcRate))   
        self.assertLess(calcRate * SamplingToleranceLow, samplingPointsAccY)
        self.assertGreater(calcRate * SamplingToleranceHigh, samplingPointsAccY)  
        self.assertEqual(samplingPointsAccY, samplingPointsAccZ)

    """
    Stream AccXXZ and receive single sampling point for Battery
    """         

    def test0356StreamingAccXYZSingleBattery(self):
        indexStart = self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 1)
        time.sleep(1.025)
        self.PeakCan.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], 1, 0, 0)
        time.sleep(9)
        indexEnd = self.PeakCan.GetReadArrayIndex()
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])
        [AccArray1, AccArray2, AccArray3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 1, indexStart, indexEnd)
        [voltage1Array, voltage2Array, voltage3Array] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[1], 1, 0, 0, indexStart, indexEnd)
        self.assertEqual(1, len(voltage1Array))
        self.assertEqual(0, len(voltage2Array))
        self.assertEqual(0, len(voltage3Array))
        samplingPointsAccX = len(AccArray1) / 10
        samplingPointsAccY = len(AccArray2) / 10
        samplingPointsAccZ = len(AccArray3) / 10
        self.PeakCan.Logger.Info("Battery Voltage Raw: " + str(voltage1Array[0]))
        self.singleValueCompare(voltage1Array, voltage2Array, voltage3Array, VoltMiddleBat, VoltToleranceBat, 0, 0, 0, 0, fVoltageBattery)
        self.PeakCan.Logger.Info("Accleration XYZ Sampling Points per seconds: " + str(samplingPointsAccY))     
        calcRate = calcSamplingRate(AdcPrescalerReset, AdcAcquisitionTimeReset, AdcAcquisitionOverSamplingRateReset) 
        calcRate /= 3
        self.PeakCan.Logger.Info("Calculated Sampling Points per seconds: " + str(calcRate))   
        self.assertLess(calcRate * SamplingToleranceLow, samplingPointsAccY)
        self.assertGreater(calcRate * SamplingToleranceHigh, samplingPointsAccY)  
        self.assertEqual(samplingPointsAccY, samplingPointsAccZ)
        self.assertEqual(samplingPointsAccX, samplingPointsAccZ)        

    """
    Stream Start and Stop -> Test communication protocol to be ok and that HW fits(will fit)
    """         

    def test0370StreamingOnfOff(self):
        _runs = 100
        # single stream, data set 3
        for _i in range(0, _runs):
            self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0)
            self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])
        
        # single stream, data set 1
        for _i in range(0, _runs):
            self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], SamplingRateSingleMaxPrescaler, SamplingRateSingleMaxAcqTime, SamplingRateSingleMaxOverSamples + 2, AdcReference["VDD"])
            self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 0, 0)
            self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])

        # multi stream, data set 3
        for _i in range(0, _runs):
            self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 1)
            self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0)
            self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])
            self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"])

        # multi stream, data set 1
        for _i in range(0, _runs):
            self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], SamplingRateSingleMaxPrescaler, SamplingRateSingleMaxAcqTime, SamplingRateSingleMaxOverSamples + 2, AdcReference["VDD"])
            self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 1)
            self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[1], 1, 0, 0)
            self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])
            self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"])                        
                                                              
    """
    Test x-Axis Line
    """

    def test0380GetStreamingTestLineAccX(self):
        [indexStart, indexEnd] = self.streamingTestSignalCollect(MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], TestCommandSignal["Line"], SthModule["Streaming"], 2 ** 15, DataSets[3], 1, 0, 0, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "TestLine(AccelerationX - " + str(2 ** 15) + ")", "")
        self.streamingValueCompare(array1, array2, array3, 2 ** 15, 0, 0, 0, 0, 0, fAdcRawDat)
        [indexStart, indexEnd] = self.streamingTestSignalCollect(MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], TestCommandSignal["Line"], SthModule["Streaming"], 2 ** 14, DataSets[3], 1, 0, 0, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "TestLine(AccelerationX - " + str(2 ** 14) + ")", "")
        self.streamingValueCompare(array1, array2, array3, 2 ** 14, 0, 0, 0, 0, 0, fAdcRawDat)

    """
    Test y-Axis Line
    """

    def test0381GetStreamingTestLineAccY(self):
        [indexStart, indexEnd] = self.streamingTestSignalCollect(MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], TestCommandSignal["Line"], SthModule["Streaming"], 2 ** 15, DataSets[3], 0, 1, 0, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 1, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "TestLine(AccelerationY - " + str(2 ** 15) + ")", "")
        self.streamingValueCompare(array1, array2, array3, 0, 0, 2 ** 15, 0, 0, 0, fAdcRawDat)
        [indexStart, indexEnd] = self.streamingTestSignalCollect(MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], TestCommandSignal["Line"], SthModule["Streaming"], 2 ** 14, DataSets[3], 0, 1, 0, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 1, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "TestLine(AccelerationY - " + str(2 ** 14) + ")", "")
        self.streamingValueCompare(array1, array2, array3, 0, 0, 2 ** 14, 0, 0, 0, fAdcRawDat)

    """
    Test z-Axis Line
    """

    def test0382GetStreamingTestLineAccZ(self):
        [indexStart, indexEnd] = self.streamingTestSignalCollect(MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], TestCommandSignal["Line"], SthModule["Streaming"], 2 ** 15, DataSets[3], 0, 0, 1, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 0, 1, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "TestLine(AccelerationZ - " + str(2 ** 15) + ")", "")
        self.streamingValueCompare(array1, array2, array3, 0, 0, 0, 0, 2 ** 15, 0, fAdcRawDat)
        [indexStart, indexEnd] = self.streamingTestSignalCollect(MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], TestCommandSignal["Line"], SthModule["Streaming"], 2 ** 14, DataSets[3], 0, 0, 1, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 0, 1, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "TestLine(AccelerationZ - " + str(2 ** 14) + ")", "")
        self.streamingValueCompare(array1, array2, array3, 0, 0, 0, 0, 2 ** 14, 0, fAdcRawDat)

    """
    Test Battery Line
    """

    def test0383GetStreamingTestLineBattery(self):
        [indexStart, indexEnd] = self.streamingTestSignalCollect(MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], TestCommandSignal["Line"], SthModule["Streaming"], 2 ** 15, DataSets[3], 1, 0, 0, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "TestLine(Battery - " + str(2 ** 15) + ")", "")
        self.streamingValueCompare(array1, array2, array3, 2 ** 15, 0, 0, 0, 0, 0, fAdcRawDat)
        [indexStart, indexEnd] = self.streamingTestSignalCollect(MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], TestCommandSignal["Line"], SthModule["Streaming"], 2 ** 14, DataSets[3], 1, 0, 0, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "TestLine(Battery - " + str(2 ** 14) + ")", "")
        self.streamingValueCompare(array1, array2, array3, 2 ** 14, 0, 0, 0, 0, 0, fAdcRawDat)

    """
    Test x-Axis Ramp
    """

    def test0384GetStreamingTestRampAccX(self):
        [indexStart, indexEnd] = self.streamingTestSignalCollect(MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], TestCommandSignal["Ramp"], SthModule["Streaming"], 2 ** 16 - 1, DataSets[3], 1, 0, 0, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "TestRamp(AccelerationX)", "")
        self.PeakCan.Logger.Info("Find 0 to determine start point for comparing")
        startPoint = None
        for i in range(0, 180):
            if 0 == array1[i]:
                startPoint = i
        self.assertNotEqual(None, startPoint)
        self.PeakCan.Logger.Info("Comparing first 180 Data Points, starting with " + str(startPoint))
        self.streamingValueCompareSignal(array1[startPoint:startPoint + 180], testRampDim((2 ** 16 - 1), 3, 60, None))
        self.PeakCan.Logger.Info("Comparing second 180 Data Points")
        self.streamingValueCompareSignal(array1[startPoint + 180:startPoint + 360], testRampDim((2 ** 16 - 1), 3, 60, None))

    """
    Test Y-Axis Ramp
    """

    def test0385GetStreamingTestRampAccY(self):
        [indexStart, indexEnd] = self.streamingTestSignalCollect(MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], TestCommandSignal["Ramp"], SthModule["Streaming"], 2 ** 16 - 1, DataSets[3], 0, 1, 0, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 1, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "TestRamp(AccelerationY)", "")
        self.PeakCan.Logger.Info("Find 0 to determine start point for comparing")
        startPoint = None
        for i in range(0, 180):
            if 0 == array2[i]:
                startPoint = i
        self.assertNotEqual(None, startPoint)
        self.PeakCan.Logger.Info("Comparing first 180 Data Points, starting with " + str(startPoint))
        self.streamingValueCompareSignal(array2[startPoint:startPoint + 180], testRampDim((2 ** 16 - 1), 3, 60, None))
        self.PeakCan.Logger.Info("Comparing second 180 Data Points")
        self.streamingValueCompareSignal(array2[startPoint + 180:startPoint + 360], testRampDim((2 ** 16 - 1), 3, 60, None))

    """
    Test Z-Axis Ramp
    """

    def test0386GetStreamingTestRampAccZ(self):
        [indexStart, indexEnd] = self.streamingTestSignalCollect(MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], TestCommandSignal["Ramp"], SthModule["Streaming"], 2 ** 16 - 1, DataSets[3], 0, 0, 1, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 0, 1, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "TestRamp(AccelerationZ)", "")
        self.PeakCan.Logger.Info("Find 0 to determine start point for comparing")
        startPoint = None
        for i in range(0, 180):
            if 0 == array3[i]:
                startPoint = i
        self.assertNotEqual(None, startPoint)
        self.PeakCan.Logger.Info("Comparing first 180 Data Points, starting with " + str(startPoint))
        self.streamingValueCompareSignal(array3[startPoint:startPoint + 180], testRampDim((2 ** 16 - 1), 3, 60, None))
        self.PeakCan.Logger.Info("Comparing second 180 Data Points")
        self.streamingValueCompareSignal(array3[startPoint + 180:startPoint + 360], testRampDim((2 ** 16 - 1), 3, 60, None))

    """
    Test Battery Ramp
    """

    def test0387GetStreamingTestRampBattery(self):
        [indexStart, indexEnd] = self.streamingTestSignalCollect(MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], TestCommandSignal["Ramp"], SthModule["Streaming"], 2 ** 16 - 1, DataSets[3], 1, 0, 0, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "TestRamp(Battery)", "")
        self.PeakCan.Logger.Info("Find 0 to determine start point for comparing")
        startPoint = None
        for i in range(0, 180):
            if 0 == array1[i]:
                startPoint = i
        self.assertNotEqual(None, startPoint)
        self.PeakCan.Logger.Info("Comparing first 180 Data Points, starting with " + str(startPoint))
        self.streamingValueCompareSignal(array1[startPoint:startPoint + 180], testRampDim((2 ** 16 - 1), 3, 60, None))
        self.PeakCan.Logger.Info("Comparing second 180 Data Points")
        self.streamingValueCompareSignal(array1[startPoint + 180:startPoint + 360], testRampDim((2 ** 16 - 1), 3, 60, None))

    """
    Testing Sampling Rate - Reset
    """

    def test0500SamplingRateReset(self):
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0, StreamingStandardTestTimeMs)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        calcRate = calcSamplingRate(AdcPrescalerReset, AdcAcquisitionTimeReset, AdcAcquisitionOverSamplingRateReset)
        samplingPoints = self.PeakCan.samplingPoints(array1, array2, array3)
        self.PeakCan.Logger.Info("Running Time: " + str(StreamingStandardTestTimeMs) + "ms")
        self.PeakCan.Logger.Info("Startup Time: " + str(StreamingStartupTimeMs) + "ms")
        self.PeakCan.Logger.Info("Assumed Sampling Points/s: " + str(calcRate))
        samplingRateDet = 1000 * samplingPoints / (StreamingStandardTestTimeMs)
        self.PeakCan.Logger.Info("Determined Sampling Points/s: " + str(samplingRateDet))
        self.PeakCan.Logger.Info("Difference: " + str((100 * samplingRateDet - calcRate) / calcRate) + "%")
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "")
        self.streamingValueCompare(array1, array2, array3, AdcRawMiddleX, AdcRawToleranceX, AdcRawMiddleY, AdcRawToleranceY, AdcRawMiddleZ, AdcRawToleranceZ, fAdcRawDat)
        self.assertLess(StreamingStandardTestTimeMs / 1000 * calcRate * SamplingToleranceLow, samplingPoints)
        self.assertGreater(StreamingStandardTestTimeMs / 1000 * calcRate * SamplingToleranceHigh, samplingPoints)

    """
    Testing ADC Sampling Rate - Prescaler
    """

    def test0501SamplingRatePreq(self):
        self.SamplingRate(5, SamplingRateSingleMaxAcqTime, SamplingRateSingleMaxOverSamples, AdcReference["VDD"])

    """
    Testing ADC Sampling Rate - Acquisiton Time
    """

    def test0502SamplingRateAqu(self):
        self.SamplingRate(2, AdcAcquisitionTime[32], AdcOverSamplingRate[64], AdcReference["VDD"])

    """
    Testing ADC Sampling Rate - Oversampling Rate
    """

    def test0503SamplingRateOverSampling(self):
        self.SamplingRate(5, AdcAcquisitionTime[8], AdcOverSamplingRate[32], AdcReference["VDD"])

    """
    Testing ADC Sampling Rate - Maximum(Single Data)
    """

    def test0504SamplingRateDataSingleMax(self):
        calcRate = self.SamplingRate(SamplingRateSingleMaxPrescaler, SamplingRateSingleMaxAcqTime, SamplingRateSingleMaxOverSamples, AdcReference["VDD"], runTime=10000)["SamplingRate"]
        print("Maximum Sampling Rate(Single Sampling): " + str(calcRate))

    """
    Testing ADC Sampling Rate - Maximum(Double Data)
    """

    def test0505SamplingRateDataDoubleMax(self):
        calcRate = self.SamplingRate(SamplingRateDoubleMaxPrescaler, SamplingRateDoubleMaxAcqTime, SamplingRateDoubleMaxOverSamples, AdcReference["VDD"], b1=1, b2=1, b3=0, runTime=10000)["SamplingRate"]
        print("Maximum Sampling Rate(Double Sampling): " + str(calcRate))

    """
    Testing ADC Sampling Rate - Maximum(Tripple Data)
    """

    def test0506SamplingRateDataTrippleMax(self):
        calcRate = self.SamplingRate(SamplingRateTrippleMaxPrescaler, SamplingRateTrippleMaxAcqTime, SamplingRateTrippleMaxOverSamples, AdcReference["VDD"], b1=1, b2=1, b3=1, runTime=10000)["SamplingRate"]
        print("Maximum Sampling Rate(Tripple Sampling): " + str(calcRate))

    """
    Testing ADC Reference voltagegs
    """

    def test0507VRef(self):
        self.PeakCan.Logger.Info("Warm Up")
        self.SamplingRate(SamplingRateTrippleMaxPrescaler, SamplingRateTrippleMaxAcqTime, SamplingRateTrippleMaxOverSamples, AdcReference["VDD"], b1=1, b2=1, b3=1, runTime=5000)
        for _vRefkey, vRefVal in AdcReference.items():
            self.PeakCan.Logger.Info("Using Voltage Reference: " + VRefName[vRefVal])
            self.SamplingRate(SamplingRateTrippleMaxPrescaler, SamplingRateTrippleMaxAcqTime, SamplingRateTrippleMaxOverSamples, vRefVal, b1=1, b2=1, b3=1, runTime=5000, compare=(AdcReference["Vfs1V65"] <= vRefVal), startupTime=False)

    """
    ADC Configuration Combine all possible settings - Single Axis (but only for prescaler 2)
    """

    def test0508AdcConfigSingle(self):
        SamplingRateMaxDet = 0
        prescaler = 2
        aquisitionTime = 0
        overSamples = 0
        for acquisitionTimeKey, acquisitionTimeValue in AdcAcquisitionTime.items():
            for overSamplingKey, overSamplingVal in AdcOverSamplingRate.items():
                samplingRate = int(calcSamplingRate(prescaler, acquisitionTimeValue, overSamplingVal))
                if SamplingRateSingleMax >= samplingRate and SamplingRateMin <= samplingRate:
                    self.PeakCan.Logger.Info("Sampling Rate: " + str(samplingRate))
                    self.PeakCan.Logger.Info("Prescaler: " + str(prescaler))
                    self.PeakCan.Logger.Info("Acquisition Time: " + AdcAcquisitionTimeName[acquisitionTimeValue])
                    self.PeakCan.Logger.Info("Oversampling Rate: " + AdcOverSamplingRateName[overSamplingVal])
                    for _vRefkey, vRefVal in AdcReference.items():
                        result = self.SamplingRate(prescaler, acquisitionTimeValue, overSamplingVal, vRefVal, b1=1, b2=0, b3=0, runTime=1000, compare=False, compareRate=False, log=False)
                        samplingPointsDet = self.PeakCan.samplingPoints(result["Value1"], result["Value2"], result["Value3"])
                        self.PeakCan.Logger.Info("Sampling Rate Determined: " + str(samplingPointsDet))
                        if samplingRate > SamplingToleranceHigh * samplingPointsDet:
                            break
                    self.assertGreaterEqual(samplingRate, SamplingToleranceLow * result["SamplingRate"])
                    if SamplingRateMaxDet < samplingRate:
                        aquisitionTime = acquisitionTimeKey
                        overSamples = overSamplingKey
                        SamplingRateMaxDet = samplingRate
                    self.PeakCan.Logger.Info("Prescaer - Proved: " + str(prescaler))
                    self.PeakCan.Logger.Info("Acquisition Time - Proved: " + AdcAcquisitionTimeName[acquisitionTimeValue])
                    self.PeakCan.Logger.Info("Oversampling Rate - Proved: " + AdcOverSamplingRateName[overSamplingVal])
                    self._resetStu()
                    self.PeakCan.Logger.Info("Connect to STH")
                    self.PeakCan.BlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])
        self.PeakCan.Logger.Info("Maximum Single Sampling Rate: " + str(SamplingRateMaxDet) + "(" + str(prescaler) + "/" + str(aquisitionTime) + "/" + str(overSamples) + ")")
        self.assertEqual(SamplingRateMaxDet, SamplingRateSingleMax)

    """
    Combine all possible settings - Double Axis (but only for prescaler 3)
    """

    def test0509AdcConfigDouble(self):
        SamplingRateMaxDet = 0
        prescaler = SamplingRateDoubleMaxPrescaler
        aquisitionTime = 0
        overSamples = 0
        for acquisitionTimeKey, acquisitionTimeValue in AdcAcquisitionTime.items():
            for overSamplingKey, overSamplingVal in AdcOverSamplingRate.items():
                samplingRate = int(calcSamplingRate(prescaler, acquisitionTimeValue, overSamplingVal))
                if SamplingRateDoubleMax >= samplingRate and SamplingRateMin <= samplingRate:
                    self.PeakCan.Logger.Info("Sampling Rate: " + str(samplingRate))
                    self.PeakCan.Logger.Info("Prescaer: " + str(prescaler))
                    self.PeakCan.Logger.Info("Acquisition Time: " + AdcAcquisitionTimeName[acquisitionTimeValue])
                    self.PeakCan.Logger.Info("Oversampling Rate: " + AdcOverSamplingRateName[overSamplingVal])
                    for _vRefkey, vRefVal in AdcReference.items():
                        result = self.SamplingRate(prescaler, acquisitionTimeValue, overSamplingVal, vRefVal, b1=1, b2=1, b3=0, runTime=1000, compare=False, compareRate=False, log=False)
                        samplingPointsDet = self.PeakCan.samplingPoints(result["Value1"], result["Value2"], result["Value3"])
                        self.PeakCan.Logger.Info("Sampling Rate Determined: " + str(samplingPointsDet))
                        if samplingRate > SamplingToleranceHigh * samplingPointsDet:
                            break
                    self.assertGreaterEqual(samplingRate, SamplingToleranceLow * result["SamplingRate"])
                    if SamplingRateMaxDet < samplingRate:
                        aquisitionTime = acquisitionTimeKey
                        overSamples = overSamplingKey
                        SamplingRateMaxDet = samplingRate
                    self.PeakCan.Logger.Info("Prescaer - Proved: " + str(prescaler))
                    self.PeakCan.Logger.Info("Acquisition Time - Proved: " + AdcAcquisitionTimeName[acquisitionTimeValue])
                    self.PeakCan.Logger.Info("Oversampling Rate - Proved: " + AdcOverSamplingRateName[overSamplingVal])
                    self._resetStu()
                    self.PeakCan.Logger.Info("Connect to STH")
                    self.PeakCan.BlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])
        self.PeakCan.Logger.Info("Maximum Double Sampling Rate: " + str(SamplingRateMaxDet) + "(" + str(prescaler) + "/" + str(aquisitionTime) + "/" + str(overSamples) + ")")
        self.assertEqual(SamplingRateMaxDet, SamplingRateDoubleMax)

    """
    Combine all possible settings - Tripple Axis (but only for prescaler 2)
    """

    def test0510AdcConfigTripple(self):
        SamplingRateMaxDet = 0
        prescaler = 2
        aquisitionTime = 0
        overSamples = 0
        for acquisitionTimeKey, acquisitionTimeValue in AdcAcquisitionTime.items():
            for overSamplingKey, overSamplingVal in AdcOverSamplingRate.items():
                samplingRate = int(calcSamplingRate(prescaler, acquisitionTimeValue, overSamplingVal))
                if SamplingRateTrippleMax >= samplingRate and SamplingRateMin <= samplingRate:
                    self.PeakCan.Logger.Info("Sampling Rate: " + str(samplingRate))
                    self.PeakCan.Logger.Info("Prescaer: " + str(prescaler))
                    self.PeakCan.Logger.Info("Acquisition Time: " + AdcAcquisitionTimeName[acquisitionTimeValue])
                    self.PeakCan.Logger.Info("Oversampling Rate: " + AdcOverSamplingRateName[overSamplingVal])
                    for _vRefkey, vRefVal in AdcReference.items():
                        result = self.SamplingRate(prescaler, acquisitionTimeValue, overSamplingVal, vRefVal, b1=1, b2=1, b3=1, runTime=1000, compare=False, compareRate=False, log=False)
                        samplingPointsDet = self.PeakCan.samplingPoints(result["Value1"], result["Value2"], result["Value3"])
                        self.PeakCan.Logger.Info("Sampling Rate Determined: " + str(samplingPointsDet))
                        if samplingRate > SamplingToleranceHigh * samplingPointsDet:
                            break
                    self.assertGreaterEqual(samplingRate, SamplingToleranceLow * result["SamplingRate"])
                    if SamplingRateMaxDet < samplingRate:
                        aquisitionTime = acquisitionTimeKey
                        overSamples = overSamplingKey
                        SamplingRateMaxDet = samplingRate
                    self.PeakCan.Logger.Info("Prescaer - Proved: " + str(prescaler))
                    self.PeakCan.Logger.Info("Acquisition Time - Proved: " + AdcAcquisitionTimeName[acquisitionTimeValue])
                    self.PeakCan.Logger.Info("Oversampling Rate - Proved: " + AdcOverSamplingRateName[overSamplingVal])
                    self._resetStu()
                    self.PeakCan.Logger.Info("Connect to STH")
                    self.PeakCan.BlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])
        self.PeakCan.Logger.Info("Maximum Tripple Sampling Rate: " + str(SamplingRateMaxDet))
        self.PeakCan.Logger.Info("Maximum Tripple Sampling Rate: " + str(SamplingRateMaxDet) + "(" + str(prescaler) + "/" + str(aquisitionTime) + "/" + str(overSamples) + ")")
        self.assertEqual(SamplingRateMaxDet, SamplingRateTrippleMax)

    """
    Testing ADC Sampling Prescaler Min
    """

    def test0511AdcPrescalerMin(self):
        self.SamplingRate(Prescaler["Min"], SamplingRateSingleMaxAcqTime, SamplingRateSingleMaxOverSamples, AdcReference["VDD"], b1=1, b2=0, b3=0, runTime=4000)

    """
    Testing ADC Sampling Prescaler Min/Max
    """

    def test0512AdcPrescalerMax(self):
        self.SamplingRate(Prescaler["Max"], AdcAcquisitionTime[1], AdcOverSamplingRate[32], AdcReference["VDD"], b1=1, b2=0, b3=0, runTime=10000)
   
    """
    Testing ADC Sampling Acquisition Min
    """

    def test0513AdcAcquisitionMin(self):
        self.SamplingRate(2, AdcAcquisitionTime[1], AdcOverSamplingRate[128], AdcReference["VDD"], b1=1, b2=0, b3=0, runTime=4000)

    """
    Testing ADC Sampling Acquisition Max
    """

    def test0514AdcAcquisitionMax(self):
        self.SamplingRate(2, AdcOverSamplingRate[256], AdcOverSamplingRate[32], AdcReference["VDD"], b1=1, b2=0, b3=0, runTime=4000)
  
    """
    Testing ADC Sampling Oversampling Rate Min
    """

    def test0515AdcOverSamplingRateMin(self):
        self.SamplingRate(32, AdcOverSamplingRate[256], AdcOverSamplingRate[2], AdcReference["VDD"], b1=1, b2=0, b3=0, runTime=4000)

    """
    Testing ADC Sampling Oversampling Rate Max
    """

    def test0516AdcOverSamplingRateMax(self):
        self.SamplingRate(2, AdcAcquisitionTime[1], AdcOverSamplingRate[4096], AdcReference["VDD"], b1=1, b2=0, b3=0, runTime=20000)
          
    """
    Testing ADC Sampling Oversampling Rate None
    """

    def test0517AdcOverSamplingRateNone(self):
        self.SamplingRate(64, AdcAcquisitionTime[256], AdcOverSamplingRate[1], AdcReference["VDD"], b1=1, b2=0, b3=0, runTime=4000)

    """
    Inject oversampling Rate fault. See that error status word is set correctly and tha the system still works
    """               

    def test0518AdcSamplingRateOverdrive(self):
        prescaler = 2
        acquisitionTime = AdcAcquisitionTime[1]
        overSamplingRate = AdcOverSamplingRate[2]
        Settings = self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], prescaler, acquisitionTime, overSamplingRate, AdcReference["VDD"])[1:]
        self.assertEqual(prescaler, Settings[0])
        self.assertEqual(acquisitionTime, Settings[1])
        self.assertEqual(overSamplingRate, Settings[2])
        self.assertEqual(AdcReference["VDD"], Settings[3])
        indexStart = self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0)
        time.sleep(10)
        self.PeakCan.GetReadArrayIndex() - 1
        ack = self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], bErrorExit=False)
        indexStop = self.PeakCan.GetReadArrayIndex() - 1
        BytesTransfered = indexStop - indexStart
        BytesTransfered *= 8
        self.assertNotEqual("Error", ack)
        ErrorWord = SthErrorWord()
        ErrorWord.asword = self.PeakCan.statusWord1(MyToolItNetworkNr["STH1"])
        self.PeakCan.Logger.Info("Reset bError Status Word")
        self.PeakCan.Logger.Info("STH bError Word Reserved: " + hex(ErrorWord.b.Reserved))
        self.PeakCan.Logger.Info("STH bError Word bAdcOverRun: " + hex(ErrorWord.b.bAdcOverRun))
        self.PeakCan.Logger.Info("STH bError Word bTxFail: " + hex(ErrorWord.b.bTxFail))
        self.PeakCan.Logger.Info("Trasnfered Bytes: " + str(BytesTransfered))
        self.assertLessEqual(BytesTransfered, 1000)
        self.assertEqual(ErrorWord.b.bAdcOverRun, 1)
        self._resetStu()        
        self.PeakCan.BlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])
        
    """
    Mixed Streaming - AccX + VoltageBattery
    """        

    def test0519SamplingRateMixedStreamingAccXBat(self):
        prescaler = SamplingRateSingleMaxPrescaler
        acquisitionTime = SamplingRateSingleMaxAcqTime
        overSamplingRate = SamplingRateSingleMaxOverSamples
        adcRef = AdcReference["VDD"]
        Settings = self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], prescaler, acquisitionTime, overSamplingRate, adcRef)[1:]
        self.assertEqual(prescaler, Settings[0])
        self.assertEqual(acquisitionTime, Settings[1])
        self.assertEqual(overSamplingRate, Settings[2])
        self.assertEqual(adcRef, Settings[3])
        calcRate = calcSamplingRate(prescaler, acquisitionTime, overSamplingRate)
        self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0)
        indexStart = self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0)
        time.sleep(StreamingStandardTestTimeMs / 1000)
        indexEnd = self.PeakCan.GetReadArrayIndex() - 1
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"])   
        time.sleep(1)    
        countDel = 0
        while StreamingStandardTestTimeMs < self.PeakCan.getReadMessageTimeMs(indexStart, indexEnd) - 0.5:
            countDel += 1
            indexEnd -= 1
        self.PeakCan.Logger.Info("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))
        self.PeakCan.Logger.Info("indexStart: " + str(indexStart))
        self.PeakCan.Logger.Info("indexEnd: " + str(indexEnd))
        if 0.2 * (indexEnd - indexStart) < countDel:
            self.PeakCan.Logger.Warning("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))        
        [arrayBat, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.assertEqual(0, len(array2))
        self.assertEqual(0, len(array3))
        [arrayAccX, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.assertEqual(0, len(array2))
        self.assertEqual(0, len(array3))
        samplePointsVoltage = len(arrayBat) / 10
        samplePointsAcceleration = len(arrayAccX) / 10
        self.PeakCan.Logger.Info("Voltage Sampling Points: " + str(samplePointsVoltage))
        self.PeakCan.Logger.Info("Acceleration Sampling Points: " + str(samplePointsAcceleration))
        self.PeakCan.Logger.Info("Total Sampling Rate(Calulated): " + str(calcRate))
        calcRate = calcRate / 2
        self.PeakCan.Logger.Info("Sampling Rate per Channel: " + str(int(calcRate)))
        self.assertLess(calcRate * SamplingToleranceLow, samplePointsVoltage)
        self.assertGreater(calcRate * SamplingToleranceHigh, samplePointsVoltage)
        self.assertLess(calcRate * SamplingToleranceLow, samplePointsAcceleration)
        self.assertGreater(calcRate * SamplingToleranceHigh, samplePointsAcceleration)
        
    """
    Mixed Streaming - AccXY + VoltageBattery
    """        

    def test0520SamplingRateMixedStreamingAccXYBat(self):
        prescaler = SamplingRateDoubleMaxPrescaler
        acquisitionTime = SamplingRateDoubleMaxAcqTime
        overSamplingRate = SamplingRateDoubleMaxOverSamples
        adcRef = AdcReference["VDD"]
        Settings = self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], prescaler, acquisitionTime, overSamplingRate, adcRef)[1:]
        self.assertEqual(prescaler, Settings[0])
        self.assertEqual(acquisitionTime, Settings[1])
        self.assertEqual(overSamplingRate, Settings[2])
        self.assertEqual(adcRef, Settings[3])
        calcRate = calcSamplingRate(prescaler, acquisitionTime, overSamplingRate)
        self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0)
        indexStart = self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 0)
        time.sleep(StreamingStandardTestTimeMs / 1000 + 0.25)
        indexEnd = self.PeakCan.GetReadArrayIndex() - 1
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"])  
         
        time.sleep(1)    
        countDel = 0
        while StreamingStandardTestTimeMs + 0.25 < self.PeakCan.getReadMessageTimeMs(indexStart, indexEnd) - 0.5:
            countDel += 1
            indexEnd -= 1
        self.PeakCan.Logger.Info("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))
        self.PeakCan.Logger.Info("indexStart: " + str(indexStart))
        self.PeakCan.Logger.Info("indexEnd: " + str(indexEnd))
        if 0.2 * (indexEnd - indexStart) < countDel:
            self.PeakCan.Logger.Warning("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))        
        [arrayBat, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.assertEqual(0, len(array2))
        self.assertEqual(0, len(array3))
        [arrayAccX, arrayAccY, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 0, indexStart, indexEnd)
        self.assertEqual(0, len(array3))
        samplePointsVoltage = len(arrayBat) / 10
        samplePointsXAcceleration = len(arrayAccX) / 10
        samplePointsYAcceleration = len(arrayAccY) / 10
        self.PeakCan.Logger.Info("Voltage Sampling Points: " + str(samplePointsVoltage))
        self.PeakCan.Logger.Info("AccelerationX Sampling Points: " + str(samplePointsXAcceleration))
        self.PeakCan.Logger.Info("AccelerationY Sampling Points: " + str(samplePointsYAcceleration))
        self.PeakCan.Logger.Info("Total Sampling Rate(Calulated): " + str(int(calcRate)))
        calcRate = calcRate / 3
        self.PeakCan.Logger.Info("Sampling Rate per Channel: " + str(int(calcRate)))
        self.assertLess(calcRate * SamplingToleranceLow, samplePointsVoltage)
        self.assertGreater(calcRate * SamplingToleranceHigh, samplePointsVoltage)
        self.assertLess(calcRate * SamplingToleranceLow, samplePointsXAcceleration)
        self.assertGreater(calcRate * SamplingToleranceHigh, samplePointsXAcceleration)
        self.assertLess(calcRate * SamplingToleranceLow, samplePointsYAcceleration)
        self.assertGreater(calcRate * SamplingToleranceHigh, samplePointsYAcceleration)
 
    """
    Mixed Streaming - AccXYZ + VoltageBattery
    """        

    def test0521SamplingRateMixedStreamingAccXYZBat(self):
        prescaler = SamplingRateSingleMaxPrescaler
        acquisitionTime = SamplingRateSingleMaxAcqTime
        overSamplingRate = SamplingRateSingleMaxOverSamples
        adcRef = AdcReference["VDD"]
        Settings = self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], prescaler, acquisitionTime, overSamplingRate, adcRef)[1:]
        self.assertEqual(prescaler, Settings[0])
        self.assertEqual(acquisitionTime, Settings[1])
        self.assertEqual(overSamplingRate, Settings[2])
        self.assertEqual(adcRef, Settings[3])
        calcRate = calcSamplingRate(prescaler, acquisitionTime, overSamplingRate)
        self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0)
        indexStart = self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 1)
        time.sleep(StreamingStandardTestTimeMs / 1000 + 0.25)
        indexEnd = self.PeakCan.GetReadArrayIndex() - 1
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"])   
        time.sleep(1)    
        countDel = 0
        while StreamingStandardTestTimeMs + 0.25 < self.PeakCan.getReadMessageTimeMs(indexStart, indexEnd) - 0.5:
            countDel += 1
            indexEnd -= 1
        self.PeakCan.Logger.Info("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))
        self.PeakCan.Logger.Info("indexStart: " + str(indexStart))
        self.PeakCan.Logger.Info("indexEnd: " + str(indexEnd))
        if 0.2 * (indexEnd - indexStart) < countDel:
            self.PeakCan.Logger.Warning("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))        
        [arrayBat, array2, array3] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.assertEqual(0, len(array2))
        self.assertEqual(0, len(array3))
        [arrayAccX, arrayAccY, arrayAccZ] = self.PeakCan.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 1, indexStart, indexEnd)
        samplePointsVoltage = len(arrayBat) / 10
        samplePointsXAcceleration = len(arrayAccX) / 10
        samplePointsYAcceleration = len(arrayAccY) / 10
        samplePointsZAcceleration = len(arrayAccZ) / 10
        self.PeakCan.Logger.Info("Voltage Sampling Points: " + str(samplePointsVoltage))
        self.PeakCan.Logger.Info("AccelerationX Sampling Points: " + str(samplePointsXAcceleration))
        self.PeakCan.Logger.Info("AccelerationY Sampling Points: " + str(samplePointsYAcceleration))
        self.PeakCan.Logger.Info("AccelerationY Sampling Points: " + str(samplePointsZAcceleration))
        self.PeakCan.Logger.Info("Total Sampling Rate(Calulated): " + str(int(calcRate)))
        calcRate = calcRate / 4
        self.PeakCan.Logger.Info("Sampling Rate per Channel: " + str(int(calcRate)))
        self.assertLess(calcRate * SamplingToleranceLow, samplePointsVoltage)
        self.assertGreater(calcRate * SamplingToleranceHigh, samplePointsVoltage)
        self.assertLess(calcRate * SamplingToleranceLow, samplePointsXAcceleration)
        self.assertGreater(calcRate * SamplingToleranceHigh, samplePointsXAcceleration)
        self.assertLess(calcRate * SamplingToleranceLow, samplePointsYAcceleration)
        self.assertGreater(calcRate * SamplingToleranceHigh, samplePointsYAcceleration)        
        self.assertLess(calcRate * SamplingToleranceLow, samplePointsZAcceleration)
        self.assertGreater(calcRate * SamplingToleranceHigh, samplePointsZAcceleration)   
 
    """
    Message Counters Mixed Signals
    """        

    def test0522MessageCountersMixerdSignals(self):
        prescaler = SamplingRateSingleMaxPrescaler
        acquisitionTime = SamplingRateSingleMaxAcqTime
        overSamplingRate = SamplingRateSingleMaxOverSamples
        adcRef = AdcReference["VDD"]
        Settings = self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], prescaler, acquisitionTime, overSamplingRate, adcRef)[1:]
        self.assertEqual(prescaler, Settings[0])
        self.assertEqual(acquisitionTime, Settings[1])
        self.assertEqual(overSamplingRate, Settings[2])
        self.assertEqual(adcRef, Settings[3])
        calcSamplingRate(prescaler, acquisitionTime, overSamplingRate)
        self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0)
        indexStart = self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 1)
        time.sleep(StreamingStandardTestTimeMs / 1000 + 0.25)
        indexEnd = self.PeakCan.GetReadArrayIndex() - 1
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"])   
        time.sleep(1)    
        countDel = 0
        while StreamingStandardTestTimeMs + 0.25 < self.PeakCan.getReadMessageTimeMs(indexStart, indexEnd) - 0.5:
            countDel += 1
            indexEnd -= 1
        self.PeakCan.Logger.Info("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))
        self.PeakCan.Logger.Info("indexStart: " + str(indexStart))
        self.PeakCan.Logger.Info("indexEnd: " + str(indexEnd))
        if 0.2 * (indexEnd - indexStart) < countDel:
            self.PeakCan.Logger.Warning("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))        
        [arrayBat, array2, array3] = self.PeakCan.streamingValueArrayMessageCounters(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.assertEqual(0, len(array2))
        self.assertEqual(0, len(array3))
        [arrayAccX, arrayAccY, arrayAccZ] = self.PeakCan.streamingValueArrayMessageCounters(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 1, indexStart, indexEnd)
        self.PeakCan.ValueLog(arrayAccX, arrayAccY, arrayAccZ, fAdcRawDat, "AccMsgCounter", "")
        self.PeakCan.ValueLog(arrayBat, array2, array3, fAdcRawDat, "BatteryMsgCounter", "")
        
        count = arrayAccX[0]
        self.assertGreaterEqual(count, 0)
        self.assertLessEqual(count, 255)
        for i in range(0, len(arrayAccX)):
            self.assertEqual(count, arrayAccX[i])
            self.assertEqual(count, arrayAccY[i])
            self.assertEqual(count, arrayAccZ[i])
            count += 1
            count %= 256
            
        count = arrayBat[0]
        self.assertGreaterEqual(count, 0)
        self.assertLessEqual(count, 255)
        i = 0
        while i < len(arrayBat):
            self.assertEqual(count, arrayBat[i])
            i += 1
            self.assertEqual(count, arrayBat[i])
            i += 1
            self.assertEqual(count, arrayBat[i])
            i += 1
            count += 1
            count %= 256
    
    """
    Message Counters AccX
    """           

    def test0523MessageCounterAccX(self):
        self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], SamplingRateSingleMaxPrescaler, SamplingRateSingleMaxAcqTime, SamplingRateSingleMaxOverSamples, AdcReference["VDD"])
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0, 10000)
        [arrayAccX, arrayAccY, arrayAccZ] = self.PeakCan.streamingValueArrayMessageCounters(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.assertEqual(0, len(arrayAccY))
        self.assertEqual(0, len(arrayAccZ))
        self.PeakCan.ValueLog(arrayAccX, arrayAccY, arrayAccZ, fAdcRawDat, "AccMsgCounter", "")
        count = arrayAccX[0]
        self.assertGreaterEqual(count, 0)
        self.assertLessEqual(count, 255)
        i = 0
        while i < len(arrayAccX):
            self.assertEqual(count, arrayAccX[i])
            i += 1
            self.assertEqual(count, arrayAccX[i])
            i += 1
            self.assertEqual(count, arrayAccX[i])
            i += 1
            count += 1
            count %= 256

    """
    Message Counters AccY
    """           

    def test0524MessageCounterAccY(self):
        self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], SamplingRateSingleMaxPrescaler, SamplingRateSingleMaxAcqTime, SamplingRateSingleMaxOverSamples, AdcReference["VDD"])
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 1, 0, 1000)
        [arrayAccX, arrayAccY, arrayAccZ] = self.PeakCan.streamingValueArrayMessageCounters(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 1, 0, indexStart, indexEnd)
        self.assertEqual(0, len(arrayAccX))
        self.assertEqual(0, len(arrayAccZ))
        self.PeakCan.ValueLog(arrayAccX, arrayAccY, arrayAccZ, fAdcRawDat, "AccMsgCounter", "")
        count = arrayAccY[0]
        self.assertGreaterEqual(count, 0)
        self.assertLessEqual(count, 255)
        i = 0
        while i < len(arrayAccY):
            self.assertEqual(count, arrayAccY[i])
            i += 1
            self.assertEqual(count, arrayAccY[i])
            i += 1
            self.assertEqual(count, arrayAccY[i])
            i += 1
            count += 1
            count %= 256
            
    """
    Message Counters AccZ
    """           

    def test0525MessageCounterAccZ(self):
        self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], SamplingRateSingleMaxPrescaler, SamplingRateSingleMaxAcqTime, SamplingRateSingleMaxOverSamples, AdcReference["VDD"])
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 0, 1, 1000)
        [arrayAccX, arrayAccY, arrayAccZ] = self.PeakCan.streamingValueArrayMessageCounters(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 0, 1, indexStart, indexEnd)
        self.assertEqual(0, len(arrayAccX))
        self.assertEqual(0, len(arrayAccY))
        self.PeakCan.ValueLog(arrayAccX, arrayAccY, arrayAccZ, fAdcRawDat, "AccMsgCounter", "")
        count = arrayAccZ[0]
        self.assertGreaterEqual(count, 0)
        self.assertLessEqual(count, 255)
        i = 0
        while i < len(arrayAccZ):
            self.assertEqual(count, arrayAccZ[i])
            i += 1
            self.assertEqual(count, arrayAccZ[i])
            i += 1
            self.assertEqual(count, arrayAccZ[i])
            i += 1
            count += 1
            count %= 256
       
    """
    Message Counters AccXY
    """           

    def test0526MessageCounterAccXY(self):
        self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], SamplingRateDoubleMaxPrescaler, SamplingRateDoubleMaxAcqTime, SamplingRateDoubleMaxOverSamples, AdcReference["VDD"])
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 0, 1000)
        [arrayAccX, arrayAccY, arrayAccZ] = self.PeakCan.streamingValueArrayMessageCounters(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 0, indexStart, indexEnd)
        self.assertEqual(0, len(arrayAccZ))
        self.PeakCan.ValueLog(arrayAccX, arrayAccY, arrayAccZ, fAdcRawDat, "AccMsgCounter", "")
        count = arrayAccX[0]
        self.assertGreaterEqual(count, 0)
        self.assertLessEqual(count, 255)
        i = 0
        while i < len(arrayAccZ):
            self.assertEqual(count, arrayAccX[i])
            self.assertEqual(count, arrayAccY[i])
            i += 1
            count += 1
            count %= 256       
       
    """
    Message Counters AccXZ
    """           

    def test0527MessageCounterAccXZ(self):
        self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], SamplingRateDoubleMaxPrescaler, SamplingRateDoubleMaxAcqTime, SamplingRateDoubleMaxOverSamples, AdcReference["VDD"])
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 0, 1, 1000)
        [arrayAccX, arrayAccY, arrayAccZ] = self.PeakCan.streamingValueArrayMessageCounters(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 0, 1, indexStart, indexEnd)
        self.assertEqual(0, len(arrayAccY))
        self.PeakCan.ValueLog(arrayAccX, arrayAccY, arrayAccZ, fAdcRawDat, "AccMsgCounter", "")
        count = arrayAccX[0]
        self.assertGreaterEqual(count, 0)
        self.assertLessEqual(count, 255)
        i = 0
        while i < len(arrayAccZ):
            self.assertEqual(count, arrayAccX[i])
            self.assertEqual(count, arrayAccZ[i])
            i += 1
            count += 1
            count %= 256            
                           
    """
    Message Counters AccXZ
    """           

    def test0528MessageCounterAccYZ(self):
        self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], SamplingRateDoubleMaxPrescaler, SamplingRateDoubleMaxAcqTime, SamplingRateDoubleMaxOverSamples, AdcReference["VDD"])
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 0, 1, 1, 1000)
        [arrayAccX, arrayAccY, arrayAccZ] = self.PeakCan.streamingValueArrayMessageCounters(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 0, 1, 1, indexStart, indexEnd)
        self.assertEqual(0, len(arrayAccX))
        self.PeakCan.ValueLog(arrayAccX, arrayAccY, arrayAccZ, fAdcRawDat, "AccMsgCounter", "")
        count = arrayAccY[0]
        self.assertGreaterEqual(count, 0)
        self.assertLessEqual(count, 255)
        i = 0
        while i < len(arrayAccY):
            self.assertEqual(count, arrayAccY[i])
            self.assertEqual(count, arrayAccZ[i])
            i += 1
            count += 1
            count %= 256 
            
    """
    Message Counters AccXYZ
    """           

    def test0529MessageCounterAccXYZ(self):
        self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], SamplingRateTrippleMaxPrescaler, SamplingRateTrippleMaxAcqTime, SamplingRateTrippleMaxOverSamples, AdcReference["VDD"])
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 1, 1000)
        [arrayAccX, arrayAccY, arrayAccZ] = self.PeakCan.streamingValueArrayMessageCounters(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 1, indexStart, indexEnd)
        self.PeakCan.ValueLog(arrayAccX, arrayAccY, arrayAccZ, fAdcRawDat, "AccMsgCounter", "")
        count = arrayAccY[0]
        self.assertGreaterEqual(count, 0)
        self.assertLessEqual(count, 255)
        i = 0
        while i < len(arrayAccY):
            self.assertEqual(count, arrayAccX[i])
            self.assertEqual(count, arrayAccY[i])
            self.assertEqual(count, arrayAccZ[i])
            i += 1
            count += 1
            count %= 256

    """
    Message Counters AccX Battery
    """        

    def test0530MessageCountersAccXBattery(self):
        prescaler = SamplingRateSingleMaxPrescaler
        acquisitionTime = SamplingRateSingleMaxAcqTime
        overSamplingRate = SamplingRateSingleMaxOverSamples
        adcRef = AdcReference["VDD"]
        Settings = self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], prescaler, acquisitionTime, overSamplingRate, adcRef)[1:]
        self.assertEqual(prescaler, Settings[0])
        self.assertEqual(acquisitionTime, Settings[1])
        self.assertEqual(overSamplingRate, Settings[2])
        self.assertEqual(adcRef, Settings[3])
        calcSamplingRate(prescaler, acquisitionTime, overSamplingRate)
        self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0)
        indexStart = self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0)
        time.sleep(StreamingStandardTestTimeMs / 1000 + 0.25)
        indexEnd = self.PeakCan.GetReadArrayIndex() - 1
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"])   
        time.sleep(1)    
        countDel = 0
        while StreamingStandardTestTimeMs + 0.25 < self.PeakCan.getReadMessageTimeMs(indexStart, indexEnd) - 0.5:
            countDel += 1
            indexEnd -= 1
        self.PeakCan.Logger.Info("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))
        self.PeakCan.Logger.Info("indexStart: " + str(indexStart))
        self.PeakCan.Logger.Info("indexEnd: " + str(indexEnd))
        if 0.2 * (indexEnd - indexStart) < countDel:
            self.PeakCan.Logger.Warning("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))        
        [arrayBat, array2, array3] = self.PeakCan.streamingValueArrayMessageCounters(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.assertEqual(0, len(array2))
        self.assertEqual(0, len(array3))
        [arrayAccX, arrayAccY, arrayAccZ] = self.PeakCan.streamingValueArrayMessageCounters(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(arrayAccX, arrayAccY, arrayAccZ, fAdcRawDat, "AccMsgCounter", "")
        self.PeakCan.ValueLog(arrayBat, array2, array3, fAdcRawDat, "BatteryMsgCounter", "")
        
        count = arrayAccX[0]
        self.assertGreaterEqual(count, 0)
        self.assertLessEqual(count, 255)
        i = 0
        while i < len(arrayAccX):
            self.assertEqual(count, arrayAccX[i])
            i += 1
            self.assertEqual(count, arrayAccX[i])
            i += 1
            self.assertEqual(count, arrayAccX[i])
            i += 1
            count += 1
            count %= 256
            
        count = arrayBat[0]
        self.assertGreaterEqual(count, 0)
        self.assertLessEqual(count, 255)
        i = 0
        while i < len(arrayBat):
            self.assertEqual(count, arrayBat[i])
            i += 1
            self.assertEqual(count, arrayBat[i])
            i += 1
            self.assertEqual(count, arrayBat[i])
            i += 1
            count += 1
            count %= 256

    """
    Message Counters AccY Battery
    """        

    def test0531MessageCountersAccYBattery(self):
        prescaler = SamplingRateSingleMaxPrescaler
        acquisitionTime = SamplingRateSingleMaxAcqTime
        overSamplingRate = SamplingRateSingleMaxOverSamples
        adcRef = AdcReference["VDD"]
        Settings = self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], prescaler, acquisitionTime, overSamplingRate, adcRef)[1:]
        self.assertEqual(prescaler, Settings[0])
        self.assertEqual(acquisitionTime, Settings[1])
        self.assertEqual(overSamplingRate, Settings[2])
        self.assertEqual(adcRef, Settings[3])
        calcSamplingRate(prescaler, acquisitionTime, overSamplingRate)
        self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0)
        indexStart = self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 1, 0)
        time.sleep(StreamingStandardTestTimeMs / 1000 + 0.25)
        indexEnd = self.PeakCan.GetReadArrayIndex() - 1
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"])   
        time.sleep(1)    
        countDel = 0
        while StreamingStandardTestTimeMs + 0.25 < self.PeakCan.getReadMessageTimeMs(indexStart, indexEnd) - 0.5:
            countDel += 1
            indexEnd -= 1
        self.PeakCan.Logger.Info("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))
        self.PeakCan.Logger.Info("indexStart: " + str(indexStart))
        self.PeakCan.Logger.Info("indexEnd: " + str(indexEnd))
        if 0.2 * (indexEnd - indexStart) < countDel:
            self.PeakCan.Logger.Warning("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))        
        [arrayBat, array2, array3] = self.PeakCan.streamingValueArrayMessageCounters(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.assertEqual(0, len(array2))
        self.assertEqual(0, len(array3))
        [arrayAccX, arrayAccY, arrayAccZ] = self.PeakCan.streamingValueArrayMessageCounters(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 1, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(arrayAccX, arrayAccY, arrayAccZ, fAdcRawDat, "AccMsgCounter", "")
        self.PeakCan.ValueLog(arrayBat, array2, array3, fAdcRawDat, "BatteryMsgCounter", "")
        
        count = arrayAccY[0]
        self.assertGreaterEqual(count, 0)
        self.assertLessEqual(count, 255)
        i = 0
        while i < len(arrayAccY):
            self.assertEqual(count, arrayAccY[i])
            i += 1
            self.assertEqual(count, arrayAccY[i])
            i += 1
            self.assertEqual(count, arrayAccY[i])
            i += 1
            count += 1
            count %= 256
            
        count = arrayBat[0]
        self.assertGreaterEqual(count, 0)
        self.assertLessEqual(count, 255)
        i = 0
        while i < len(arrayBat):
            self.assertEqual(count, arrayBat[i])
            i += 1
            self.assertEqual(count, arrayBat[i])
            i += 1
            self.assertEqual(count, arrayBat[i])
            i += 1
            count += 1
            count %= 256            

    """
    Message Counters AccZ Battery
    """        

    def test0532MessageCountersAccZBattery(self):
        prescaler = SamplingRateSingleMaxPrescaler
        acquisitionTime = SamplingRateSingleMaxAcqTime
        overSamplingRate = SamplingRateSingleMaxOverSamples
        adcRef = AdcReference["VDD"]
        Settings = self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], prescaler, acquisitionTime, overSamplingRate, adcRef)[1:]
        self.assertEqual(prescaler, Settings[0])
        self.assertEqual(acquisitionTime, Settings[1])
        self.assertEqual(overSamplingRate, Settings[2])
        self.assertEqual(adcRef, Settings[3])
        calcSamplingRate(prescaler, acquisitionTime, overSamplingRate)
        self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0)
        indexStart = self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 0, 1)
        time.sleep(StreamingStandardTestTimeMs / 1000 + 0.25)
        indexEnd = self.PeakCan.GetReadArrayIndex() - 1
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])
        self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"])   
        time.sleep(1)    
        countDel = 0
        while StreamingStandardTestTimeMs + 0.25 < self.PeakCan.getReadMessageTimeMs(indexStart, indexEnd) - 0.5:
            countDel += 1
            indexEnd -= 1
        self.PeakCan.Logger.Info("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))
        self.PeakCan.Logger.Info("indexStart: " + str(indexStart))
        self.PeakCan.Logger.Info("indexEnd: " + str(indexEnd))
        if 0.2 * (indexEnd - indexStart) < countDel:
            self.PeakCan.Logger.Warning("Deleted Messages do achieve " + str(StreamingStandardTestTimeMs) + "ms: " + str(countDel + 180))        
        [arrayBat, array2, array3] = self.PeakCan.streamingValueArrayMessageCounters(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.assertEqual(0, len(array2))
        self.assertEqual(0, len(array3))
        [arrayAccX, arrayAccY, arrayAccZ] = self.PeakCan.streamingValueArrayMessageCounters(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 0, 0, 1, indexStart, indexEnd)
        self.PeakCan.ValueLog(arrayAccX, arrayAccY, arrayAccZ, fAdcRawDat, "AccMsgCounter", "")
        self.PeakCan.ValueLog(arrayBat, array2, array3, fAdcRawDat, "BatteryMsgCounter", "")
        
        count = arrayAccZ[0]
        self.assertGreaterEqual(count, 0)
        self.assertLessEqual(count, 255)
        i = 0
        while i < len(arrayAccZ):
            self.assertEqual(count, arrayAccZ[i])
            i += 1
            self.assertEqual(count, arrayAccZ[i])
            i += 1
            self.assertEqual(count, arrayAccZ[i])
            i += 1
            count += 1
            count %= 256
            
        count = arrayBat[0]
        self.assertGreaterEqual(count, 0)
        self.assertLessEqual(count, 255)
        i = 0
        while i < len(arrayBat):
            self.assertEqual(count, arrayBat[i])
            i += 1
            self.assertEqual(count, arrayBat[i])
            i += 1
            self.assertEqual(count, arrayBat[i])
            i += 1
            count += 1
            count %= 256   
                        
    """
    Message Counters Battery - Data Set 1
    """           

    def test0533MessageCounterBattery(self):
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, 1000)
        [arrayBattery, array2, array3] = self.PeakCan.streamingValueArrayMessageCounters(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[3], 1, 0, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(arrayBattery, array2, array3, fAdcRawDat, "BatteryMsgCounter", "")
        count = arrayBattery[0]
        self.assertGreaterEqual(count, 0)
        self.assertLessEqual(count, 255)
        count = arrayBattery[0]
        self.assertGreaterEqual(count, 0)
        self.assertLessEqual(count, 255)
        i = 0
        while i < len(arrayBattery):
            self.assertEqual(count, arrayBattery[i])
            i += 1
            self.assertEqual(count, arrayBattery[i])
            i += 1
            self.assertEqual(count, arrayBattery[i])
            i += 1
            count += 1
            count %= 256 
            
    """
    Message Counters Battery with single Data Set
    """           

    def test0534MessageCounterAccBatteryDataSetSingle(self):
        self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], SamplingRateSingleMaxPrescaler, SamplingRateSingleMaxAcqTime, SamplingRateSingleMaxOverSamples + 2, AdcReference["VDD"])
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[1], 1, 0, 0, 1000)
        [arrayBattery, array2, array3] = self.PeakCan.streamingValueArrayMessageCounters(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], DataSets[1], 1, 0, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(arrayBattery, array2, array3, fAdcRawDat, "BatteryMsgCounter", "")
        count = arrayBattery[0]
        self.assertGreaterEqual(count, 0)
        self.assertLessEqual(count, 255)
        count = arrayBattery[0]
        self.assertGreaterEqual(count, 0)
        self.assertLessEqual(count, 255)
        i = 0
        while i < len(arrayBattery):
            self.assertEqual(count, arrayBattery[i])
            i += 1
            count += 1
            count %= 256
                   
    """
    Check Calibration Measurement
    """

    def test0600CalibrationMeasurement(self):
        ret = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["Acc"], 1, AdcReference["VDD"])
        result = messageWordGet(ret[4:])
        self.PeakCan.Logger.Info("Calibration Result AccX: " + str(result))
        self.assertLessEqual(AdcRawMiddleX - AdcRawToleranceX, result)
        self.assertGreaterEqual(AdcRawMiddleX + AdcRawToleranceX, result)
        ret = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["Acc"], 2, AdcReference["VDD"])
        result = messageWordGet(ret[4:])
        self.PeakCan.Logger.Info("Calibration Result AccY: " + str(result))
        self.assertLessEqual(AdcRawMiddleY - AdcRawToleranceY, result)
        self.assertGreaterEqual(AdcRawMiddleY + AdcRawToleranceY, result)
        ret = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["Acc"], 3, AdcReference["VDD"])
        result = messageWordGet(ret[4:])
        self.PeakCan.Logger.Info("Calibration Result AccZ: " + str(result))
        self.assertLessEqual(AdcRawMiddleZ - AdcRawToleranceZ, result)
        self.assertGreaterEqual(AdcRawMiddleZ + AdcRawToleranceZ, result)
        ret = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["Temp"], 1, AdcReference["VDD"])
        result = messageWordGet(ret[4:])
        self.PeakCan.Logger.Info("Calibration Result Temperature: " + str(result))
        self.assertLessEqual(TempInternal3V3Middle - TempInternal3V3Tolerance, result)
        self.assertGreaterEqual(TempInternal3V3Middle + TempInternal3V3Tolerance, result)
        ret = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["Voltage"], 1, AdcReference["VDD"])
        result = messageWordGet(ret[4:])
        self.PeakCan.Logger.Info("Calibration Result Voltage: " + str(result))
        self.assertLessEqual(VoltRawMiddleBat - VoltRawToleranceBat, result)
        self.assertGreaterEqual(VoltRawMiddleBat + VoltRawToleranceBat, result)
        ret = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["Vss"], 1, AdcReference["VDD"])
        result = messageWordGet(ret[4:])
        self.PeakCan.Logger.Info("Calibration Result VSS(Ground): " + str(result))
        self.assertLessEqual(0, result)
        self.assertGreaterEqual(VoltRawVssTolerance, result)
        ret = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["Avdd"], 1, AdcReference["VDD"])
        result = messageWordGet(ret[4:])
        self.PeakCan.Logger.Info("Calibration Result AVDD(3V3): " + str(result))
        self.assertLessEqual(2 ^ 16 - 100, result)
        ret = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["RegulatedInternalPower"], 1, AdcReference["VDD"])
        result = messageWordGet(ret[4:])
        self.PeakCan.Logger.Info("Calibration Result Regulated Internal Power(DECOUPLE): " + str(result))
        self.assertLessEqual(VoltRawDecoupleMiddle - VoltRawDecoupleTolerance, result)
        self.assertGreaterEqual(VoltRawDecoupleMiddle + VoltRawDecoupleTolerance, result)
        ret = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["OpvOutput"], 1, AdcReference["VDD"])
        result = messageWordGet(ret[4:])
        self.PeakCan.Logger.Info("Calibration Result OPA2: " + str(result))
        self.assertLessEqual(VoltRawOpa2Middle - VoltRawOpa2Tolerance, result)
        self.assertGreaterEqual(VoltRawOpa2Middle + VoltRawOpa2Tolerance, result)
        ret = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["OpvOutput"], 2, AdcReference["VDD"])
        result = messageWordGet(ret[4:])
        self.PeakCan.Logger.Info("Calibration Result OPA3: " + str(result))
        self.assertLessEqual(VoltRawOpa3Middle - VoltRawOpa3Tolerance, result)
        self.assertGreaterEqual(VoltRawOpa3Middle + VoltRawOpa3Tolerance, result)
        
    """
    Calibration - Check On-Die Temperature
    """

    def test0601CalibrationMeasurementTemperature(self):
        ret = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["Temp"], 1, AdcReference["1V25"], log=False)
        result = float(messageWordGet(ret[4:]))
        result /= 1000
        self.PeakCan.Logger.Info("Temperature(Chip): " + str(result) + "°C") 
        self.assertLessEqual(result, TempInternalMax)
        self.assertGreaterEqual(result, TempInternalMin)      

    """
    Calibration - Check all VRef combinations
    """

    def test0602CalibrationMeasurementVRef(self):
        self.test0601CalibrationMeasurementTemperature()  # 1V25
        for vRefKey, vRefValue in AdcReference.items():
            if AdcReference["Vfs1V65"] <= AdcReference[vRefKey]:
                ret = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["Acc"], 1, vRefValue)
                result = messageWordGet(ret[4:])
                self.PeakCan.Logger.Info("ADC Value: " + str(result))
                result = result * ((vRefValue) / (AdcReference["VDD"]))
                self.PeakCan.Logger.Info("Recalculated value(result*" + str(vRefValue * 50) + "/" + str(AdcReference["VDD"] * 50) + "): " + str(result))
                self.assertLessEqual(AdcRawMiddleX - AdcRawToleranceX, result * SamplingToleranceHigh)
                self.assertGreaterEqual(AdcRawMiddleX + AdcRawToleranceX, result * SamplingToleranceLow)
            
    """
    Calibration - Check Injection and Ejection
    """

    def test0603CalibrationMeasurementEjectInject(self):
        kX1ack = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["Acc"], 1, AdcReference["VDD"])
        kX1 = messageWordGet(kX1ack[4:])
        kY1ack = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["Acc"], 2, AdcReference["VDD"])
        kY1 = messageWordGet(kY1ack[4:])
        kZ1ack = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["Acc"], 3, AdcReference["VDD"])
        kZ1 = messageWordGet(kZ1ack[4:])
        ackInjectX = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Inject"], CalibMeassurementTypeNr["Acc"], 1, AdcReference["VDD"])
        stateInjectX = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Inject"], CalibMeassurementTypeNr["Acc"], 1, AdcReference["VDD"], bSet=False)
        ackInjectY = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Inject"], CalibMeassurementTypeNr["Acc"], 2, AdcReference["VDD"])
        stateInjectY = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Inject"], CalibMeassurementTypeNr["Acc"], 2, AdcReference["VDD"], bSet=False)
        ackInjectZ = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Inject"], CalibMeassurementTypeNr["Acc"], 3, AdcReference["VDD"])
        stateInjectZ = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Inject"], CalibMeassurementTypeNr["Acc"], 3, AdcReference["VDD"], bSet=False)
        time.sleep(0.1)
        kX2ack = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["Acc"], 1, AdcReference["VDD"])
        kX2 = messageWordGet(kX2ack[4:])
        kY2ack = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["Acc"], 2, AdcReference["VDD"])
        kY2 = messageWordGet(kY2ack[4:])
        kZ2ack = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["Acc"], 3, AdcReference["VDD"])
        kZ2 = messageWordGet(kZ2ack[4:])
        ackEjectX = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Eject"], CalibMeassurementTypeNr["Acc"], 1, AdcReference["VDD"])
        stateEjectX = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Inject"], CalibMeassurementTypeNr["Acc"], 1, AdcReference["VDD"], bSet=False)
        ackEjectY = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Eject"], CalibMeassurementTypeNr["Acc"], 2, AdcReference["VDD"])
        stateEjectY = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Inject"], CalibMeassurementTypeNr["Acc"], 2, AdcReference["VDD"], bSet=False)
        ackEjectZ = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Eject"], CalibMeassurementTypeNr["Acc"], 3, AdcReference["VDD"])
        stateEjectZ = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Inject"], CalibMeassurementTypeNr["Acc"], 3, AdcReference["VDD"], bSet=False)
        kX3ack = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["Acc"], 1, AdcReference["VDD"])
        kX3 = messageWordGet(kX3ack[4:])
        kY3ack = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["Acc"], 2, AdcReference["VDD"])
        kY3 = messageWordGet(kY3ack[4:])
        kZ3ack = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["Acc"], 3, AdcReference["VDD"])
        kZ3 = messageWordGet(kZ3ack[4:])
        kX4ack = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["Acc"], 1, AdcReference["VDD"])
        kX4 = messageWordGet(kX4ack[4:])
        kY4ack = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["Acc"], 2, AdcReference["VDD"])
        kY4 = messageWordGet(kY4ack[4:])
        kZ4ack = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["Acc"], 3, AdcReference["VDD"])
        kZ4 = messageWordGet(kZ4ack[4:])
        self.PeakCan.Logger.Info("ackInjectX: " + payload2Hex(ackInjectX))
        self.PeakCan.Logger.Info("stateInjectX: " + payload2Hex(stateInjectX))
        self.PeakCan.Logger.Info("ackInjectY: " + payload2Hex(ackInjectY))
        self.PeakCan.Logger.Info("stateInjectY: " + payload2Hex(stateInjectY))
        self.PeakCan.Logger.Info("ackInjectZ: " + payload2Hex(ackInjectZ))
        self.PeakCan.Logger.Info("stateInjectZ: " + payload2Hex(stateInjectZ))
        self.PeakCan.Logger.Info("ackEject: " + payload2Hex(ackEjectX))
        self.PeakCan.Logger.Info("stateEject: " + payload2Hex(stateEjectX))
        self.PeakCan.Logger.Info("ackEject: " + payload2Hex(ackEjectY))
        self.PeakCan.Logger.Info("stateEject: " + payload2Hex(stateEjectY))
        self.PeakCan.Logger.Info("ackEject: " + payload2Hex(ackEjectZ))
        self.PeakCan.Logger.Info("stateEject: " + payload2Hex(stateEjectZ))
        self.PeakCan.Logger.Info("X Ack before Injection: " + payload2Hex(kX1ack))
        self.PeakCan.Logger.Info("Y Ack before Injection: " + payload2Hex(kY1ack))
        self.PeakCan.Logger.Info("Z Ack before Injection: " + payload2Hex(kZ1ack))
        self.PeakCan.Logger.Info("X Ack after Injection: " + payload2Hex(kX2ack))
        self.PeakCan.Logger.Info("Y Ack after Injection: " + payload2Hex(kY2ack))
        self.PeakCan.Logger.Info("Z Ack after Injection: " + payload2Hex(kZ2ack))
        self.PeakCan.Logger.Info("X Ack after Injection: " + payload2Hex(kX3ack))
        self.PeakCan.Logger.Info("Y Ack after Injection: " + payload2Hex(kY3ack))
        self.PeakCan.Logger.Info("Z Ack after Injection: " + payload2Hex(kZ3ack))
        self.PeakCan.Logger.Info("X Ack after Injection: " + payload2Hex(kX4ack))
        self.PeakCan.Logger.Info("Y Ack after Injection: " + payload2Hex(kY4ack))
        self.PeakCan.Logger.Info("Z Ack after Injection: " + payload2Hex(kZ4ack))
        self.PeakCan.Logger.Info("X k1 (before Injection): " + str(kX1))
        self.PeakCan.Logger.Info("Y k1 (before Injection): " + str(kY1))
        self.PeakCan.Logger.Info("Z k1 (before Injection): " + str(kZ1))
        self.PeakCan.Logger.Info("X k2 (after Injection): " + str(kX2))
        self.PeakCan.Logger.Info("Y k2 (after Injection): " + str(kY2))
        self.PeakCan.Logger.Info("Z k2 (after Injection): " + str(kZ2))
        self.PeakCan.Logger.Info("X k3 (after Ejection): " + str(kX3))
        self.PeakCan.Logger.Info("Y k3 (after Ejection): " + str(kY3))
        self.PeakCan.Logger.Info("Z k3 (after Ejection): " + str(kZ3))
        self.PeakCan.Logger.Info("X k4 (after k3): " + str(kX4))
        self.PeakCan.Logger.Info("Y k4 (after k3): " + str(kY4))
        self.PeakCan.Logger.Info("Z k4 (after k3): " + str(kZ4))      
        k1mVX = (50 * AdcReference["VDD"]) * kX1 / AdcMax
        k2mVX = (50 * AdcReference["VDD"]) * kX2 / AdcMax
        k1mVY = (50 * AdcReference["VDD"]) * kY1 / AdcMax
        k2mVY = (50 * AdcReference["VDD"]) * kY2 / AdcMax
        k1mVZ = (50 * AdcReference["VDD"]) * kZ1 / AdcMax
        k2mVZ = (50 * AdcReference["VDD"]) * kZ2 / AdcMax
        self.PeakCan.Logger.Info("Xk1: " + str(k1mVX) + "mV")
        self.PeakCan.Logger.Info("Yk1: " + str(k1mVY) + "mV")
        self.PeakCan.Logger.Info("Zk1: " + str(k1mVZ) + "mV")
        self.PeakCan.Logger.Info("Xk2: " + str(k2mVX) + "mV")
        self.PeakCan.Logger.Info("Yk2: " + str(k2mVY) + "mV")
        self.PeakCan.Logger.Info("Zk2: " + str(k2mVZ) + "mV")
        self.PeakCan.Logger.Info("ADC Max: " + str(AdcMax))
        self.PeakCan.Logger.Info("Voltage Max: " + str(50 * AdcReference["VDD"]) + "mV")
        difKX = k2mVX - k1mVX
        difKY = k2mVY - k1mVY
        difKZ = k2mVZ - k1mVZ
        self.PeakCan.Logger.Info("Xk2-Xk1(measured): " + str(difKX) + "mV")
        self.PeakCan.Logger.Info("Yk2-YXk1(measured): " + str(difKY) + "mV")
        self.PeakCan.Logger.Info("Yk2-Yk1(measured): " + str(difKZ) + "mV")
        self.PeakCan.Logger.Info("k2-k1(assumed) Mininimum: " + str(SelfTestOutputChangemVMin) + "mV")
        self.PeakCan.Logger.Info("k2-k1(assumed) Typical: " + str(SelfTestOutputChangemVTyp) + "mV")
        self.assertGreaterEqual(difKX, SelfTestOutputChangemVMin)
        self.assertLessEqual(difKX, SelfTestOutputChangemVTyp)
        if 1 < Axis:
            self.assertGreaterEqual(difKY, SelfTestOutputChangemVMin)
            self.assertLowerEqual(difKY, SelfTestOutputChangemVTyp)
            self.assertGreaterEqual(difKZ, SelfTestOutputChangemVMin)
            self.assertLowerEqual(difKZ, SelfTestOutputChangemVTyp)
        # Inject State Check
        self.assertEqual(ackInjectX[0], 0xa0)
        self.assertEqual(ackInjectY[0], 0xa0)
        self.assertEqual(ackInjectZ[0], 0xa0)
        self.assertEqual(ackInjectX[1], 0x0)
        self.assertEqual(ackInjectY[1], 0x0)
        self.assertEqual(ackInjectZ[1], 0x0)
        self.assertEqual(ackInjectX[2], 0x1)
        self.assertEqual(ackInjectY[2], 0x2)
        self.assertEqual(ackInjectZ[2], 0x3)
        self.assertEqual(ackInjectX[3], 0x42)
        self.assertEqual(ackInjectY[3], 0x42)
        self.assertEqual(ackInjectZ[3], 0x42)
        for i in range(4, 8):
            self.assertEqual(ackInjectX[i], 0x00)
            self.assertEqual(ackInjectY[i], 0x00)
            self.assertEqual(ackInjectZ[i], 0x00)
            
        self.assertEqual(stateInjectX[0], 0x20)
        self.assertEqual(stateInjectY[0], 0x20)
        self.assertEqual(stateInjectZ[0], 0x20)
        self.assertEqual(stateInjectX[1], 0x0)
        self.assertEqual(stateInjectY[1], 0x0)
        self.assertEqual(stateInjectZ[1], 0x0)
        self.assertEqual(stateInjectX[2], 0x1)
        self.assertEqual(stateInjectY[2], 0x2)
        self.assertEqual(stateInjectZ[2], 0x3)
        self.assertEqual(stateInjectX[3], 0x42)
        self.assertEqual(stateInjectY[3], 0x42)
        self.assertEqual(stateInjectZ[3], 0x42)
        for i in range(4, 8):
            self.assertEqual(stateInjectX[i], 0x00)  
            self.assertEqual(stateInjectY[i], 0x00)  
            self.assertEqual(stateInjectZ[i], 0x00)  
            
        # Eject State Check    
        self.assertEqual(ackEjectX[0], 0xC0)
        self.assertEqual(ackEjectY[0], 0xC0)
        self.assertEqual(ackEjectZ[0], 0xC0)
        self.assertEqual(ackEjectX[1], 0x0)
        self.assertEqual(ackEjectY[1], 0x0)
        self.assertEqual(ackEjectZ[1], 0x0)
        self.assertEqual(ackEjectX[2], 0x1)
        self.assertEqual(ackEjectY[2], 0x2)
        self.assertEqual(ackEjectZ[2], 0x3)
        self.assertEqual(ackEjectX[3], 0x42)
        self.assertEqual(ackEjectY[3], 0x42)
        self.assertEqual(ackEjectZ[3], 0x42)
        for i in range(4, 8):
            self.assertEqual(ackEjectX[i], 0x00)
            self.assertEqual(ackEjectY[i], 0x00)
            self.assertEqual(ackEjectZ[i], 0x00)
            
        self.assertEqual(stateEjectX[0], 0x40)
        self.assertEqual(stateEjectY[0], 0x40)
        self.assertEqual(stateEjectZ[0], 0x40)
        self.assertEqual(stateEjectX[1], 0x0)
        self.assertEqual(stateEjectY[1], 0x0)
        self.assertEqual(stateEjectZ[1], 0x0)
        self.assertEqual(stateEjectX[2], 0x1)
        self.assertEqual(stateEjectY[2], 0x2)
        self.assertEqual(stateEjectZ[2], 0x3)
        self.assertEqual(stateEjectX[3], 0x42)
        self.assertEqual(stateEjectY[3], 0x42)
        self.assertEqual(stateEjectZ[3], 0x42)
        for i in range(4, 8):
            self.assertEqual(stateEjectX[i], 0x00)  
            self.assertEqual(stateEjectY[i], 0x00)
            self.assertEqual(stateEjectZ[i], 0x00)
        
    """
    Check State at startup without any action
    """

    def test0604CalibrationMeasurementState(self):
        stateStartX = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Inject"], CalibMeassurementTypeNr["Acc"], 1, AdcReference["VDD"], bSet=False, bErrorAck=True)
        stateStartY = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Inject"], CalibMeassurementTypeNr["Acc"], 2, AdcReference["VDD"], bSet=False, bErrorAck=True)
        stateStartZ = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Inject"], CalibMeassurementTypeNr["Acc"], 3, AdcReference["VDD"], bSet=False, bErrorAck=True)
        stateStartTemp = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Inject"], CalibMeassurementTypeNr["Temp"], 1, AdcReference["VDD"], bSet=False, bErrorAck=True)
        stateStartVoltage = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Inject"], CalibMeassurementTypeNr["Voltage"], 1, AdcReference["VDD"], bSet=False, bErrorAck=True)        
        stateStartVss = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Inject"], CalibMeassurementTypeNr["Vss"], 1, AdcReference["VDD"], bSet=False, bErrorAck=True)
        stateStartAvdd = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Inject"], CalibMeassurementTypeNr["Avdd"], 1, AdcReference["VDD"], bSet=False, bErrorAck=True)
        stateStartDecouple = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Inject"], CalibMeassurementTypeNr["RegulatedInternalPower"], 1, AdcReference["VDD"], bSet=False, bErrorAck=True)
        stateStartOpa1 = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Inject"], CalibMeassurementTypeNr["OpvOutput"], 1, AdcReference["VDD"], bSet=False, bErrorAck=True)
        stateStartOpa2 = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Inject"], CalibMeassurementTypeNr["OpvOutput"], 2, AdcReference["VDD"], bSet=False, bErrorAck=True)
        ErrorPayloadAssumed = [0x0, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
        self.PeakCan.Logger.Info("Assumed bError Payload: " + payload2Hex(ErrorPayloadAssumed)) 
        self.PeakCan.Logger.Info("State Start AccX: " + payload2Hex(stateStartX)) 
        self.PeakCan.Logger.Info("State Start AccY: " + payload2Hex(stateStartY)) 
        self.PeakCan.Logger.Info("State Start AccZ: " + payload2Hex(stateStartZ)) 
        self.PeakCan.Logger.Info("State Start Temp: " + payload2Hex(stateStartTemp)) 
        self.PeakCan.Logger.Info("State Start Voltage: " + payload2Hex(stateStartVoltage)) 
        self.PeakCan.Logger.Info("State Start Vss: " + payload2Hex(stateStartVss)) 
        self.PeakCan.Logger.Info("State Start Avdd: " + payload2Hex(stateStartAvdd)) 
        self.PeakCan.Logger.Info("State Start Decouple: " + payload2Hex(stateStartDecouple))        
        self.PeakCan.Logger.Info("State Start Opa1: " + payload2Hex(stateStartOpa1))  
        self.PeakCan.Logger.Info("State Start Opa2: " + payload2Hex(stateStartOpa2))  
        for i in range(0, 8):
            self.assertEqual(stateStartX[i], ErrorPayloadAssumed[i])
            self.assertEqual(stateStartY[i], ErrorPayloadAssumed[i])
            self.assertEqual(stateStartZ[i], ErrorPayloadAssumed[i])
            self.assertEqual(stateStartTemp[i], ErrorPayloadAssumed[i])
            self.assertEqual(stateStartVoltage[i], ErrorPayloadAssumed[i])
            self.assertEqual(stateStartVss[i], ErrorPayloadAssumed[i])
            self.assertEqual(stateStartAvdd[i], ErrorPayloadAssumed[i])
            self.assertEqual(stateStartDecouple[i], ErrorPayloadAssumed[i])      
            self.assertEqual(stateStartOpa1[i], ErrorPayloadAssumed[i])
            self.assertEqual(stateStartOpa2[i], ErrorPayloadAssumed[i])        
      
    """
    Check Reset Subcommand of Calibration Measurement Command
    """  

    def test0605StateCalibrationMeasurementReset(self):
        ackInjectX = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Inject"], CalibMeassurementTypeNr["Acc"], 1, AdcReference["VDD"])
        stateInjectX = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Inject"], CalibMeassurementTypeNr["Acc"], 1, AdcReference["VDD"], bSet=False)          
        ackReset = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Inject"], CalibMeassurementTypeNr["Acc"], 1, AdcReference["VDD"], bReset=True)
        stateStartX = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Inject"], CalibMeassurementTypeNr["Acc"], 1, AdcReference["VDD"], bSet=False, bErrorAck=True)
        stateStartAvdd = self.PeakCan.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Inject"], CalibMeassurementTypeNr["Avdd"], 1, AdcReference["VDD"], bSet=False, bErrorAck=True)
        self.PeakCan.Logger.Info("Ack from Inject AccX Command: " + payload2Hex(ackInjectX))
        self.PeakCan.Logger.Info("State after Inject AccX Command: " + payload2Hex(stateInjectX))  
        self.PeakCan.Logger.Info("Ack from Reset Command: " + payload2Hex(ackReset))
        self.PeakCan.Logger.Info("State AccX after Reset Command: " + payload2Hex(stateStartX))
        self.PeakCan.Logger.Info("State AVDD after Reset Command: " + payload2Hex(stateStartAvdd))
        # Inject State Check
        self.assertEqual(ackInjectX[0], 0xa0)
        self.assertEqual(ackInjectX[1], 0x0)
        self.assertEqual(ackInjectX[2], 0x1)
        self.assertEqual(ackInjectX[3], 0x42)
        for i in range(4, 8):
            self.assertEqual(ackInjectX[i], 0x00)
        self.assertEqual(stateInjectX[0], 0x20)
        self.assertEqual(stateInjectX[1], 0x0)
        self.assertEqual(stateInjectX[2], 0x1)
        self.assertEqual(stateInjectX[3], 0x42)
        for i in range(4, 8):
            self.assertEqual(stateInjectX[i], 0x00)          
        self.PeakCan.Logger.Info("test0303GetSingleAccX")
        self.test0302GetSingleAccX()
        
    """
    Check Power On and Power Off Counters
    """   

    def test0700StatisticsPowerOnCounterPowerOffCounter(self):
        PowerOnOff1 = self.PeakCan.statisticalData(MyToolItNetworkNr["STH1"], MyToolItStatData["PocPof"])
        PowerOn1 = messageWordGet(PowerOnOff1[:4])
        PowerOff1 = messageWordGet(PowerOnOff1[4:])
        self._resetSth()
        self.PeakCan.BlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])
        PowerOnOff2 = self.PeakCan.statisticalData(MyToolItNetworkNr["STH1"], MyToolItStatData["PocPof"])
        PowerOn2 = messageWordGet(PowerOnOff2[:4])
        PowerOff2 = messageWordGet(PowerOnOff2[4:])
        self.PeakCan.BlueToothDisconnect(MyToolItNetworkNr["STU1"])
        self.PeakCan.BlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])
        PowerOnOff3 = self.PeakCan.statisticalData(MyToolItNetworkNr["STH1"], MyToolItStatData["PocPof"])
        PowerOn3 = messageWordGet(PowerOnOff3[:4])
        PowerOff3 = messageWordGet(PowerOnOff3[4:])                
        self._resetStu()        
        self.PeakCan.BlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])
        PowerOnOff4 = self.PeakCan.statisticalData(MyToolItNetworkNr["STH1"], MyToolItStatData["PocPof"])
        PowerOn4 = messageWordGet(PowerOnOff4[:4])
        PowerOff4 = messageWordGet(PowerOnOff4[4:]) 
        self.PeakCan.Logger.Info("PowerOnOff Payload before STH Reset: " + payload2Hex(PowerOnOff1))
        self.PeakCan.Logger.Info("Power On Counter before STH Reset: " + str(PowerOn1))
        self.PeakCan.Logger.Info("Power Off Counter before STH Reset: " + str(PowerOff1))
        self.PeakCan.Logger.Info("PowerOnOff Payload after STH Reset: " + payload2Hex(PowerOnOff2))
        self.PeakCan.Logger.Info("Power On Counter after STH Reset: " + str(PowerOn2))
        self.PeakCan.Logger.Info("Power Off Counter after STH Reset: " + str(PowerOff2))
        self.PeakCan.Logger.Info("PowerOnOff Payload after Disconnect/Connect: " + payload2Hex(PowerOnOff3))
        self.PeakCan.Logger.Info("Power On Counter after Disconnect/Connect: " + str(PowerOn3))
        self.PeakCan.Logger.Info("Power Off Counter after Disconnect/Connect: " + str(PowerOff3))
        self.PeakCan.Logger.Info("PowerOnOff Payload after STU Reset: " + payload2Hex(PowerOnOff4))
        self.PeakCan.Logger.Info("Power On Counter after STU Reset: " + str(PowerOn4))
        self.PeakCan.Logger.Info("Power Off Counter after STU Reset: " + str(PowerOff4))
        self.assertEqual(PowerOn1 + 1, PowerOn2)
        self.assertEqual(PowerOff1 + 1, PowerOff2)
        self.assertEqual(PowerOn2 + 1, PowerOn3)
        self.assertEqual(PowerOff2 + 1, PowerOff3)
        self.assertEqual(PowerOn3 + 1, PowerOn4)
        self.assertEqual(PowerOff3 + 1, PowerOff4)

    """
    Check Operating Minutes
    """   

    def test0701StatisticsOperatingMinutes(self):
        OperatingMinutes1 = self.PeakCan.statisticalData(MyToolItNetworkNr["STH1"], MyToolItStatData["OperatingTime"])    
        MinutesReset1 = messageWordGet(OperatingMinutes1[:4])
        MinutesOveral1 = messageWordGet(OperatingMinutes1[4:])
        time.sleep(60)
        OperatingMinutes2 = self.PeakCan.statisticalData(MyToolItNetworkNr["STH1"], MyToolItStatData["OperatingTime"])    
        MinutesReset2 = messageWordGet(OperatingMinutes2[:4])
        MinutesOveral2 = messageWordGet(OperatingMinutes2[4:])
        self.PeakCan.BlueToothDisconnect(MyToolItNetworkNr["STU1"])
        self.PeakCan.BlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])
        OperatingMinutes3 = self.PeakCan.statisticalData(MyToolItNetworkNr["STH1"], MyToolItStatData["OperatingTime"])    
        MinutesReset3 = messageWordGet(OperatingMinutes3[:4])
        MinutesOveral3 = messageWordGet(OperatingMinutes3[4:])
        self.PeakCan.Logger.Info("Operating Minutes Payload: " + payload2Hex(OperatingMinutes1))
        self.PeakCan.Logger.Info("Operating Minutes since Reset: " + str(MinutesReset1))
        self.PeakCan.Logger.Info("Operating Minutes since frist PowerOn: " + str(MinutesOveral1))
        self.PeakCan.Logger.Info("Operating Minutes Payload(+1 minute): " + payload2Hex(OperatingMinutes2))
        self.PeakCan.Logger.Info("Operating Minutes since Reset(+1 minute): " + str(MinutesReset2))
        self.PeakCan.Logger.Info("Operating Minutes since frist PowerOn(+1minute): " + str(MinutesOveral2))    
        self.PeakCan.Logger.Info("Operating Minutes Payload(After Disconnect/Connect): " + payload2Hex(OperatingMinutes3))
        self.PeakCan.Logger.Info("Operating Minutes since Reset(After Disconnect/Connect): " + str(MinutesReset3))
        self.PeakCan.Logger.Info("Operating Minutes since frist PowerOn(After Disconnect/Connect): " + str(MinutesOveral3))     
        self.assertEqual(MinutesReset1, 0)                
        self.assertEqual(MinutesReset2, 1)
        self.assertEqual(MinutesReset3, 1)
        self.assertEqual(MinutesOveral1, MinutesOveral2)                
        self.assertEqual(MinutesOveral1 + 1, MinutesOveral3)
   
    """
    Check Watchdog counter to not increment
    """   

    def test0702WdogNotIncrementing(self):
        WDogCounter1 = self._SthWDog()
        self._resetSth()
        self.PeakCan.BlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])
        WDogCounter2 = self._SthWDog()
        self._resetSth()
        self.PeakCan.BlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])
        WDogCounter3 = self._SthWDog()
        self._resetSth()
        self.PeakCan.BlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])
        self.PeakCan.Logger.Info("Watchdog Counter at start: " + str(WDogCounter1))
        self.PeakCan.Logger.Info("Watchdog Counter after first reset: " + str(WDogCounter2))
        self.PeakCan.Logger.Info("Watchdog Counter after second reset: " + str(WDogCounter3))
        self.assertEqual(WDogCounter1, WDogCounter2)
        self.assertEqual(WDogCounter1, WDogCounter3)

    """
    Check Watchdog counter to not increment
    """   

    def test0750StatisticPageWriteRead(self):
        # Write 0xFF over the page
        timeStamp = self.PeakCan.getTimeMs()
        for offset in range(0, 256, 4):
            self.PeakCan.cmdSend(MyToolItNetworkNr["STH1"], MyToolItBlock["Eeprom"], MyToolItEeprom["Write"], [EepromPage["Statistics"], 0xFF & offset, 4, 0, 0xFF, 0xFF, 0xFF, 0xFF])
        self.PeakCan.Logger.Info("Page Write Time: " + str(self.PeakCan.getTimeMs() - timeStamp) + "ms")
        # Read back 0xFF over the page
        timeStamp = self.PeakCan.getTimeMs()
        for offset in range(0, 256, 4):
            index = self.PeakCan.cmdSend(MyToolItNetworkNr["STH1"], MyToolItBlock["Eeprom"], MyToolItEeprom["Read"], [EepromPage["Statistics"], 0xFF & offset, 4, 0, 0, 0, 0, 0])   
            dataReadBack = self.PeakCan.getReadMessageData(index)     
            for dataByte in dataReadBack[4:]:
                self.assertEqual(dataByte, 0xFF)
        self.PeakCan.Logger.Info("Page Read Time: " + str(self.PeakCan.getTimeMs() - timeStamp) + "ms")
        # Write 0x00 over the page
        timeStamp = self.PeakCan.getTimeMs()
        for offset in range(0, 256, 4):
            self.PeakCan.cmdSend(MyToolItNetworkNr["STH1"], MyToolItBlock["Eeprom"], MyToolItEeprom["Write"], [EepromPage["Statistics"], 0xFF & offset, 4, 0, 0, 0, 0, 0])
        self.PeakCan.Logger.Info("Page Write Time: " + str(self.PeakCan.getTimeMs() - timeStamp) + "ms")
        # Read back 0x00 over the page    
        timeStamp = self.PeakCan.getTimeMs()
        for offset in range(0, 256, 4):
            index = self.PeakCan.cmdSend(MyToolItNetworkNr["STH1"], MyToolItBlock["Eeprom"], MyToolItEeprom["Read"], [EepromPage["Statistics"], 0xFF & offset, 4, 0, 0, 0, 0, 0])   
            dataReadBack = self.PeakCan.getReadMessageData(index)     
            for dataByte in dataReadBack[4:]:
                self.assertEqual(dataByte, 0x00)             
        self.PeakCan.Logger.Info("Page Read Time: " + str(self.PeakCan.getTimeMs() - timeStamp) + "ms")       
                       
    """
    Status Word after Reset
    """        

    def test0800StatusWords0Reset(self):
        StateWord = SthStateWord()
        StateWord.asword = self.PeakCan.statusWord0(MyToolItNetworkNr["STH1"])
        self.PeakCan.Logger.Info("STH State Word: " + hex(StateWord.asword))
        self.PeakCan.Logger.Info("STH State Word - bError: " + str(StateWord.b.bError))
        self.PeakCan.Logger.Info("STH State Word - " + NetworkStateName[StateWord.b.u3NetworkState])
        self.assertEqual(StateWord.b.bError, 0)
        self.assertEqual(StateWord.b.u3NetworkState, NetworkState["Operating"])

    """
    Status Word in ADC overrun error case
    """        

    def test0801StatusWords0AdcOverRun(self):
        prescaler = 2
        acquisitionTime = AdcAcquisitionTime[1]
        overSamplingRate = AdcOverSamplingRate[2]
        Settings = self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], prescaler, acquisitionTime, overSamplingRate, AdcReference["VDD"])[1:]
        self.assertEqual(prescaler, Settings[0])
        self.assertEqual(acquisitionTime, Settings[1])
        self.assertEqual(overSamplingRate, Settings[2])
        self.assertEqual(AdcReference["VDD"], Settings[3])
        self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0)
        time.sleep(1)
        self.PeakCan.GetReadArrayIndex() - 1
        ack = self.PeakCan.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], bErrorExit=False)
        self.assertNotEqual("Error", ack)
        StateWord = SthStateWord()
        StateWord.asword = self.PeakCan.statusWord0(MyToolItNetworkNr["STH1"])
        self.PeakCan.Logger.Info("STH State Word: " + hex(StateWord.asword))
        self.PeakCan.Logger.Info("STH State Word - bError: " + str(StateWord.b.bError))
        self.PeakCan.Logger.Info("STH State Word - " + NetworkStateName[StateWord.b.u3NetworkState])
        self.assertEqual(StateWord.b.bError, 1)
        self.assertEqual(StateWord.b.u3NetworkState, NetworkState["Error"])
        self._resetStu()        
        self.PeakCan.BlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])

    """
    Status Word after Reset
    """

    def test0820StatusWords1Reset(self):
        ErrorWord = SthErrorWord()
        ErrorWord.asword = self.PeakCan.statusWord1(MyToolItNetworkNr["STH1"])
        self.PeakCan.Logger.Info("STH bError Word: " + hex(ErrorWord.asword))
        self.PeakCan.Logger.Info("STH bError Word Reserved: " + hex(ErrorWord.b.Reserved))
        self.PeakCan.Logger.Info("STH bError Word bAdcOverRun: " + hex(ErrorWord.b.bAdcOverRun))
        self.PeakCan.Logger.Info("STH bError Word bTxFail: " + hex(ErrorWord.b.bTxFail))
        self.assertEqual(ErrorWord.asword, 0)
                    
    """
    Status Word after ADC Overrun
    """

    def test0821StatusWords1AdcOverRun(self):
        prescaler = 2
        acquisitionTime = AdcAcquisitionTime[1]
        overSamplingRate = AdcOverSamplingRate[2]
        Settings = self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], prescaler, acquisitionTime, overSamplingRate, AdcReference["VDD"])[1:]
        self.assertEqual(prescaler, Settings[0])
        self.assertEqual(acquisitionTime, Settings[1])
        self.assertEqual(overSamplingRate, Settings[2])
        self.assertEqual(AdcReference["VDD"], Settings[3])
        self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0)
        time.sleep(1)
        ErrorWord = SthErrorWord()
        ErrorWord.asword = self.PeakCan.statusWord1(MyToolItNetworkNr["STH1"])
        self.PeakCan.Logger.Info("STH bError Word: " + hex(ErrorWord.asword))
        self.PeakCan.Logger.Info("STH bError Word Reserved: " + hex(ErrorWord.b.Reserved))
        self.PeakCan.Logger.Info("STH bError Word bAdcOverRun: " + hex(ErrorWord.b.bAdcOverRun))
        self.PeakCan.Logger.Info("STH bError Word bTxFail: " + hex(ErrorWord.b.bTxFail))
        self.assertEqual(ErrorWord.b.bAdcOverRun, 1)
        self._resetStu()        
        self.PeakCan.BlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])
        
    """
    Status Word after Overspeed
    """

    def test0822StatusWords1TxFail(self):
        prescaler = 2
        acquisitionTime = AdcAcquisitionTime[8]
        overSamplingRate = AdcOverSamplingRate[32]
        Settings = self.PeakCan.ConfigAdc(MyToolItNetworkNr["STH1"], prescaler, acquisitionTime, overSamplingRate, AdcReference["VDD"])[1:]
        self.assertEqual(prescaler, Settings[0])
        self.assertEqual(acquisitionTime, Settings[1])
        self.assertEqual(overSamplingRate, Settings[2])
        self.assertEqual(AdcReference["VDD"], Settings[3])
        self.PeakCan.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0)
        time.sleep(10)
        ErrorWord = SthErrorWord()
        ErrorWord.asword = self.PeakCan.statusWord1(MyToolItNetworkNr["STH1"])
        self.PeakCan.Logger.Info("STH bError Word: " + hex(ErrorWord.asword))
        self.PeakCan.Logger.Info("STH bError Word Reserved: " + hex(ErrorWord.b.Reserved))
        self.PeakCan.Logger.Info("STH bError Word bAdcOverRun: " + hex(ErrorWord.b.bAdcOverRun))
        self.PeakCan.Logger.Info("STH bError Word bTxFail: " + hex(ErrorWord.b.bTxFail))
        self.assertEqual(ErrorWord.b.bAdcOverRun, 0)
        self.assertEqual(ErrorWord.b.bTxFail, 1)
        self._resetStu()        
        self.PeakCan.BlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])
 
    """
    Active State
    """

    def test0880ActiveStateReset(self):     
        activeState = ActiveState()
        activeState.asbyte = 0  # Set=0 ->Read
        indexAssumed = self.PeakCan.cmdSend(MyToolItNetworkNr["STH1"], MyToolItBlock["System"], MyToolItSystem["ActiveState"], [activeState.asbyte])        
        activeState.asbyte = self.PeakCan.getReadMessageData(indexAssumed)[0]
        self.PeakCan.Logger.Info("STH Active State: " + hex(activeState.asbyte))
        self.PeakCan.Logger.Info("STH Active State(Read Ack): - bSetState: " + str(activeState.b.bSetState))
        self.PeakCan.Logger.Info("STH Active State(Read Ack): - bReserved: " + str(activeState.b.bReserved))
        self.PeakCan.Logger.Info("STH Active State(Read Ack): - u2NodeState: " + str(activeState.b.u2NodeState))
        self.PeakCan.Logger.Info("STH Active State(Read Ack): - bReserved1: " + str(activeState.b.bReserved1))
        self.PeakCan.Logger.Info("STH Active State(Read Ack): - u3NetworkState: " + str(activeState.b.u3NetworkState))
        self.assertEqual(activeState.b.bSetState, 0)
        self.assertEqual(activeState.b.bReserved, 0)
        self.assertEqual(activeState.b.u2NodeState, Node["Application"])
        self.assertEqual(activeState.b.bReserved1, 0)
        self.assertEqual(activeState.b.u3NetworkState, NetworkState["Operating"])

    """
    Active State
    """

    def test0881ActiveStateError(self):     
        activeState = ActiveState()
        activeState.asbyte = 0  # Set=0 ->Read
        activeState.b.u2NodeState = Node["Application"]
        activeState.b.u3NetworkState = NetworkState["Error"]
        activeState.b.bSetState = 1
        indexAssumed = self.PeakCan.cmdSend(MyToolItNetworkNr["STH1"], MyToolItBlock["System"], MyToolItSystem["ActiveState"], [activeState.asbyte])        
        activeState.asbyte = self.PeakCan.getReadMessageData(indexAssumed)[0]
        self.PeakCan.Logger.Info("STH Active State(Write Ack): " + hex(activeState.asbyte))
        self.PeakCan.Logger.Info("STH Active State(Write Ack): - bSetState: " + str(activeState.b.bSetState))
        self.PeakCan.Logger.Info("STH Active State(Write Ack): - bReserved: " + str(activeState.b.bReserved))
        self.PeakCan.Logger.Info("STH Active State(Write Ack): - u2NodeState: " + str(activeState.b.u2NodeState))
        self.PeakCan.Logger.Info("STH Active State(Write Ack): - bReserved1: " + str(activeState.b.bReserved1))
        self.PeakCan.Logger.Info("STH Active State(Write Ack): - u3NetworkState: " + str(activeState.b.u3NetworkState))
        self.assertEqual(activeState.b.bSetState, 1)
        self.assertEqual(activeState.b.bReserved, 0)
        self.assertEqual(activeState.b.u2NodeState, Node["Application"])
        self.assertEqual(activeState.b.bReserved1, 0)
        self.assertEqual(activeState.b.u3NetworkState, NetworkState["Error"])
        indexAssumed = self.PeakCan.cmdSend(MyToolItNetworkNr["STH1"], MyToolItBlock["System"], MyToolItSystem["ActiveState"], [0])        
        activeState.asbyte = self.PeakCan.getReadMessageData(indexAssumed)[0]
        self.PeakCan.Logger.Info("STH Active State(Read Ack): " + hex(activeState.asbyte))
        self.PeakCan.Logger.Info("STH Active State(Read Ack): - bSetState: " + str(activeState.b.bSetState))
        self.PeakCan.Logger.Info("STH Active State(Read Ack): - bReserved: " + str(activeState.b.bReserved))
        self.PeakCan.Logger.Info("STH Active State(Read Ack): - u2NodeState: " + str(activeState.b.u2NodeState))
        self.PeakCan.Logger.Info("STH Active State(Read Ack): - bReserved1: " + str(activeState.b.bReserved1))
        self.PeakCan.Logger.Info("STH Active State(Read Ack): - u3NetworkState: " + str(activeState.b.u3NetworkState))
        self.assertEqual(activeState.b.bSetState, 0)
        self.assertEqual(activeState.b.bReserved, 0)
        self.assertEqual(activeState.b.u2NodeState, Node["Application"])
        self.assertEqual(activeState.b.bReserved1, 0)
        self.assertEqual(activeState.b.u3NetworkState, NetworkState["Error"])  
        self.PeakCan.Logger.Info("Trying to receive Stream (Must not work)")
        accFormat = AtvcFormat()
        accFormat.asbyte = 0
        accFormat.b.bStreaming = 1
        accFormat.b.bNumber1 = 1
        accFormat.b.bNumber2 = 0
        accFormat.b.bNumber3 = 0
        accFormat.b.u3DataSets = DataSets[3] 
        cmd = self.PeakCan.CanCmd(MyToolItBlock["Streaming"], MyToolItStreaming["Acceleration"], 1, 0)
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [accFormat.asbyte])
        ack = self.PeakCan.WriteFrameWaitAckRetries(message, bErrorExit=False)
        self.assertEqual("Error", ack)
        self.PeakCan.CanTimeStampStart(self._resetStu()["CanTime"])
        self.PeakCan.Logger.Info("Connect to STH")
        self.PeakCan.BlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])

    """
    Test that nothing happens when sinding Command 0x0000 to STH1
    """

    def test0900ErrorCmdVerbotenSth1(self):
        cmd = self.PeakCan.CanCmd(0, 0, 1, 0)
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [])
        msgAck = self.PeakCan.WriteFrameWaitAckRetries(message, waitMs=1000, retries=3, bErrorExit=False)
        self.assertEqual("Error", msgAck)
        cmd = self.PeakCan.CanCmd(0, 0, 1, 1)
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [])
        msgAck = self.PeakCan.WriteFrameWaitAckRetries(message, waitMs=1000, retries=3, bErrorExit=False)
        self.assertEqual("Error", msgAck)
        cmd = self.PeakCan.CanCmd(0, 0, 0, 0)
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [])
        msgAck = self.PeakCan.WriteFrameWaitAckRetries(message, waitMs=1000, retries=3, bErrorExit=False)
        self.assertEqual("Error", msgAck)
        cmd = self.PeakCan.CanCmd(0, 0, 0, 1)
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [])
        msgAck = self.PeakCan.WriteFrameWaitAckRetries(message, waitMs=1000, retries=3, bErrorExit=False)
        self.assertEqual("Error", msgAck)
               
    """
    Test that nothing happens when sinding Reqest(1) and bError(1) to STH1
    """

    def test0901ErrorRequestErrorSth1(self):
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["Reset"], 1, 1)
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [])
        msgAck = self.PeakCan.WriteFrameWaitAckRetries(message, waitMs=1000, retries=3, bErrorExit=False)
        self.assertEqual("Error", msgAck)
        cmd = self.PeakCan.CanCmd(MyToolItBlock["Streaming"], MyToolItStreaming["Acceleration"], 1, 1)
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [])
        msgAck = self.PeakCan.WriteFrameWaitAckRetries(message, waitMs=1000, retries=3, bErrorExit=False)
        self.assertEqual("Error", msgAck)          
     
    """
    Test Routing - Wrong Sender to STH1
    """

    def test0902WrongSenderSth1(self):
        for numberKey, numberVal in MyToolItNetworkNr.items():
            if "SPU1" != numberKey:
                cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["Reset"], 1, 0)
                message = self.PeakCan.CanMessage20(cmd, numberVal, MyToolItNetworkNr["STH1"], [])
                msgAck = self.PeakCan.WriteFrameWaitAckRetries(message, waitMs=1000, retries=3, bErrorExit=False)
                self.assertEqual("Error", msgAck)
                    
                
if __name__ == "__main__":
    print(sys.version)
    log_location = sys.argv[1]
    log_file = sys.argv[2]
    if '/' != log_location[-1]:
        log_location += '/'
    logFileLocation = log_location + log_file
    dir_name = os.path.dirname(logFileLocation)
    sys.path.append(dir_name)

    print("Log Files will be saved at: " + str(logFileLocation))
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    with open(logFileLocation, "w") as f:
        print(f)     
        runner = unittest.TextTestRunner(f)
        unittest.main(argv=['first-arg-is-ignored'], testRunner=runner)  

