import unittest
import sys
import os
# Required to add peakcan
dir_name = os.path.dirname('')
sys.path.append(dir_name)
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
        self.bError = False
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
        if False == self.PeakCan.bError:
            self._statusWords()
            self.PeakCan.Logger.Info("Test Time End Time Stamp")
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
        return False       
    
    def _resetStu(self, retries=5, log=True):
        return self.PeakCan.cmdReset(MyToolItNetworkNr["STU1"], retries=retries, log=log)

    def _StuWDog(self):
        WdogCounter = iMessage2Value(self.PeakCan.statisticalData(MyToolItNetworkNr["STU1"], MyToolItStatData["Wdog"])[:4])
        self.PeakCan.Logger.Info("WatchDog Counter: " + str(WdogCounter))
        return WdogCounter 
        
    def _statusWords(self):
        ErrorWord = StuErrorWord()
        psw0 = self.PeakCan.statusWord0(MyToolItNetworkNr["STU1"])
        self.PeakCan.Logger.Info("STU Status Word: " + hex(psw0))
        ErrorWord.asword = self.PeakCan.statusWord1(MyToolItNetworkNr["STU1"])
        self.PeakCan.Logger.Info("STU bError Word: " + hex(ErrorWord.asword))    
    
    """
    Test Acknowledgement from STU. Write message and check identifier to be ack (No bError)
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
            self.assertNotEqual("bError", self.PeakCan.WriteFrameWaitAck(msg))
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
            self.assertNotEqual("bError", self.PeakCan.WriteFrameWaitAckRetries(msg, retries=3))
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
        self.assertEqual("bError", self.PeakCan.WriteFrameWaitAck(msg)[0])
        # Test that it still works
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [0])
        self.PeakCan.WriteFrameWaitAckRetries(msg, retries=0)
        
    """
    "Christmas Tree" packages
    """ 

    def test0007ChristmasTree(self):
        self.PeakCan.Logger.Info("bError Request Frame from STU1 to STU1")
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 1, 1)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["STU1"], MyToolItNetworkNr["STU1"], [0])
        self.assertEqual("bError", self.PeakCan.WriteFrameWaitAck(msg)[0])
        self.PeakCan.Logger.Info("bError Request Frame from SPU1 to STU1")
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 1, 1)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [0])
        self.assertEqual("bError", self.PeakCan.WriteFrameWaitAck(msg)[0])
        self.PeakCan.Logger.Info("bError Ack Frame from STU1 to STU1")
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 0, 1)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["STU1"], MyToolItNetworkNr["STU1"], [0])
        self.assertEqual("bError", self.PeakCan.WriteFrameWaitAck(msg)[0])
        self.PeakCan.Logger.Info("bError Ack Frame from SPU1 to STU1")
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 0, 1)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [0])
        self.assertEqual("bError", self.PeakCan.WriteFrameWaitAck(msg)[0])
        self.PeakCan.Logger.Info("Ack Frame from STU1 to STU1")
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 0, 0)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["STU1"], MyToolItNetworkNr["STU1"], [0])
        self.assertEqual("bError", self.PeakCan.WriteFrameWaitAck(msg)[0])
        self.PeakCan.Logger.Info("Ack Frame from SPU1 to STU1")
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 0, 0)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [0])
        self.assertEqual("bError", self.PeakCan.WriteFrameWaitAck(msg)[0])
        
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
                self.PeakCan.Logger.bError("Bluetooth STH not Connected")
            self.assertNotEqual(0, connectToDevice)
            self.PeakCan.Logger.Info("Disconnect from Bluetooth Device")
            connectToDevice = self.BlueToothDisconnect()
            if(0 != connectToDevice):
                self.PeakCan.Logger.bError("Bluetooth STH connected")
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
    Check that correct Bluetooth addresses are (correctly)  listed
    """

    def test0104BluetoothAddressDevices(self):
        for _i in range(0, 10):
            self.PeakCan.BlueToothConnectConnect(MyToolItNetworkNr["STU1"])
            endTime = time.time() + 5
            while 0 == self.PeakCan.BlueToothConnectTotalScannedDeviceNr(MyToolItNetworkNr["STU1"]):
                if time.time() > endTime:
                    break
            time.sleep(0.5)
            devNrs = self.PeakCan.BlueToothConnectTotalScannedDeviceNr(MyToolItNetworkNr["STU1"])
            for devNr in range(0, devNrs):
                self.PeakCan.Logger.Info("Device Number " + str(devNr))
                Address = self.PeakCan.BlueToothAddressGet(MyToolItNetworkNr["STU1"], devNr)
            self.PeakCan.Logger.Info("Address: " + hex(Address))
            self.assertGreater(Address, 0)
            self.PeakCan.BlueToothDisconnect(MyToolItNetworkNr["STU1"])
    
    """
    Check that correct Bluetooth RSSIs are listed
    """    

    def test105BluetoothRssi(self):
        for _i in range(0, 10):
            self.PeakCan.BlueToothConnectConnect(MyToolItNetworkNr["STU1"])
            endTime = time.time() + 5
            while 0 == self.PeakCan.BlueToothConnectTotalScannedDeviceNr(MyToolItNetworkNr["STU1"]):
                if time.time() > endTime:
                    break
            time.sleep(0.5)
            Rssi = self.PeakCan.BlueToothRssiGet(MyToolItNetworkNr["STU1"], 0)
            self.PeakCan.Logger.Info("RSSI: " + int(Rssi))
            self.assertNotEqual(Rssi, 127)
            self.PeakCan.BlueToothDisconnect(MyToolItNetworkNr["STU1"])

    """
    Check that correct Bluetooth RSSIs change
    """    

    def test106BluetoothRssiChange(self):
        self.PeakCan.BlueToothConnectConnect(MyToolItNetworkNr["STU1"])
        endTime = time.time() + 5
        while 0 == self.PeakCan.BlueToothConnectTotalScannedDeviceNr(MyToolItNetworkNr["STU1"]):
            if time.time() > endTime:
                break
        time.sleep(0.5)
        Rssi = []
        for _i in range(0, 20):
            Rssi.append(self.PeakCan.BlueToothRssiGet(MyToolItNetworkNr["STU1"], 0))
            self.PeakCan.Logger.Info("RSSI: " + int(Rssi[-1]))
            self.assertNotEqual(Rssi, 127)
        self.PeakCan.BlueToothDisconnect(MyToolItNetworkNr["STU1"])
        Rssi.sort()
        self.assertNotEqual(Rssi[1], Rssi[-2])
            
    """
    Check that correct Bluetooth name, addresses and RSSIs are (correctly) listed
    """   

    def test107BluetoothNameAddressRssi(self):
        self.PeakCan.BlueToothConnectConnect(MyToolItNetworkNr["STU1"])
        endTime = time.time() + 5
        while 0 == self.PeakCan.BlueToothConnectTotalScannedDeviceNr(MyToolItNetworkNr["STU1"]):
            if time.time() > endTime:
                break
        Name = self.PeakCan.BlueToothNameGet(MyToolItNetworkNr["STU1"], 0)
        Address = self.PeakCan.BlueToothAddressGet(MyToolItNetworkNr["STU1"], 0)
        Rssi = self.PeakCan.BlueToothRssiGet(MyToolItNetworkNr["STU1"], 0)
        self.PeakCan.Logger.Info("Name: " + Name)
        self.PeakCan.Logger.Info("Address: " + hex(Address))
        self.PeakCan.Logger.Info("RSSI: " + str(Rssi))
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
                self.assertEqual("bError", ack[0])

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
            self.assertNotEqual("bError", self.PeakCan.WriteFrameWaitAck(msg))
         
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
            self.assertNotEqual("bError", self.PeakCan.WriteFrameWaitAckRetries(msg, retries=0))
         
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
            self.assertNotEqual("bError", self.PeakCan.WriteFrameWaitAckRetries(msg, retries=0))
         
    """
    Send addressing same sender and receiver via Routing
    """ 

    def test0208RoutingSenderReceiver(self):
        self.PeakCan.Logger.Info("Connect to STH and send message with STH1=sender/receiver")
        self.PeakCan.Logger.Info("Connect")
        self.assertEqual(1, self.BlueToothConnect(0))
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 1, 0)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["STH1"], MyToolItNetworkNr["STH1"], [0])
        self.assertEqual("bError", self.PeakCan.WriteFrameWaitAck(msg)[0])
        # Test that it still works
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [0])
        self.PeakCan.WriteFrameWaitAckRetries(msg, retries=0)
         
    """
    "Christmas Tree" packages via routing
    """ 

    def test0209RoutingChristmasTree(self):
        self.PeakCan.Logger.Info("bError Request Frame from STH1 to STH1")
        self.PeakCan.Logger.Info("Connect")
        self.assertEqual(1, self.BlueToothConnect(0))
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 1, 1)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["STH1"], MyToolItNetworkNr["STH1"], [0])
        self.assertEqual("bError", self.PeakCan.WriteFrameWaitAck(msg)[0])
        self.PeakCan.Logger.Info("bError Request Frame from SPU1 to STH1")
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 1, 1)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [0])
        self.assertEqual("bError", self.PeakCan.WriteFrameWaitAck(msg)[0])
        self.PeakCan.Logger.Info("bError Ack Frame from STH1 to STH1")
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 0, 1)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["STH1"], MyToolItNetworkNr["STH1"], [0])
        self.assertEqual("bError", self.PeakCan.WriteFrameWaitAck(msg)[0])
        self.PeakCan.Logger.Info("bError Ack Frame from SPU1 to STH1")
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 0, 1)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [0])
        self.assertEqual("bError", self.PeakCan.WriteFrameWaitAck(msg)[0])
        self.PeakCan.Logger.Info("Ack Frame from STH1 to STH1")
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 0, 0)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["STH1"], MyToolItNetworkNr["STH1"], [0])
        self.assertEqual("bError", self.PeakCan.WriteFrameWaitAck(msg)[0])
        self.PeakCan.Logger.Info("Ack Frame from SPU1 to STH1")
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 0, 0)
        msg = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [0])
        self.assertEqual("bError", self.PeakCan.WriteFrameWaitAck(msg)[0])
         
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
        PowerOn1 = iMessage2Value(PowerOnOff1[:4])
        PowerOff1 = iMessage2Value(PowerOnOff1[4:])              
        self._resetStu()        
        PowerOnOff2 = self.PeakCan.statisticalData(MyToolItNetworkNr["STU1"], MyToolItStatData["PocPof"])
        PowerOn2 = iMessage2Value(PowerOnOff2[:4])
        PowerOff2 = iMessage2Value(PowerOnOff2[4:]) 
        self.PeakCan.Logger.Info("PowerOnOff Payload before STU Reset: " + payload2Hex(PowerOnOff1))
        self.PeakCan.Logger.Info("Power On Counter before STU Reset: " + str(PowerOn1))
        self.PeakCan.Logger.Info("Power Off Counter before STU Reset: " + str(PowerOff1))
        self.PeakCan.Logger.Info("PowerOnOff Payload after STU Reset: " + payload2Hex(PowerOnOff2))
        self.PeakCan.Logger.Info("Power On Counter after STU Reset: " + str(PowerOn1))
        self.PeakCan.Logger.Info("Power Off Counter after STU Reset: " + str(PowerOff1))
        self.assertEqual(PowerOn1 + 1, PowerOn2)
        self.assertEqual(PowerOff1, PowerOff2)

    """
    Check Operating Seconds
    """   

    def test0701StatisticsOperatingSeconds(self):
        OperatingSeconds = self.PeakCan.statisticalData(MyToolItNetworkNr["STU1"], MyToolItStatData["OperatingTime"])    
        SecondsReset1 = iMessage2Value(OperatingSeconds[:4])
        SecondsOveral1 = iMessage2Value(OperatingSeconds[4:])
        time.sleep(60)
        OperatingSeconds = self.PeakCan.statisticalData(MyToolItNetworkNr["STU1"], MyToolItStatData["OperatingTime"])    
        SecondsReset2 = iMessage2Value(OperatingSeconds[:4])
        SecondsOveral2 = iMessage2Value(OperatingSeconds[4:])
        self._resetStu()
        OperatingSeconds = self.PeakCan.statisticalData(MyToolItNetworkNr["STU1"], MyToolItStatData["OperatingTime"])    
        SecondsReset3 = iMessage2Value(OperatingSeconds[:4])
        SecondsOveral3 = iMessage2Value(OperatingSeconds[4:])
        time.sleep(60*30+2)
        OperatingSeconds = self.PeakCan.statisticalData(MyToolItNetworkNr["STU1"], MyToolItStatData["OperatingTime"])    
        SecondsReset4 = iMessage2Value(OperatingSeconds[:4])
        SecondsOveral4 = iMessage2Value(OperatingSeconds[4:])
        self.PeakCan.Logger.Info("Operating Seconds since Reset: " + str(SecondsReset1))
        self.PeakCan.Logger.Info("Operating Seconds since frist PowerOn: " + str(SecondsOveral1))
        self.PeakCan.Logger.Info("Operating Seconds since Reset(+1 minute): " + str(SecondsReset2))
        self.PeakCan.Logger.Info("Operating Seconds since frist PowerOn(+1minute): " + str(SecondsOveral2))    
        self.PeakCan.Logger.Info("Operating Seconds since Reset(After Disconnect/Connect): " + str(SecondsReset3))
        self.PeakCan.Logger.Info("Operating Seconds since frist PowerOn(After Disconnect/Connect): " + str(SecondsOveral3))    
        self.PeakCan.Logger.Info("Operating Seconds since Reset(+30 minutes): " + str(SecondsReset4))
        self.PeakCan.Logger.Info("Operating Seconds since frist PowerOn(+30minutes): " + str(SecondsOveral4))  
        self.assertLess(SecondsReset1, 10)                
        self.assertGreater(SecondsReset2, 60)
        self.assertLess(SecondsReset2, 70)
        self.assertLess(SecondsReset3, 10)
        self.assertGreater(SecondsReset4, 60*30)
        self.assertLess(SecondsReset4, 10+60*30)
        self.assertEqual(SecondsOveral1, SecondsOveral2)    
        self.assertLess(SecondsOveral1 + 58, SecondsOveral3)            
        self.assertGreater(SecondsOveral1 + 63, SecondsOveral3)
        self.assertLess(SecondsOveral1 + 58, SecondsOveral3)            
        self.assertGreater(SecondsOveral1 + 63, SecondsOveral3)  
        self.assertLess(SecondsOveral3 + 30*60-3, SecondsOveral4)
        self.assertGreater(SecondsOveral3 + 30*60+4, SecondsOveral4)  
   
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
    Check EEPROM Read/Write
    """   

    def test0750StatisticPageWriteRead(self):
        # Write 0xFF over the page
        timeStamp = self.PeakCan.getTimeMs()
        for offset in range(0, 256, 4):
            self.PeakCan.cmdSend(MyToolItNetworkNr["STU1"], MyToolItBlock["Eeprom"], MyToolItEeprom["Write"], [EepromPage["Statistics"], 0xFF & offset, 4, 0, 0xFF, 0xFF, 0xFF, 0xFF])
        self.PeakCan.Logger.Info("Page Write Time: " + str(self.PeakCan.getTimeMs() - timeStamp) + "ms")
        # Read back 0xFF over the page
        timeStamp = self.PeakCan.getTimeMs()
        for offset in range(0, 256, 4):
            index = self.PeakCan.cmdSend(MyToolItNetworkNr["STU1"], MyToolItBlock["Eeprom"], MyToolItEeprom["Read"], [EepromPage["Statistics"], 0xFF & offset, 4, 0, 0, 0, 0, 0])   
            dataReadBack = self.PeakCan.getReadMessageData(index)     
            for dataByte in dataReadBack[4:]:
                self.assertEqual(dataByte, 0xFF)
        self.PeakCan.Logger.Info("Page Read Time: " + str(self.PeakCan.getTimeMs() - timeStamp) + "ms")
        # Write 0x00 over the page
        timeStamp = self.PeakCan.getTimeMs()
        for offset in range(0, 256, 4):
            self.PeakCan.cmdSend(MyToolItNetworkNr["STU1"], MyToolItBlock["Eeprom"], MyToolItEeprom["Write"], [EepromPage["Statistics"], 0xFF & offset, 4, 0, 0, 0, 0, 0])
        self.PeakCan.Logger.Info("Page Write Time: " + str(self.PeakCan.getTimeMs() - timeStamp) + "ms")
        # Read back 0x00 over the page    
        timeStamp = self.PeakCan.getTimeMs()
        for offset in range(0, 256, 4):
            index = self.PeakCan.cmdSend(MyToolItNetworkNr["STU1"], MyToolItBlock["Eeprom"], MyToolItEeprom["Read"], [EepromPage["Statistics"], 0xFF & offset, 4, 0, 0, 0, 0, 0])   
            dataReadBack = self.PeakCan.getReadMessageData(index)     
            for dataByte in dataReadBack[4:]:
                self.assertEqual(dataByte, 0x00)             
        self.PeakCan.Logger.Info("Page Read Time: " + str(self.PeakCan.getTimeMs() - timeStamp) + "ms")     
        
        
    """
    Test that nothing happens when sinding Command 0x0000 to STU1
    """

    def test0900ErrorCmdVerbotenStu1(self):
        cmd = self.PeakCan.CanCmd(0, 0, 1, 0)
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [])
        msgAck = self.PeakCan.WriteFrameWaitAckRetries(message, waitMs=1000, retries=3, bErrorExit=False)
        self.assertEqual("bError", msgAck)
        cmd = self.PeakCan.CanCmd(0, 0, 1, 1)
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [])
        msgAck = self.PeakCan.WriteFrameWaitAckRetries(message, waitMs=1000, retries=3, bErrorExit=False)
        self.assertEqual("bError", msgAck)
        cmd = self.PeakCan.CanCmd(0, 0, 0, 0)
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [])
        msgAck = self.PeakCan.WriteFrameWaitAckRetries(message, waitMs=1000, retries=3, bErrorExit=False)
        self.assertEqual("bError", msgAck)
        cmd = self.PeakCan.CanCmd(0, 0, 0, 1)
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [])
        msgAck = self.PeakCan.WriteFrameWaitAckRetries(message, waitMs=1000, retries=3, bErrorExit=False)
        self.assertEqual("bError", msgAck)
               
    """
    Test that nothing happens when sinding Reqest(1) and bError(1) to STU1
    """

    def test0901ErrorRequestErrorStu1(self):
        cmd = self.PeakCan.CanCmd(MyToolItBlock["System"], MyToolItSystem["Reset"], 1, 1)
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [])
        msgAck = self.PeakCan.WriteFrameWaitAckRetries(message, waitMs=1000, retries=3, bErrorExit=False)
        self.assertEqual("bError", msgAck)
        cmd = self.PeakCan.CanCmd(MyToolItBlock["Streaming"], MyToolItStreaming["Acceleration"], 1, 1)
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [])
        msgAck = self.PeakCan.WriteFrameWaitAckRetries(message, waitMs=1000, retries=3, bErrorExit=False)
        self.assertEqual("bError", msgAck)          

         
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
