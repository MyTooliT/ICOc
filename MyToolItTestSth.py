import unittest
import sys
import os
file_path = 'C:\Program Files\PCAN-Basic API\Include\PCANBasic.py'
dir_name = os.path.dirname(file_path)
sys.path.append(dir_name)
import math
from PCANBasic import *
from PeakCanFd import *
from MyToolItNetworkNumbers import *
from time import sleep
from time import time
from random import randint
from MyToolItSth import *
from SthLimits import *
from testSignal import *

log_file = 'TestStu.txt'
log_location = '../Logs/STH/'


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
        self.PeakCan = PeakCanFd(PCAN_BAUD_1M, self.fileName, self.fileNameError, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1)
        self.PeakCan.Logger.Info("TestCase: " + str(self._testMethodName))
        self.PeakCan.CanTimeStampStart(self._resetStu()["CanTime"])
        self.PeakCan.Logger.Info("Connect to STH")
        self.PeakCan.BlueToothConnectPollingName(MY_TOOL_IT_NETWORK_STU1, TestDeviceName)
        self._resetSth()
        self.PeakCan.Logger.Info("Connect to STH")
        self.PeakCan.BlueToothConnectPollingName(MY_TOOL_IT_NETWORK_STU1, TestDeviceName)
        self.Error = False
        self.PeakCan.Logger.Info("STU BlueTooth Address: " + hex(self.PeakCan.BlueToothAddress(MY_TOOL_IT_NETWORK_STU1)))
        self.PeakCan.Logger.Info("STH BlueTooth Address: " + hex(self.PeakCan.BlueToothAddress(MY_TOOL_IT_NETWORK_STH1)))
        self._statusWords()
        temp = self._SthAdcTemp()
        self.assertGreaterEqual(TempInternalMax, temp)
        self.assertLessEqual(TempInternalMin, temp)
        print("Start")
        self.PeakCan.Logger.Info("_______________________________________________________________________________________________________________")
        self.PeakCan.Logger.Info("Start")

    def tearDown(self):
        self.PeakCan.Logger.Info("Fin")
        self.PeakCan.Logger.Info("_______________________________________________________________________________________________________________")
        if False == self.PeakCan.Error:
            self._streamingStop()
            self._BlueToothStatistics()
            ReceiveFailCounter = self._RoutingInformation()
            self._statusWords()
            temp = self._SthAdcTemp()
            self.assertGreaterEqual(TempInternalMax, temp)
            self.assertLessEqual(TempInternalMin, temp)
            self.PeakCan.Logger.Info("Test Time End Time Stamp")
            self.PeakCan.BlueToothDisconnect(MY_TOOL_IT_NETWORK_STU1)
        else:
            ReceiveFailCounter = 0
        if(0 < ReceiveFailCounter):
            self.Error = True
        if False != self.PeakCan.Error:
            self.Error = True
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
        if True == self.Error:
            return True
        return False

    def _resetStu(self, retries=5, log=True):
        return self.PeakCan.cmdReset(MY_TOOL_IT_NETWORK_STU1, retries=retries, log=log)

    def _resetSth(self, retries=5, log=True):
        return self.PeakCan.cmdReset(MY_TOOL_IT_NETWORK_STH1, retries=retries, log=log)
        
    def _SthAdcTemp(self):
        ret = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionMeasure, CalibMeassurementTypeTemp, 1, AdcReference1V25, log=False)
        result = float(messageWordGet(ret[4:]))
        result /= 1000
        self.PeakCan.Logger.Info("Temperature(Chip): " + str(result) + "°C") 
        self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionNone, CalibMeassurementTypeTemp, 1, AdcReferenceNone, log=False, bReset=True)
        return result

    def _statusWords(self):
        ErrorWord = SthErrorWord()
        psw0 = self.PeakCan.statusWord0(MY_TOOL_IT_NETWORK_STH1)
        self.PeakCan.Logger.Info("STH Status Word: " + hex(psw0))
        psw0 = self.PeakCan.statusWord0(MY_TOOL_IT_NETWORK_STU1)
        self.PeakCan.Logger.Info("STU Status Word: " + hex(psw0))
        ErrorWord.asword = self.PeakCan.statusWord1(MY_TOOL_IT_NETWORK_STH1)
        if True == ErrorWord.b.bAdcOverRun:
            print("STH Error Word: " + hex(ErrorWord.asword))
            self.Error = True
        self.PeakCan.Logger.Info("STH Error Word: " + hex(ErrorWord.asword))
        ErrorWord.asword = self.PeakCan.statusWord1(MY_TOOL_IT_NETWORK_STU1)
        if True == ErrorWord.b.bAdcOverRun:
            print("STU Error Word: " + hex(ErrorWord.asword))
            self.Error = True
        self.PeakCan.Logger.Info("STU Error Word: " + hex(ErrorWord.asword))

    def _streamingStop(self):
        self.PeakCan.streamingStop(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION)
        self.PeakCan.streamingStop(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_VOLTAGE)

    def _BlueToothStatistics(self):
        SendCounter = self.PeakCan.BlueToothCmd(MY_TOOL_IT_NETWORK_STH1, SystemCommandBlueToothSendCounter)
        self.PeakCan.Logger.Info("BlueTooth Send Counter(STH1): " + str(SendCounter))
        Rssi = self.PeakCan.BlueToothRssi(MY_TOOL_IT_NETWORK_STH1)
        self.PeakCan.Logger.Info("BlueTooth Rssi(STH1): " + str(Rssi) + "dBm")
        SendCounter = self.PeakCan.BlueToothCmd(MY_TOOL_IT_NETWORK_STU1, SystemCommandBlueToothSendCounter)
        self.PeakCan.Logger.Info("BlueTooth Send Counter(STU1): " + str(SendCounter))
        ReceiveCounter = self.PeakCan.BlueToothCmd(MY_TOOL_IT_NETWORK_STU1, SystemCommandBlueToothReceiveCounter)
        self.PeakCan.Logger.Info("BlueTooth Receive Counter(STU1): " + str(ReceiveCounter))
        Rssi = self.PeakCan.BlueToothRssi(MY_TOOL_IT_NETWORK_STU1)
        self.PeakCan.Logger.Info("BlueTooth Rssi(STU1): " + str(Rssi) + "dBm")

    def _RoutingInformationSthSend(self):
        SendCounter = self.PeakCan.RoutingInformationCmd(MY_TOOL_IT_NETWORK_STH1, SystemCommandRoutingSendCounter, MY_TOOL_IT_NETWORK_STU1)
        self.PeakCan.Logger.Info("STH1 - Send Counter(Port STU1): " + str(SendCounter))
        SendCounter = self.PeakCan.RoutingInformationCmd(MY_TOOL_IT_NETWORK_STH1, SystemCommandRoutingSendFailCounter, MY_TOOL_IT_NETWORK_STU1)
        self.PeakCan.Logger.Info("STH1 - Send Fail Counter(Port STU1): " + str(SendCounter))
        SendCounter = self.PeakCan.RoutingInformationCmd(MY_TOOL_IT_NETWORK_STH1, SystemCommandRoutingSendLowLevelByteCounter, MY_TOOL_IT_NETWORK_STU1)
        self.PeakCan.Logger.Info("STH1 - Send Byte Counter(Port STU1): " + str(SendCounter))

    def _RoutingInformationSthReceive(self):
        ReceiveCounter = self.PeakCan.RoutingInformationCmd(MY_TOOL_IT_NETWORK_STH1, SystemCommandRoutingReceiveCounter, MY_TOOL_IT_NETWORK_STU1)
        self.PeakCan.Logger.Info("STH1 - Receive Counter(Port STU1): " + str(ReceiveCounter))
        ReceiveFailCounter = self.PeakCan.RoutingInformationCmd(MY_TOOL_IT_NETWORK_STH1, SystemCommandRoutingReceiveFailCounter, MY_TOOL_IT_NETWORK_STU1)
        self.PeakCan.Logger.Info("STH1 - Receive Fail Counter(Port STU1): " + str(ReceiveFailCounter))
        ReceiveCounter = self.PeakCan.RoutingInformationCmd(MY_TOOL_IT_NETWORK_STH1, SystemCommandRoutingReceiveLowLevelByteCounter, MY_TOOL_IT_NETWORK_STU1)
        self.PeakCan.Logger.Info("STH1 - Receive Byte Counter(Port STU1): " + str(ReceiveCounter))
        return ReceiveFailCounter

    def _RoutingInformationSth(self):
        self._RoutingInformationSthSend()
        ReceiveFailCounter = self._RoutingInformationSthReceive()
        return ReceiveFailCounter

    def _RoutingInformationStuPortSpuSend(self):
        SendCounter = self.PeakCan.RoutingInformationCmd(MY_TOOL_IT_NETWORK_STU1, SystemCommandRoutingSendCounter, MY_TOOL_IT_NETWORK_SPU1)
        self.PeakCan.Logger.Info("STU1 - Send Counter(Port SPU1): " + str(SendCounter))
        SendCounter = self.PeakCan.RoutingInformationCmd(MY_TOOL_IT_NETWORK_STU1, SystemCommandRoutingSendFailCounter, MY_TOOL_IT_NETWORK_SPU1)
        self.PeakCan.Logger.Info("STU1 - Send Fail Counter(Port SPU1): " + str(SendCounter))
        SendCounter = self.PeakCan.RoutingInformationCmd(MY_TOOL_IT_NETWORK_STU1, SystemCommandRoutingSendLowLevelByteCounter, MY_TOOL_IT_NETWORK_SPU1)
        self.PeakCan.Logger.Info("STU1 - Send Byte Counter(Port SPU1): " + str(SendCounter))

    def _RoutingInformationStuPortSpuReceive(self):
        ReceiveCounter = self.PeakCan.RoutingInformationCmd(MY_TOOL_IT_NETWORK_STU1, SystemCommandRoutingReceiveCounter, MY_TOOL_IT_NETWORK_SPU1)
        self.PeakCan.Logger.Info("STU1 - Receive Counter(Port SPU1): " + str(ReceiveCounter))
        ReceiveFailCounter = self.PeakCan.RoutingInformationCmd(MY_TOOL_IT_NETWORK_STU1, SystemCommandRoutingReceiveFailCounter, MY_TOOL_IT_NETWORK_SPU1)
        self.PeakCan.Logger.Info("STU1 - Receive Fail Counter(Port SPU1): " + str(ReceiveFailCounter))
        ReceiveCounter = self.PeakCan.RoutingInformationCmd(MY_TOOL_IT_NETWORK_STU1, SystemCommandRoutingReceiveLowLevelByteCounter, MY_TOOL_IT_NETWORK_SPU1)
        self.PeakCan.Logger.Info("STU1 - Receive Byte Counter(Port SPU1): " + str(ReceiveCounter))
        return ReceiveFailCounter

    def _RoutingInformationStuPortSpu(self):
        self._RoutingInformationStuPortSpuSend()
        ReceiveFailCounter = self._RoutingInformationStuPortSpuReceive()
        return ReceiveFailCounter

    def _RoutingInformationStuPortSthSend(self):
        SendCounter = self.PeakCan.RoutingInformationCmd(MY_TOOL_IT_NETWORK_STU1, SystemCommandRoutingSendCounter, MY_TOOL_IT_NETWORK_STH1)
        self.PeakCan.Logger.Info("STU1 - Send Counter(Port STH1): " + str(SendCounter))
        SendCounter = self.PeakCan.RoutingInformationCmd(MY_TOOL_IT_NETWORK_STU1, SystemCommandRoutingSendFailCounter, MY_TOOL_IT_NETWORK_STH1)
        self.PeakCan.Logger.Info("STU1 - Send Fail Counter(Port STH1): " + str(SendCounter))
        SendCounter = self.PeakCan.RoutingInformationCmd(MY_TOOL_IT_NETWORK_STU1, SystemCommandRoutingSendLowLevelByteCounter, MY_TOOL_IT_NETWORK_STH1)
        self.PeakCan.Logger.Info("STU1 - Send Byte Counter(Port STH1): " + str(SendCounter))

    def _RoutingInformationStuPortSthReceive(self):
        ReceiveCounter = self.PeakCan.RoutingInformationCmd(MY_TOOL_IT_NETWORK_STU1, SystemCommandRoutingReceiveCounter, MY_TOOL_IT_NETWORK_STH1)
        self.PeakCan.Logger.Info("STU1 - Receive Counter(Port STH1): " + str(ReceiveCounter))
        ReceiveFailCounter = self.PeakCan.RoutingInformationCmd(MY_TOOL_IT_NETWORK_STU1, SystemCommandRoutingReceiveFailCounter, MY_TOOL_IT_NETWORK_STH1)
        self.PeakCan.Logger.Info("STU1 - Receive Fail Counter(Port STH1): " + str(ReceiveFailCounter))
        ReceiveCounter = self.PeakCan.RoutingInformationCmd(MY_TOOL_IT_NETWORK_STU1, SystemCommandRoutingReceiveLowLevelByteCounter, MY_TOOL_IT_NETWORK_STH1)
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
        Settings = self.PeakCan.ConfigAdc(MY_TOOL_IT_NETWORK_STH1, prescaler, acquisitionTime, overSamplingRate, adcRef, log=log)[1:]
        self.assertEqual(prescaler, Settings[0])
        self.assertEqual(acquisitionTime, Settings[1])
        self.assertEqual(overSamplingRate, Settings[2])
        self.assertEqual(adcRef, Settings[3])
        calcRate = calcSamplingRate(prescaler, acquisitionTime, overSamplingRate)
        if False != log:
            self.PeakCan.Logger.Info("Start sending package")
        logCollect = log
        dataSets = self.PeakCan.Can20DataSet(b1, b2, b3)
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, dataSets, b1, b2, b3, runTime, log=logCollect, StartupTimeMs=startupTime)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, dataSets, b1, b2, b3, indexStart, indexEnd)
        self.PeakCan.ReadArrayReset()
        samplingPoints = self.PeakCan.samplingPoints(array1, array2, array3)
        if False != log:
            samplingPoints = self.PeakCan.samplingPoints(array1, array2, array3)
            self.PeakCan.Logger.Info("Running Time: " + str(runTime) + "ms")
            if False != startupTime:
                self.PeakCan.Logger.Info("Startup Time: " + str(StreamingStartupTimeMs) + "ms")
            self.PeakCan.Logger.Info("Assumed Sampling Points/s: " + str(calcRate))
            samplingRateDet = 1000 * samplingPoints / (runTime)
            self.PeakCan.Logger.Info("Determined Sampling Points/s: " + str(samplingRateDet))
            self.PeakCan.Logger.Info("Difference to Assumed Sampling Points: " + str((100 * samplingRateDet - calcRate) / calcRate) + "%")
            self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "")
        ratM = AdcVRefValuemV[AdcReferenceVDD] / AdcVRefValuemV[adcRef]
        ratT = 1
        if adcRef != AdcReferenceVDD:
            ratT = SamplingRateVfsToleranceRation
        if False != compare:
            self.streamingValueCompare(array1, array2, array3, AdcRawMiddleX * ratM, AdcRawToleranceX * ratT, AdcRawMiddleY * ratM, AdcRawToleranceY * ratT, AdcRawMiddleZ * ratM, AdcRawToleranceZ * ratT, fAdcRawDat)
        if False != compareRate:
            self.assertLess(runTime / 1000 * calcRate * SamplingToleranceLow, samplingPoints)
            self.assertGreater(runTime / 1000 * calcRate * SamplingToleranceHigh, samplingPoints)
        result = {"SamplingRate" : calcRate, "Value1" : array1, "Value2" : array2, "Value3" : array3}
        return result

    def TurnOffLed(self):
        self.PeakCan.Logger.Info("Turn Off LED")
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_CONFIGURATION, MY_TOOL_IT_CONFIGURATION_CONFIGURATION_HMI, 1, 0)
        message = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [129, 1, 2, 0, 0, 0, 0, 0])
        self.PeakCan.WriteFrameWaitAckRetries(message)

    def TurnOnLed(self):
        self.PeakCan.Logger.Info("Turn On LED")
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_CONFIGURATION, MY_TOOL_IT_CONFIGURATION_CONFIGURATION_HMI, 1, 0)
        message = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [129, 1, 1, 0, 0, 0, 0, 0])
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
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_STREAMING, subCmd, 1, 0)
        message = self.PeakCan.CanMessage20(cmd, sender, receiver, [accFormat.asbyte])
        if False != log:
            self.PeakCan.Logger.Info("Start sending package")
        self.PeakCan.WriteFrameWaitAckRetries(message, retries=1)
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_TEST, MY_TOOL_IT_TEST_SIGNAL, 1, 0)
        message = self.PeakCan.CanMessage20(cmd, sender, receiver, [testSignal, testModule, 0, 0, 0 , 0, 0xFF & value, 0xFF & (value >> 8)])
        if False != log:
            self.PeakCan.Logger.Info("Start sending test signal")
        self.PeakCan.WriteFrame(message)
        sleep(0.5)
        indexStart = self.PeakCan.GetReadArrayIndex()
        timeEnd = self.PeakCan.getTimeMs() + testTimeMs
        if False != log:
            self.PeakCan.Logger.Info("indexStart: " + str(indexStart))
        while self.PeakCan.getTimeMs() < timeEnd:
            pass
        self.PeakCan.streamingStop(MY_TOOL_IT_NETWORK_STH1, subCmd)
        sleep(0.2)  # synch to read thread
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
    Test Acknowledgement from STH. Write message and check identifier to be ack (No Error)
    """

    def test0001Ack(self):
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 1, 0)
        expectedData = ActiveState()
        expectedData.asbyte = 0
        expectedData.b.u2NodeState = 0
        expectedData.b.u3NetworkState = 6
        msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [expectedData.asbyte])
        self.PeakCan.Logger.Info("Write Message")
        self.PeakCan.WriteFrame(msg)
        self.PeakCan.Logger.Info("Wait 200ms")
        sleep(0.2)
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 0, 0)
        msgAckExpected = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_NETWORK_SPU1, [0])
        self.PeakCan.Logger.Info("Send ID: " + hex(msg.ID) + "; Expected ID: " + hex(msgAckExpected.ID) + "; Received ID: " + hex(self.PeakCan.getReadMessage(-1).ID))
        self.PeakCan.Logger.Info("Send Data: " + hex(0) + "; Expected Data: " + hex(expectedData.asbyte) + "; Received Data: " + hex(self.PeakCan.getReadMessage(-1).DATA[0]))
        self.assertEqual(hex(msgAckExpected.ID), hex(self.PeakCan.getReadMessage(-1).ID))
        self.assertEqual(expectedData.asbyte, self.PeakCan.getReadMessage(-1).DATA[0])

    """
    Test Energy Mode 1 - If you like to evaluate power consumption: Please do it manually
    """

    def test0011EnergySaveMode1(self):
        self.PeakCan.Logger.Info("Read out parameters from EEPORM")
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode([SystemCommandBlueToothEnergyModeReducedRead, self.PeakCan.DeviceNr, 0, 0, 0, 0, 0, 0])
        self.PeakCan.Logger.Info("First Read Time Sleep Time1: " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("First Read Time Advertisement Time 1: " + str(timeAdvertisement) + " ms")
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode([SystemCommandBlueToothEnergyModeReducedWrite, self.PeakCan.DeviceNr, 0xE8, 0x03, 0, 0, 0xE8, 0x03])
        self.PeakCan.Logger.Info("First Write Time Sleep Time1(ACK): " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("First Write Time Advertisement Time 1(ACK): " + str(timeAdvertisement) + " ms")
        self.assertEqual(timeReset, 1000)
        self.assertEqual(timeAdvertisement, 1000)
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode([SystemCommandBlueToothEnergyModeReducedRead, self.PeakCan.DeviceNr, 0, 0, 0, 0, 0, 0])
        self.PeakCan.Logger.Info("Read Time Sleep Time1: " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("Read Time Advertisement Time 1: " + str(timeAdvertisement) + " ms")
        self.assertEqual(timeReset, 1000)
        self.assertEqual(timeAdvertisement, 1000)
        self._resetSth()
        self.PeakCan.BlueToothConnectPollingName(MY_TOOL_IT_NETWORK_STU1, TestDeviceName)
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode([SystemCommandBlueToothEnergyModeReducedRead, self.PeakCan.DeviceNr, 0, 0, 0, 0, 0, 0])
        self.PeakCan.Logger.Info("Read Time Sleep Time1: " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("Read Time Advertisement Time 1: " + str(timeAdvertisement) + " ms")
        self.assertEqual(timeReset, 1000)
        self.assertEqual(timeAdvertisement, 1000)
        # Reset to default values
        self.PeakCan.Logger.Info("Write Time Sleep Time1: " + str(Sleep1TimeReset) + " ms")
        self.PeakCan.Logger.Info("Write Time Advertisement Time 1: " + str(Sleep1AdvertisementTimeReset) + " ms")
        S1B0 = Sleep1TimeReset & 0xFF
        S1B1 = (Sleep1TimeReset >> 8) & 0xFF
        S1B2 = (Sleep1TimeReset >> 16) & 0xFF
        S1B3 = (Sleep1TimeReset >> 24) & 0xFF
        A1B0 = Sleep1AdvertisementTimeReset & 0xFF
        A1B1 = (Sleep1AdvertisementTimeReset >> 8) & 0xFF
        Payload = [SystemCommandBlueToothEnergyModeReducedWrite, self.PeakCan.DeviceNr, S1B0, S1B1, S1B2, S1B3, A1B0, A1B1]
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode(Payload)
        self.PeakCan.Logger.Info("Write Time Sleep Time1(ACK): " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("Write Time Advertisement Time 1(ACK): " + str(timeAdvertisement) + " ms")
        self.assertEqual(timeReset, Sleep1TimeReset)
        self.assertEqual(timeAdvertisement, Sleep1AdvertisementTimeReset)
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode([SystemCommandBlueToothEnergyModeReducedRead, self.PeakCan.DeviceNr, 0, 0, 0, 0, 0, 0])
        self.PeakCan.Logger.Info("Read Time Sleep Time1: " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("Read Time Advertisement Time 1: " + str(timeAdvertisement) + " ms")
        self.assertEqual(timeReset, Sleep1TimeReset)
        self.assertEqual(timeAdvertisement, Sleep1AdvertisementTimeReset)
        self._resetSth()
        self.PeakCan.BlueToothConnectPollingName(MY_TOOL_IT_NETWORK_STU1, TestDeviceName)
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode([SystemCommandBlueToothEnergyModeReducedRead, self.PeakCan.DeviceNr, 0, 0, 0, 0, 0, 0])
        self.PeakCan.Logger.Info("Read Time Sleep Time1: " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("Read Time Advertisement Time 1: " + str(timeAdvertisement) + " ms")
        self.assertEqual(timeReset, Sleep1TimeReset)
        self.assertEqual(timeAdvertisement, Sleep1AdvertisementTimeReset)

    """
    Test Energy Mode 2 - If you like to evaluate power consumption: Please do it manually
    """

    def test0011EnergySaveMode2(self):
        self.PeakCan.Logger.Info("Set Energy Mode1 parameters")
        self.PeakCan.Logger.Info("Write EM1 parameters to EEPORM")
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode([SystemCommandBlueToothEnergyModeReducedWrite, self.PeakCan.DeviceNr, 0xE8, 0x03, 0, 0, 0xE8, 0x03])
        self.PeakCan.Logger.Info("First Write Time Sleep Time1(ACK): " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("First Write Time Advertisement Time 1(ACK): " + str(timeAdvertisement) + " ms")
        self.PeakCan.Logger.Info("Doing Energy Mode2 stuff")
        self.PeakCan.Logger.Info("Read out EM2 parameters from EEPORM")
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode([SystemCommandBlueToothEnergyModeLowestRead, self.PeakCan.DeviceNr, 0, 0, 0, 0, 0, 0])
        self.PeakCan.Logger.Info("First Read Time Sleep Time1: " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("First Read Time Advertisement Time 1: " + str(timeAdvertisement) + " ms")
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode([SystemCommandBlueToothEnergyModeLowestWrite, self.PeakCan.DeviceNr, 0xD0, 0x07, 0, 0, 0xD0, 0x07])
        self.PeakCan.Logger.Info("First Write Time Sleep Time1(ACK): " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("First Write Time Advertisement Time 1(ACK): " + str(timeAdvertisement) + " ms")
        self.assertEqual(timeReset, 2000)
        self.assertEqual(timeAdvertisement, 2000)
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode([SystemCommandBlueToothEnergyModeLowestRead, self.PeakCan.DeviceNr, 0, 0, 0, 0, 0, 0])
        self.PeakCan.Logger.Info("Read Time Sleep Time1: " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("Read Time Advertisement Time 1: " + str(timeAdvertisement) + " ms")
        self.assertEqual(timeReset, 2000)
        self.assertEqual(timeAdvertisement, 2000)
        self._resetSth()
        self.PeakCan.BlueToothConnectPollingName(MY_TOOL_IT_NETWORK_STU1, TestDeviceName)
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode([SystemCommandBlueToothEnergyModeLowestRead, self.PeakCan.DeviceNr, 0, 0, 0, 0, 0, 0])
        self.PeakCan.Logger.Info("Read Time Sleep Time1: " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("Read Time Advertisement Time 1: " + str(timeAdvertisement) + " ms")
        self.assertEqual(timeReset, 2000)
        self.assertEqual(timeAdvertisement, 2000)
        # Reset to default values
        self.PeakCan.Logger.Info("Write Time Sleep Time1: " + str(Sleep2TimeReset) + " ms")
        self.PeakCan.Logger.Info("Write Time Advertisement Time 1: " + str(Sleep2AdvertisementTimeReset) + " ms")
        S1B0 = Sleep2TimeReset & 0xFF
        S1B1 = (Sleep2TimeReset >> 8) & 0xFF
        S1B2 = (Sleep2TimeReset >> 16) & 0xFF
        S1B3 = (Sleep2TimeReset >> 24) & 0xFF
        A1B0 = Sleep2AdvertisementTimeReset & 0xFF
        A1B1 = (Sleep2AdvertisementTimeReset >> 8) & 0xFF
        Payload = [SystemCommandBlueToothEnergyModeLowestWrite, self.PeakCan.DeviceNr, S1B0, S1B1, S1B2, S1B3, A1B0, A1B1]
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode(Payload)
        self.PeakCan.Logger.Info("Write Time Sleep Time1(ACK): " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("Write Time Advertisement Time 1(ACK): " + str(timeAdvertisement) + " ms")
        self.assertEqual(timeReset, Sleep2TimeReset)
        self.assertEqual(timeAdvertisement, Sleep2AdvertisementTimeReset)
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode([SystemCommandBlueToothEnergyModeLowestRead, self.PeakCan.DeviceNr, 0, 0, 0, 0, 0, 0])
        self.PeakCan.Logger.Info("Read Time Sleep Time1: " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("Read Time Advertisement Time 1: " + str(timeAdvertisement) + " ms")
        self.assertEqual(timeReset, Sleep2TimeReset)
        self.assertEqual(timeAdvertisement, Sleep2AdvertisementTimeReset)
        self._resetSth()
        self.PeakCan.BlueToothConnectPollingName(MY_TOOL_IT_NETWORK_STU1, TestDeviceName)
        [timeReset, timeAdvertisement] = self.PeakCan.BlueToothEnergyMode([SystemCommandBlueToothEnergyModeLowestRead, self.PeakCan.DeviceNr, 0, 0, 0, 0, 0, 0])
        self.PeakCan.Logger.Info("Read Time Sleep Time1: " + str(timeReset) + " ms")
        self.PeakCan.Logger.Info("Read Time Advertisement Time 1: " + str(timeAdvertisement) + " ms")
        self.assertEqual(timeReset, Sleep2TimeReset)
        self.assertEqual(timeAdvertisement, Sleep2AdvertisementTimeReset)
        self.PeakCan.Logger.Info("Reset via test0011EnergySaveMode1 EM1 parameters")
        self.test0011EnergySaveMode1()

    
    """
    Test HMI
    """

    def test0020HmiLedGeckoModule(self):
        self.PeakCan.Logger.Info("Get LED state")
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_CONFIGURATION, MY_TOOL_IT_CONFIGURATION_CONFIGURATION_HMI, 1, 0)
        message = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [1, 1, 0, 0, 0, 0, 0, 0])
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
        message = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [129, 1, 2, 0, 0, 0, 0, 0])
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
        sleep(5)
        self.PeakCan.Logger.Info("Get LED state")
        message = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [1, 1, 0, 0, 0, 0, 0, 0])
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
        message = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [129, 1, 1, 0, 0, 0, 0, 0])
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
        sleep(5)
        self.PeakCan.Logger.Info("Get LED state")
        message = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [1, 1, 0, 0, 0, 0, 0, 0])
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
    Write name and get name (bluetooth command)
    """

    def test0103BlueToothName(self):
        self.PeakCan.Logger.Info("Bluetooth name command")
        self.PeakCan.Logger.Info("Write Walther0")
        self.PeakCan.BlueToothNameWrite(0, "Walther0")
        self.PeakCan.Logger.Info("Check Walther0")
        Name = self.PeakCan.BlueToothNameGet(0)[0:8]
        self.PeakCan.Logger.Info("Received: " + Name)
        self.assertEqual("Walther0", Name)
        self.PeakCan.Logger.Info("Write " + TestDeviceName)
        self.PeakCan.BlueToothNameWrite(0, TestDeviceName)
        self.PeakCan.Logger.Info("Check " + TestDeviceName)
        Name = self.PeakCan.BlueToothNameGet(0)[0:8]
        self.PeakCan.Logger.Info("Received: " + Name)
        self.assertEqual(TestDeviceName, Name)
        print("Last Set Name: " + Name)
    
    

        
    """
    Get Bluetooth Address
    """

    def test0104BlueToothAddress(self):
        self.PeakCan.Logger.Info("Get Bluetooth Address")
        self.PeakCan.Logger.Info("BlueTooth Address: " + hex(self.PeakCan.BlueToothAddress(MY_TOOL_IT_NETWORK_STH1)))

    """
    Check Bluetooth connectablity
    """

    def test0105BlueToothConnect(self):
        self.PeakCan.BlueToothEnergyModeNr(8000, Sleep1AdvertisementTimeReset, 1)
        self.PeakCan.BlueToothEnergyModeNr(SleepTimeMin, Sleep2AdvertisementTimeReset, 2)  
        for _i in range(0, 10):      
            self.PeakCan.BlueToothDisconnect(MY_TOOL_IT_NETWORK_STU1)
            sleep(9)
            self.PeakCan.BlueToothConnectPollingName(MY_TOOL_IT_NETWORK_STU1, TestDeviceName)
        self.PeakCan.BlueToothEnergyModeNr(SleepTimeMin, Sleep1AdvertisementTimeReset, 1)
        self.PeakCan.BlueToothEnergyModeNr(Sleep2TimeReset, Sleep2AdvertisementTimeReset, 2)  
        for _i in range(0,100):      
            self.PeakCan.BlueToothDisconnect(MY_TOOL_IT_NETWORK_STU1)
            sleep(0.5)
            self.PeakCan.BlueToothConnectPollingName(MY_TOOL_IT_NETWORK_STU1, TestDeviceName)        
        self.PeakCan.BlueToothEnergyModeNr(Sleep1TimeReset, Sleep1AdvertisementTimeReset, 1)
        self.PeakCan.BlueToothEnergyModeNr(Sleep2TimeReset, Sleep2AdvertisementTimeReset, 2)  
                
    """
    Get Battery Voltage via single command
    """

    def test0301GetSingleVoltageBattery(self):
        index = self.PeakCan.singleValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_VOLTAGE, 1, 0, 0)
        [val1, val2, val3] = self.PeakCan.singleValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_VOLTAGE, 1, 0, 0, index)
        self.PeakCan.ValueLog(val1, val2, val3, fVoltageBattery, "Battery Voltage", "V")
        self.singleValueCompare(val1, val2, val3, VoltMiddleBat, VoltToleranceBat, 0, 0, 0, 0, fVoltageBattery)

    """
    Test multi single battery meassurement
    """

    def test0302GetSingleVoltageBatteryMultipleTimes(self):
        for _i in range(0, 10):
            index = self.PeakCan.singleValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_VOLTAGE, 1, 0, 0)
            [val1, val2, val3] = self.PeakCan.singleValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_VOLTAGE, 1, 0, 0, index)
            self.PeakCan.ValueLog(val1, val2, val3, fVoltageBattery, "Battery Voltage", "V")
            self.singleValueCompare(val1, val2, val3, VoltMiddleBat, VoltToleranceBat, 0, 0, 0, 0, fVoltageBattery)

    """
    Test single battery Acceleration X-Axis meassurement
    """

    def test0303GetSingleAccX(self):
        index = self.PeakCan.singleValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, 1, 0, 0)
        [val1, val2, val3] = self.PeakCan.singleValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, 1, 0, 0, index)
        self.PeakCan.ValueLog(val1, val2, val3, fAcceleration, "Acceleration X", "g")
        self.singleValueCompare(val1, val2, val3, AdcMiddleX, AdcToleranceX, 0, 0, 0, 0, fAcceleration)

    """
    Test single battery Acceleration Y-Axis meassurement
    """

    def test0304GetSingleAccY(self):
        index = self.PeakCan.singleValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, 0, 1, 0)
        [val1, val2, val3] = self.PeakCan.singleValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, 0, 1, 0, index)
        self.PeakCan.ValueLog(val1, val2, val3, fAcceleration, "Acceleration Y", "g")
        self.singleValueCompare(val1, val2, val3, 0, 0, AdcMiddleY, AdcToleranceY, 0, 0, fAcceleration)

    """
    Test single battery Acceleration Z-Axis meassurement
    """

    def test0305GetSingleAccZ(self):
        index = self.PeakCan.singleValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, 0, 0, 1)
        [val1, val2, val3] = self.PeakCan.singleValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, 0, 0, 1, index)
        self.PeakCan.ValueLog(val1, val2, val3, fAcceleration, "Acceleration X", "g")
        self.singleValueCompare(val1, val2, val3, 0, 0, 0, 0, AdcMiddleZ, AdcToleranceZ, fAcceleration)

    """
    Test multi single X Acc meassurement
    """

    def test0306GetSingleSingleAccXMultipleTimes(self):
        for _i in range(0, 10):
            index = self.PeakCan.singleValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, 1, 0, 0)
            [val1, val2, val3] = self.PeakCan.singleValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, 1, 0, 0, index)
            self.PeakCan.ValueLog(val1, val2, val3, fAcceleration, "Acceleration X", "g")
            self.singleValueCompare(val1, val2, val3, AdcMiddleX, AdcToleranceX, 0, 0, 0, 0, fAcceleration)

    """
    Test multi single Y Acc meassurement
    """

    def test0307GetSingleSingleAccYMultipleTimes(self):
        for _i in range(0, 10):
            index = self.PeakCan.singleValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, 0, 1, 0)
            [val1, val2, val3] = self.PeakCan.singleValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, 0, 1, 0, index)
            self.PeakCan.ValueLog(val1, val2, val3, fAcceleration, "Acceleration Y", "g")
            self.singleValueCompare(val1, val2, val3, 0, 0, AdcMiddleY, AdcToleranceY, 0, 0, fAcceleration)

    """
    Test multi single Z Acc meassurement
    """

    def test0308GetSingleSingleAccZMultipleTimes(self):
        for _i in range(0, 10):
            index = self.PeakCan.singleValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, 0, 0, 1)
            [val1, val2, val3] = self.PeakCan.singleValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, 0, 0, 1, index)
            self.PeakCan.ValueLog(val1, val2, val3, fAcceleration, "Acceleration Z", "g")
            self.singleValueCompare(val1, val2, val3, 0, 0, 0, 0, AdcMiddleZ, AdcToleranceZ, fAcceleration)
            
    """
    Test streaming battery meassurement
    """

    def test0320GetStreamingVoltageBattery(self):
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_VOLTAGE, DataSets3, 1, 0, 0, StreamingStandardTestTimeMs)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_VOLTAGE, DataSets3, 1, 0, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fVoltageBattery, "Battery", "V",)
        self.streamingValueCompare(array1, array2, array3, VoltMiddleBat, VoltToleranceBat, 0, 0, 0, 0, fVoltageBattery)

    """
    Test streaming x-Axis meassurement
    """

    def test0321GetStreamingAccX(self):
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 1, 0, 0, StreamingStandardTestTimeMs)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 1, 0, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAcceleration, "Acc", "g",)
        self.streamingValueCompare(array1, array2, array3, AdcMiddleX, AdcToleranceX, 0, 2 ** 32, 0, 2 ** 32, fAcceleration)

    """
    Test streaming y-Axis meassurement
    """

    def test0322GetStreamingAccY(self):
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 0, 1, 0, StreamingStandardTestTimeMs)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 0, 1, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAcceleration, "Acc", "g",)
        self.streamingValueCompare(array1, array2, array3, 0, 2 ** 32, AdcMiddleY, AdcToleranceY, 0, 2 ** 32, fAcceleration)

    """
    Test streaming z-Axis meassurement
    """

    def test0323GetStreamingAccZ(self):
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 0, 0, 1, StreamingStandardTestTimeMs)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 0, 0, 1, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAcceleration, "Acc", "g",)
        self.streamingValueCompare(array1, array2, array3, 0, 2 ** 32, 0, 2 ** 32, AdcMiddleZ, AdcToleranceZ, fAcceleration)

    """
    Test streaming xyz-Axis meassurement
    """

    def test0324GetStreamingAccXYZ(self):
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets1, 1, 1, 1, StreamingStandardTestTimeMs)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets1, 1, 1, 1, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "",)
        self.streamingValueCompare(array1, array2, array3, AdcMiddleX, AdcToleranceX, AdcMiddleY, AdcToleranceY, AdcMiddleZ, AdcToleranceZ, fAcceleration)

    """
    Test streaming Double-Axis meassurement
    """

    def test0325GetStreamingAccDouble(self):
        self.PeakCan.ConfigAdc(MY_TOOL_IT_NETWORK_STH1, 2, AdcAcquisitionTime16, AdcOverSamplingRate64, AdcReferenceVDD)
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets1, 1, 1, 0, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets1, 1, 1, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "",)
        self.streamingValueCompare(array1, array2, array3, AdcMiddleX, AdcToleranceX, AdcMiddleY, AdcToleranceY, AdcMiddleZ, AdcToleranceZ, fAcceleration)
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets1, 1, 0, 1, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets1, 1, 0, 1, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "",)
        self.streamingValueCompare(array1, array2, array3, AdcMiddleX, AdcToleranceX, AdcMiddleY, AdcToleranceY, AdcMiddleZ, AdcToleranceZ, fAcceleration)
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets1, 0, 1, 1, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets1, 0, 1, 1, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "",)
        self.streamingValueCompare(array1, array2, array3, AdcMiddleX, AdcToleranceX, AdcMiddleY, AdcToleranceY, AdcMiddleZ, AdcToleranceZ, fAcceleration)

    """
    Test Signal-to-Noise Ration - x
    """

    def test0326SignalIndicatorsAccX(self):
        self.TurnOffLed()
        self.PeakCan.ConfigAdc(MY_TOOL_IT_NETWORK_STH1, 2, AdcAcquisitionTime8, AdcOverSamplingRate64, AdcReferenceVDD)
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 1, 0, 0, StreamingStandardTestTimeMs)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 1, 0, 0, indexStart, indexEnd)
        statistics = self.signalIndicators(array1, array2, array3)
        self.siginalIndicatorCheck("ADC X", statistics["Value1"], SigIndAccXQ1, SigIndAccXQ25, SigIndAccXMedL, SigIndAccXMedH, SigIndAccXQ75, SigIndAccXQ99, SigIndAccXVar, SigIndAccXSkewness, SigIndAccXSNR)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "")
        
    """
    Test Signal-to-Noise Ration - Y
    """

    def test0327SignalIndicatorsAccY(self):
        self.TurnOffLed()
        self.PeakCan.ConfigAdc(MY_TOOL_IT_NETWORK_STH1, 2, AdcAcquisitionTime8, AdcOverSamplingRate64, AdcReferenceVDD)
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 0, 1, 0, StreamingStandardTestTimeMs)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 0, 1, 0, indexStart, indexEnd)
        statistics = self.signalIndicators(array1, array2, array3)
        self.siginalIndicatorCheck("ADC Y", statistics["Value2"], SigIndAccYQ1, SigIndAccYQ25, SigIndAccYMedL, SigIndAccYMedH, SigIndAccYQ75, SigIndAccYQ99, SigIndAccYVar, SigIndAccYSkewness, SigIndAccYSNR)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "")

    """
    Test Signal-to-Noise Ration - Z
    """

    def test0328SignalIndicatorsAccZ(self):
        self.TurnOffLed()
        self.PeakCan.ConfigAdc(MY_TOOL_IT_NETWORK_STH1, 2, AdcAcquisitionTime8, AdcOverSamplingRate64, AdcReferenceVDD)
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 0, 0, 1, StreamingStandardTestTimeMs)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 0, 0, 1, indexStart, indexEnd)
        statistics = self.signalIndicators(array1, array2, array3)
        self.siginalIndicatorCheck("ADC Z", statistics["Value3"], SigIndAccZQ1, SigIndAccZQ25, SigIndAccZMedL, SigIndAccZMedH, SigIndAccZQ75, SigIndAccZQ99, SigIndAccZVar, SigIndAccZSkewness, SigIndAccZSNR)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "")

    """
    Test Signal-to-Noise Ration - Z
    """

    def test0329SignalIndicatorsBattery(self):
        self.TurnOffLed()
        self.PeakCan.ConfigAdc(MY_TOOL_IT_NETWORK_STH1, 2, AdcAcquisitionTime8, AdcOverSamplingRate64, AdcReferenceVDD)
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_VOLTAGE, DataSets3, 1, 0, 0, StreamingStandardTestTimeMs)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_VOLTAGE, DataSets3, 1, 0, 0, indexStart, indexEnd)
        statistics = self.signalIndicators(array1, array2, array3)
        self.siginalIndicatorCheck("Battery", statistics["Value1"], SigIndAccZQ1, SigIndAccZQ25, SigIndAccZMedL, SigIndAccZMedH, SigIndAccZQ75, SigIndAccZQ99, SigIndAccZVar, SigIndAccZSkewness, SigIndAccZSNR)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Voltage", "")

    """
    Test Signal-to-Noise Ration - Acc Multi
    """

    def test0330SignalIndicatorsMulti(self):
        self.TurnOffLed()
        self.PeakCan.ConfigAdc(MY_TOOL_IT_NETWORK_STH1, 2, AdcAcquisitionTime16, AdcOverSamplingRate64, AdcReferenceVDD)
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets1, 1, 1, 0, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets1, 1, 1, 0, indexStart, indexEnd)
        statistics = self.signalIndicators(array1, array2, array3)
        self.siginalIndicatorCheck("ADC X", statistics["Value1"], SigIndAccXQ1, SigIndAccXQ25, SigIndAccXMedL, SigIndAccXMedH, SigIndAccXQ75, SigIndAccXQ99, SigIndAccXVar, SigIndAccXSkewness, SigIndAccXSNR)
        self.siginalIndicatorCheck("ADC Y", statistics["Value2"], SigIndAccYQ1, SigIndAccYQ25, SigIndAccYMedL, SigIndAccYMedH, SigIndAccYQ75, SigIndAccYQ99, SigIndAccYVar, SigIndAccYSkewness, SigIndAccYSNR)
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets1, 1, 0, 1, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets1, 1, 0, 1, indexStart, indexEnd)
        statistics = self.signalIndicators(array1, array2, array3)
        self.siginalIndicatorCheck("ADC X", statistics["Value1"], SigIndAccXQ1, SigIndAccXQ25, SigIndAccXMedL, SigIndAccXMedH, SigIndAccXQ75, SigIndAccXQ99, SigIndAccXVar, SigIndAccXSkewness, SigIndAccXSNR)
        self.siginalIndicatorCheck("ADC Z", statistics["Value3"], SigIndAccZQ1, SigIndAccZQ25, SigIndAccZMedL, SigIndAccZMedH, SigIndAccZQ75, SigIndAccZQ99, SigIndAccZVar, SigIndAccZSkewness, SigIndAccZSNR)
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets1, 0, 1, 1, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets1, 0, 1, 1, indexStart, indexEnd)
        statistics = self.signalIndicators(array1, array2, array3)
        self.siginalIndicatorCheck("ADC Y", statistics["Value2"], SigIndAccYQ1, SigIndAccYQ25, SigIndAccYMedL, SigIndAccYMedH, SigIndAccYQ75, SigIndAccYQ99, SigIndAccYVar, SigIndAccYSkewness, SigIndAccYSNR)
        self.siginalIndicatorCheck("ADC Z", statistics["Value3"], SigIndAccZQ1, SigIndAccZQ25, SigIndAccZMedL, SigIndAccZMedH, SigIndAccZQ75, SigIndAccZQ99, SigIndAccZVar, SigIndAccZSkewness, SigIndAccZSNR)
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets1, 1, 1, 1, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets1, 1, 1, 1, indexStart, indexEnd)
        statistics = self.signalIndicators(array1, array2, array3)
        self.siginalIndicatorCheck("ADC X", statistics["Value1"], SigIndAccXQ1, SigIndAccXQ25, SigIndAccXMedL, SigIndAccXMedH, SigIndAccXQ75, SigIndAccXQ99, SigIndAccXVar, SigIndAccXSkewness, SigIndAccXSNR)
        self.siginalIndicatorCheck("ADC Y", statistics["Value2"], SigIndAccYQ1, SigIndAccYQ25, SigIndAccYMedL, SigIndAccYMedH, SigIndAccYQ75, SigIndAccYQ99, SigIndAccYVar, SigIndAccYSkewness, SigIndAccYSNR)
        self.siginalIndicatorCheck("ADC Z", statistics["Value3"], SigIndAccZQ1, SigIndAccZQ25, SigIndAccZMedL, SigIndAccZMedH, SigIndAccZQ75, SigIndAccZQ99, SigIndAccZVar, SigIndAccZSkewness, SigIndAccZSNR)

    """
    Test Streaming multiple Times
    """

    def test0331GetStreamingMultipleTimes(self):
        for _i in range(0, 3):
            [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_VOLTAGE, DataSets3, 1, 0, 0, 1000)
            [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_VOLTAGE, DataSets3, 1, 0, 0, indexStart, indexEnd)
            self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Voltage", "")
            self.streamingValueCompare(array1, array2, array3, VoltMiddleBat, VoltToleranceBat, 0, 0, 0, 0, fVoltageBattery)
        for _i in range(0, 3):
            [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 1, 0, 0, 1000)
            [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 1, 0, 0, indexStart, indexEnd)
            self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "")
            self.streamingValueCompare(array1, array2, array3, AdcMiddleX, AdcToleranceX, AdcMiddleY, AdcToleranceY, AdcMiddleZ, AdcToleranceZ, fAcceleration)
        for _i in range(0, 3):
            [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 0, 1, 0, 1000)
            [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 0, 1, 0, indexStart, indexEnd)
            self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "")
            self.streamingValueCompare(array1, array2, array3, AdcMiddleX, AdcToleranceX, AdcMiddleY, AdcToleranceY, AdcMiddleZ, AdcToleranceZ, fAcceleration)
        for _i in range(0, 3):
            [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 0, 0, 1, 1000)
            [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 0, 0, 1, indexStart, indexEnd)
            self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "")
            self.streamingValueCompare(array1, array2, array3, AdcMiddleX, AdcToleranceX, AdcMiddleY, AdcToleranceY, AdcMiddleZ, AdcToleranceZ, fAcceleration)

    """
    Test multiple config battery, x, y, z
    """

    def test0332StreamingMultiConfigBatAccXAccYAccZ(self):
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_VOLTAGE, DataSets3, 1, 0, 0, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_VOLTAGE, DataSets3, 1, 0, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Voltage", "")
        self.streamingValueCompare(array1, array2, array3, VoltMiddleBat, VoltToleranceBat, 0, 0, 0, 0, fVoltageBattery)
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 1, 0, 0, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 1, 0, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "")
        self.streamingValueCompare(array1, array2, array3, AdcMiddleX, AdcToleranceX, AdcMiddleY, AdcToleranceY, AdcMiddleZ, AdcToleranceZ, fAcceleration)
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 0, 1, 0, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 0, 1, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "")
        self.streamingValueCompare(array1, array2, array3, AdcMiddleX, AdcToleranceX, AdcMiddleY, AdcToleranceY, AdcMiddleZ, AdcToleranceZ, fAcceleration)
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 0, 0, 1, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 0, 0, 1, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "Acc", "")
        self.streamingValueCompare(array1, array2, array3, AdcMiddleX, AdcToleranceX, AdcMiddleY, AdcToleranceY, AdcMiddleZ, AdcToleranceZ, fAcceleration)

    """
    Test multiple config x-xyz-x
    """

    def test0333StreamingMultiConfig(self):
        self.PeakCan.Logger.Info("Streaming AccX starts")
        self.test0321GetStreamingAccX()
        self.PeakCan.ReadArrayReset()
        self.PeakCan.Logger.Info("Streaming AccXYZ starts")
        self.test0324GetStreamingAccXYZ()
        self.PeakCan.ReadArrayReset()
        self.PeakCan.Logger.Info("Streaming AccX starts")
        self.test0321GetStreamingAccX()
        self.PeakCan.ReadArrayReset()
        
    """
    Test heavy usage of data acquiring
    """        

    def test0334StreamingHeavyDuty(self):
        for _i in range(0, 90):
            self.SamplingRate(2, AdcAcquisitionTime3, AdcOverSamplingRate64, AdcReferenceVDD, runTime=5000)
            self._streamingStop()
            self.PeakCan.ReadArrayReset()
        
    """
    Test x-Axis Line
    """

    def test0380GetStreamingTestLineAccX(self):
        [indexStart, indexEnd] = self.streamingTestSignalCollect(MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, TestCommandSignalLine, SthModuleStreaming, 2 ** 15, DataSets3, 1, 0, 0, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 1, 0, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "TestLine(AccelerationX - " + str(2 ** 15) + ")", "")
        self.streamingValueCompare(array1, array2, array3, 2 ** 15, 0, 0, 0, 0, 0, fAdcRawDat)
        [indexStart, indexEnd] = self.streamingTestSignalCollect(MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, TestCommandSignalLine, SthModuleStreaming, 2 ** 14, DataSets3, 1, 0, 0, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 1, 0, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "TestLine(AccelerationX - " + str(2 ** 14) + ")", "")
        self.streamingValueCompare(array1, array2, array3, 2 ** 14, 0, 0, 0, 0, 0, fAdcRawDat)

    """
    Test y-Axis Line
    """

    def test0381GetStreamingTestLineAccY(self):
        [indexStart, indexEnd] = self.streamingTestSignalCollect(MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, TestCommandSignalLine, SthModuleStreaming, 2 ** 15, DataSets3, 0, 1, 0, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 0, 1, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "TestLine(AccelerationY - " + str(2 ** 15) + ")", "")
        self.streamingValueCompare(array1, array2, array3, 0, 0, 2 ** 15, 0, 0, 0, fAdcRawDat)
        [indexStart, indexEnd] = self.streamingTestSignalCollect(MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, TestCommandSignalLine, SthModuleStreaming, 2 ** 14, DataSets3, 0, 1, 0, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 0, 1, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "TestLine(AccelerationY - " + str(2 ** 14) + ")", "")
        self.streamingValueCompare(array1, array2, array3, 0, 0, 2 ** 14, 0, 0, 0, fAdcRawDat)

    """
    Test z-Axis Line
    """

    def test0382GetStreamingTestLineAccZ(self):
        [indexStart, indexEnd] = self.streamingTestSignalCollect(MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, TestCommandSignalLine, SthModuleStreaming, 2 ** 15, DataSets3, 0, 0, 1, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 0, 0, 1, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "TestLine(AccelerationZ - " + str(2 ** 15) + ")", "")
        self.streamingValueCompare(array1, array2, array3, 0, 0, 0, 0, 2 ** 15, 0, fAdcRawDat)
        [indexStart, indexEnd] = self.streamingTestSignalCollect(MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, TestCommandSignalLine, SthModuleStreaming, 2 ** 14, DataSets3, 0, 0, 1, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 0, 0, 1, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "TestLine(AccelerationZ - " + str(2 ** 14) + ")", "")
        self.streamingValueCompare(array1, array2, array3, 0, 0, 0, 0, 2 ** 14, 0, fAdcRawDat)

    """
    Test Battery Line
    """

    def test0383GetStreamingTestLineBattery(self):
        [indexStart, indexEnd] = self.streamingTestSignalCollect(MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_VOLTAGE, TestCommandSignalLine, SthModuleStreaming, 2 ** 15, DataSets3, 1, 0, 0, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_VOLTAGE, DataSets3, 1, 0, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "TestLine(Battery - " + str(2 ** 15) + ")", "")
        self.streamingValueCompare(array1, array2, array3, 2 ** 15, 0, 0, 0, 0, 0, fAdcRawDat)
        [indexStart, indexEnd] = self.streamingTestSignalCollect(MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_VOLTAGE, TestCommandSignalLine, SthModuleStreaming, 2 ** 14, DataSets3, 1, 0, 0, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_VOLTAGE, DataSets3, 1, 0, 0, indexStart, indexEnd)
        self.PeakCan.ValueLog(array1, array2, array3, fAdcRawDat, "TestLine(Battery - " + str(2 ** 14) + ")", "")
        self.streamingValueCompare(array1, array2, array3, 2 ** 14, 0, 0, 0, 0, 0, fAdcRawDat)

    """
    Test x-Axis Ramp
    """

    def test0384GetStreamingTestRampAccX(self):
        [indexStart, indexEnd] = self.streamingTestSignalCollect(MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, TestCommandSignalRamp, SthModuleStreaming, 2 ** 16 - 1, DataSets3, 1, 0, 0, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 1, 0, 0, indexStart, indexEnd)
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
        [indexStart, indexEnd] = self.streamingTestSignalCollect(MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, TestCommandSignalRamp, SthModuleStreaming, 2 ** 16 - 1, DataSets3, 0, 1, 0, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 0, 1, 0, indexStart, indexEnd)
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
        [indexStart, indexEnd] = self.streamingTestSignalCollect(MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, TestCommandSignalRamp, SthModuleStreaming, 2 ** 16 - 1, DataSets3, 0, 0, 1, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 0, 0, 1, indexStart, indexEnd)
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
        [indexStart, indexEnd] = self.streamingTestSignalCollect(MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_VOLTAGE, TestCommandSignalRamp, SthModuleStreaming, 2 ** 16 - 1, DataSets3, 1, 0, 0, 1000)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_VOLTAGE, DataSets3, 1, 0, 0, indexStart, indexEnd)
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
        [indexStart, indexEnd] = self.PeakCan.streamingValueCollect(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 1, 0, 0, StreamingStandardTestTimeMs)
        [array1, array2, array3] = self.PeakCan.streamingValueArray(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 1, 0, 0, indexStart, indexEnd)
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
        self.SamplingRate(5, AdcAcquisitionTime8, AdcOverSamplingRate64, AdcReferenceVDD)

    """
    Testing ADC Sampling Rate - Acquisiton Time
    """

    def test0502SamplingRateAqu(self):
        self.SamplingRate(2, AdcAcquisitionTime32, AdcOverSamplingRate64, AdcReferenceVDD)

    """
    Testing ADC Sampling Rate - Oversampling Rate
    """

    def test0503SamplingRateOverSampling(self):
        self.SamplingRate(5, AdcAcquisitionTime8, AdcOverSamplingRate32, AdcReferenceVDD)

    """
    Testing ADC Sampling Rate - Single Sampling
    """

    def test0504SamplingRateSingleSampling(self):
        self.SamplingRate(2, AdcAcquisitionTime3, AdcOverSamplingRate64, AdcReferenceVDD, runTime=5000)

    """
    Testing ADC Sampling Rate - Maximum(Single Data)
    """

    def test0505SamplingRateDataSingleMax(self):
        calcRate = self.SamplingRate(2, AdcAcquisitionTime3, AdcOverSamplingRate64, AdcReferenceVDD, runTime=5000)["SamplingRate"]
        print("Maximum Sampling Rate(Single Sampling): " + str(calcRate))

    """
    Testing ADC Sampling Rate - Maximum(Double Data)
    """

    def test0506SamplingRateDataDoubleMax(self):
        calcRate = self.SamplingRate(3, AdcAcquisitionTime8, AdcOverSamplingRate64, AdcReferenceVDD, b1=1, b2=1, b3=0, runTime=5000)["SamplingRate"]
        print("Maximum Sampling Rate(Double Sampling): " + str(calcRate))

    """
    Testing ADC Sampling Rate - Maximum(Tripple Data)
    """

    def test0507SamplingRateDataTrippleMax(self):
        calcRate = self.SamplingRate(2, AdcAcquisitionTime3, AdcOverSamplingRate64, AdcReferenceVDD, b1=1, b2=1, b3=1, runTime=5000)["SamplingRate"]
        print("Maximum Sampling Rate(Tripple Sampling): " + str(calcRate))

    """
    Testing ADC Reference voltagegs
    """

    def test0508VRef(self):
        self.PeakCan.Logger.Info("Warm Up")
        self.SamplingRate(2, AdcAcquisitionTime3, AdcOverSamplingRate64, AdcReferenceVDD, b1=1, b2=1, b3=1, runTime=5000)
        for vRef in AdcReferenceList:
            self.PeakCan.Logger.Info("Using Voltage Reference: " + VRefName[vRef])
            self.SamplingRate(2, AdcAcquisitionTime3, AdcOverSamplingRate64, vRef, b1=1, b2=1, b3=1, runTime=5000, compare=(AdcReferenceVfs1V65 <= vRef), startupTime=False)

    """
    ADC Configuration Combine all possible settings - Single Axis
    """

    def test0509AdcConfigSingle(self):
        SamplingRateMaxDet = 0
        for prescaler in range(2, AdcConfigAllPrescalerMax):
            for acquisitionTime in AdcAcquisitionTimeList:
                for overSampling in AdcOverSamplingRateList:
                    samplingRate = calcSamplingRate(prescaler, acquisitionTime, overSampling)
                    if SamplingRateSingleMax >= samplingRate and SamplingRateMin <= samplingRate:
                        self.PeakCan.Logger.Info("Sampling Rate: " + str(samplingRate))
                        self.PeakCan.Logger.Info("Prescaer: " + str(prescaler))
                        self.PeakCan.Logger.Info("Acquisition Time: " + str(acquisitionTime))
                        self.PeakCan.Logger.Info("Oversampling Rate: " + str(overSampling))
                        for vRef in AdcReferenceList:
                            result = self.SamplingRate(prescaler, acquisitionTime, overSampling, vRef, b1=1, b2=0, b3=0, runTime=1000, compare=False, compareRate=False, log=False)
                            samplingPointsDet = self.PeakCan.samplingPoints(result["Value1"], result["Value2"], result["Value3"])
                            self.PeakCan.Logger.Info("Sampling Rate Determined: " + str(samplingPointsDet))
                            if samplingRate > SamplingToleranceHigh * samplingPointsDet:
                                break
                        self.assertGreaterEqual(samplingRate, SamplingToleranceLow * result["SamplingRate"])
                        if SamplingRateMaxDet < samplingRate:
                            SamplingRateMaxDet = samplingRate
                        self.PeakCan.Logger.Info("Prescaer - Proved: " + str(prescaler))
                        self.PeakCan.Logger.Info("Acquisition Time - Proved: " + str(acquisitionTime))
                        self.PeakCan.Logger.Info("Oversampling Rate - Proved: " + str(overSampling))
                        self._resetStu()
                        self.PeakCan.Logger.Info("Connect to STH")
                        self.PeakCan.BlueToothConnectPollingName(MY_TOOL_IT_NETWORK_STU1, TestDeviceName)
        SamplingRateMaxDet += 0.5
        SamplingRateMaxDet = int(SamplingRateMaxDet)
        self.PeakCan.Logger.Info("Maximum Single Sampling Rate: " + str(SamplingRateMaxDet))
        print("Maximum Single Sampling Rate: " + str(SamplingRateMaxDet))
        self.assertEqual(SamplingRateMaxDet, SamplingRateSingleMax)

    """
    Combine all possible settings - Double Axis
    """

    def test0510AdcConfigDouble(self):
        SamplingRateMaxDet = 0
        for prescaler in range(2, AdcConfigAllPrescalerMax):
            for acquisitionTime in AdcAcquisitionTimeList:
                for overSampling in AdcOverSamplingRateList:
                    samplingRate = calcSamplingRate(prescaler, acquisitionTime, overSampling)
                    if SamplingRateDoubleMax >= samplingRate and SamplingRateMin <= samplingRate:
                        self.PeakCan.Logger.Info("Sampling Rate: " + str(samplingRate))
                        self.PeakCan.Logger.Info("Prescaer: " + str(prescaler))
                        self.PeakCan.Logger.Info("Acquisition Time: " + str(acquisitionTime))
                        self.PeakCan.Logger.Info("Oversampling Rate: " + str(overSampling))
                        for vRef in AdcReferenceList:
                            result = self.SamplingRate(prescaler, acquisitionTime, overSampling, vRef, b1=1, b2=1, b3=0, runTime=1000, compare=False, compareRate=False, log=False)
                            samplingPointsDet = self.PeakCan.samplingPoints(result["Value1"], result["Value2"], result["Value3"])
                            self.PeakCan.Logger.Info("Sampling Rate Determined: " + str(samplingPointsDet))
                            if samplingRate > SamplingToleranceHigh * samplingPointsDet:
                                break
                        self.assertGreaterEqual(samplingRate, SamplingToleranceLow * result["SamplingRate"])
                        if SamplingRateMaxDet < samplingRate:
                            SamplingRateMaxDet = samplingRate
                        self.PeakCan.Logger.Info("Prescaer - Proved: " + str(prescaler))
                        self.PeakCan.Logger.Info("Acquisition Time - Proved: " + str(acquisitionTime))
                        self.PeakCan.Logger.Info("Oversampling Rate - Proved: " + str(overSampling))
                        self._resetStu()
                        self.PeakCan.Logger.Info("Connect to STH")
                        self.PeakCan.BlueToothConnectPollingName(MY_TOOL_IT_NETWORK_STU1, TestDeviceName)
        SamplingRateMaxDet += 0.5
        SamplingRateMaxDet = int(SamplingRateMaxDet)
        self.PeakCan.Logger.Info("Maximum Double Sampling Rate: " + str(SamplingRateMaxDet))
        print("Maximum Double Sampling Rate: " + str(SamplingRateMaxDet))
        self.assertEqual(SamplingRateMaxDet, SamplingRateDoubleMax)

    """
    Combine all possible settings - Tripple Axis
    """

    def test0511AdcConfigTripple(self):
        SamplingRateMaxDet = 0
        for prescaler in range(2, AdcConfigAllPrescalerMax):
            for acquisitionTime in AdcAcquisitionTimeList:
                for overSampling in AdcOverSamplingRateList:
                    samplingRate = calcSamplingRate(prescaler, acquisitionTime, overSampling)
                    if SamplingRateTrippleMax >= samplingRate and SamplingRateMin <= samplingRate:
                        self.PeakCan.Logger.Info("Sampling Rate: " + str(samplingRate))
                        self.PeakCan.Logger.Info("Prescaer: " + str(prescaler))
                        self.PeakCan.Logger.Info("Acquisition Time: " + str(acquisitionTime))
                        self.PeakCan.Logger.Info("Oversampling Rate: " + str(overSampling))
                        for vRef in AdcReferenceList:
                            result = self.SamplingRate(prescaler, acquisitionTime, overSampling, vRef, b1=1, b2=1, b3=1, runTime=1000, compare=False, compareRate=False, log=False)
                            samplingPointsDet = self.PeakCan.samplingPoints(result["Value1"], result["Value2"], result["Value3"])
                            self.PeakCan.Logger.Info("Sampling Rate Determined: " + str(samplingPointsDet))
                            if samplingRate > SamplingToleranceHigh * samplingPointsDet:
                                break
                        self.assertGreaterEqual(samplingRate, SamplingToleranceLow * result["SamplingRate"])
                        if SamplingRateMaxDet < samplingRate:
                            SamplingRateMaxDet = samplingRate
                        self.PeakCan.Logger.Info("Prescaer - Proved: " + str(prescaler))
                        self.PeakCan.Logger.Info("Acquisition Time - Proved: " + str(acquisitionTime))
                        self.PeakCan.Logger.Info("Oversampling Rate - Proved: " + str(overSampling))
                        self._resetStu()
                        self.PeakCan.Logger.Info("Connect to STH")
                        self.PeakCan.BlueToothConnectPollingName(MY_TOOL_IT_NETWORK_STU1, TestDeviceName)
        self.PeakCan.Logger.Info("Maximum Tripple Sampling Rate: " + str(SamplingRateMaxDet))
        SamplingRateMaxDet += 0.5
        SamplingRateMaxDet = int(SamplingRateMaxDet)
        print("Maximum Tripple Sampling Rate: " + str(SamplingRateMaxDet))
        self.assertEqual(SamplingRateMaxDet, SamplingRateTrippleMax)

    """
    Check Calibration Measurement
    """

    def test0600CalibrationMeasurement(self):
        ret = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionMeasure, CalibMeassurementTypeAcc, 1, AdcReferenceVDD)
        result = messageWordGet(ret[4:])
        self.PeakCan.Logger.Info("Calibration Result AccX: " + str(result))
        self.assertLessEqual(AdcRawMiddleX - AdcRawToleranceX, result)
        self.assertGreaterEqual(AdcRawMiddleX + AdcRawToleranceX, result)
        ret = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionMeasure, CalibMeassurementTypeAcc, 2, AdcReferenceVDD)
        result = messageWordGet(ret[4:])
        self.PeakCan.Logger.Info("Calibration Result AccY: " + str(result))
        self.assertLessEqual(AdcRawMiddleY - AdcRawToleranceY, result)
        self.assertGreaterEqual(AdcRawMiddleY + AdcRawToleranceY, result)
        ret = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionMeasure, CalibMeassurementTypeAcc, 3, AdcReferenceVDD)
        result = messageWordGet(ret[4:])
        self.PeakCan.Logger.Info("Calibration Result AccZ: " + str(result))
        self.assertLessEqual(AdcRawMiddleZ - AdcRawToleranceZ, result)
        self.assertGreaterEqual(AdcRawMiddleZ + AdcRawToleranceZ, result)
        ret = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionMeasure, CalibMeassurementTypeTemp, 1, AdcReferenceVDD)
        result = messageWordGet(ret[4:])
        self.PeakCan.Logger.Info("Calibration Result Temperature: " + str(result))
        self.assertLessEqual(TempInternal3V3Middle - TempInternal3V3Tolerance, result)
        self.assertGreaterEqual(TempInternal3V3Middle + TempInternal3V3Tolerance, result)
        ret = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionMeasure, CalibMeassurementTypeVoltage, 1, AdcReferenceVDD)
        result = messageWordGet(ret[4:])
        self.PeakCan.Logger.Info("Calibration Result Voltage: " + str(result))
        self.assertLessEqual(VoltRawMiddleBat - VoltRawToleranceBat, result)
        self.assertGreaterEqual(VoltRawMiddleBat + VoltRawToleranceBat, result)
        ret = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionMeasure, CalibMeassurementTypeVss, 1, AdcReferenceVDD)
        result = messageWordGet(ret[4:])
        self.PeakCan.Logger.Info("Calibration Result VSS(Ground): " + str(result))
        self.assertLessEqual(0, result)
        self.assertGreaterEqual(VoltRawVssTolerance, result)
        ret = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionMeasure, CalibMeassurementTypeAvdd, 1, AdcReferenceVDD)
        result = messageWordGet(ret[4:])
        self.PeakCan.Logger.Info("Calibration Result AVDD(3V3): " + str(result))
        self.assertLessEqual(2 ^ 16 - 100, result)
        ret = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionMeasure, CalibMeassurementTypeRegulatedInternalPower, 1, AdcReferenceVDD)
        result = messageWordGet(ret[4:])
        self.PeakCan.Logger.Info("Calibration Result Regulated Internal Power(DECOUPLE): " + str(result))
        self.assertLessEqual(VoltRawDecoupleMiddle - VoltRawDecoupleTolerance, result)
        self.assertGreaterEqual(VoltRawDecoupleMiddle + VoltRawDecoupleTolerance, result)
        ret = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionMeasure, CalibMeassurementTypeOpvOutput, 1, AdcReferenceVDD)
        result = messageWordGet(ret[4:])
        self.PeakCan.Logger.Info("Calibration Result OPA2: " + str(result))
        self.assertLessEqual(VoltRawOpa2Middle - VoltRawOpa2Tolerance, result)
        self.assertGreaterEqual(VoltRawOpa2Middle + VoltRawOpa2Tolerance, result)
        ret = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionMeasure, CalibMeassurementTypeOpvOutput, 2, AdcReferenceVDD)
        result = messageWordGet(ret[4:])
        self.PeakCan.Logger.Info("Calibration Result OPA3: " + str(result))
        self.assertLessEqual(VoltRawOpa3Middle - VoltRawOpa3Tolerance, result)
        self.assertGreaterEqual(VoltRawOpa3Middle + VoltRawOpa3Tolerance, result)
        
    """
    Calibration - Check On-Die Temperature
    """

    def test0601CalibrationMeasurementTemperature(self):
        ret = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionMeasure, CalibMeassurementTypeTemp, 1, AdcReference1V25, log=False)
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
        VrefList = AdcReferenceList[1:]
        for VRef in VrefList:
            ret = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionMeasure, CalibMeassurementTypeAcc, 1, VRef)
            result = messageWordGet(ret[4:])
            self.PeakCan.Logger.Info("ADC Value: " + str(result))
            result = result * ((VRef * 50) / (AdcReferenceVDD * 50))
            self.PeakCan.Logger.Info("Recalculated value(result*" + str(VRef * 50) + "/" + str(AdcReferenceVDD * 50) + "): " + str(result))
            self.assertLessEqual(AdcRawMiddleX - AdcRawToleranceX, result * SamplingToleranceHigh)
            self.assertGreaterEqual(AdcRawMiddleX + AdcRawToleranceX, result * SamplingToleranceLow)
            
    """
    Calibration - Check Injection and Ejection
    """

    def test0603CalibrationMeasurementEjectInject(self):
        kX1ack = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionMeasure, CalibMeassurementTypeAcc, 1, AdcReferenceVDD)
        kX1 = messageWordGet(kX1ack[4:])
        kY1ack = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionMeasure, CalibMeassurementTypeAcc, 2, AdcReferenceVDD)
        kY1 = messageWordGet(kY1ack[4:])
        kZ1ack = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionMeasure, CalibMeassurementTypeAcc, 3, AdcReferenceVDD)
        kZ1 = messageWordGet(kZ1ack[4:])
        ackInjectX = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionInject, CalibMeassurementTypeAcc, 1, AdcReferenceVDD)
        stateInjectX = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionInject, CalibMeassurementTypeAcc, 1, AdcReferenceVDD, bSet=False)
        ackInjectY = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionInject, CalibMeassurementTypeAcc, 2, AdcReferenceVDD)
        stateInjectY = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionInject, CalibMeassurementTypeAcc, 2, AdcReferenceVDD, bSet=False)
        ackInjectZ = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionInject, CalibMeassurementTypeAcc, 3, AdcReferenceVDD)
        stateInjectZ = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionInject, CalibMeassurementTypeAcc, 3, AdcReferenceVDD, bSet=False)
        sleep(0.1)
        kX2ack = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionMeasure, CalibMeassurementTypeAcc, 1, AdcReferenceVDD)
        kX2 = messageWordGet(kX2ack[4:])
        kY2ack = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionMeasure, CalibMeassurementTypeAcc, 2, AdcReferenceVDD)
        kY2 = messageWordGet(kY2ack[4:])
        kZ2ack = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionMeasure, CalibMeassurementTypeAcc, 3, AdcReferenceVDD)
        kZ2 = messageWordGet(kZ2ack[4:])
        ackEjectX = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionEject, CalibMeassurementTypeAcc, 1, AdcReferenceVDD)
        stateEjectX = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionInject, CalibMeassurementTypeAcc, 1, AdcReferenceVDD, bSet=False)
        ackEjectY = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionEject, CalibMeassurementTypeAcc, 2, AdcReferenceVDD)
        stateEjectY = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionInject, CalibMeassurementTypeAcc, 2, AdcReferenceVDD, bSet=False)
        ackEjectZ = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionEject, CalibMeassurementTypeAcc, 3, AdcReferenceVDD)
        stateEjectZ = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionInject, CalibMeassurementTypeAcc, 3, AdcReferenceVDD, bSet=False)
        kX3ack = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionMeasure, CalibMeassurementTypeAcc, 1, AdcReferenceVDD)
        kX3 = messageWordGet(kX3ack[4:])
        kY3ack = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionMeasure, CalibMeassurementTypeAcc, 2, AdcReferenceVDD)
        kY3 = messageWordGet(kY3ack[4:])
        kZ3ack = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionMeasure, CalibMeassurementTypeAcc, 3, AdcReferenceVDD)
        kZ3 = messageWordGet(kZ3ack[4:])
        kX4ack = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionMeasure, CalibMeassurementTypeAcc, 1, AdcReferenceVDD)
        kX4 = messageWordGet(kX4ack[4:])
        kY4ack = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionMeasure, CalibMeassurementTypeAcc, 2, AdcReferenceVDD)
        kY4 = messageWordGet(kY4ack[4:])
        kZ4ack = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionMeasure, CalibMeassurementTypeAcc, 3, AdcReferenceVDD)
        kZ4 = messageWordGet(kZ4ack[4:])
        self.PeakCan.Logger.Info("ackInjectX: " + self.PeakCan.payload2Hex(ackInjectX))
        self.PeakCan.Logger.Info("stateInjectX: " + self.PeakCan.payload2Hex(stateInjectX))
        self.PeakCan.Logger.Info("ackInjectY: " + self.PeakCan.payload2Hex(ackInjectY))
        self.PeakCan.Logger.Info("stateInjectY: " + self.PeakCan.payload2Hex(stateInjectY))
        self.PeakCan.Logger.Info("ackInjectZ: " + self.PeakCan.payload2Hex(ackInjectZ))
        self.PeakCan.Logger.Info("stateInjectZ: " + self.PeakCan.payload2Hex(stateInjectZ))
        self.PeakCan.Logger.Info("ackEject: " + self.PeakCan.payload2Hex(ackEjectX))
        self.PeakCan.Logger.Info("stateEject: " + self.PeakCan.payload2Hex(stateEjectX))
        self.PeakCan.Logger.Info("ackEject: " + self.PeakCan.payload2Hex(ackEjectY))
        self.PeakCan.Logger.Info("stateEject: " + self.PeakCan.payload2Hex(stateEjectY))
        self.PeakCan.Logger.Info("ackEject: " + self.PeakCan.payload2Hex(ackEjectZ))
        self.PeakCan.Logger.Info("stateEject: " + self.PeakCan.payload2Hex(stateEjectZ))
        self.PeakCan.Logger.Info("X Ack before Injection: " + self.PeakCan.payload2Hex(kX1ack))
        self.PeakCan.Logger.Info("Y Ack before Injection: " + self.PeakCan.payload2Hex(kY1ack))
        self.PeakCan.Logger.Info("Z Ack before Injection: " + self.PeakCan.payload2Hex(kZ1ack))
        self.PeakCan.Logger.Info("X Ack after Injection: " + self.PeakCan.payload2Hex(kX2ack))
        self.PeakCan.Logger.Info("Y Ack after Injection: " + self.PeakCan.payload2Hex(kY2ack))
        self.PeakCan.Logger.Info("Z Ack after Injection: " + self.PeakCan.payload2Hex(kZ2ack))
        self.PeakCan.Logger.Info("X Ack after Injection: " + self.PeakCan.payload2Hex(kX3ack))
        self.PeakCan.Logger.Info("Y Ack after Injection: " + self.PeakCan.payload2Hex(kY3ack))
        self.PeakCan.Logger.Info("Z Ack after Injection: " + self.PeakCan.payload2Hex(kZ3ack))
        self.PeakCan.Logger.Info("X Ack after Injection: " + self.PeakCan.payload2Hex(kX4ack))
        self.PeakCan.Logger.Info("Y Ack after Injection: " + self.PeakCan.payload2Hex(kY4ack))
        self.PeakCan.Logger.Info("Z Ack after Injection: " + self.PeakCan.payload2Hex(kZ4ack))
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
        k1mVX = (50 * AdcReferenceVDD) * kX1 / AdcMax
        k2mVX = (50 * AdcReferenceVDD) * kX2 / AdcMax
        k1mVY = (50 * AdcReferenceVDD) * kY1 / AdcMax
        k2mVY = (50 * AdcReferenceVDD) * kY2 / AdcMax
        k1mVZ = (50 * AdcReferenceVDD) * kZ1 / AdcMax
        k2mVZ = (50 * AdcReferenceVDD) * kZ2 / AdcMax
        self.PeakCan.Logger.Info("Xk1: " + str(k1mVX) + "mV")
        self.PeakCan.Logger.Info("Yk1: " + str(k1mVY) + "mV")
        self.PeakCan.Logger.Info("Zk1: " + str(k1mVZ) + "mV")
        self.PeakCan.Logger.Info("Xk2: " + str(k2mVX) + "mV")
        self.PeakCan.Logger.Info("Yk2: " + str(k2mVY) + "mV")
        self.PeakCan.Logger.Info("Zk2: " + str(k2mVZ) + "mV")
        self.PeakCan.Logger.Info("ADC Max: " + str(AdcMax))
        self.PeakCan.Logger.Info("Voltage Max: " + str(50 * AdcReferenceVDD) + "mV")
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
        stateStartX = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionInject, CalibMeassurementTypeAcc, 1, AdcReferenceVDD, bSet=False, ErrorAck=True)
        stateStartY = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionInject, CalibMeassurementTypeAcc, 2, AdcReferenceVDD, bSet=False, ErrorAck=True)
        stateStartZ = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionInject, CalibMeassurementTypeAcc, 3, AdcReferenceVDD, bSet=False, ErrorAck=True)
        stateStartTemp = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionInject, CalibMeassurementTypeTemp, 1, AdcReferenceVDD, bSet=False, ErrorAck=True)
        stateStartVoltage = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionInject, CalibMeassurementTypeVoltage, 1, AdcReferenceVDD, bSet=False, ErrorAck=True)        
        stateStartVss = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionInject, CalibMeassurementTypeVss, 1, AdcReferenceVDD, bSet=False, ErrorAck=True)
        stateStartAvdd = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionInject, CalibMeassurementTypeAvdd, 1, AdcReferenceVDD, bSet=False, ErrorAck=True)
        stateStartDecouple = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionInject, CalibMeassurementTypeRegulatedInternalPower, 1, AdcReferenceVDD, bSet=False, ErrorAck=True)
        stateStartOpa1 = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionInject, CalibMeassurementTypeOpvOutput, 1, AdcReferenceVDD, bSet=False, ErrorAck=True)
        stateStartOpa2 = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionInject, CalibMeassurementTypeOpvOutput, 2, AdcReferenceVDD, bSet=False, ErrorAck=True)
        ErrorPayloadAssumed = [0x0, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
        self.PeakCan.Logger.Info("Assumed Error Payload: " + self.PeakCan.payload2Hex(ErrorPayloadAssumed)) 
        self.PeakCan.Logger.Info("State Start AccX: " + self.PeakCan.payload2Hex(stateStartX)) 
        self.PeakCan.Logger.Info("State Start AccY: " + self.PeakCan.payload2Hex(stateStartY)) 
        self.PeakCan.Logger.Info("State Start AccZ: " + self.PeakCan.payload2Hex(stateStartZ)) 
        self.PeakCan.Logger.Info("State Start Temp: " + self.PeakCan.payload2Hex(stateStartTemp)) 
        self.PeakCan.Logger.Info("State Start Voltage: " + self.PeakCan.payload2Hex(stateStartVoltage)) 
        self.PeakCan.Logger.Info("State Start Vss: " + self.PeakCan.payload2Hex(stateStartVss)) 
        self.PeakCan.Logger.Info("State Start Avdd: " + self.PeakCan.payload2Hex(stateStartAvdd)) 
        self.PeakCan.Logger.Info("State Start Decouple: " + self.PeakCan.payload2Hex(stateStartDecouple))        
        self.PeakCan.Logger.Info("State Start Opa1: " + self.PeakCan.payload2Hex(stateStartOpa1))  
        self.PeakCan.Logger.Info("State Start Opa2: " + self.PeakCan.payload2Hex(stateStartOpa2))  
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
        ackInjectX = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionInject, CalibMeassurementTypeAcc, 1, AdcReferenceVDD)
        stateInjectX = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionInject, CalibMeassurementTypeAcc, 1, AdcReferenceVDD, bSet=False)          
        ackReset = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionInject, CalibMeassurementTypeAcc, 1, AdcReferenceVDD, bReset=True)
        stateStartX = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionInject, CalibMeassurementTypeAcc, 1, AdcReferenceVDD, bSet=False, ErrorAck=True)
        stateStartAvdd = self.PeakCan.calibMeasurement(MY_TOOL_IT_NETWORK_STH1, CalibMeassurementActionInject, CalibMeassurementTypeAvdd, 1, AdcReferenceVDD, bSet=False, ErrorAck=True)
        self.PeakCan.Logger.Info("Ack from Inject AccX Command: " + self.PeakCan.payload2Hex(ackInjectX))
        self.PeakCan.Logger.Info("State after Inject AccX Command: " + self.PeakCan.payload2Hex(stateInjectX))  
        self.PeakCan.Logger.Info("Ack from Reset Command: " + self.PeakCan.payload2Hex(ackReset))
        self.PeakCan.Logger.Info("State AccX after Reset Command: " + self.PeakCan.payload2Hex(stateStartX))
        self.PeakCan.Logger.Info("State AVDD after Reset Command: " + self.PeakCan.payload2Hex(stateStartAvdd))
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
        self.test0303GetSingleAccX()
        
    """
    Check Power On and Power Off Counters
    """   

    def test0700StatisticsPowerOnCounterPowerOffCounter(self):
        PowerOnOff1 = self.PeakCan.statisticalData(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STATISTICAL_DATA_POC_POF)
        PowerOn1 = messageWordGet(PowerOnOff1[:4])
        PowerOff1 = messageWordGet(PowerOnOff1[4:])
        self._resetSth()
        self.PeakCan.BlueToothConnectPollingName(MY_TOOL_IT_NETWORK_STU1, TestDeviceName)
        PowerOnOff2 = self.PeakCan.statisticalData(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STATISTICAL_DATA_POC_POF)
        PowerOn2 = messageWordGet(PowerOnOff2[:4])
        PowerOff2 = messageWordGet(PowerOnOff2[4:])
        self.PeakCan.BlueToothDisconnect(MY_TOOL_IT_NETWORK_STU1)
        self.PeakCan.BlueToothConnectPollingName(MY_TOOL_IT_NETWORK_STU1, TestDeviceName)
        PowerOnOff3 = self.PeakCan.statisticalData(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STATISTICAL_DATA_POC_POF)
        PowerOn3 = messageWordGet(PowerOnOff3[:4])
        PowerOff3 = messageWordGet(PowerOnOff3[4:])                
        self._resetStu()        
        self.PeakCan.BlueToothConnectPollingName(MY_TOOL_IT_NETWORK_STU1, TestDeviceName)
        PowerOnOff4 = self.PeakCan.statisticalData(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STATISTICAL_DATA_POC_POF)
        PowerOn4 = messageWordGet(PowerOnOff4[:4])
        PowerOff4 = messageWordGet(PowerOnOff4[4:]) 
        self.PeakCan.Logger.Info("PowerOnOff Payload before STH Reset: " + self.PeakCan.payload2Hex(PowerOnOff1))
        self.PeakCan.Logger.Info("Power On Counter before STH Reset: " + str(PowerOn1))
        self.PeakCan.Logger.Info("Power Off Counter before STH Reset: " + str(PowerOff1))
        self.PeakCan.Logger.Info("PowerOnOff Payload after STH Reset: " + self.PeakCan.payload2Hex(PowerOnOff2))
        self.PeakCan.Logger.Info("Power On Counter after STH Reset: " + str(PowerOn2))
        self.PeakCan.Logger.Info("Power Off Counter after STH Reset: " + str(PowerOff2))
        self.PeakCan.Logger.Info("PowerOnOff Payload after Disconnect/Connect: " + self.PeakCan.payload2Hex(PowerOnOff3))
        self.PeakCan.Logger.Info("Power On Counter after Disconnect/Connect: " + str(PowerOn3))
        self.PeakCan.Logger.Info("Power Off Counter after Disconnect/Connect: " + str(PowerOff3))
        self.PeakCan.Logger.Info("PowerOnOff Payload after STU Reset: " + self.PeakCan.payload2Hex(PowerOnOff4))
        self.PeakCan.Logger.Info("Power On Counter after STU Reset: " + str(PowerOn4))
        self.PeakCan.Logger.Info("Power Off Counter after STU Reset: " + str(PowerOff4))
        self.assertEqual(PowerOn1 + 2, PowerOn2)
        self.assertEqual(PowerOff1, PowerOff2)
        self.assertEqual(PowerOff2 + 1, PowerOff3)
        self.assertEqual(PowerOn2 + 1, PowerOn3)
        self.assertEqual(PowerOff3 + 1, PowerOff4)
        self.assertEqual(PowerOn3 + 1, PowerOn4)

    """
    Check Operating Minutes
    """   

    def test0701StatisticsOperatingMinutes(self):
        OperatingMinutes1 = self.PeakCan.statisticalData(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STATISTICAL_DATA_OPERATING_TIME)    
        MinutesReset1 = messageWordGet(OperatingMinutes1[:4])
        MinutesOveral1 = messageWordGet(OperatingMinutes1[4:])
        sleep(60)
        OperatingMinutes2 = self.PeakCan.statisticalData(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STATISTICAL_DATA_OPERATING_TIME)    
        MinutesReset2 = messageWordGet(OperatingMinutes2[:4])
        MinutesOveral2 = messageWordGet(OperatingMinutes2[4:])
        self.PeakCan.BlueToothDisconnect(MY_TOOL_IT_NETWORK_STU1)
        self.PeakCan.BlueToothConnectPollingName(MY_TOOL_IT_NETWORK_STU1, TestDeviceName)
        OperatingMinutes3 = self.PeakCan.statisticalData(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STATISTICAL_DATA_OPERATING_TIME)    
        MinutesReset3 = messageWordGet(OperatingMinutes3[:4])
        MinutesOveral3 = messageWordGet(OperatingMinutes3[4:])
        self.PeakCan.Logger.Info("Operating Minutes Payload: " + self.PeakCan.payload2Hex(OperatingMinutes1))
        self.PeakCan.Logger.Info("Operating Minutes since Reset: " + str(MinutesReset1))
        self.PeakCan.Logger.Info("Operating Minutes since frist PowerOn: " + str(MinutesOveral1))
        self.PeakCan.Logger.Info("Operating Minutes Payload(+1minute): " + self.PeakCan.payload2Hex(OperatingMinutes2))
        self.PeakCan.Logger.Info("Operating Minutes since Reset(+1minute): " + str(MinutesReset2))
        self.PeakCan.Logger.Info("Operating Minutes since frist PowerOn(+1minute): " + str(MinutesOveral2))    
        self.PeakCan.Logger.Info("Operating Minutes Payload(After Disconnect/Connect): " + self.PeakCan.payload2Hex(OperatingMinutes3))
        self.PeakCan.Logger.Info("Operating Minutes since Reset(After Disconnect/Connect): " + str(MinutesReset3))
        self.PeakCan.Logger.Info("Operating Minutes since frist PowerOn(After Disconnect/Connect): " + str(MinutesOveral3))     
        self.assertEqual(MinutesReset1, 0)                
        self.assertEqual(MinutesReset2, 1)
        self.assertEqual(MinutesReset3, 1)
        self.assertEqual(MinutesOveral1, MinutesOveral2)                
        self.assertEqual(MinutesOveral1 + 1, MinutesOveral3)
        
                
if __name__ == "__main__":
    print(sys.version)
    if not os.path.exists(os.path.dirname(log_location + log_file)):
        os.makedirs(os.path.dirname(log_location + log_file))
    f = open(log_location + log_file, "w")
    loader = unittest.TestLoader()
    start_dir = 'path/to/your/test/files'
    suite = loader.discover(start_dir)
    runner = unittest.TextTestRunner(f)
    unittest.main(suite)
    f.close()
