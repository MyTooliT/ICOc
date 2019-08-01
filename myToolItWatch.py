import sys
import os

import xml.etree.ElementTree as ET
from PCANBasic import *   
from PeakCanFd import *
from MyToolItNetworkNumbers import *
from MyToolItCommands import *
from time import sleep, time
from random import randint
from MyToolItSth import *
from datetime import datetime
import getopt
import xlsxwriter
import openpyxl

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


# def __init__(self, log_location, iAcc1, iAcc2, iAcc3, dev, prescaler, aquistionTime, oversampling, runtime):
class aquAcc():

    def __init__(self):
        self.KeyBoadInterrupt = False  
        self.Error = False     
        self.Close = True   
        self.bConnected = False
        self.iStartTime = time()
        self.vLogSet(self, "../Logs/STH/", "AccX12k5", None)
        self.vSheetFileSet(None, None)
        self.vAccSet(1, 0, 0, DataSets[3])
        self.vVoltageSet(1, 0, 0, DataSets[3])
        self.vDeviceNameSet(TestConfig["DevName"])
        self.vAdcConfig(2, 3, 64, "VDD")
        self.vDisplayTime(10)  
        self.vRunTime(10, 0)
        self.PeakCan = PeakCanFd.PeakCanFd(PeakCanFd.PCAN_BAUD_1M, self.logName, self.logNameError, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"])
            
    def __exit__(self):
        self.PeakCan.ReadArrayReset()
        if False != self.bConnected:
            self._BlueToothStatistics()
            ReceiveFailCounter = self._RoutingInformation()
            self._statusWords()
            self.PeakCan.Disconnect()
        self.PeakCan.Logger.Info("End Time Stamp")
        
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


#Setter Methods
    def vConfigSet(self, fileName, configName):
        self.sConfigFile = fileName
        self.sConfig = configName
    
    def vLogSet(self, sLogLocation, sLogFileName, iLogCount):
        self.logLocation = sLogLocation
        self.logName = sLogFileName
        self.logNameError =  self.logName
        self.logNameError.rreplace('.', "Error.txt")
        self.logNameCount = iLogCount
        
    def vSheetFileSet(self, sSheetFile, sConfig):
        self.sSheetFile = sSheetFile
        self.sConfig = sConfig
        
    def vAccSet(self, iX, iY, iZ, dataSets):
        self.bAccX = int(bool(0 < iX))
        self.bAccY = int(bool(0 < iY))
        self.bAccZ = int(bool(0 < iZ))
        if dataSets in DataSets:
            self.tAccDataFormat = dataSets
        else:
            number = 0
            if(False != self.bAccX):
                number += 1
            if(False != self.bAccY):
                number += 1
            if(False != self.bAccZ):
                number += 1
            while not dataSets in DataSets:
                    dataSets += 1
            self.tAccDataFormat = dataSets
        
    def vVoltageSet(self, iX, iY, iZ, dataSets):
        self.iVoltageX = int(bool(0 < iX))
        self.iVoltageY = int(bool(0 < iY))
        self.iVoltageZ = int(bool(0 < iZ))
        if dataSets in DataSets:
            self.tVoltageDataFormat = dataSets
        else:
            number = 0
            if(False != self.bAccX):
                number += 1
            if(False != self.bAccY):
                number += 1
            if(False != self.bAccZ):
                number += 1
            while not dataSets in DataSets:
                    dataSets += 1
            self.tVoltageDataFormat = dataSets
         
    def vDeviceNameSet(self, sDevName):
        if 8 < len(sDevName):
            sDevName = sDevName[:8]
        self.sDevName = sDevName
        self.iDevNr = None
        
    def vAdcConfig(self, iPrescaler, iAquistionTime, iOversampling, sAdcRef):
        if Prescaler["Min"] > iPrescaler:
            iPrescaler = Prescaler["Min"]
        elif Prescaler["Max"] < iPrescaler:
            iPrescaler = Prescaler["Max"]    
        iAcquisitionTime = AdcAcquisitionTimeReverse[iAquistionTime]
        iOversampling = AdcOverSamplingRateReverse[iOversampling]
        self.samplingRate = int(calcSamplingRate(iPrescaler, iAcquisitionTime, iOversampling) + 0.5)
        self.iPrescaler = iPrescaler
        self.sAquistionTime = iAcquisitionTime
        self.sOversampling = iOversampling
        self.sAdcRef = sAdcRef
        
    def vDisplayTime(self, displayTime):
        self.iDisplayTime = int(displayTime) 
        
    def vRunTime(self, runTime, intervalTime):
        self.iIntervalTime = intervalTime
        self.iRunTime = runTime
    
    def vVersion(self, major, minor, build):
        if 2 <= major and 1 <= minor:
            self.Major = major
            self.Minor = minor
            self.Build = build
            
    def sDateClock(self):
        DataClockTimeStamp = datetime.fromtimestamp(self.iStartTime).strftime('%Y-%m-%d_%H:%M:%S')
        return DataClockTimeStamp
    
    def sLogName(self):
        if None != self.logNameCount:
            logName = self.logName + "_" + self.sDateClock() + "_" + str(self.logNameCount).format(16) + ".txt"
            self.logNameCount += 1
        else:
            logName = self.logName + "_" + self.sDateClock() + ".txt"
        return logName    
    
    def reset(self):
        if False == self.KeyBoadInterrupt:
            try:
                self.PeakCan.cmdReset(MyToolItNetworkNr["STU1"])
                sleep(1)  
                if 0 == self.PeakCan.GetReadArrayIndex():  
                    self.KeyBoadInterrupt = True
                else:
                    self.Close = False
            except KeyboardInterrupt:
                self.KeyBoadInterrupt = True

    def BlueToothConnect(self):
        try:
            self.iDevNr = int(input('Input:'))  
            try:
                self.PeakCan.BlueToothConnect(MyToolItNetworkNr["STU1"], self.iDevNr)          
            except KeyboardInterrupt:
                self.KeyBoadInterrupt = True
        except ValueError:
            print("Not a number") 
    
    def getBlueToothDeviceList(self): 
        self.PeakCan.BlueToothConnectConnect(MyToolItNetworkNr["STH1"])
        deviceNumbers = 0
        endTime = time() + BlueToothDeviceListAquireTime
        while(time() < endTime):
            deviceNumbers = self.PeakCan.BlueToothConnectTotalScannedDeviceNr(MyToolItNetworkNr["STH1"])
        nameList = []
        for dev in range(deviceNumbers):
            nameList.append([dev, self.PeakCan.BlueToothNameGet(dev)])
        return nameList   
                
    def BlueToothConnectName(self):
        if False == self.KeyBoadInterrupt:
            try:
                self.PeakCan.BlueToothConnectPollingName(MyToolItNetworkNr["STU1"], self.sDevName)
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
   

    
    def GetStreamingAccDataProcess(self, endTime):
        try:
            while(self.PeakCan.getTimeMs() < endTime):
                ack = self.ReadMessage()
                if(None != ack):
                    if(self.AckExpected.ID != ack["CanMsg"].ID):
                        self.PeakCan.Logger.Error("CanId Error: " + str(ack["CanMsg"].ID))
                    elif(self.AckExpected.DATA[0] != ack["CanMsg"].DATA[0]):
                        self.PeakCan.Logger.Error("Wrong Subheader-Format(Acceleration Format): " + str(ack["CanMsg"].ID))
                    else:
                        self.GetMessageAcc(ack)       
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
        accFormat.b.bNumber1 = self.bAccX
        accFormat.b.bNumber2 = self.bAccY
        accFormat.b.bNumber3 = self.bAccZ
        accFormat.b.u3DataSets = self.tAccDataFormat
        cmd = self.PeakCan.CanCmd(MyToolItBlock["Streaming"], MyToolItStreaming["Acceleration"], 0, 0)
        self.AckExpected = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["STH1"], MyToolItNetworkNr["SPU1"], [accFormat.asbyte])
        cmd = self.PeakCan.CanCmd(MyToolItBlock["Streaming"], MyToolItStreaming["Acceleration"], 1, 0)
        message = self.PeakCan.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [accFormat.asbyte])
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
                
    def GetMessageAccSingle(self, prefix, canMsg):       
        canData = canMsg["CanMsg"].DATA
        canTimeStamp = canMsg["PeakCanTime"]
        canTimeStamp = round(canTimeStamp, 3)
        ackMsg = ("MsgCounter: " + str(canData[1]) + "; ")
        ackMsg += (format(canTimeStamp, '0.3f') + "; ")
        ackMsg += (prefix + " ")
        ackMsg += str(messageValueGet(canData[2:4]))
        ackMsg += "; "
        self.PeakCan.Logger.Info(ackMsg)
        ackMsg = ("MsgCounter: " + str(canData[1]) + "; ")
        ackMsg += (format(canTimeStamp, '0.3f') + "; ")
        ackMsg += (prefix + " ")
        ackMsg += str(messageValueGet(canData[4:6]))
        ackMsg += "; "
        self.PeakCan.Logger.Info(ackMsg)
        ackMsg = ("MsgCounter: " + str(canData[1]) + "; ")
        ackMsg += (format(canTimeStamp, '0.3f') + "; ")
        ackMsg += (prefix + " ")
        ackMsg += str(messageValueGet(canData[6:8]))
        ackMsg += "; "
        self.PeakCan.Logger.Info(ackMsg)   
        
    def GetMessageAccDouble(self, prefix1, prefix2, canMsg):
        canData = canMsg["CanMsg"].DATA
        canTimeStamp = canMsg["PeakCanTime"]
        canTimeStamp = round(canTimeStamp, 3)
        ackMsg = ("MsgCounter: " + str(canData[1]) + "; ")
        ackMsg += (format(canTimeStamp, '0.3f') + "; ")
        ackMsg += (prefix1 + " ")
        ackMsg += str(messageValueGet(canData[2:4]))
        ackMsg += "; "
        ackMsg += prefix2
        ackMsg += " "
        ackMsg += str(messageValueGet(canData[4:6]))
        ackMsg += "; "
        self.PeakCan.Logger.Info(ackMsg)       

    def GetMessageAccTripple(self, prefix1, prefix2, prefix3, canMsg):
        canData = canMsg["CanMsg"].DATA
        canTimeStamp = canMsg["PeakCanTime"]
        canTimeStamp = round(canTimeStamp, 3)
        ackMsg = ("MsgCounter: " + str(canData[1]) + "; ")
        ackMsg += (format(canTimeStamp, '0.3f') + "; ")
        ackMsg += (prefix1 + " ")
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
        if self.DataFormat == DataSets[1]:
            if (0 != self.bAccX) and (0 != self.bAccY) and (0 == self.bAccZ):
                self.GetMessageAccDouble("AccX", "AccY", canData)
            elif (0 != self.bAccX) and (0 == self.bAccY) and (0 != self.bAccZ):
                self.GetMessageAccDouble("AccX", "AccZ", canData)
            elif (0 == self.bAccX) and (0 != self.bAccY) and (0 != self.bAccZ):
                self.GetMessageAccDouble("AccY", "AccZ", canData) 
            else:
                self.GetMessageAccTripple("AccX", "AccY", "AccZ", canData)   
        elif self.DataFormat == DataSets[3]:
            if 0 != self.bAccX:
                self.GetMessageAccSingle("AccX", canData)               
            elif 0 != self.bAccY:
                self.GetMessageAccSingle("AccY", canData)               
            elif 0 != self.bAccZ:
                self.GetMessageAccSingle("AccZ", canData)       
        else:               
            self.PeakCan.Logger.Error("Wrong Ack format")
            
    def ReadMessage(self):
        message = None
        result = self.m_objPCANBasic.Read(self.m_PcanHandle)
        if result[0] == PCAN_ERROR_OK:
            peakCanTimeStamp = result[2].millis_overflow * (2 ** 32) + result[2].millis + result[2].micros / 1000
            message = {"CanMsg" : result[1], "PcTime" : self.getTimeMs(), "PeakCanTime" : peakCanTimeStamp}   
        elif result[0] == PCAN_ERROR_QOVERRUN:
            self.Logger.Error("RxOverRun")
            print("RxOverRun")
            self.RunReadThread = False
        return message

    """
    Create Excel Sheet by xml definition
    """
    def excelSheetCreate(self):
        tree = ET.parse('configKeys.xml')
        root = tree.getroot()
        dataDef = root.Data
        config = None
        for data in dataDef.findall('data'):
            if data.get('name') == self.sConfig:
                config = data
        if None != config and None != self.sSheetFile:
            workbook = openpyxl.Workbook()
            i = 1
            for page in config.findall('page'):
                worksheet = workbook.create_sheet(page.get('name')+"@" +hex(page.get('pageAddress')))
                worksheet['A1'] = 'Address'
                worksheet['B1'] = 'Length'
                worksheet['C1'] = 'readOnly'
                worksheet['D1'] = 'Value'
                worksheet['E1'] = 'Unit'
                worksheet['F1'] = 'Format'
                worksheet['G1'] = 'Description'
                for entry in page.findall('entry'):
                    worksheet['A'+str(i)] = entry.get('subAddress')
                    worksheet['B'+str(i)] = entry.get('length')
                    worksheet['C'+str(i)] = entry.get('readOnly')
                    worksheet['D'+str(i)] = entry.get('Value')
                    worksheet['E'+str(i)] = entry.get('unit')
                    worksheet['F'+str(i)] = entry.get('format')
                    worksheet['G'+str(i)] = entry.get('description')
            workbook.save(self.sSheetFile)
    
    """
    Create xml definiton by Excel Sheet
    """
    def excelSheetConfig(self):
        tree = ET.parse('configKeys.xml')
        root = tree.getroot()
        dataDef = root.Data
        config = None
        for data in dataDef.findall('data'):
            if data.get('name') == self.sConfig:
                config = data
        workbook = openpyxl.load_workbook(self.sSheetFile)
        if None == config and workbook:
            sheets = workbook.sheetnames
            newPage = dataDef.SubElement(self.sConfig)
            for sheet in sheets:
                nameAddress = sheet.split('@')
                newPage.SubElement('name', nameAddress[0])
                newPage.SubElement('pageAddress', nameAddress[1])
                worksheet = workbook[sheet]
                newPage.SubElement('name', worksheet)
                for i in range(1,worksheet.max_row + 1):
                    newPage.SubElement('subAddress', sheet.cell(row=i,column=1) )
                    newPage.SubElement('length', sheet.cell(row=i,column=2) )
                    newPage.SubElement('readOnly', sheet.cell(row=i,column=3) )
                    newPage.SubElement('Value', sheet.cell(row=i,column=4) )
                    newPage.SubElement('unit', sheet.cell(row=i,column=5) )
                    newPage.SubElement('format', sheet.cell(row=i,column=6) )
                    newPage.SubElement('description', sheet.cell(row=i,column=7) )
            root.write('configKeys.xml')
        
        
    """
    Read EEPROM to write values in Excel Sheet
    """    
    def excelSheetRead(self):
        pass
    
    def run(self, **args):
        for arg in args:
            print(arg)
           
if __name__ == "__main__":
    # (self, log_location, bAcc1, bAcc2, bAcc3, dev, prescaler, aquistionTime, oversampling, runtime):
    acquireData = aquAcc()
    #(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7], sys.argv[8], sys.argv[9])
    acquireData.reset()
    acquireData.run(sys.argv)
    acquireData.close()
        
