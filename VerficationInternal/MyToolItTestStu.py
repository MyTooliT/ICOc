import unittest
import sys
import os
file_path = 'C:\Program Files\PCAN-Basic API\Include\PCANBasic.py'
dir_name = os.path.dirname(file_path)
sys.path.append(dir_name)

from PCANBasic import *   
from PeakCanFd import *
from MyToolItNetworkNumbers import *
from MyToolItCommands import *
from time import sleep
from time import time
from random import randint

log_file = 'TestStu.txt'
log_location='../Logs/STU/'
        

class TestStu(unittest.TestCase):
    def setUp(self):
        print("TestCase: ", self._testMethodName)
        self.fileName = log_location + self._testMethodName + ".txt"
        self.fileNameError = log_location + "Error_" + self._testMethodName + ".txt"
        self.PeakCan = PeakCanFd(PCAN_BAUD_1M, self.fileName, self.fileNameError, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1)
        self.PeakCan.Logger.Info("TestCase: "+ str(self._testMethodName))
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_RESET, 1, 0)
        lastIndex=self.PeakCan.GetReadArrayIndex()
        while lastIndex==self.PeakCan.GetReadArrayIndex():
            self.PeakCan.WriteFrame(self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, []) )
            sleep(0.2)
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 1, 0)
        lastIndex=self.PeakCan.GetReadArrayIndex()
        while lastIndex==self.PeakCan.GetReadArrayIndex():
            self.PeakCan.WriteFrame(self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [0]) )
            sleep(0.2)
        print("Start")
        self.PeakCan.Logger.Info("Start")

    def tearDown(self): 
        self.PeakCan.Logger.Info("Test Time End Time Stamp")
        self.PeakCan.__exit__()  
        if self._test_has_failed():  
            errorFileName=log_location+"Error_" + self._testMethodName+".txt"   
            if os.path.isfile(errorFileName):
                os.remove(errorFileName)
            os.rename(log_location+self._testMethodName+".txt", errorFileName)
 
    def _test_has_failed(self):
        for method, error in self._outcome.errors:
            if error:
                return True
        return False       
        
    """
    Test Acknowledgement from STU. Write message and check identifier to be ack (No Error)
    """    
    def test0001Ack(self):
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 1, 0)
        msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [0])
        self.PeakCan.Logger.Info("Write Message")
        self.PeakCan.WriteFrame(msg)
        self.PeakCan.Logger.Info("Wait 200ms")
        sleep(0.2)
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 0, 0)
        msgAckExpected = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_STU1, MY_TOOL_IT_NETWORK_SPU1, [0])
        self.PeakCan.Logger.Info("Send ID: " + hex(msg.ID) + "; Expected ID: "+hex(msgAckExpected.ID) + "; Received ID: "+hex(self.PeakCan.getReadMessage(-1).ID))
        expectedData=ActiveState()
        expectedData.asbyte=0
        expectedData.b.u2NodeState=2
        expectedData.b.u3NetworkState=6
        self.PeakCan.Logger.Info("Send Data: " + hex(0) + "; Expected Data: " + hex(expectedData.asbyte) + "; Received Data: " + hex(self.PeakCan.getReadMessage(-1).DATA[0]))
        self.assertEqual(hex(msgAckExpected.ID), hex(self.PeakCan.getReadMessage(-1).ID))
        self.assertEqual(expectedData.asbyte, self.PeakCan.getReadMessage(-1).DATA[0])
        
        
    """ Send Mutliple Frames without waiting for an ACK, do ACK after 100 times send flooding to check functionallity"""
    def test0002MultiSend(self):
        self.PeakCan.Logger.Info("Send command 100 times, check number of write/reads and do ack test at the end; do that for 1000 times")
        for i in range(1, 1001):
            self.PeakCan.Logger.Info("Received Index: " + str(self.PeakCan.GetReadArrayIndex()))
            self.PeakCan.Logger.Info("Run: " + str(i))
            for j in range(1, 101):
                if( 1== randint(0,1)):
                    cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 1, 0)
                    message=self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [0])                    
                else:
                    cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
                    message=self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothDeviceCheckConnected, 0, 0, 0, 0, 0, 0, 0])
                self.PeakCan.WriteFrame(message)
            self.PeakCan.Reset()
            sleep(0.2) 
            self.PeakCan.WriteFrameWaitAckRetries(message)
        
       
       
    
    """ Send Mutliple Frames with waiting for an ACK: Send->Ack->Send->Ack"""
    def test0003MultiSendAck(self):
        self.PeakCan.Logger.Info("Send and get ACK for 10000 times AND do it with two messages randomly ")
        for i in range(1, 10001):
            self.PeakCan.Logger.Info("Received Index: " + str(self.PeakCan.GetReadArrayIndex()))
            self.PeakCan.Logger.Info("Run: " + str(i))
            if( 1== randint(0,1)):
                cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 1, 0)
                msg=self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [0])
            else:
                cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
                msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothDeviceCheckConnected, 0, 0, 0, 0, 0, 0, 0])
            self.assertNotEqual("Error", self.PeakCan.WriteFrameWaitAck(msg))
        self.test0001Ack() #Test that it still works
        
        
    """ Send Mutliple Frames with waiting for an ACK: Send->Ack->Send->Ack, this also do a retry, tests the test framework - Multiple Messages"""
    def test0004MultiSendMultiAckRetries(self):
        self.PeakCan.Logger.Info("Send and get ACK for 10000 times AND do it with two messages randomly ")
        for i in range(1, 10001):
            self.PeakCan.Logger.Info("Received Index: " + str(self.PeakCan.GetReadArrayIndex()))
            self.PeakCan.Logger.Info("Run: " + str(i))
            if( 1== randint(0,1)):
                cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 1, 0)
                msg=self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [0])
            else:
                cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
                msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothDeviceCheckConnected, 0, 0, 0, 0, 0, 0, 0])
            self.assertNotEqual("Error", self.PeakCan.WriteFrameWaitAckRetries(msg))
        self.test0001Ack() #Test that it still works
        
        """ Send Mutliple Frames with waiting for an ACK: Send->Ack->Send->Ack, this also do a retry, tests the test framework - Single Message"""
    def test0005MultiSendSingleAckRetries(self):
        self.PeakCan.Logger.Info("Send and get ACK for 10000 times AND do it with two messages randomly ")
        for i in range(1, 10001):
            self.PeakCan.Logger.Info("Received Index: " + str(self.PeakCan.GetReadArrayIndex()))
            self.PeakCan.Logger.Info("Run: " + str(i))
            cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
            msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothDeviceCheckConnected, 0, 0, 0, 0, 0, 0, 0])
            self.assertNotEqual("Error", self.PeakCan.WriteFrameWaitAckRetries(msg))
        self.test0001Ack() #Test that it still works
        
        
    """
    Send addressing same sender and receiver
    """ 
    def test0006SenderReceiver(self):
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 1, 0)
        msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_STU1, MY_TOOL_IT_NETWORK_STU1, [0])
        self.assertEqual("Error", self.PeakCan.WriteFrameWaitAck(msg))
        #Test that it still works
        msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [0])
        self.PeakCan.WriteFrameWaitAckRetries(msg)
        
    """
    "Christmas Tree" packages
    """ 
    def test0007ChristmasTree(self):
        self.PeakCan.Logger.Info("Error Request Frame from STU1 to STU1")
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 1, 1)
        msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_STU1, MY_TOOL_IT_NETWORK_STU1, [0])
        self.assertEqual("Error", self.PeakCan.WriteFrameWaitAck(msg))
        self.PeakCan.Logger.Info("Error Request Frame from SPU1 to STU1")
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 1, 1)
        msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [0])
        self.assertEqual("Error", self.PeakCan.WriteFrameWaitAck(msg))
        self.PeakCan.Logger.Info("Error Ack Frame from STU1 to STU1")
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 0, 1)
        msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_STU1, MY_TOOL_IT_NETWORK_STU1, [0])
        self.assertEqual("Error", self.PeakCan.WriteFrameWaitAck(msg))
        self.PeakCan.Logger.Info("Error Ack Frame from SPU1 to STU1")
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 0, 1)
        msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [0])
        self.assertEqual("Error", self.PeakCan.WriteFrameWaitAck(msg))
        self.PeakCan.Logger.Info("Ack Frame from STU1 to STU1")
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 0, 0)
        msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_STU1, MY_TOOL_IT_NETWORK_STU1, [0])
        self.assertEqual("Error", self.PeakCan.WriteFrameWaitAck(msg))
        self.PeakCan.Logger.Info("Ack Frame from SPU1 to STU1")
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 0, 0)
        msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [0])
        self.assertEqual("Error", self.PeakCan.WriteFrameWaitAck(msg))
        
        #Test that it still works
        self.PeakCan.Logger.Info("Normal Request to STU1")
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 1, 0)
        msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [0])
        self.PeakCan.WriteFrameWaitAckRetries(msg)
        
        
    """
    Connect and disconnect device, check device number after each connect/disconnect to check correctness
    """
    def test0101BlueToothConncectDeviceNr(self): 
        self.PeakCan.Logger.Info("Connect and get Device Number, disconnect and get device number")
        for i in  range(0, 100):
            self.PeakCan.Logger.Info("Loop Run: " + str(i))
            self.PeakCan.Logger.Info("Connect")
            cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
            message=self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothConnect, 0, 0, 0, 0, 0, 0, 0])
            self.PeakCan.WriteFrameWaitAckRetries(message)
            sleep(SystemCommandBlueToothConnectTime)
            self.PeakCan.Logger.Info("Get number of available devices command")
            message=self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothGetNumberAvailableDevices, 0, 0, 0, 0, 0, 0, 0])
            msg=self.PeakCan.WriteFrameWaitAckRetries(message)
            deviceNumbers=int(chr(msg[1][2]))
            self.PeakCan.Logger.Info("Number of available devices: " + str(deviceNumbers))
            self.assertGreater(deviceNumbers, 0)
            self.PeakCan.Logger.Info("Disconnect")
            message=self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothDisconnect, 0, 0, 0, 0, 0, 0, 0])
            self.PeakCan.WriteFrameWaitAckRetries(message)
            self.PeakCan.Logger.Info("Number of available devices command")
            message=self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothGetNumberAvailableDevices, 0, 0, 0, 0, 0, 0, 0])
            msg=self.PeakCan.WriteFrameWaitAckRetries(message)
            deviceNumbers=int(chr(msg[1][2]))
            self.PeakCan.Logger.Info("Number of available devices: " + str(deviceNumbers))
            self.assertEqual(deviceNumbers, 0)

    def BlueToothConnect(self, deviceNr):
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
        message=self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothConnect, 0, 0, 0, 0, 0, 0, 0])
        self.PeakCan.WriteFrameWaitAckRetries(message)
        sleep(SystemCommandBlueToothConnectTime)
        message=self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothDeviceConnect, deviceNr, 0, 0, 0, 0, 0, 0])
        connected = self.PeakCan.WriteFrameWaitAckRetries(message)
        connected = int(connected[1][2])
        self.assertNotEqual(0, connected)
        sleep(SystemCommandBlueToothConnectTime)        
        message=self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothDeviceCheckConnected, 0, 0, 0, 0, 0, 0, 0])
        connectToDevice=self.PeakCan.WriteFrameWaitAckRetries(message)[1][2]
        return int(connectToDevice)
    
    def BlueToothDisconnect(self):
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
        message=self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothDisconnect, 0, 0, 0, 0, 0, 0, 0])
        self.PeakCan.WriteFrameWaitAckRetries(message)
        sleep(SystemCommandBlueToothDisconnectTime)
        message=self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothDeviceCheckConnected, 0, 0, 0, 0, 0, 0, 0])
        connectToDevice=int(self.PeakCan.WriteFrameWaitAckRetries(message)[1][2])
        return connectToDevice
    
    """
    Connect and disconnect to device 100 times
    """
    def test0102BlueToothConnectDisconnectDevice(self):
        self.PeakCan.Logger.Info("Bluetooth connect command and check connected command and disconnect command")
        for i in range(0,100):
            self.PeakCan.Logger.Info("Loop Run: " + str(i))
            self.PeakCan.Logger.Info("Connect to Bluetooth Device")
            connectToDevice=self.BlueToothConnect(0)
            if(0 != connectToDevice):
                self.PeakCan.Logger.Info("Bluetooth STH connected")
            else:
                self.PeakCan.Logger.Error("Bluetooth STH not Connected")
            self.assertNotEqual(0,connectToDevice)
            self.PeakCan.Logger.Info("Disconnect from Bluetooth Device")
            connectToDevice=self.BlueToothDisconnect()
            if(0 != connectToDevice):
                self.PeakCan.Logger.Error("Bluetooth STH connected")
            else:
                self.PeakCan.Logger.Info("Bluetooth STH not Connected")
            self.assertEqual(0,connectToDevice)
       
    def BlueToothNameWrite(self, DeviceNr, Name):
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
        self.assertEqual(1, self.BlueToothConnect(0))
        Payload=[SystemCommandBlueToothSetName1, DeviceNr, 0, 0, 0, 0, 0, 0]
        for i in range(0, 6):
            if(len(Name) <= i):
                break
            Payload[i+2]=ord(Name[i])
        message=self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, Payload)
        self.PeakCan.WriteFrameWaitAckRetries(message)
        Payload=[SystemCommandBlueToothSetName2, DeviceNr, 0, 0, 0, 0, 0, 0]
        for i in range(0, 6):
            if(len(Name) <= i+6):
                break
            Payload[i+2]=ord(Name[i+6])
        message=self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, Payload)
        self.PeakCan.WriteFrameWaitAckRetries(message)
        self.assertEqual(0, self.BlueToothDisconnect())
    
    def BlueToothNameGet(self, DeviceNr):
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
        message=self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothConnect, 0, 0, 0, 0, 0, 0, 0])
        self.PeakCan.WriteFrameWaitAckRetries(message)
        sleep(SystemCommandBlueToothConnectTime)
        message=self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothGetName1, DeviceNr, 0, 0, 0, 0, 0, 0])
        Name=self.PeakCan.WriteFrameWaitAckRetries(message)[1][2:]
        message=self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothGetName2, DeviceNr, 0, 0, 0, 0, 0, 0])
        Name = Name + self.PeakCan.WriteFrameWaitAckRetries(message)[1][2:]     
        self.assertEqual(0, self.BlueToothDisconnect())
        i=0
        while i < len(Name):
            Name[i]=chr(Name[i])
            i+=1
        Name = ''.join(Name)
        return Name  

    """
    Write name and get name (bluetooth command)
    """ 
    def test0103BlueToothName(self):
        for i in range(0,10):
            self.PeakCan.Logger.Info("Bluetooth name command")
            self.PeakCan.Logger.Info("Connect")
            self.PeakCan.Logger.Info("Write Walther0")
            self.BlueToothNameWrite(0, "Walther0")
            self.PeakCan.Logger.Info("Check Walther0")
            Name = self.BlueToothNameGet(0)[0:8]
            self.PeakCan.Logger.Info("Received Name: " + Name)
            self.assertEqual("Walther0",Name)
            self.PeakCan.Logger.Info("Write Marlies0")
            self.BlueToothNameWrite(0, "Marlies0")
            self.PeakCan.Logger.Info("Check Marlies0")
            Name = self.BlueToothNameGet(0)[0:8]
            self.PeakCan.Logger.Info("Received Name: " + Name)
            self.assertEqual("Marlies0" ,Name)
    
    def BlueToothCheckConnect(self, checkConnected):    
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
        message=self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothDeviceCheckConnected, 0, 0, 0, 0, 0, 0, 0])
        connectToDevice = checkConnected+1
        currentTime=time()
        endTime=currentTime+SystemCommandBlueToothConnectTime
        while (currentTime<endTime) and (checkConnected != connectToDevice):
            connectToDevice=int(self.PeakCan.WriteFrameWaitAckRetries(message)[1][2])
            currentTime=time() 
        if(currentTime>=endTime):
            raise("Error")
        return connectToDevice
        
    def BlueToothConnect(self, deviceNr):
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
        message=self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothConnect, 0, 0, 0, 0, 0, 0, 0])
        self.PeakCan.WriteFrameWaitAckRetries(message)
        message=self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothGetNumberAvailableDevices, 0, 0, 0, 0, 0, 0, 0])
        deviceNumbers=0
        currentTime=time()
        endTime= currentTime+SystemCommandBlueToothConnectTime
        while (currentTime < endTime) and (0 == deviceNumbers):
            msg=self.PeakCan.WriteFrameWaitAckRetries(message)
            deviceNumbers=int(chr(msg[1][2]))
            currentTime=time()
        if(currentTime>=endTime):
            raise("Error")
        message=self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothDeviceConnect, deviceNr, 0, 0, 0, 0, 0, 0])
        deviceNumbers=0
        currentTime=time()
        endTime=currentTime+SystemCommandBlueToothConnectTime
        while (currentTime < endTime) and (0 == deviceNumbers):
            msg=self.PeakCan.WriteFrameWaitAckRetries(message)
            deviceNumbers=int(msg[1][2])
            currentTime=time()
        if(currentTime>=endTime):
            raise("Error")
        return self.BlueToothCheckConnect(1)
    
    def BlueToothDisconnect(self):
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
        message=self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothDisconnect, 0, 0, 0, 0, 0, 0, 0])
        self.PeakCan.WriteFrameWaitAckRetries(message)
        return self.BlueToothCheckConnect(0)


    """
    Connect and disconnect to device 20 times, do it without time out, use connection chec    """
    def test0110BlueToothConnectDisconnectDevicePolling(self):
        self.PeakCan.Logger.Info("Bluetooth connect command and check connected command and disconnect command")
        for i in range(0,100):
            self.PeakCan.Logger.Info("Loop Run: " + str(i))
            self.PeakCan.Logger.Info("Connect to Bluetooth Device")
            self.BlueToothConnect(0)
            self.PeakCan.Logger.Info("Disconnect from Bluetooth Device")
            self.BlueToothDisconnect()
            
            
    """
    Send Message to STH without connecting. Assumed result = not receiving anything. This especially tests the routing functionallity.
    """ 
    def test0201MyToolItTestNotConnectedAck(self):
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 1, 0)
        msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [0])
        self.PeakCan.Logger.Info("Write Message")
        lastIndex=self.PeakCan.GetReadArrayIndex()
        self.PeakCan.WriteFrame(msg)
        self.PeakCan.Logger.Info("Wait 2000ms")
        sleep(2)
        self.assertEqual(self.PeakCan.GetReadArrayIndex(), lastIndex)
        
    """
    Send Message to STH with connecting. Assumed result = receive correct ack. This especially tests the routing functionallity.
    """ 
    def test0202MyToolItTestAck(self):
        self.PeakCan.Logger.Info("Connect")
        self.assertEqual(1, self.BlueToothConnect(0))
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 1, 0)
        msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [0])
        self.PeakCan.Logger.Info("Write Message")
        self.PeakCan.WriteFrame(msg)
        self.PeakCan.Logger.Info("Wait 200ms")
        sleep(0.2)
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 0, 0)
        msgAckExpected = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_NETWORK_SPU1, [0])
        self.PeakCan.Logger.Info("Send ID: " + hex(msg.ID) + "; Expected ID: "+hex(msgAckExpected.ID) + "; Received ID: "+hex(self.PeakCan.getReadMessage(-1).ID))
        expectedData=ActiveState()
        expectedData.asbyte=0
        expectedData.b.u2NodeState=2
        expectedData.b.u3NetworkState=6
        self.PeakCan.Logger.Info("Send Data: " + hex(0) + "; Expected Data: " + hex(expectedData.asbyte) + "; Received Data: " + hex(self.PeakCan.getReadMessage(-1).DATA[0]))
        self.assertEqual(hex(msgAckExpected.ID), hex(self.PeakCan.getReadMessage(-1).ID))
        self.assertEqual(hex(expectedData.asbyte), hex(self.PeakCan.getReadMessage(-1).DATA[0]))
        self.PeakCan.WriteFrameWaitAckRetries(msg)
        
        
    """
    Send Message to STH with connecting. Assumed result = receive correct ack. This especially tests the routing functionallity.
    """ 
    def test0203MyToolItTestWrongReceiver(self):
        self.PeakCan.Logger.Info("Connect")
        self.assertEqual(1, self.BlueToothConnect(0))
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 1, 0)
        for i in range(MY_TOOL_IT_NETWORK_STH2,32):
            if (MY_TOOL_IT_NETWORK_STU1 != i):
                msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, i, [0])
                self.assertEqual("Error", self.PeakCan.WriteFrameWaitAck(msg))

        #Test that it still works
        msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [0])
        self.PeakCan.WriteFrameWaitAckRetries(msg)
        
 
    """ Send Mutliple Frames without waiting for an ACK via routing, do ACK after 100 times send flooding to check functionallity"""
    def test0204RoutingMultiSend(self):
        self.PeakCan.Logger.Info("Send command 100 times over STU to STH, check number of write/reads and do ack test at the end; do that for 1000 times")
        self.PeakCan.Logger.Info("Connect")
        self.assertEqual(1, self.BlueToothConnect(0))
        for i in range(1, 1001):
            self.PeakCan.Logger.Info("Received Index: " + str(self.PeakCan.GetReadArrayIndex()))
            self.PeakCan.Logger.Info("Run: " + str(i))
            for j in range(1, 101):
                if( 1== randint(0,1)):
                    cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 1, 0)
                    message=self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [0])                    
                else:
                    cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_STATUS_WORD0, 1, 0)
                    message=self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [0, 0, 0, 0, 0, 0, 0, 0])
                self.PeakCan.WriteFrame(message)
            self.PeakCan.Reset()
            sleep(0.2) 
            self.PeakCan.WriteFrameWaitAckRetries(message)
                
        
     
    """ Send Mutliple Frames with waiting for an ACK with routing: Send->Ack->Send->Ack"""
    def test0205RoutingMultiSendAck(self):
        self.PeakCan.Logger.Info("Send and get ACK for 10000 times AND do it with two messages randomly ")
        self.PeakCan.Logger.Info("Connect")
        self.assertEqual(1, self.BlueToothConnect(0))
        for i in range(1, 10001):
            self.PeakCan.Logger.Info("Received Index: " + str(self.PeakCan.GetReadArrayIndex()))
            self.PeakCan.Logger.Info("Run: " + str(i))
            if( 1== randint(0,1)):
                cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 1, 0)
                msg=self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [0])
            else:
                cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_STATUS_WORD0, 1, 0)
                msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [0, 0, 0, 0, 0, 0, 0, 0])
            self.assertNotEqual("Error", self.PeakCan.WriteFrameWaitAck(msg))
         
         
    """ Send Mutliple Frames with waiting for an ACK: Send->Ack->Send->Ack with routing, this also do a retry, tests the test framework - Multiple Messages"""
    def test0206RoutingMultiSendAckRetries(self):
        self.PeakCan.Logger.Info("Send and get ACK for 10000 times AND do it with two messages randomly ")
        self.PeakCan.Logger.Info("Connect")
        self.assertEqual(1, self.BlueToothConnect(0))
        for i in range(1, 10001):
            self.PeakCan.Logger.Info("Received Index: " + str(self.PeakCan.GetReadArrayIndex()))
            self.PeakCan.Logger.Info("Run: " + str(i))
            if( 1== randint(0,1)):
                cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 1, 0)
                msg=self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [0])
            else:
                cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_STATUS_WORD0, 1, 0)
                msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [0, 0, 0, 0, 0, 0, 0, 0])
            self.assertNotEqual("Error", self.PeakCan.WriteFrameWaitAckRetries(msg))
         
         
        """ Send Mutliple Frames with waiting for an ACK: Send->Ack->Send->Ack with routing, this also do a retry, tests the test framework - Single Message"""
    def test0207RoutingMultiSendSingleAckRetries(self):
        self.PeakCan.Logger.Info("Send and get ACK for 10000 times AND do it with two messages randomly ")
        self.PeakCan.Logger.Info("Connect")
        self.assertEqual(1, self.BlueToothConnect(0))
        for i in range(1, 10001):
            self.PeakCan.Logger.Info("Received Index: " + str(self.PeakCan.GetReadArrayIndex()))
            self.PeakCan.Logger.Info("Run: " + str(i))
            cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_STATUS_WORD0, 1, 0)
            msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [0, 0, 0, 0, 0, 0, 0, 0])
            self.assertNotEqual("Error", self.PeakCan.WriteFrameWaitAckRetries(msg))

         
         
    """
    Send addressing same sender and receiver via Routing
    """ 
    def test0208RoutingSenderReceiver(self):
        self.PeakCan.Logger.Info("Connect to STH and send message with STH1=sender/receiver")
        self.PeakCan.Logger.Info("Connect")
        self.assertEqual(1, self.BlueToothConnect(0))
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 1, 0)
        msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_NETWORK_STH1, [0])
        self.assertEqual("Error", self.PeakCan.WriteFrameWaitAck(msg))
        #Test that it still works
        msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [0])
        self.PeakCan.WriteFrameWaitAckRetries(msg)
         
    """
    "Christmas Tree" packages via routing
    """ 
    def test0209RoutingChristmasTree(self):
        self.PeakCan.Logger.Info("Error Request Frame from STH1 to STH1")
        self.PeakCan.Logger.Info("Connect")
        self.assertEqual(1, self.BlueToothConnect(0))
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 1, 1)
        msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_NETWORK_STH1, [0])
        self.assertEqual("Error", self.PeakCan.WriteFrameWaitAck(msg))
        self.PeakCan.Logger.Info("Error Request Frame from SPU1 to STH1")
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 1, 1)
        msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [0])
        self.assertEqual("Error", self.PeakCan.WriteFrameWaitAck(msg))
        self.PeakCan.Logger.Info("Error Ack Frame from STH1 to STH1")
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 0, 1)
        msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_NETWORK_STH1, [0])
        self.assertEqual("Error", self.PeakCan.WriteFrameWaitAck(msg))
        self.PeakCan.Logger.Info("Error Ack Frame from SPU1 to STH1")
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 0, 1)
        msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [0])
        self.assertEqual("Error", self.PeakCan.WriteFrameWaitAck(msg))
        self.PeakCan.Logger.Info("Ack Frame from STH1 to STH1")
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 0, 0)
        msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_NETWORK_STH1, [0])
        self.assertEqual("Error", self.PeakCan.WriteFrameWaitAck(msg))
        self.PeakCan.Logger.Info("Ack Frame from SPU1 to STH1")
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 0, 0)
        msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [0])
        self.assertEqual("Error", self.PeakCan.WriteFrameWaitAck(msg))
         
        #Test that it still works
        self.PeakCan.Logger.Info("Normal Request to STH1")
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, 1, 0)
        msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [0])
        self.PeakCan.WriteFrameWaitAckRetries(msg)       
        
 
if __name__ == "__main__":
    print(sys.version)    
    if not os.path.exists(os.path.dirname(log_location+log_file)):
        os.makedirs(os.path.dirname(log_location+log_file))
    f = open(log_location+log_file, "w")
    loader = unittest.TestLoader()
    start_dir = 'path/to/your/test/files'
    suite = loader.discover(start_dir)
    runner = unittest.TextTestRunner(f)
    unittest.main(suite)
    f.close()
