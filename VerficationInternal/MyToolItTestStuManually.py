import unittest
import sys
import os

#Required to add peakcan
file_path = '../'
dir_name = os.path.dirname(file_path)
sys.path.append(dir_name)
                
import PeakCanFd
from MyToolItNetworkNumbers import MyToolItNetworkNr
import time
from MyToolItStu import StuErrorWord
from MyToolItCommands import *

log_location='../../Logs/STH/'

class TestSthManually(unittest.TestCase):

    def setUp(self):
        print("TestCase: ", self._testMethodName)
        input('Press Any Key to Continue')
        self.fileName = log_location + self._testMethodName + ".txt"
        self.fileNameError = log_location + "Error_" + self._testMethodName + ".txt"
        self.PeakCan = PeakCanFd.PeakCanFd(PeakCanFd.PCAN_BAUD_1M, self.fileName, self.fileNameError, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"])
        self.PeakCan.Logger.Info("TestCase: " + str(self._testMethodName))
        self._resetStu()
        self.Error = False
        self.PeakCan.Logger.Info("STU BlueTooth Address: " + hex(self.PeakCan.BlueToothAddress(MyToolItNetworkNr["STU1"])))
        self.PeakCan.Logger.Info("STH BlueTooth Address: " + hex(self.PeakCan.BlueToothAddress(MyToolItNetworkNr["STH1"])))
        self._statusWords()
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
        return self.PeakCan.cmdReset(MyToolItNetworkNr["STU1"], retries=retries, log=log)
    
    def _statusWords(self):
        ErrorWord = StuErrorWord()
        psw0 = self.PeakCan.statusWord0(MyToolItNetworkNr["STH1"])
        self.PeakCan.Logger.Info("STH Status Word: " + hex(psw0))
        psw0 = self.PeakCan.statusWord0(MyToolItNetworkNr["STU1"])
        self.PeakCan.Logger.Info("STU Status Word: " + hex(psw0))
        ErrorWord.asword = self.PeakCan.statusWord1(MyToolItNetworkNr["STH1"])
        if True == ErrorWord.b.bAdcOverRun:
            print("STH Error Word: " + hex(ErrorWord.asword))
            self.Error = True
        self.PeakCan.Logger.Info("STH Error Word: " + hex(ErrorWord.asword))
        ErrorWord.asword = self.PeakCan.statusWord1(MyToolItNetworkNr["STU1"])
        if True == ErrorWord.b.bAdcOverRun:
            print("STU Error Word: " + hex(ErrorWord.asword))
            self.Error = True
        self.PeakCan.Logger.Info("STU Error Word: " + hex(ErrorWord.asword))
 
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
    Test Acknowledgement from STH. Write message and check identifier to be ack (No Error)
    """

    def testManually0001Ack(self):
        activeState = ActiveState()
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 1, 0)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [0])
        self.PeakCan.Logger.Info("Write Message")
        self.PeakCan.WriteFrame(msg)
        self.PeakCan.Logger.Info("Wait 200ms")
        time.sleep(0.2)
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 0, 0)
        msgAckExpected = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["STH1"], MyToolItNetworkNr["SPU1"], [0])
        activeState.asbyte = self.PeakCan.getReadMessage(-1).DATA[0]
        self.PeakCan.Logger.Info("Send ID: " + hex(msg.ID) + "; Expected ID: " + hex(msgAckExpected.ID) + "; Received ID: " + hex(self.PeakCan.getReadMessage(-1).ID))
        self.PeakCan.Logger.Info("Send Data: " + hex(0) + "; Received Data: " + hex(activeState.asbyte))
        self.assertEqual(hex(msgAckExpected.ID), hex(self.PeakCan.getReadMessage(-1).ID))
        self.assertEqual(activeState.b.bSetState, 0)
        self.assertEqual(activeState.b.bReserved, 0)
        self.assertEqual(activeState.b.u2NodeState, Node["Application"])
        self.assertEqual(activeState.b.bReserved1, 0)
        self.assertEqual(activeState.b.u3NetworkState, NetworkState["Operating"])
        
                          
    """
    Under Voltage Counter
    """   

    def testManually0700UnderVoltageCounter(self):
        PowerOnOff1 = self.PeakCan.statisticalData(MyToolItNetworkNr["STU1"], MyToolItStatData["PocPof"])
        PowerOn1 = messageWordGet(PowerOnOff1[:4])
        PowerOff1 = messageWordGet(PowerOnOff1[4:])
        self.PeakCan.Logger.Info("Power On Counter since first Power On: " + payload2Hex(PowerOn1))
        self.PeakCan.Logger.Info("Power On Counter since first Power On: " + str(PowerOff1))
        input('Power Off Device and wait 1s, power on again and then press Any Key to Continue')
        PowerOnOff2 = self.PeakCan.statisticalData(MyToolItNetworkNr["STU1"], MyToolItStatData["PocPof"])
        PowerOn2 = messageWordGet(PowerOnOff2[:4])
        PowerOff2 = messageWordGet(PowerOnOff2[4:])
        self.PeakCan.Logger.Info("Power On Counter since first Power On: " + payload2Hex(PowerOn2))
        self.PeakCan.Logger.Info("Power On Counter since first Power On: " + str(PowerOff2))
        self.assertEqual(PowerOn1+1, PowerOn2)
        self.assertEqual(PowerOff1+1, PowerOff2)
        
        
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