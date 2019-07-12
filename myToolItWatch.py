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
from MyToolItSth import *
import getopt

BlueToothDeviceListAquireTime = 5
BlueToothNoneDev = 255

StreamingStopTimeMs = 200


def to8bitSigned(num): 
    mask7 = 128  # Check 8th bit ~ 2^8
    mask2s = 127  # Keep first 7 bits
    if (mask7 & num == 128):  # Check Sign (8th bit)
        num = -((~int(num) + 1) & mask2s)  # 2's complement
    return num


def messageValueGet(m):        
    Acc = ((0xFF & m[1]) << 8) | (0xFF & m[0])
    return Acc  


class aquAcc():

    def __init__(self, log_location, iAcc1, iAcc2, iAcc3, dev, prescaler, aquistionTime, oversampling, runtime):
        self.Error = False
        self.connected = 0
        self.log_location = log_location
        self.iAcc1 = int(iAcc1)
        self.iAcc2 = int(iAcc2)
        self.iAcc3 = int(iAcc3)
        self.DataFormat = DataSetsNone
        self.dev = int(dev)
        self.prescaler = prescaler
        self.aquistionTime = aquistionTime
        self.oversampling = oversampling
        self.runTime = int(runtime)   
        self.KeyBoadInterrupt = False    
        self.Close = True     
        
    def __exit__(self):
        self._streamingStop()
        self.PeakCan.readThreadStart()
        self._BlueToothStatistics()
        ReceiveFailCounter = self._RoutingInformation()
        self._statusWords()
        self.PeakCan.Logger.Info("Test Time End Time Stamp")
        self.BlueToothDisconnectPolling()
        if(0 < ReceiveFailCounter):
            self.Error = True
        if(False != self.Error):
            self.PeakCan.Logger.Info("Error")
            print("Error")
        else:
            self.PeakCan.Logger.Info("Fin")
        self.PeakCan.__exit__()  
        if(False != self.Error):
            raise
        print("Fin")

    def reset(self):
        if False == self.KeyBoadInterrupt:
            try:
                self.PeakCan = PeakCanFd(PCAN_BAUD_1M, self.log_location)        
                cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_RESET, 1, 0)
                self.PeakCan.WriteFrameWaitAckRetries(self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, []))
                sleep(1)  
                if 0 == self.PeakCan.GetReadArrayIndex():  
                    self.KeyBoadInterrupt = True
                else:
                    self.Close = False
            except KeyboardInterrupt:
                self.KeyBoadInterrupt = True
                          
        
    def connect(self):
        if False == self.KeyBoadInterrupt:
            try:
                if BlueToothNoneDev == self.dev:
                    self.connected = self.BlueToothConnect()
                else:
                    self.connected = self.BlueToothConnectPolling(self.dev)
            except KeyboardInterrupt:
                self.KeyBoadInterrupt = True
                self.__exit__()
                
    def execute(self):  
        if False == self.KeyBoadInterrupt:
            try:
                if 1 == self.connected:
                    self.configStreamingAcc(self.prescaler, self.aquistionTime, self.oversampling)    
                    self.PeakCan.readThreadStop()            
                    print("Start")
                    self.PeakCan.Logger.Info("Start")
                    self.GetStreamingAccData()
                else:
                    print("Device not allocable")    
                    self.PeakCan.Logger.Error("Device not allocable")     
            except KeyboardInterrupt:
                self.KeyBoadInterrupt = True
                self.__exit__()
                
    def close(self):
        if False != self.Close:
            self.__exit__()          
                
    def BlueToothConnect(self):
        devList = self.getBlueToothDeviceList()
        print("Please choose device to connect via pressing number 0 - 8")
        for dev in devList:
            print(str(dev[1]) + ": " + str(dev[0]))
            self.PeakCan.Logger.Info("Found Device" + str(dev[1]) + ": " + str(dev[0]))
        dev = 255
        try:
            dev = int(input('Input:'))            
        except ValueError:
            print("Not a number") 
        if 255 != dev:
            dev = self.BlueToothConnectPolling(dev)
        return dev
    
    def getBlueToothDeviceList(self): 
        availableDevices = self.BlueToothDeviceNrList()
        nameList = []
        for dev in range(availableDevices):
            nameList.append([dev, self.BlueToothNameGet(dev)])
        return nameList   

    def BlueToothDeviceNrList(self):
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
        message = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothConnect, 0, 0, 0, 0, 0, 0, 0])
        self.PeakCan.WriteFrameWaitAckRetries(message)
        message = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothGetNumberAvailableDevices, 0, 0, 0, 0, 0, 0, 0])
        deviceNumbers = 0
        currentTime = time()
        endTime = currentTime + BlueToothDeviceListAquireTime
        while(currentTime < endTime):
            msg = self.PeakCan.WriteFrameWaitAckRetries(message)
            deviceNumbers = int(chr(msg[1][2]))
            currentTime = time()
        return deviceNumbers    
            
    def BlueToothNameGet(self, DeviceNr):
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
        message = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothConnect, 0, 0, 0, 0, 0, 0, 0])
        self.PeakCan.WriteFrameWaitAckRetries(message)
        sleep(SystemCommandBlueToothConnectTime)
        message = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothGetName1, DeviceNr, 0, 0, 0, 0, 0, 0])
        Name = self.PeakCan.WriteFrameWaitAckRetries(message)[1][2:]
        message = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothGetName2, DeviceNr, 0, 0, 0, 0, 0, 0])
        Name = Name + self.PeakCan.WriteFrameWaitAckRetries(message)[1][2:]     
        i = 0
        while i < len(Name):
            Name[i] = chr(Name[i])
            i += 1
        Name = ''.join(Name)
        return Name 
    
    def BlueToothConnectPolling(self, deviceNr):
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
        message = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothConnect, 0, 0, 0, 0, 0, 0, 0])
        self.PeakCan.WriteFrameWaitAckRetries(message)
        message = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothGetNumberAvailableDevices, 0, 0, 0, 0, 0, 0, 0])
        deviceNumbers = 0
        currentTime = time()
        endTime = currentTime + SystemCommandBlueToothConnectTime
        while (currentTime < endTime) and (0 == deviceNumbers):
            msg = self.PeakCan.WriteFrameWaitAckRetries(message)
            deviceNumbers = int(msg[1][2])
            currentTime = time()
        if(currentTime >= endTime):
            raise("Error")
        message = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothDeviceConnect, deviceNr, 0, 0, 0, 0, 0, 0])
        deviceNumbers = 0
        currentTime = time()
        endTime = currentTime + SystemCommandBlueToothConnectTime
        while (currentTime < endTime) and (0 == deviceNumbers):
            msg = self.PeakCan.WriteFrameWaitAckRetries(message)
            deviceNumbers = msg[1][2]
            currentTime = time()
        if(currentTime >= endTime):
            return 0
        else:
            return self.BlueToothCheckConnectPoll(1)    

    def BlueToothDisconnectPolling(self):
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
        message = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothDisconnect, 0, 0, 0, 0, 0, 0, 0])
        self.PeakCan.WriteFrameWaitAckRetries(message)
        return self.BlueToothCheckConnectPoll(0)

    def BlueToothCheckConnectPoll(self, checkConnected):    
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
        message = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STU1, [SystemCommandBlueToothDeviceCheckConnected, 0, 0, 0, 0, 0, 0, 0])
        connectToDevice = checkConnected + 1
        currentTime = time()
        endTime = currentTime + SystemCommandBlueToothConnectTimeIdle
        while (currentTime < endTime) and (checkConnected != connectToDevice):
            connectToDevice = self.PeakCan.WriteFrameWaitAckRetries(message)[1][2]
            currentTime = time() 
        if(currentTime >= endTime):
            raise("Error")
        return connectToDevice

    def _statusWords(self):
        ErrorWord = SthErrorWord()
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_STATUS_WORD0, 1, 0)
        msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [])
        psw0 = self.PeakCan.WriteFrameWaitAckRetries(msg)[1]
        psw0 = self.PeakCan.AsciiStringWordBigEndian(psw0[0:4])
        self.PeakCan.Logger.Info("Status Word: " + hex(psw0))
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_STATUS_WORD1, 1, 0)
        msg = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [])
        psw1 = self.PeakCan.WriteFrameWaitAckRetries(msg)[1]
        psw1 = self.PeakCan.AsciiStringWordBigEndian(psw1[0:4])
        ErrorWord.asword = psw1
        if True == ErrorWord.b.bAdcOverRun:
            print("Error Word: " + hex(psw1))
            self.Error = True
        self.PeakCan.Logger.Info("Error Word: " + hex(psw1))
        
    def _streamingStop(self):
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_STREAMING, MY_TOOL_IT_STREAMING_VOLTAGE, 1, 0)
        message = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [(1 << 7)])
        i = 0
        
        while(i < 5):            
            self.PeakCan.WriteFrame(message) 
            timeEnd = self.PeakCan.getTimeMs() + StreamingStopTimeMs
            while(self.PeakCan.getTimeMs() < timeEnd):
                self.ReadMessage() 
            i += 1
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_STREAMING, MY_TOOL_IT_STREAMING_ACCELERATION, 1, 0)
        message = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [(1 << 7)])
        i = 0
        while(i < 5):
            self.PeakCan.WriteFrame(message)
            timeEnd = self.PeakCan.getTimeMs() + StreamingStopTimeMs
            while(self.PeakCan.getTimeMs() < timeEnd):
                self.ReadMessage() 
            i += 1
        sleep(1)  # Waiting for remaining returns
        return 1
    
    def _BlueToothCmd(self, subscriber, subCmd):
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
        payload = [subCmd, 0, 0, 0, 0, 0, 0, 0]
        message = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, subscriber, payload)
        ack = self.PeakCan.WriteFrameWaitAckRetries(message)[1][2:]
        ack = self.PeakCan.AsciiStringWordLittleEndian(ack)
        return ack
    
    def _BlueToothRssi(self, subscriber):
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
        payload = [SystemCommandBlueToothRssi, 0, 0, 0, 0, 0, 0, 0]
        message = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, subscriber, payload)
        ack = self.PeakCan.WriteFrameWaitAckRetries(message)[1][2]
        ack = to8bitSigned(ack)
        return ack
       
    def _BlueToothStatistics(self):
        SendCounter = self._BlueToothCmd(MY_TOOL_IT_NETWORK_STH1, SystemCommandBlueToothSendCounter)
        self.PeakCan.Logger.Info("BlueTooth Send Counter(STH1): " + str(SendCounter))
        Rssi = self._BlueToothRssi(MY_TOOL_IT_NETWORK_STH1)
        self.PeakCan.Logger.Info("BlueTooth Rssi(STH1): " + str(Rssi) + "dBm")
        SendCounter = self._BlueToothCmd(MY_TOOL_IT_NETWORK_STU1, SystemCommandBlueToothSendCounter)
        self.PeakCan.Logger.Info("BlueTooth Send Counter(STU1): " + str(SendCounter))
        ReceiveCounter = self._BlueToothCmd(MY_TOOL_IT_NETWORK_STU1, SystemCommandBlueToothReceiveCounter)
        self.PeakCan.Logger.Info("BlueTooth Receive Counter(STU1): " + str(ReceiveCounter))
        Rssi = self._BlueToothRssi(MY_TOOL_IT_NETWORK_STU1)
        self.PeakCan.Logger.Info("BlueTooth Rssi(STU): " + str(Rssi) + "dBm")
    
    def _RoutingInformationCmd(self, subscriber, subCmd, port):
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ROUTING, 1, 0)
        payload = [subCmd, port, 0, 0, 0, 0, 0, 0]
        message = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, subscriber, payload)
        ack = self.PeakCan.WriteFrameWaitAckRetries(message)[1][2:]
        ack = self.PeakCan.AsciiStringWordLittleEndian(ack)
        return ack
        
    def _RoutingInformationSthSend(self):
        SendCounter = self._RoutingInformationCmd(MY_TOOL_IT_NETWORK_STH1, SystemCommandRoutingSendCounter, MY_TOOL_IT_NETWORK_STU1)
        self.PeakCan.Logger.Info("STH1 - Send Counter(Port STU1): " + str(SendCounter))
        SendCounter = self._RoutingInformationCmd(MY_TOOL_IT_NETWORK_STH1, SystemCommandRoutingSendFailCounter, MY_TOOL_IT_NETWORK_STU1)
        self.PeakCan.Logger.Info("STH1 - Send Fail Counter(Port STU1): " + str(SendCounter))
        SendCounter = self._RoutingInformationCmd(MY_TOOL_IT_NETWORK_STH1, SystemCommandRoutingSendLowLevelByteCounter, MY_TOOL_IT_NETWORK_STU1)
        self.PeakCan.Logger.Info("STH1 - Send Byte Counter(Port STU1): " + str(SendCounter))

    def _RoutingInformationSthReceive(self):
        ReceiveCounter = self._RoutingInformationCmd(MY_TOOL_IT_NETWORK_STH1, SystemCommandRoutingReceiveCounter, MY_TOOL_IT_NETWORK_STU1)
        self.PeakCan.Logger.Info("STH1 - Receive Counter(Port STU1): " + str(ReceiveCounter))       
        ReceiveFailCounter = self._RoutingInformationCmd(MY_TOOL_IT_NETWORK_STH1, SystemCommandRoutingReceiveFailCounter, MY_TOOL_IT_NETWORK_STU1)
        self.PeakCan.Logger.Info("STH1 - Receive Fail Counter(Port STU1): " + str(ReceiveFailCounter))           
        ReceiveCounter = self._RoutingInformationCmd(MY_TOOL_IT_NETWORK_STH1, SystemCommandRoutingReceiveLowLevelByteCounter, MY_TOOL_IT_NETWORK_STU1)
        self.PeakCan.Logger.Info("STH1 - Receive Byte Counter(Port STU1): " + str(ReceiveCounter))    
        return ReceiveFailCounter    
                
    def _RoutingInformationSth(self):
        self._RoutingInformationSthSend()
        ReceiveFailCounter = self._RoutingInformationSthReceive()
        return ReceiveFailCounter
    
    def _RoutingInformationStuPortSpuSend(self):
        SendCounter = self._RoutingInformationCmd(MY_TOOL_IT_NETWORK_STU1, SystemCommandRoutingSendCounter, MY_TOOL_IT_NETWORK_SPU1)
        self.PeakCan.Logger.Info("STU1 - Send Counter(Port SPU1): " + str(SendCounter))
        SendCounter = self._RoutingInformationCmd(MY_TOOL_IT_NETWORK_STU1, SystemCommandRoutingSendFailCounter, MY_TOOL_IT_NETWORK_SPU1)
        self.PeakCan.Logger.Info("STU1 - Send Fail Counter(Port SPU1): " + str(SendCounter))
        SendCounter = self._RoutingInformationCmd(MY_TOOL_IT_NETWORK_STU1, SystemCommandRoutingSendLowLevelByteCounter, MY_TOOL_IT_NETWORK_SPU1)
        self.PeakCan.Logger.Info("STU1 - Send Byte Counter(Port SPU1): " + str(SendCounter))
     
    def _RoutingInformationStuPortSpuReceive(self):   
        ReceiveCounter = self._RoutingInformationCmd(MY_TOOL_IT_NETWORK_STU1, SystemCommandRoutingReceiveCounter, MY_TOOL_IT_NETWORK_SPU1)
        self.PeakCan.Logger.Info("STU1 - Receive Counter(Port SPU1): " + str(ReceiveCounter))
        ReceiveFailCounter = self._RoutingInformationCmd(MY_TOOL_IT_NETWORK_STU1, SystemCommandRoutingReceiveFailCounter, MY_TOOL_IT_NETWORK_SPU1)
        self.PeakCan.Logger.Info("STU1 - Receive Fail Counter(Port SPU1): " + str(ReceiveFailCounter))
        ReceiveCounter = self._RoutingInformationCmd(MY_TOOL_IT_NETWORK_STU1, SystemCommandRoutingReceiveLowLevelByteCounter, MY_TOOL_IT_NETWORK_SPU1)
        self.PeakCan.Logger.Info("STU1 - Receive Byte Counter(Port SPU1): " + str(ReceiveCounter))        
        return ReceiveFailCounter
        
    def _RoutingInformationStuPortSpu(self):
        self._RoutingInformationStuPortSpuSend()
        ReceiveFailCounter = self._RoutingInformationStuPortSpuReceive()
        return ReceiveFailCounter

    def _RoutingInformationStuPortSthSend(self):
        SendCounter = self._RoutingInformationCmd(MY_TOOL_IT_NETWORK_STU1, SystemCommandRoutingSendCounter, MY_TOOL_IT_NETWORK_STH1)
        self.PeakCan.Logger.Info("STU1 - Send Counter(Port STH1): " + str(SendCounter))
        SendCounter = self._RoutingInformationCmd(MY_TOOL_IT_NETWORK_STU1, SystemCommandRoutingSendFailCounter, MY_TOOL_IT_NETWORK_STH1)
        self.PeakCan.Logger.Info("STU1 - Send Fail Counter(Port STH1): " + str(SendCounter))       
        SendCounter = self._RoutingInformationCmd(MY_TOOL_IT_NETWORK_STU1, SystemCommandRoutingSendLowLevelByteCounter, MY_TOOL_IT_NETWORK_STH1)
        self.PeakCan.Logger.Info("STU1 - Send Byte Counter(Port STH1): " + str(SendCounter))
    
    def _RoutingInformationStuPortSthReceive(self):
        ReceiveCounter = self._RoutingInformationCmd(MY_TOOL_IT_NETWORK_STU1, SystemCommandRoutingReceiveCounter, MY_TOOL_IT_NETWORK_STH1)
        self.PeakCan.Logger.Info("STU1 - Receive Counter(Port STH1): " + str(ReceiveCounter))
        ReceiveFailCounter = self._RoutingInformationCmd(MY_TOOL_IT_NETWORK_STU1, SystemCommandRoutingReceiveFailCounter, MY_TOOL_IT_NETWORK_STH1)
        self.PeakCan.Logger.Info("STU1 - Receive Fail Counter(Port STH1): " + str(ReceiveFailCounter))
        ReceiveCounter = self._RoutingInformationCmd(MY_TOOL_IT_NETWORK_STU1, SystemCommandRoutingReceiveLowLevelByteCounter, MY_TOOL_IT_NETWORK_STH1)
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

    def configStreamingAcc(self, prescaler, aquistionTime, oversampling):
        self.PeakCan.Logger.Info("Config")
        byte1 = 1 << 7  # Set Sampling Rate
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_CONFIGURATION, MY_TOOL_IT_CONFIGURATION_ACCELERATION_SAMPLING_RATE, 1, 0)
        message = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [byte1, prescaler, aquistionTime, oversampling, 0, 0, 0, 0])
        self.PeakCan.Logger.Info("Config ADC with Prescaler/AquistionTime/OverSampling/" + str(prescaler) + "/" + str(aquistionTime) + "/" + str(oversampling))
        self.PeakCan.WriteFrameWaitAckRetries(message)        
    
    def GetStreamingAccDataProcess(self, endTime):
        try:
            while(self.PeakCan.getTimeMs() < endTime):
                ack = self.ReadMessage()
                if(None != ack):
                    if(self.AckExpected.ID != ack.ID):
                        self.PeakCan.Logger.Error("CanId Error: " + str(ack.ID))
                    elif(self.AckExpected.DATA[0] != ack.DATA[0]):
                        self.PeakCan.Logger.Error("Wrong Subheader-Format(Acceleration Format): " + str(ack.ID))
                    else:
                        self.GetMessageAcc(ack.DATA)       
        except KeyboardInterrupt:
            self.KeyBoadInterrupt = True
            print("Data acquisition determined")
            self.__exit__()     
        finally:
            self.__exit__()               
                    
                              
    def GetStreamingAccData(self):
        accFormat = AtvcFormat()
        accFormat.asbyte = 0
        accFormat.b.bStreaming = 1
        accFormat.b.bNumber1 = int(self.iAcc1)
        accFormat.b.bNumber2 = int(self.iAcc2)
        accFormat.b.bNumber3 = int(self.iAcc3)
                
        number = 0
        if(False != self.iAcc1):
            number += 1
        if(False != self.iAcc2):
            number += 1
        if(False != self.iAcc3):
            number += 1

        if((3 == number) or (2 == number)):
            self.DataFormat = DataSets1
            accFormat.b.u3DataSets = DataSets1
        elif(1 == number):
            self.DataFormat = DataSets3
            accFormat.b.u3DataSets = DataSets3
        else:
            self.DataFormat = DataSetsNone
            accFormat.b.u3DataSets = DataSetsNone

        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_STREAMING, MY_TOOL_IT_STREAMING_ACCELERATION, 0, 0)
        self.AckExpected = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_STH1, MY_TOOL_IT_NETWORK_SPU1, [accFormat.asbyte])
        cmd = self.PeakCan.CanCmd(MY_TOOL_IT_BLOCK_STREAMING, MY_TOOL_IT_STREAMING_ACCELERATION, 1, 0)
        message = self.PeakCan.CanMessage20(cmd, MY_TOOL_IT_NETWORK_SPU1, MY_TOOL_IT_NETWORK_STH1, [accFormat.asbyte])
        self.PeakCan.Logger.Info("MsgId/Subpayload: " + hex(message.ID) + "/" + hex(accFormat.asbyte))
        ack = None
        endTime = self.PeakCan.getTimeMs() + 4000
        while (None == ack) and (self.PeakCan.getTimeMs() < endTime):
            self.PeakCan.WriteFrame(message)
            readEndTime = self.PeakCan.getTimeMs() + 500
            while((None == ack) and  (self.PeakCan.getTimeMs() < readEndTime)):
                ack = self.ReadMessage()
        
        currentTime = self.PeakCan.getTimeMs()
        if None == ack:
            self.PeakCan.Logger.Error("No Ack received from Device: " + str(self.dev))
            endTime = currentTime
        elif(0 == self.runTime):
            endTime = currentTime + (1 << 32)
        else:
            endTime = currentTime + self.runTime * 1000
        self.GetStreamingAccDataProcess(endTime)

                
    def GetMessageAccSingle(self, prefix, canData):       
        ackMsg = ("MsgCounter: " + str(canData[1]) + "; ") + prefix + " "
        ackMsg += str(messageValueGet(canData[2:4]))
        ackMsg += "; "
        self.PeakCan.Logger.Info(ackMsg)
        ackMsg = ("MsgCounter: " + str(canData[1]) + "; ") + prefix + " "
        ackMsg += str(messageValueGet(canData[4:6]))
        ackMsg += "; "
        self.PeakCan.Logger.Info(ackMsg)
        ackMsg = ("MsgCounter: " + str(canData[1]) + "; ") + prefix + " "
        ackMsg += str(messageValueGet(canData[6:8]))
        ackMsg += "; "
        self.PeakCan.Logger.Info(ackMsg)   
        
    def GetMessageAccDouble(self, prefix1, prefix2, canData):
        ackMsg = ("MsgCounter: " + str(canData[1]) + "; ") + prefix1 + " "
        ackMsg += str(messageValueGet(canData[2:4]))
        ackMsg += "; "
        ackMsg += prefix2
        ackMsg += " "
        ackMsg += str(messageValueGet(canData[4:6]))
        ackMsg += "; "
        self.PeakCan.Logger.Info(ackMsg)       

    def GetMessageAccTripple(self, prefix1, prefix2, prefix3, canData):
        ackMsg = ("MsgCounter: " + str(canData[1]) + "; ")
        ackMsg += prefix1
        ackMsg += " "
        ackMsg += str(messageValueGet(canData[2:4]))
        ackMsg += "; "
        ackMsg += prefix2
        ackMsg += " "
        ackMsg += str(messageValueGet(canData[4:6]))
        ackMsg += "; "
        ackMsg += prefix3
        ackMsg += " "
        ackMsg += str(messageValueGet(canData[6:8]))
        ackMsg += "; "
        self.PeakCan.Logger.Info(ackMsg)                        
        
    def GetMessageAcc(self, canData):
        if self.DataFormat == DataSets1:
            if (0 != self.iAcc1) and (0 != self.iAcc2) and (0 == self.iAcc3):
                self.GetMessageAccDouble("AccX", "AccY", canData)
            elif (0 != self.iAcc1) and (0 == self.iAcc2) and (0 != self.iAcc3):
                self.GetMessageAccDouble("AccX", "AccZ", canData)
            elif (0 == self.iAcc1) and (0 != self.iAcc2) and (0 != self.iAcc3):
                self.GetMessageAccDouble("AccY", "AccZ", canData) 
            else:
                self.GetMessageAccTripple("AccX", "AccY", "AccZ", canData)   
        elif self.DataFormat == DataSets3:
            if 0 != self.iAcc1:
                self.GetMessageAccSingle("AccX", canData)               
            elif 0 != self.iAcc2:
                self.GetMessageAccSingle("AccY", canData)               
            elif 0 != self.iAcc3:
                self.GetMessageAccSingle("AccZ", canData)       
        else:               
            self.PeakCan.Logger.Error("Wrong Ack format")

            
    def ReadMessage(self):
        readMessage = None
        result = self.PeakCan.ReadMessage()
        if result[0] == PCAN_ERROR_OK:
            readMessage = result[1]
        elif result[0] == PCAN_ERROR_QOVERRUN:
            self.PeakCan.Logger.Error("RxOverRun")
            raise
        return readMessage

        
if __name__ == "__main__":
    # (self, log_location, bAcc1, bAcc2, bAcc3, dev, prescaler, aquistionTime, oversampling, runtime):
    acquireData = aquAcc(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], \
             sys.argv[5], sys.argv[6], sys.argv[7], sys.argv[8], sys.argv[9])
    acquireData.reset()
    acquireData.connect()
    acquireData.execute()
    acquireData.close()
        
