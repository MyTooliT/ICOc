import unittest
from PeakCanFd import *
from MyToolItNetworkNumbers import *
from SthLimits import *

log_location='../Logs/STH/'

class TestSthManually(unittest.TestCase):

    def setUp(self):
        print("TestCase: ", self._testMethodName)
        input('Press Any Key to Continue')
        self.fileName = log_location + self._testMethodName + ".txt"
        self.fileNameError = log_location + "Error_" + self._testMethodName + ".txt"
        self.PeakCan = PeakCanFd(PCAN_BAUD_1M, self.fileName, self.fileNameError, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1)
        self.PeakCan.Logger.Info("TestCase: " + str(self._testMethodName))
        self._resetStu()
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
        self.PeakCan.Logger.Info("Start")

    def tearDown(self):
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
    Test Acknowledgement from STH. Write message and check identifier to be ack (No Error)
    """

    def testManually0001Ack(self):
        expectedData = ActiveState()
        expectedData.asbyte = 0
        expectedData.b.u2NodeState = 0
        expectedData.b.u3NetworkState = 6
        self.PeakCan.cmdSend(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, [expectedData.asbyte])
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 1, 0)

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
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 1, 0)
        message = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [sendData.asbyte])
        self.PeakCan.Logger.Info("Send Shut Down Command")
        receivedData.asbyte = self.PeakCan.WriteFrameWaitAckRetries(message)["Payload"][0]
        self.PeakCan.Logger.Info("Send try should fail")
        message = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [failTry.asbyte])
        self.PeakCan.WriteFrame(message)
        self.PeakCan.Logger.Info("Wait 200ms")
        sleep(0.2)
        receivedDataFailTry.asbyte = self.PeakCan.getReadMessage(-1).DATA[0]
        self.PeakCan.Logger.Info("Fail Try Payload Byte for Active State Command(send): " + str(sendData.asbyte))
        self.PeakCan.Logger.Info("Fail Try Payload Byte for Active State Command(Received): " + str(receivedData.asbyte))
        self.PeakCan.Logger.Info("Fail Try Payload Byte for Active State Command(send with fail): " + str(failTry.asbyte))
        self.PeakCan.Logger.Info("Fail Try Payload Byte for Active State Command(last received): " + str(receivedDataFailTry.asbyte))
        self.assertEqual(receivedData.asbyte, sendData.asbyte)
        self.assertEqual(receivedData.asbyte, receivedDataFailTry.asbyte)
        print("Power off device and wait 1 minute(power consumpiton of the target is actually REALLY low)")
        input('Press any key to continue')
        
    """
    Power Consumption - Energy Save Modes
    """   

    def testManually0012PowerConsumptionEnergySaveMode(self):
        self.PeakCan.BlueToothEnergyModeNr(SleepTimeMin, Sleep1AdvertisementTimeReset, 1)
        self.PeakCan.BlueToothEnergyModeNr(Sleep2TimeReset, Sleep1AdvertisementTimeReset, 2)
        self.PeakCan.BlueToothDisconnect(MY_TOOL_IT_NETWORK_STU1)        
        print("Start Simplicty Energy Profiler and connect to target (STH)")
        print("Waiting" + str(SleepTimeMin) + "ms")
        sleep(SleepTimeMin/1000)
        print("Measure Power Consumption for advertisement time " + str(Sleep1AdvertisementTimeReset) + "ms")
        input('Press any key to continue')
        self.PeakCan.BlueToothConnectPollingName(MY_TOOL_IT_NETWORK_STU1, TestDeviceName)
        self.PeakCan.BlueToothEnergyModeNr(SleepTimeMin, Sleep2AdvertisementTimeReset, 1)
        self.PeakCan.BlueToothEnergyModeNr(Sleep2TimeReset, Sleep2AdvertisementTimeReset, 2)
        self.PeakCan.BlueToothDisconnect(MY_TOOL_IT_NETWORK_STU1)
        print("Waiting" + str(SleepTimeMin) + "ms")
        sleep(SleepTimeMin/1000)
        print("Measure Power Consumption for advertisement time " + str(Sleep2AdvertisementTimeReset) + "ms")
        input('Press any key to continue')
        self.PeakCan.BlueToothConnectPollingName(MY_TOOL_IT_NETWORK_STU1, TestDeviceName)
        self.PeakCan.BlueToothEnergyModeNr(SleepTimeMin, ConnectionTimeNormalMaxMs, 1)
        self.PeakCan.BlueToothEnergyModeNr(Sleep2TimeReset, ConnectionTimeNormalMaxMs, 2)
        self.PeakCan.BlueToothDisconnect(MY_TOOL_IT_NETWORK_STU1)
        print("Waiting" + str(SleepTimeMin) + "ms")
        sleep(SleepTimeMin/1000)
        print("Measure Power Consumption for advertisement time " + str(ConnectionTimeNormalMaxMs) + "ms")
        input('Press any key to continue')
        self.PeakCan.BlueToothConnectPollingName(MY_TOOL_IT_NETWORK_STU1, TestDeviceName)
        self.PeakCan.BlueToothEnergyModeNr(Sleep1TimeReset, Sleep1AdvertisementTimeReset, 1)
        self.PeakCan.BlueToothEnergyModeNr(Sleep2TimeReset, Sleep2AdvertisementTimeReset, 2)  


    """
    Power Consumption - Energy Save Most
    """   

    def testManually0013PowerConsumptionEnergySaveMode(self):
        self.PeakCan.BlueToothEnergyModeNr(SleepTimeMin, SleepAdvertisementTimeMax, 1)
        self.PeakCan.BlueToothEnergyModeNr(Sleep2TimeReset, SleepAdvertisementTimeMax, 2)
        self.PeakCan.BlueToothDisconnect(MY_TOOL_IT_NETWORK_STU1)        
        print("Start Simplicty Energy Profiler and connect to target (STH)")
        print("Waiting" + str(SleepTimeMin) + "ms")
        sleep(SleepTimeMin/1000)
        print("Measure Power Consumption for advertisement time " + str(Sleep1AdvertisementTimeReset) + "ms")
        input('Press any key to continue')
        self.PeakCan.BlueToothConnectPollingName(MY_TOOL_IT_NETWORK_STU1, TestDeviceName)
        self.PeakCan.BlueToothEnergyModeNr(Sleep1TimeReset, Sleep1AdvertisementTimeReset, 1)
        self.PeakCan.BlueToothEnergyModeNr(Sleep2TimeReset, Sleep2AdvertisementTimeReset, 2)

    """
    Power Consumption - Energy Save Modes
    """   

    def testManually0014PowerConsumptionStandby(self):
        self.PeakCan.Standby(MY_TOOL_IT_NETWORK_STH1)
        print("Start Simplicty Energy Profiler and connect to target (STH)")    
        print("Measure Power Consumption for standby.") 
        input('Press any key to continue')
        print("Power off device and wait 1 minute(power consumpiton of the target is actually REALLY low)")
        input('Press any key to continue')
        
        
    """
    Power Consumption - Connected
    """   
    def testManually0015PowerConsumptionConnected(self):
        self.PeakCan.BlueToothEnergyModeNr(~0, Sleep1AdvertisementTimeReset, 1)
        self.PeakCan.BlueToothEnergyModeNr(~0, Sleep1AdvertisementTimeReset, 2)
        print("Start Simplicty Energy Profiler and connect to target (STH)")   
        input('Press any key to continue') 
        print("Measure Power Consumption for standby.") 
        input('Press any key to continue')
        self.PeakCan.BlueToothEnergyModeNr(Sleep1TimeReset, Sleep1AdvertisementTimeReset, 1)
        self.PeakCan.BlueToothEnergyModeNr(Sleep2TimeReset, Sleep2AdvertisementTimeReset, 2)  
 
    """
    Power Consumption - Measuring at reset conditions
    """   
    def testManually0016PowerConsumptionMeasuring(self):
        print("Start Simplicty Energy Profiler and connect to target (STH)") 
        input('Press any key to continue')
        self.PeakCan.streamingStart(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 1, 0, 0)
        print("Measure Power Consumption for standby.") 
        input('Press any key to continue')
        self.PeakCan.streamingStop(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION)     
        
    """
    Power Consumption - Measuring at reset conditions - LED turned off
    """   
    def testManually0017PowerConsumptionMeasuringLedOff(self):
        self.TurnOffLed()
        print("Start Simplicty Energy Profiler and connect to target (STH)") 
        input('Press any key to continue')
        self.PeakCan.streamingStart(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION, DataSets3, 1, 0, 0)
        print("Measure Power Consumption for standby.") 
        input('Press any key to continue')
        self.PeakCan.streamingStop(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STREAMING_ACCELERATION)  
                  
    """
    Under Voltage Counter
    """   

    def testManually0700UnderVoltageCounter(self):
        UnderVoltage1 = self.PeakCan.statisticalData(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STATISTICAL_DATA_UVC, printLog=True)    
        UnderVoltagePowerOnFirst1 = messageWordGet(UnderVoltage1[:4])
        self.PeakCan.Logger.Info("Under Voltage Counter since first Power On: " + self.PeakCan.payload2Hex(UnderVoltage1))
        self.PeakCan.Logger.Info("Under Voltage Counter since first Power On: " + str(UnderVoltagePowerOnFirst1))
        input('Power Off Device an press Any Key to Continue')
        self.PeakCan.BlueToothConnectPollingName(MY_TOOL_IT_NETWORK_STU1, TestDeviceName)
        UnderVoltage2 = self.PeakCan.statisticalData(MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_STATISTICAL_DATA_UVC, printLog=True)    
        UnderVoltagePowerOnFirst2 = messageWordGet(UnderVoltage2[:4])
        self.PeakCan.Logger.Info("Under Voltage Counter since first Power On: " + self.PeakCan.payload2Hex(UnderVoltage2))
        self.PeakCan.Logger.Info("Under Voltage Counter since first Power On: " + str(UnderVoltagePowerOnFirst2))
        self.assertEqual(UnderVoltagePowerOnFirst1+1, UnderVoltagePowerOnFirst2)