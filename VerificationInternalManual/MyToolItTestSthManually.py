import unittest
import sys
import os

# Required to add peakcan
sDirName = os.path.dirname('')
sys.path.append(sDirName)
file_path = '../'
sDirName = os.path.dirname(file_path)
sys.path.append(sDirName)
                
import CanFd
from MyToolItNetworkNumbers import MyToolItNetworkNr
from SthLimits import *
import time
from MyToolItSth import TestConfig, SthErrorWord, SleepTime
from MyToolItCommands import *

sLogLocation = '../../Logs/STH/'


class TestSthManually(unittest.TestCase):

    def setUp(self):
        print("TestCase: ", self._testMethodName)
        input('Press Any Key to Continue')
        self.fileName = sLogLocation + self._testMethodName + ".txt"
        self.fileNameError = sLogLocation + "Error_" + self._testMethodName + ".txt"
        self.Can = CanFd.CanFd(CanFd.PCAN_BAUD_1M, self.fileName, self.fileNameError, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], AdcPrescalerReset, AdcAcquisitionTimeReset, AdcAcquisitionOverSamplingRateReset, FreshLog=True)
        self.Can.Logger.Info("TestCase: " + str(self._testMethodName))
        self._resetStu()
        self.Can.Logger.Info("Connect to STH")
        self.Can.bBlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])
        self._resetSth()
        self.Can.Logger.Info("Connect to STH")
        self.Can.bBlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])
        self.bError = False
        self.Can.Logger.Info("STU BlueTooth Address: " + hex(self.Can.BlueToothAddress(MyToolItNetworkNr["STU1"])))
        self.Can.Logger.Info("STH BlueTooth Address: " + hex(self.Can.BlueToothAddress(MyToolItNetworkNr["STH1"])))
        self._statusWords()
        temp = self._SthAdcTemp()
        self.assertGreaterEqual(TempInternalMax, temp)
        self.assertLessEqual(TempInternalMin, temp)
        print("Start")
        self.Can.Logger.Info("Start")

    def tearDown(self):
        if False != self.Can.bError:
            self.bError = True
        self.Can.__exit__()
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
        self.Can.bConnected = False
        return self.Can.cmdReset(MyToolItNetworkNr["STU1"], retries=retries, log=log)

    def _resetSth(self, retries=5, log=True):
        self.Can.bConnected = False
        return self.Can.cmdReset(MyToolItNetworkNr["STH1"], retries=retries, log=log)    

    def _SthAdcTemp(self):
        ret = self.Can.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["Temp"], 1, AdcReference["1V25"], log=False)
        result = float(iMessage2Value(ret[4:]))
        result /= 1000
        self.Can.Logger.Info("Temperature(Chip): " + str(result) + "°C") 
        self.Can.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["None"], CalibMeassurementTypeNr["Temp"], 1, AdcReference["VDD"], log=False, bReset=True)
        return result
    
    def _statusWords(self):
        ErrorWord = SthErrorWord()
        psw0 = self.Can.statusWord0(MyToolItNetworkNr["STH1"])
        self.Can.Logger.Info("STH Status Word: " + hex(psw0))
        psw0 = self.Can.statusWord0(MyToolItNetworkNr["STU1"])
        self.Can.Logger.Info("STU Status Word: " + hex(psw0))
        ErrorWord.asword = self.Can.statusWord1(MyToolItNetworkNr["STH1"])
        if True == ErrorWord.b.bAdcOverRun:
            print("STH bError Word: " + hex(ErrorWord.asword))
            self.bError = True
        self.Can.Logger.Info("STH bError Word: " + hex(ErrorWord.asword))
        ErrorWord.asword = self.Can.statusWord1(MyToolItNetworkNr["STU1"])
        self.Can.Logger.Info("STU bError Word: " + hex(ErrorWord.asword))
 
    def TurnOffLed(self):
        self.Can.Logger.Info("Turn Off LED")
        cmd = self.Can.CanCmd(MyToolItBlock["Configuration"], MyToolItConfiguration["Hmi"], 1, 0)
        message = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [129, 1, 2, 0, 0, 0, 0, 0])
        self.Can.tWriteFrameWaitAckRetries(message)

    def TurnOnLed(self):
        self.Can.Logger.Info("Turn On LED")
        cmd = self.Can.CanCmd(MyToolItBlock["Configuration"], MyToolItConfiguration["Hmi"], 1, 0)
        message = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [129, 1, 1, 0, 0, 0, 0, 0])
        self.Can.tWriteFrameWaitAckRetries(message)        
        
    """
    Test Acknowledgement from STH. Write message and check identifier to be ack (No bError)
    """

    def testManually0001Ack(self):
        activeState = ActiveState()
        cmd = self.Can.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 1, 0)
        msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [0])
        self.Can.Logger.Info("Write Message")
        self.Can.WriteFrame(msg)
        self.Can.Logger.Info("Wait 200ms")
        time.sleep(0.2)
        cmd = self.Can.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 0, 0)
        msgAckExpected = self.Can.CanMessage20(cmd, MyToolItNetworkNr["STH1"], MyToolItNetworkNr["SPU1"], [0])
        activeState.asbyte = self.Can.getReadMessage(-1).DATA[0]
        self.Can.Logger.Info("Send ID: " + hex(msg.ID) + "; Expected ID: " + hex(msgAckExpected.ID) + "; Received ID: " + hex(self.Can.getReadMessage(-1).ID))
        self.Can.Logger.Info("Send Data: " + hex(0) + "; Received Data: " + hex(activeState.asbyte))
        self.assertEqual(hex(msgAckExpected.ID), hex(self.Can.getReadMessage(-1).ID))
        self.assertEqual(activeState.b.bSetState, 0)
        self.assertEqual(activeState.b.bReserved, 0)
        self.assertEqual(activeState.b.u2NodeState, Node["Application"])
        self.assertEqual(activeState.b.bReserved1, 0)
        self.assertEqual(activeState.b.u3NetworkState, NetworkState["Operating"])
        
    """
    Test Standby Command - Run this manually! Only (power on) reset gets out of that (or replay firmware)
    """

    def testManually0010Standby(self):
        failTry = ActiveState()
        receivedData = ActiveState()
        receivedDataFailTry = ActiveState()
        sendData = ActiveState()
        sendData.asbyte = 0
        sendData.b.bSetState = 1
        sendData.b.u2NodeState = 2
        sendData.b.u3NetworkState = 2
        failTry.asbyte = 0
        failTry.b.bSetState = 1
        failTry.b.u2NodeState = 2
        failTry.b.u3NetworkState = 6
        cmd = self.Can.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 1, 0)
        message = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [sendData.asbyte])
        self.Can.Logger.Info("Send Shut Down Command")
        receivedData.asbyte = self.Can.tWriteFrameWaitAckRetries(message)["Payload"][0]
        self.Can.Logger.Info("Send try should fail")
        message = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [failTry.asbyte])
        self.Can.WriteFrame(message)
        self.Can.Logger.Info("Wait 200ms")
        time.sleep(0.2)
        receivedDataFailTry.asbyte = self.Can.getReadMessage(-1).DATA[0]
        self.Can.Logger.Info("Fail Try Payload Byte for Active State Command(send): " + str(sendData.asbyte))
        self.Can.Logger.Info("Fail Try Payload Byte for Active State Command(Received): " + str(receivedData.asbyte))
        self.Can.Logger.Info("Fail Try Payload Byte for Active State Command(send with fail): " + str(failTry.asbyte))
        self.Can.Logger.Info("Fail Try Payload Byte for Active State Command(last received): " + str(receivedDataFailTry.asbyte))
        self.assertEqual(receivedData.asbyte, sendData.asbyte)
        self.assertEqual(receivedData.asbyte, receivedDataFailTry.asbyte)
        print("Power off device for 1 minute(power consumpiton of the target is actually REALLY low)")
        input('Press any key to continue')
        
    """
    Power Consumption - Energy Save Modes
    """   

    def testManually0011PowerConsumptionEnergySaveMode(self):
        self.Can.BlueToothEnergyModeNr(SleepTime["Min"], SleepTime["AdvertisementReset1"], 1)
        self.Can.BlueToothEnergyModeNr(SleepTime["Reset2"], SleepTime["AdvertisementReset1"], 2)
        self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])        
        print("Start Simplicty Energy Profiler and connect to target (STH)")
        print("Waiting" + str(SleepTime["Min"]) + "ms")
        time.sleep(SleepTime["Min"] / 1000)
        print("Measure Power Consumption for advertisement time " + str(SleepTime["AdvertisementReset1"]) + "ms")
        input('Press any key to continue')
        self.Can.bBlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])
        self.Can.BlueToothEnergyModeNr(SleepTime["Min"], SleepTime["AdvertisementReset2"], 1)
        self.Can.BlueToothEnergyModeNr(SleepTime["Reset2"], SleepTime["AdvertisementReset2"], 2)
        self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])
        print("Waiting" + str(SleepTime["Min"]) + "ms")
        time.sleep(SleepTime["Min"] / 1000)
        print("Measure Power Consumption for advertisement time " + str(SleepTime["AdvertisementReset2"]) + "ms")
        input('Press any key to continue')
        self.Can.bBlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])
        self.Can.BlueToothEnergyModeNr(SleepTime["Min"], SleepTime["AdvertisementMax"], 1)
        self.Can.BlueToothEnergyModeNr(SleepTime["Reset2"], SleepTime["AdvertisementMax"], 2)
        self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])
        print("Waiting" + str(SleepTime["Min"]) + "ms")
        time.sleep(SleepTime["Min"] / 1000)
        print("Measure Power Consumption for advertisement time " + str(SleepTime["AdvertisementMax"]) + "ms")
        input('Press any key to continue')
        self.Can.bBlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])
        self.Can.BlueToothEnergyModeNr(SleepTime["Reset1"], SleepTime["AdvertisementReset1"], 1)
        self.Can.BlueToothEnergyModeNr(SleepTime["Reset2"], SleepTime["AdvertisementReset2"], 2)  

    """
    Power Consumption - Energy Save Modes
    """   

    def testManually0012PowerConsumptionStandby(self):
        self.Can.Standby(MyToolItNetworkNr["STH1"])
        print("Start Simplicty Energy Profiler and connect to target (STH)")    
        print("Measure Power Consumption for standby.") 
        input('Press any key to continue')
        print("Power off device for 1 minute(power consumpiton of the target is actually REALLY low)")
        input('Press any key to continue')
        
    """
    Power Consumption - Connected
    """   

    def testManually0013PowerConsumptionConnected(self):
        self.Can.BlueToothEnergyModeNr(~0, SleepTime["AdvertisementReset1"], 1)
        self.Can.BlueToothEnergyModeNr(~0, SleepTime["AdvertisementReset1"], 2)
        print("Start Simplicty Energy Profiler and connect to target (STH)")   
        input('Press any key to continue') 
        print("Measure Power Consumption for connected.") 
        input('Press any key to continue')
        self.Can.BlueToothEnergyModeNr(SleepTime["Reset1"], SleepTime["AdvertisementReset1"], 1)
        self.Can.BlueToothEnergyModeNr(SleepTime["Reset2"], SleepTime["AdvertisementReset2"], 2)  
 
    """
    Power Consumption - Measuring at reset conditions
    """   

    def testManually0014PowerConsumptionMeasuring(self):
        print("Start Simplicty Energy Profiler and connect to target (STH)") 
        input('Press any key to continue')
        self.Can.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0)
        print("Measure Power Consumption for meassuring.") 
        input('Press any key to continue')
        self.Can.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])     
        
    """
    Power Consumption - Measuring at reset conditions - LED turned off
    """   

    def testManually0015PowerConsumptionMeasuringLedOff(self):
        self.TurnOffLed()
        print("Start Simplicty Energy Profiler and connect to target (STH)") 
        input('Press any key to continue')
        self.Can.streamingStart(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[3], 1, 0, 0)
        print("Measure Power Consumption for meassuring with turned off LED.") 
        input('Press any key to continue')
        self.Can.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])  
                  
    """
    Under Voltage Counter
    """   

    def testManually0700UnderVoltageCounter(self):
        UnderVoltage1 = self.Can.statisticalData(MyToolItNetworkNr["STH1"], MyToolItStatData["Uvc"], printLog=True)    
        UnderVoltagePowerOnFirst1 = iMessage2Value(UnderVoltage1[:4])
        self.Can.Logger.Info("Under Voltage Counter since first Power On: " + payload2Hex(UnderVoltage1))
        self.Can.Logger.Info("Under Voltage Counter since first Power On: " + str(UnderVoltagePowerOnFirst1))
        input('Power Off Device and wait 1s, power on again and then press Any Key to Continue')
        self.Can.bBlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"])
        UnderVoltage2 = self.Can.statisticalData(MyToolItNetworkNr["STH1"], MyToolItStatData["Uvc"], printLog=True)    
        UnderVoltagePowerOnFirst2 = iMessage2Value(UnderVoltage2[:4])
        self.Can.Logger.Info("Under Voltage Counter since first Power On: " + payload2Hex(UnderVoltage2))
        self.Can.Logger.Info("Under Voltage Counter since first Power On: " + str(UnderVoltagePowerOnFirst2))
        self.assertEqual(0xFFFFFFFF & (UnderVoltagePowerOnFirst1 + 1), UnderVoltagePowerOnFirst2)
        
        
if __name__ == "__main__":
    print(sys.version)
    sLogLocation = sys.argv[1]
    sLogFile = sys.argv[2]
    if '/' != sLogLocation[-1]:
        sLogLocation += '/'
    sLogFileLocation = sLogLocation + sLogFile
    sDirName = os.path.dirname(sLogFileLocation)
    sys.path.append(sDirName)

    print("Log Files will be saved at: " + str(sLogFileLocation))
    if not os.path.exists(sDirName):
        os.makedirs(sDirName)
    with open(sLogFileLocation, "w") as f:
        print(f)     
        runner = unittest.TextTestRunner(f)
        unittest.main(argv=['first-arg-is-ignored'], testRunner=runner)  
