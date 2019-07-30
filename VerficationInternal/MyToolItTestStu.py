import unittest
import sys
import os
# Required to add peakcan
file_path = '../'
dir_name = os.path.dirname(file_path)
sys.path.append(dir_name)

# from PCANBasic import *   
import PeakCanFd
from MyToolItNetworkNumbers import MyToolItNetworkNr
from MyToolItCommands import *
from random import randint
import time
from MyToolItStu import Version, StuErrorWord
log_file = 'TestStu.txt'
log_location = '../../Logs/STU/'
        

class TestStu(unittest.TestCase):

    def setUp(self):
        print("TestCase: ", self._testMethodName)
        self.fileName = log_location + self._testMethodName + ".txt"
        self.fileNameError = log_location + "Error_" + self._testMethodName + ".txt"
        self.PeakCan = PeakCanFd.PeakCanFd(PeakCanFd.PCAN_BAUD_1M, self.fileName, self.fileNameError, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"])
        self.PeakCan.Logger.Info("TestCase: " + str(self._testMethodName))
        self.PeakCan.CanTimeStampStart(self._resetStu()["CanTime"])
        self.Error = False
        self.PeakCan.Logger.Info("STU BlueTooth Address: " + hex(self.PeakCan.BlueToothAddress(MyToolItNetworkNr["STU1"])))
        self._statusWords()
        self._StuWDog()
        while False != self.BlueToothDisconnect():
            pass
        print("Start")
        self.PeakCan.Logger.Info("_______________________________________________________________________________________________________________")
        self.PeakCan.Logger.Info("Start")

    def tearDown(self): 
        self.PeakCan.Logger.Info("Fin")
        self.PeakCan.Logger.Info("_______________________________________________________________________________________________________________")
        if False == self.PeakCan.Error:
            self._statusWords()
            self.PeakCan.Logger.Info("Test Time End Time Stamp")
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
        return False       
    
    def _resetStu(self, retries=5, log=True):
        return self.PeakCan.cmdReset(MyToolItNetworkNr["STU1"], retries=retries, log=log)

    def _StuWDog(self):
        WdogCounter = messageWordGet(self.PeakCan.statisticalData(MyToolItNetworkNr["STU1"], MyToolItStatData["Wdog"])[:4])
        self.PeakCan.Logger.Info("WatchDog Counter: " + str(WdogCounter))
        return WdogCounter 
        
    def _statusWords(self):
        ErrorWord = StuErrorWord()
        psw0 = self.PeakCan.statusWord0(MyToolItNetworkNr["STU1"])
        self.PeakCan.Logger.Info("STU Status Word: " + hex(psw0))
        ErrorWord.asword = self.PeakCan.statusWord1(MyToolItNetworkNr["STU1"])
        self.PeakCan.Logger.Info("STU Error Word: " + hex(ErrorWord.asword))    
    
    """
    Test Acknowledgement from STU. Write message and check identifier to be ack (No Error)
    """    

    def test0001Ack(self):
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 1, 0)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [0])
        self.PeakCan.Logger.Info("Write Message")
        self.PeakCan.WriteFrame(msg)
        self.PeakCan.Logger.Info("Wait 200ms")
        time.sleep(0.25)
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 0, 0)
        msgAckExpected = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["STU1"], MyToolItNetworkNr["SPU1"], [0])
        self.PeakCan.Logger.Info("Send ID: " + hex(msg.ID) + "; Expected ID: " + hex(msgAckExpected.ID) + "; Received ID: " + hex(self.PeakCan.getReadMessage(-1).ID))
        expectedData = ActiveState()
        expectedData.asbyte = 0
        expectedData.b.u2NodeState = Node["Application"]
        expectedData.b.u3NetworkState = NetworkState["Operating"]
        self.PeakCan.Logger.Info("Send Data: " + hex(0) + "; Expected Data: " + hex(expectedData.asbyte) + "; Received Data: " + hex(self.PeakCan.getReadMessage(-1).DATA[0]))
        self.assertEqual(hex(msgAckExpected.ID), hex(self.PeakCan.getReadMessage(-1).ID))
        self.assertEqual(expectedData.asbyte, self.PeakCan.getReadMessage(-1).DATA[0])
        
    """ Send Mutliple Frames without waiting for an ACK, do ACK after 100 times send flooding to check functionallity"""

    def test0002MultiSend(self):
        self.PeakCan.Logger.Info("Send command 100 times, check number of write/reads and do ack test at the end; do that for 100 times")
        for i in range(1, 101):
            self.PeakCan.Logger.Info("Received Index: " + str(self.PeakCan.GetReadArrayIndex()))
            self.PeakCan.Logger.Info("Run: " + str(i))
            for _j in range(1, 101):
                if(1 == randint(0, 1)):
                    cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 1, 0)
                    message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [0])                    
                else:
                    cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["Bluetooth"], 1, 0)
                    message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [SystemCommandBlueTooth["DeviceCheckConnected"], 0, 0, 0, 0, 0, 0, 0])
                self.PeakCan.WriteFrame(message)
            time.sleep(0.5) 
            self.PeakCan.WriteFrameWaitAckRetries(message, retries=0)
    
    """ Send Mutliple Frames with waiting for an ACK: Send->Ack->Send->Ack"""

    def test0003MultiSendAck(self):
        self.PeakCan.Logger.Info("Send and get ACK for 1000 times AND do it with two messages randomly ")
        for i in range(1, 1001):
            self.PeakCan.Logger.Info("Received Index: " + str(self.PeakCan.GetReadArrayIndex()))
            self.PeakCan.Logger.Info("Run: " + str(i))
            if(1 == randint(0, 1)):
                cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 1, 0)
                msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [0])
            else:
                cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["Bluetooth"], 1, 0)
                msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [SystemCommandBlueTooth["DeviceCheckConnected"], 0, 0, 0, 0, 0, 0, 0])
            self.assertNotEqual("Error", self.PeakCan.WriteFrameWaitAck(msg))
        self.test0001Ack()  # Test that it still works
        
    """ Send Mutliple Frames with waiting for an ACK: Send->Ack->Send->Ack, this also do a retry, tests the test framework - Multiple Messages"""

    def test0004MultiSendMultiAckRetries(self):
        self.PeakCan.Logger.Info("Send and get ACK for 1000 times AND do it with two messages randomly ")
        for i in range(1, 1001):
            self.PeakCan.Logger.Info("Received Index: " + str(self.PeakCan.GetReadArrayIndex()))
            self.PeakCan.Logger.Info("Run: " + str(i))
            if(1 == randint(0, 1)):
                cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 1, 0)
                msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [0])
            else:
                cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["Bluetooth"], 1, 0)
                msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [SystemCommandBlueTooth["DeviceCheckConnected"], 0, 0, 0, 0, 0, 0, 0])
            self.assertNotEqual("Error", self.PeakCan.WriteFrameWaitAckRetries(msg, retries=3))
        self.test0001Ack()  # Test that it still works
        
        """ Send Mutliple Frames with waiting for an ACK: Send->Ack->Send->Ack, this also do a retry, tests the test framework - Single Message"""

    def test0005MultiSendSingleAckRetries(self):
        self.PeakCan.Logger.Info("Send and get ACK for 1000 times AND do it with two messages randomly ")
        for _i in range(1, 10001):
            self.PeakCan.cmdSend(MyToolItNetworkNr["STU1"], MyToolItBlock["System"], MyToolItSystem["Bluetooth"], [SystemCommandBlueTooth["DeviceCheckConnected"], 0, 0, 0, 0, 0, 0, 0], retries=0)
        self.test0001Ack()  # Test that it still works
        
    """
    Send addressing same sender and receiver
    """ 

    def test0006SenderReceiver(self):
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 1, 0)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["STU1"], MyToolItNetworkNr["STU1"], [0])
        self.assertEqual("Error", self.PeakCan.WriteFrameWaitAck(msg)[0])
        # Test that it still works
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [0])
        self.PeakCan.WriteFrameWaitAckRetries(msg, retries=0)
        
    """
    "Christmas Tree" packages
    """ 

    def test0007ChristmasTree(self):
        self.PeakCan.Logger.Info("Error Request Frame from STU1 to STU1")
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 1, 1)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["STU1"], MyToolItNetworkNr["STU1"], [0])
        self.assertEqual("Error", self.PeakCan.WriteFrameWaitAck(msg)[0])
        self.PeakCan.Logger.Info("Error Request Frame from SPU1 to STU1")
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 1, 1)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [0])
        self.assertEqual("Error", self.PeakCan.WriteFrameWaitAck(msg)[0])
        self.PeakCan.Logger.Info("Error Ack Frame from STU1 to STU1")
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 0, 1)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["STU1"], MyToolItNetworkNr["STU1"], [0])
        self.assertEqual("Error", self.PeakCan.WriteFrameWaitAck(msg)[0])
        self.PeakCan.Logger.Info("Error Ack Frame from SPU1 to STU1")
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 0, 1)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [0])
        self.assertEqual("Error", self.PeakCan.WriteFrameWaitAck(msg)[0])
        self.PeakCan.Logger.Info("Ack Frame from STU1 to STU1")
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 0, 0)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["STU1"], MyToolItNetworkNr["STU1"], [0])
        self.assertEqual("Error", self.PeakCan.WriteFrameWaitAck(msg)[0])
        self.PeakCan.Logger.Info("Ack Frame from SPU1 to STU1")
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 0, 0)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [0])
        self.assertEqual("Error", self.PeakCan.WriteFrameWaitAck(msg)[0])
        
        # Test that it still works
        self.PeakCan.Logger.Info("Normal Request to STU1")
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 1, 0)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [0])
        self.PeakCan.WriteFrameWaitAckRetries(msg, retries=0)
        
    """
    Connect and disconnect device, check device number after each connect/disconnect to check correctness
    """

    def test0101BlueToothConncectDeviceNr(self): 
        self.PeakCan.Logger.Info("Connect and get Device Number, disconnect and get device number")
        for i in  range(0, 100):
            self.PeakCan.Logger.Info("Loop Run: " + str(i))
            self.PeakCan.Logger.Info("Connect")
            cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["Bluetooth"], 1, 0)
            message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [SystemCommandBlueTooth["Connect"], 0, 0, 0, 0, 0, 0, 0])
            self.PeakCan.WriteFrameWaitAckRetries(message, retries=0)
            time.sleep(BluetoothTime["GetDeviceNumber"])
            self.PeakCan.Logger.Info("Get number of available devices command")
            message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [SystemCommandBlueTooth["GetNumberAvailableDevices"], 0, 0, 0, 0, 0, 0, 0])
            msg = self.PeakCan.WriteFrameWaitAckRetries(message, retries=0)
            deviceNumbers = int(msg["Payload"][2]) - ord('0')
            self.PeakCan.Logger.Info("Number of available devices: " + str(deviceNumbers))
            self.assertGreater(deviceNumbers, 0)
            self.PeakCan.Logger.Info("Disconnect")
            message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [SystemCommandBlueTooth["Disconnect"], 0, 0, 0, 0, 0, 0, 0])
            self.PeakCan.WriteFrameWaitAckRetries(message, retries=0)
            self.PeakCan.Logger.Info("Number of available devices command")
            message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [SystemCommandBlueTooth["GetNumberAvailableDevices"], 0, 0, 0, 0, 0, 0, 0])
            msg = self.PeakCan.WriteFrameWaitAckRetries(message, retries=0)
            deviceNumbers = int(msg["Payload"][2]) - ord('0')
            self.PeakCan.Logger.Info("Number of available devices: " + str(deviceNumbers))
            self.assertEqual(deviceNumbers, 0)

    def BlueToothConnect(self, deviceNr):
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["Bluetooth"], 1, 0)
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [SystemCommandBlueTooth["Connect"], 0, 0, 0, 0, 0, 0, 0])
        self.PeakCan.WriteFrameWaitAckRetries(message)
        time.sleep(BluetoothTime["TestConnect"])
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [SystemCommandBlueTooth["DeviceConnect"], deviceNr, 0, 0, 0, 0, 0, 0])
        connected = self.PeakCan.WriteFrameWaitAckRetries(message)
        connected = int(connected["Payload"][2])
        self.assertNotEqual(0, connected)
        time.sleep(BluetoothTime["TestConnect"])        
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [SystemCommandBlueTooth["DeviceCheckConnected"], 0, 0, 0, 0, 0, 0, 0])
        connectToDevice = self.PeakCan.WriteFrameWaitAckRetries(message)["Payload"][2]
        return int(connectToDevice)
    
    def BlueToothDisconnect(self):
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["Bluetooth"], 1, 0)
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [SystemCommandBlueTooth["Disconnect"], 0, 0, 0, 0, 0, 0, 0])
        self.PeakCan.WriteFrameWaitAckRetries(message)
        time.sleep(BluetoothTime["Disconnect"])
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [SystemCommandBlueTooth["DeviceCheckConnected"], 0, 0, 0, 0, 0, 0, 0])
        connectToDevice = int(self.PeakCan.WriteFrameWaitAckRetries(message)["Payload"][2])
        return connectToDevice
    
    """
    Connect and disconnect to device 30 times
    """

    def test0102BlueToothConnectDisconnectDevice(self):
        self.PeakCan.Logger.Info("Bluetooth connect command and check connected command and disconnect command")
        for i in range(0, 30):
            self.PeakCan.Logger.Info("Loop Run: " + str(i))
            self.PeakCan.Logger.Info("Connect to Bluetooth Device")
            connectToDevice = self.BlueToothConnect(0)
            if(0 != connectToDevice):
                self.PeakCan.Logger.Info("Bluetooth STH connected")
            else:
                self.PeakCan.Logger.Error("Bluetooth STH not Connected")
            self.assertNotEqual(0, connectToDevice)
            self.PeakCan.Logger.Info("Disconnect from Bluetooth Device")
            connectToDevice = self.BlueToothDisconnect()
            if(0 != connectToDevice):
                self.PeakCan.Logger.Error("Bluetooth STH connected")
            else:
                self.PeakCan.Logger.Info("Bluetooth STH not Connected")
            self.assertEqual(0, connectToDevice)

    """
    Write name and get name (bluetooth command)
    """ 

    def test0103BlueToothName(self):
        for _i in range(0, 10):
            while 0 == self.PeakCan.BlueToothConnect(MyToolItNetworkNr["STU1"], 0):
                pass
            self.PeakCan.Logger.Info("Bluetooth name command")
            self.PeakCan.Logger.Info("Connect")
            self.PeakCan.Logger.Info("Write Walther0")
            self.PeakCan.BlueToothNameWrite(0, "Walther0")
            self.PeakCan.Logger.Info("Check Walther0")
            self.PeakCan.BlueToothDisconnect(MyToolItNetworkNr["STU1"])
            self.PeakCan.cmdSend(MyToolItNetworkNr["STU1"], MyToolItBlock["System"], MyToolItSystem["Bluetooth"], [SystemCommandBlueTooth["Connect"], 0, 0, 0, 0, 0, 0, 0])
            time.sleep(BluetoothTime["Disconnect"])
            Name = self.PeakCan.BlueToothNameGet(0)
            self.PeakCan.Logger.Info("Received Name: " + Name)
            self.assertEqual("Walther0", Name)
            self.PeakCan.Logger.Info("Write Marlies")
            while 0 == self.PeakCan.BlueToothConnect(MyToolItNetworkNr["STU1"], 0):
                pass
            self.PeakCan.BlueToothNameWrite(0, "Marlies")
            self.PeakCan.Logger.Info("Check Marlies")
            self.PeakCan.BlueToothDisconnect(MyToolItNetworkNr["STU1"])
            self.PeakCan.cmdSend(MyToolItNetworkNr["STU1"], MyToolItBlock["System"], MyToolItSystem["Bluetooth"], [SystemCommandBlueTooth["Connect"], 0, 0, 0, 0, 0, 0, 0])
            time.sleep(BluetoothTime["Disconnect"])
            Name = self.PeakCan.BlueToothNameGet(0)
            self.PeakCan.Logger.Info("Received Name: " + Name)
            self.assertEqual("Marlies" , Name)
            self.PeakCan.BlueToothDisconnect(MyToolItNetworkNr["STU1"])

    """
    Connect and disconnect to device 100 times, do it without time out, use connection chec    """

    def test0110BlueToothConnectDisconnectDevicePolling(self):
        self.PeakCan.Logger.Info("Bluetooth connect command and check connected command and disconnect command")
        startTime = self.PeakCan.Logger.getTimeStamp()
        for _i in range(0, 100):
            while 0 == self.PeakCan.BlueToothConnect(MyToolItNetworkNr["STU1"], 0):
                pass
            self.PeakCan.BlueToothDisconnect(MyToolItNetworkNr["STU1"])
        endTime = self.PeakCan.Logger.getTimeStamp() 
        ConnectDisconnectTime = endTime - startTime
        ConnectDisconnectTime /= 100
        self.PeakCan.Logger.Info("Average Time for connect and disconnect: " + str(ConnectDisconnectTime) + "ms")
         
    """
    Get Bluetooth Address
    """

    def test0111BlueToothAddress(self):
        self.PeakCan.Logger.Info("Get Bluetooth Address")
        self.PeakCan.Logger.Info("BlueTooth Address: " + hex(self.PeakCan.BlueToothAddress(MyToolItNetworkNr["STU1"])))
                    
    """
    Send Message to STH without connecting. Assumed result = not receiving anything. This especially tests the routing functionallity.
    """ 

    def test0201MyToolItTestNotConnectedAck(self):
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 1, 0)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [0])
        self.PeakCan.Logger.Info("Write Message")
        lastIndex = self.PeakCan.GetReadArrayIndex()
        self.PeakCan.WriteFrame(msg)
        self.PeakCan.Logger.Info("Wait 2000ms")
        time.sleep(2)
        self.assertEqual(self.PeakCan.GetReadArrayIndex(), lastIndex)
        
    """
    Send Message to STH with connecting. Assumed result = receive correct ack. This especially tests the routing functionallity.
    """ 

    def test0202MyToolItTestAck(self):
        expectedData = ActiveState()
        expectedData.asbyte = 0
        expectedData.b.u2NodeState = Node["Application"]
        expectedData.b.u3NetworkState = NetworkState["Operating"]  
        self.PeakCan.Logger.Info("Connect")
        self.assertEqual(1, self.BlueToothConnect(0))
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 1, 0)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [0])
        self.PeakCan.Logger.Info("Write Message")
        self.PeakCan.WriteFrame(msg)
        self.PeakCan.Logger.Info("Wait 200ms")
        time.sleep(0.25)
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 0, 0)
        msgAckExpected = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["STH1"], MyToolItNetworkNr["SPU1"], [expectedData.asbyte])
        self.PeakCan.Logger.Info("Send ID: " + hex(msg.ID) + "; Expected ID: " + hex(msgAckExpected.ID) + "; Received ID: " + hex(self.PeakCan.getReadMessage(-1).ID))
        self.PeakCan.Logger.Info("Send Data: " + hex(0) + "; Expected Data: " + hex(expectedData.asbyte) + "; Received Data: " + hex(self.PeakCan.getReadMessage(-1).DATA[0]))
        self.assertEqual(hex(msgAckExpected.ID), hex(self.PeakCan.getReadMessage(-1).ID))
        self.assertEqual(hex(msgAckExpected.DATA[0]), hex(self.PeakCan.getReadMessage(-1).DATA[0]))
        self.PeakCan.WriteFrameWaitAckRetries(msg, retries=0)
        self.PeakCan.BlueToothDisconnect(MyToolItNetworkNr["STU1"])     
           
    """
    Send Message to STH with connecting. Assumed result = receive correct ack. This especially tests the routing functionallity.
    """ 

    def test0203MyToolItTestWrongReceiver(self):
        self.PeakCan.Logger.Info("Connect")
        self.assertEqual(1, self.BlueToothConnect(0))
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 1, 0)
        for i in range(MyToolItNetworkNr["STH2"], 32):
            if (MyToolItNetworkNr["STU1"] != i):
                msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], i, [0])
                ack = self.PeakCan.WriteFrameWaitAck(msg)
                self.assertEqual("Error", ack[0])

        # Test that it still works
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [0])
        self.PeakCan.WriteFrameWaitAckRetries(msg, retries=0)
 
    """ Send Mutliple Frames without waiting for an ACK via routing, do ACK after 100 times send flooding to check functionallity"""

    def test0204RoutingMultiSend(self):
        self.PeakCan.Logger.Info("Send command 100 times over STU to STH, check number of write/reads and do ack test at the end; do that for 1000 times")
        self.PeakCan.Logger.Info("Connect")
        while 0 == self.PeakCan.BlueToothConnect(MyToolItNetworkNr["STU1"], 0):
            pass
        for i in range(1, 101):
            self.PeakCan.Logger.Info("Received Index: " + str(self.PeakCan.GetReadArrayIndex()))
            self.PeakCan.Logger.Info("Run: " + str(i))
            for _j in range(1, 101):
                if(1 == randint(0, 1)):
                    cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 1, 0)
                    message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [0])                    
                else:
                    cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["StatusWord0"], 1, 0)
                    message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [0, 0, 0, 0, 0, 0, 0, 0])
                self.PeakCan.WriteFrame(message)
            self.PeakCan.Reset()
            time.sleep(0.25) 
            self.PeakCan.WriteFrameWaitAckRetries(message, retries=0)
     
    """ Send Mutliple Frames with waiting for an ACK with routing: Send->Ack->Send->Ack"""

    def test0205RoutingMultiSendAck(self):
        self.PeakCan.Logger.Info("Send and get ACK for 10000 times AND do it with two messages randomly ")
        self.PeakCan.Logger.Info("Connect")
        self.assertEqual(1, self.BlueToothConnect(0))
        for i in range(1, 1001):
            self.PeakCan.Logger.Info("Received Index: " + str(self.PeakCan.GetReadArrayIndex()))
            self.PeakCan.Logger.Info("Run: " + str(i))
            if(1 == randint(0, 1)):
                cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 1, 0)
                msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [0])
            else:
                cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["StatusWord0"], 1, 0)
                msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [0, 0, 0, 0, 0, 0, 0, 0])
            self.assertNotEqual("Error", self.PeakCan.WriteFrameWaitAck(msg))
         
    """ Send Mutliple Frames with waiting for an ACK: Send->Ack->Send->Ack with routing, this also do a retry, tests the test framework - Multiple Messages"""

    def test0206RoutingMultiSendAckRetries(self):
        self.PeakCan.Logger.Info("Send and get ACK for 10000 times AND do it with two messages randomly ")
        self.PeakCan.Logger.Info("Connect")
        self.assertEqual(1, self.BlueToothConnect(0))
        for i in range(1, 1001):
            self.PeakCan.Logger.Info("Received Index: " + str(self.PeakCan.GetReadArrayIndex()))
            self.PeakCan.Logger.Info("Run: " + str(i))
            if(1 == randint(0, 1)):
                cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 1, 0)
                msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [0])
            else:
                cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["StatusWord0"], 1, 0)
                msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [0, 0, 0, 0, 0, 0, 0, 0])
            self.assertNotEqual("Error", self.PeakCan.WriteFrameWaitAckRetries(msg, retries=0))
         
        """ Send Mutliple Frames with waiting for an ACK: Send->Ack->Send->Ack with routing, this also do a retry, tests the test framework - Single Message"""

    def test0207RoutingMultiSendSingleAckRetries(self):
        self.PeakCan.Logger.Info("Send and get ACK for 10000 times AND do it with two messages randomly ")
        self.PeakCan.Logger.Info("Connect")
        self.assertEqual(1, self.BlueToothConnect(0))
        for i in range(1, 1001):
            self.PeakCan.Logger.Info("Received Index: " + str(self.PeakCan.GetReadArrayIndex()))
            self.PeakCan.Logger.Info("Run: " + str(i))
            cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["StatusWord0"], 1, 0)
            msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [0, 0, 0, 0, 0, 0, 0, 0])
            self.assertNotEqual("Error", self.PeakCan.WriteFrameWaitAckRetries(msg, retries=0))
         
    """
    Send addressing same sender and receiver via Routing
    """ 

    def test0208RoutingSenderReceiver(self):
        self.PeakCan.Logger.Info("Connect to STH and send message with STH1=sender/receiver")
        self.PeakCan.Logger.Info("Connect")
        self.assertEqual(1, self.BlueToothConnect(0))
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 1, 0)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["STH1"], MyToolItNetworkNr["STH1"], [0])
        self.assertEqual("Error", self.PeakCan.WriteFrameWaitAck(msg)[0])
        # Test that it still works
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [0])
        self.PeakCan.WriteFrameWaitAckRetries(msg, retries=0)
         
    """
    "Christmas Tree" packages via routing
    """ 

    def test0209RoutingChristmasTree(self):
        self.PeakCan.Logger.Info("Error Request Frame from STH1 to STH1")
        self.PeakCan.Logger.Info("Connect")
        self.assertEqual(1, self.BlueToothConnect(0))
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 1, 1)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["STH1"], MyToolItNetworkNr["STH1"], [0])
        self.assertEqual("Error", self.PeakCan.WriteFrameWaitAck(msg)[0])
        self.PeakCan.Logger.Info("Error Request Frame from SPU1 to STH1")
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 1, 1)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [0])
        self.assertEqual("Error", self.PeakCan.WriteFrameWaitAck(msg)[0])
        self.PeakCan.Logger.Info("Error Ack Frame from STH1 to STH1")
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 0, 1)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["STH1"], MyToolItNetworkNr["STH1"], [0])
        self.assertEqual("Error", self.PeakCan.WriteFrameWaitAck(msg)[0])
        self.PeakCan.Logger.Info("Error Ack Frame from SPU1 to STH1")
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 0, 1)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [0])
        self.assertEqual("Error", self.PeakCan.WriteFrameWaitAck(msg)[0])
        self.PeakCan.Logger.Info("Ack Frame from STH1 to STH1")
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 0, 0)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["STH1"], MyToolItNetworkNr["STH1"], [0])
        self.assertEqual("Error", self.PeakCan.WriteFrameWaitAck(msg)[0])
        self.PeakCan.Logger.Info("Ack Frame from SPU1 to STH1")
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 0, 0)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [0])
        self.assertEqual("Error", self.PeakCan.WriteFrameWaitAck(msg)[0])
         
        # Test that it still works
        self.PeakCan.Logger.Info("Normal Request to STH1")
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 1, 0)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [0])
        self.PeakCan.WriteFrameWaitAckRetries(msg, retries=0)       
        
    """
    Check Power On and Power Off Counters
    """   

    def test0700StatisticsPowerOnCounterPowerOffCounter(self):
        PowerOnOff1 = self.PeakCan.statisticalData(MyToolItNetworkNr["STU1"], MyToolItStatData["PocPof"])
        PowerOn1 = messageWordGet(PowerOnOff1[:4])
        PowerOff1 = messageWordGet(PowerOnOff1[4:])              
        self._resetStu()        
        PowerOnOff2 = self.PeakCan.statisticalData(MyToolItNetworkNr["STU1"], MyToolItStatData["PocPof"])
        PowerOn2 = messageWordGet(PowerOnOff2[:4])
        PowerOff2 = messageWordGet(PowerOnOff2[4:]) 
        self.PeakCan.Logger.Info("PowerOnOff Payload before STU Reset: " + payload2Hex(PowerOnOff1))
        self.PeakCan.Logger.Info("Power On Counter before STU Reset: " + str(PowerOn1))
        self.PeakCan.Logger.Info("Power Off Counter before STU Reset: " + str(PowerOff1))
        self.PeakCan.Logger.Info("PowerOnOff Payload after STU Reset: " + payload2Hex(PowerOnOff2))
        self.PeakCan.Logger.Info("Power On Counter after STU Reset: " + str(PowerOn1))
        self.PeakCan.Logger.Info("Power Off Counter after STU Reset: " + str(PowerOff1))
        self.assertEqual(PowerOn1 + 1, PowerOn2)
        self.assertEqual(PowerOff1, PowerOff2)

    """
    Check Operating Minutes
    """   

    def test0701StatisticsOperatingMinutes(self):
        OperatingMinutes1 = self.PeakCan.statisticalData(MyToolItNetworkNr["STU1"], MyToolItStatData["OperatingTime"])    
        MinutesReset1 = messageWordGet(OperatingMinutes1[:4])
        MinutesOveral1 = messageWordGet(OperatingMinutes1[4:])
        time.sleep(60)
        OperatingMinutes2 = self.PeakCan.statisticalData(MyToolItNetworkNr["STU1"], MyToolItStatData["OperatingTime"])    
        MinutesReset2 = messageWordGet(OperatingMinutes2[:4])
        MinutesOveral2 = messageWordGet(OperatingMinutes2[4:])
        self._resetStu()
        OperatingMinutes3 = self.PeakCan.statisticalData(MyToolItNetworkNr["STU1"], MyToolItStatData["OperatingTime"])    
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
        self.assertEqual(MinutesReset3, 0)
        self.assertEqual(MinutesOveral1, MinutesOveral2)                
        self.assertEqual(MinutesOveral1 + 1, MinutesOveral3)
   
    """
    Check Watchdog counter to not increment
    """   

    def test0702WdogNotIncrementing(self):
        WDogCounter1 = self._StuWDog()
        self._resetStu()
        WDogCounter2 = self._StuWDog()
        self._resetStu()
        self.PeakCan.Logger.Info("Watchdog Counter at start: " + str(WDogCounter1))
        self.PeakCan.Logger.Info("Watchdog Counter after reset: " + str(WDogCounter2))
        self.assertEqual(WDogCounter1, WDogCounter2)

    """
    Test that nothing happens when sinding Command 0x0000 to STU1
    """

    def test0900ErrorCmdVerbotenStu1(self):
        cmd = self.PeakCan.CanCmd(0, 0, 1, 0)
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [])
        msgAck = self.PeakCan.WriteFrameWaitAckRetries(message, waitMs=1000, retries=3, bErrorExit=False)
        self.assertEqual("Error", msgAck)
        cmd = self.PeakCan.CanCmd(0, 0, 1, 1)
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [])
        msgAck = self.PeakCan.WriteFrameWaitAckRetries(message, waitMs=1000, retries=3, bErrorExit=False)
        self.assertEqual("Error", msgAck)
        cmd = self.PeakCan.CanCmd(0, 0, 0, 0)
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [])
        msgAck = self.PeakCan.WriteFrameWaitAckRetries(message, waitMs=1000, retries=3, bErrorExit=False)
        self.assertEqual("Error", msgAck)
        cmd = self.PeakCan.CanCmd(0, 0, 0, 1)
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [])
        msgAck = self.PeakCan.WriteFrameWaitAckRetries(message, waitMs=1000, retries=3, bErrorExit=False)
        self.assertEqual("Error", msgAck)
               
    """
    Test that nothing happens when sinding Reqest(1) and Error(1) to STU1
    """

    def test0901ErrorRequestErrorStu1(self):
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["Reset"], 1, 1)
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [])
        msgAck = self.PeakCan.WriteFrameWaitAckRetries(message, waitMs=1000, retries=3, bErrorExit=False)
        self.assertEqual("Error", msgAck)
        cmd = self.PeakCan.CanCmd(MyToolItBlock["Streaming"], MyToolItStreaming["Acceleration"], 1, 1)
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [])
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
