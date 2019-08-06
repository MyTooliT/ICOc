import sys
import os

import xml.etree.ElementTree as ET
import PeakCanFd
from PeakCanFd import rreplace 
from MyToolItNetworkNumbers import *
from MyToolItCommands import *
from time import sleep, time
from random import randint
from MyToolItSth import *
from datetime import datetime
import getopt
import openpyxl
from openpyxl.styles import Font
import copy
import argparse

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


Gui = {
    "IntervalDimMinX" : 10, # Minimum interval time in ms
}


# def __init__(self, log_location, iAcc1, iAcc2, iAcc3, dev, prescaler, aquistionTime, oversampling, runtime):
class myToolItWatch():

    def __init__(self, parseArguments=True):
        self.KeyBoadInterrupt = False  
        self.bError = False     
        self.bClose = True   
        self.bConnected = False
        self.PeakCan = PeakCanFd.PeakCanFd(PeakCanFd.PCAN_BAUD_1M, "init.txt", "", MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"])
        self.vSave2Xml(False)
        self.vSthAutoConnect(False)
        self.iStartTime = time()
        self.vLogSet("init.txt")
        self.vConfigFileSet('configKeys.xml')
        self.bSampleConfigSet(None)
        self.vConfigSet("STH", "v2.1.1")
        self.vSheetFileSet("test.xlsx")
        self.vAccSet(True, False, False, DataSets[3])
        self.vVoltageSet(True, False, False, DataSets[3])
        self.vDeviceNameSet(TestConfig["DevName"])
        self.vDeviceNameSerial(None)
        self.vAdcConfig(2, 3, 64)
        self.vAdcRefVConfig("VDD")
        self.vDisplayTime(10)  
        self.vRunTime(10, 0)
        if False != parseArguments:
            self._ParserInit()
            self._ParserConsoleArguments()
        self.PeakCan.readThreadStop()       
            
    def __exit__(self):
        self.PeakCan.ReadArrayReset()
        if False != self.bConnected:
            self._BlueToothStatistics()
            ReceiveFailCounter = self._RoutingInformation()
            self._statusWords()
            self.PeakCan.Disconnect()
            if(0 < ReceiveFailCounter):
                self.bError = True
        self.PeakCan.Logger.Info("End Time Stamp")
        
        if(False != self.bError):
            self.PeakCan.Logger.Info("bError")
            print("bError")
        else:
            self.PeakCan.Logger.Info("Fin")
        self.PeakCan.__exit__()  
        if(False != self.bError):
            raise
        if False != self.bSave:
            self.xmlConfigSave(self.tree, self.root)
        print("Fin")
       
    def _ParserInit(self):
        self.parser = argparse.ArgumentParser(description='Command Line Oprtions')
        self.parser.add_argument('-a', '--adc', dest='adc_config', action='store', nargs=3, type=int, required=False, help='Prescaler AcquisitionTime OversamplingRate (3 inputs required in that row) - Note that acceleration and battery voltage measurements share a single ADC that samples up to 4 channels)')
        self.parser.add_argument('-c', '--show_config', dest='show_config', action='store_true', required=False, help='Shows actual configuration (including command line arguments)')
        self.parser.add_argument('-d', '--devs', dest='devNameList', action='store_true', required=False, help='Get Device Names of all available STHs')    
        self.parser.add_argument('-e', '--xlsx', dest='xlsx', action='store', nargs=1, type=int, required=False, help='xlsx File to save take configuraton to a product')
        self.parser.add_argument('-i', '--interval', dest='interval', action='store', nargs=1, type=int, required=False, help='Sets Interval Time (Time to save files in ms. Must be creater than 10')
        self.parser.add_argument('-l', '--log_location', dest='log_name', action='store', nargs=1, type=str, required=False, help='Where to save Log Files (relative/absolute path+file name')
        self.parser.add_argument('-n', '--name_connect', dest='name_connect', action='store', nargs=1, type=str, required=False, help='Connects to device Name and starts sampling as configured')
        self.parser.add_argument('-p', '--points', dest='points', action='store', nargs=1, type=int, required=False, help='PPP samples X/Y/Z where P must be 1(Active) or 0(Off)')
        self.parser.add_argument('-r', '--run_time', dest='run_time', action='store', nargs=1, type=int, required=False, help='Sets RunTime')
        self.parser.add_argument('-s', '--sample_setup', dest='sample_setup', action='store', nargs=1, type=int, required=False, help='Starts sampling with configuration as given including additional command line arguments')
        self.parser.add_argument('-x', '--xml', dest='xml_file_name', action='store', nargs=1, type=str, required=True, help='Selects xml configuration/data base file')
        self.parser.add_argument('-v', '--version', dest='version', action='store', nargs=2, type=str, required=False, help='Product ProductVersion chooses product with version for handling Table Calculation Files (e.g. STH v2.1.2)')
        self.parser.add_argument('--create', dest='create', action='store_true', required=False, help='Creates a config in the setup file. Configuration name is the same as configured in -x argument')
        self.parser.add_argument('--gui_x_dim', dest='create', action='store', nargs=1, required=False, help='Time to show interval GUI window in ms. Value below 10 turns it off')
        self.parser.add_argument('--refv', dest='refv', action='store', nargs=1, type=str, required=False, help='Prescaler AcquisitionTime OversamplingRate (3 inputs required in that row) - Note that acceleration and battery voltage measurements share a single ADC that samples up to 4 channels)')
        self.parser.add_argument('--remove', dest='remove', action='store_true', required=False, help='Removes a config in the setup file. Configuration name is the same as configured in -x argument')
        self.parser.add_argument('--save', dest='save', action='store_true', required=False, help='Saves Configuration in setup-xml File (Chose parameters as actually configured)')
        self.parser.add_argument('--serials', dest='serials', action='store_true', required=False, help='Show all STH serials and bluetooth mac addresses')
        self.parser.add_argument('--serial_connect', dest='serial_connect', action='store', nargs=1, type=int, required=False, help='Connects to device with specific serial number and starts sampliing as configured')
        args = self.parser.parse_args()
        self.args_dict = vars(args)
     
    def _ParserConsoleArguments(self):  
        if None != self.args_dict['xml_file_name']:
            self.vConfigFileSet(self.args_dict['xml_file_name'][0])
        if None != self.args_dict['gui_x_dim']:
            self.vLogSet(self.args_dict['gui_x_dim'][0])            
        if None != self.args_dict['log_name']:
            self.vLogSet(self.args_dict['log_name'][0]) 
        if None != self.args_dict['adc_config']:
            adcConfig = self.args_dict['adc_config']
            self.vAdcConfig(adcConfig[0], adcConfig[1], adcConfig[2])
        if None != self.args_dict['refv']:
            self.vAdcRefVConfig(self.args_dict['refv'][0])
        if None != self.args_dict['xlsx']:
            self.vSheetFileSet(self.args_dict['xlsx'][0])
        iIntervalTime = self.iIntervalTime
        if None != self.args_dict['interval']:
            iIntervalTime = self.args_dict['interval'][0]
        if Gui["IntervalDimMinX"] > iIntervalTime:
            iIntervalTime = 0
            
        iRunTime = self.iRunTime
        if None != self.args_dict['run_time']:
            iRunTime = self.args_dict['run_time'][0]
        self.vRunTime(iRunTime, iIntervalTime)

        if None != self.args_dict['name_connect']:
            self.vDeviceNameSet(self.args_dict['name_connect'][0])
            self.vSthAutoConnect(True)
        elif None != self.args_dict['serial_connect']:    
            self.vDeviceNameSerial(self.args_dict['serial_connect'][0])
            self.vSthAutoConnect(True)
            
        if None != self.args_dict['points']: 
            points = self.args_dict['points'][0] & 0x03
            bX = bool(points & 1)
            bY = bool((points >> 1) & 1)
            bZ = bool((points >> 2) & 1)
            pointBool = [bX, bY, bZ]
            self.vAccSet(pointBool[2], pointBool[1], pointBool[0], pointBool.count(True))
        
        if None != self.args_dict['save']:
            self.vSave2Xml(True)
        
        bRemove = False  
        if None != self.args_dict['remove']:
            bRemove = True
                
        bCreate = False
        if None != self.args_dict['create'] and False == bRemove:
            bCreate = True
            self.vSave2Xml(True)
        if None != self.args_dict['sample_setup']: 
            sSampleConfig = self.args_dict['sample_setup']
            if False == self.bSampleConfigSet() and False != bCreate:
                self.newXmlConfig(sSampleConfig)
                self.vSave2Xml(True)
                bCreate = False
                
        if None != self.args_dict['version']: 
            product = self.args_dict['version'][0]
            version = self.args_dict['version'][1]
            self.vConfigSet(product, version)
            if False != bCreate:
                dataDef = self.root.find('Data')
                for product in dataDef.find('Product'):
                    if product.get('name') == self.sProduct:
                        break
                if product.get('name') == self.sProduct:
                    for version in product.find('Version'):
                        if version.get('name') == self.sConfig:
                            break
                    if version.get('name') != self.sConfig:
                        self.newXmlVersion(product)
                        self.vSave2Xml(True)

                
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

# Setter Methods

    def vSave2Xml(self, bSave):
        self.bSave = bSave
        
    def vConfigFileSet(self, sfileName):
        self.sConfigFile = sfileName
        self.tree = ET.parse(self.sConfigFile)
        self.root = self.tree.getroot()
        
    def vConfigSet(self, product, sConfig):
        if "STH" == product:
            self.sProduct = "STH"
            self.PeakCan.vSetReceiver(MyToolItNetworkNr["STH1"])    
            self.sConfig = sConfig  
        elif "STU" == product: 
            self.sProduct = "STU"
            self.PeakCan.vSetReceiver(MyToolItNetworkNr["STU1"])
            self.sConfig = sConfig        

    def bSampleConfigSet(self, sSetupConfig):
        bReturn = False
        self.sSampleConfig = sSetupConfig
        for config in self.tree.find('Config'):
            if self.sSampleConfig == config.get('name'):
                self.sConfig = config
                bReturn = True
                break
        return bReturn
        
    def vLogSet(self, sLogLocation):
        if -1 != sLogLocation.rfind('.'):
            sLogLocation = rreplace(sLogLocation, '.', "_" + self.sDateClock() + ".")
            logNameError = sLogLocation
            logNameError = rreplace(logNameError, '.', "bError.")
            self.PeakCan.vLogNameChange(sLogLocation, logNameError)
    
    def vLogCountInc(self):
        fileName = self.PeakCanFd.Logger.fileName[:-24]
        fileName = fileName + "_" + self.sDateClock() + ".txt"
        self.PeakCanFd.vLogNameCloseInterval(fileName, self.PeakCanFd.Logger.fileNameError)
        
    def vSheetFileSet(self, sSheetFile):
        self.sSheetFile = sSheetFile
        
    def vAccSet(self, bX, bY, bZ, dataSets):
        self.bAccX = bool(bX) 
        self.bAccY = bool(bY) 
        self.bAccZ = bool(bZ) 
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
        
    def vVoltageSet(self, bX, bY, bZ, dataSets):
        self.bVoltageX = bool(bX)
        self.bVoltageY = bool(bY)
        self.bVoltageZ = bool(bZ)
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
    
    def vSthAutoConnect(self, bSthAutoConnect):     
        self.bSthAutoConnect = bool(bSthAutoConnect)
     
    def vDeviceNameSerial(self, sDevName):   
        self.sSerial = sDevName
        
    def vDeviceNameSet(self, sDevName):
        if 8 < len(sDevName):
            sDevName = sDevName[:8]
        self.sDevName = sDevName
        self.iDevNr = None
        
    def vAdcConfig(self, iPrescaler, iAquistionTime, iOversampling):
        if Prescaler["Min"] > iPrescaler:
            iPrescaler = Prescaler["Min"]
        elif Prescaler["Max"] < iPrescaler:
            iPrescaler = Prescaler["Max"]    
        iAcquisitionTime = AdcAcquisitionTime[iAquistionTime]
        iOversampling = AdcOverSamplingRate[iOversampling]
        self.samplingRate = int(calcSamplingRate(iPrescaler, iAcquisitionTime, iOversampling) + 0.5)
        self.iPrescaler = iPrescaler
        self.sAquistionTime = iAcquisitionTime
        self.sOversampling = iOversampling
        
    def vAdcRefVConfig(self, sAdcRef):
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
        DataClockTimeStamp = datetime.fromtimestamp(self.iStartTime).strftime('%Y-%m-%d_%H-%M-%S')
        return DataClockTimeStamp
   
    def reset(self):
        if False == self.KeyBoadInterrupt:
            try:
                self.PeakCan.cmdReset(MyToolItNetworkNr["STU1"])
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
                    self.PeakCan.Logger.bError("Device not allocable")     
            except KeyboardInterrupt:
                self.KeyBoadInterrupt = True
                self.__exit__()
                
    def close(self):
        if False != self.bClose:
            self.__exit__()          
    
    def GetStreamingAccDataProcess(self, endTime):
        try:
            while(self.PeakCan.getTimeMs() < endTime):
                ack = self.ReadMessage()
                if(None != ack):
                    if(self.AckExpected.ID != ack["CanMsg"].ID):
                        self.PeakCan.Logger.bError("CanId bError: " + str(ack["CanMsg"].ID))
                    elif(self.AckExpected.DATA[0] != ack["CanMsg"].DATA[0]):
                        self.PeakCan.Logger.bError("Wrong Subheader-Format(Acceleration Format): " + str(ack["CanMsg"].ID))
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
            self.PeakCan.Logger.bError("No Ack received from Device: " + str(self.dev))
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
            self.PeakCan.Logger.bError("Wrong Ack format")
            
    def ReadMessage(self):
        message = None
        result = self.m_objPCANBasic.Read(self.m_PcanHandle)
        if result[0] == PeakCanFd.PCAN_ERROR_OK:
            peakCanTimeStamp = result[2].millis_overflow * (2 ** 32) + result[2].millis + result[2].micros / 1000
            message = {"CanMsg" : result[1], "PcTime" : self.getTimeMs(), "PeakCanTime" : peakCanTimeStamp}   
        elif result[0] == PeakCanFd.PCAN_ERROR_QOVERRUN:
            self.Logger.bError("RxOverRun")
            print("RxOverRun")
            self.RunReadThread = False
        return message

    def excelCellWidthAdjust(self, worksheet, factor=1.2, bSmaller=True):
        for col in worksheet.columns:
            max_length = 0
            column = col[0].column  # Get the column name
            for cell in col:
                if cell.coordinate in worksheet.merged_cells:  # not check merge_cells
                    continue
                try:  # Necessary to avoid error on empty cells
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            adjusted_width = (max_length + 2) * factor
            columLetter = chr(ord('A') + column - 1)
            if adjusted_width > worksheet.column_dimensions[columLetter].width or False == bSmaller:
                worksheet.column_dimensions[columLetter].width = adjusted_width
            
    """
    Create Excel Sheet by xml definition
    """

    def excelSheetCreate(self):
        dataDef = self.root.find('Data')
        for product in dataDef.find('Product'):
            if product.get('name') == self.sProduct:
                break
        for version in product.find('Version'):
            if version.get('name') == self.sConfig:
                break
        if version.get('name') == self.sConfig:
            workbook = openpyxl.Workbook()
            FontRow1 = Font(bold=True, size=20)
            FontRowRow2 = Font(bold=False, size=12)
            workbook.remove_sheet(workbook.get_sheet_by_name('Sheet'))
            
            for page in version.find('Page'):
                i = 2
                name = page.get('name')
                pageAddress = int(page.find('pageAddress').text)
                worksheet = workbook.create_sheet(name + "@" + hex(pageAddress))
                worksheet['A1'] = 'Name'
                worksheet['A1'].font = FontRow1
                worksheet['B1'] = 'Address'
                worksheet['B1'].font = FontRow1
                worksheet['C1'] = 'Length'
                worksheet['C1'].font = FontRow1
                worksheet['D1'] = 'Read Only'
                worksheet['D1'].font = FontRow1
                worksheet['E1'] = 'Value'
                worksheet['E1'].font = FontRow1
                worksheet['F1'] = 'Unit'
                worksheet['F1'].font = FontRow1
                worksheet['G1'] = 'Format'
                worksheet['G1'].font = FontRow1
                worksheet['H1'] = 'Description'
                worksheet['H1'].font = FontRow1
                self.excelCellWidthAdjust(worksheet, 1.6, False)
                for entry in page.find('Entry'):
                    worksheet['A' + str(i)] = entry.get('name')
                    worksheet['A' + str(i)].font = FontRowRow2
                    worksheet['B' + str(i)] = int(entry.find('subAddress').text)
                    worksheet['B' + str(i)].font = FontRowRow2
                    worksheet['C' + str(i)] = int(entry.find('length').text)
                    worksheet['C' + str(i)].font = FontRowRow2
                    worksheet['D' + str(i)] = entry.find('readOnly').text
                    worksheet['D' + str(i)].font = FontRowRow2
                    try:
                        worksheet['E' + str(i)] = int(entry.find('value').text)
                    except ValueError:
                        worksheet['E' + str(i)] = entry.find('value').text
                    worksheet['E' + str(i)].font = FontRowRow2
                    worksheet['F' + str(i)] = entry.find('unit').text
                    worksheet['F' + str(i)].font = FontRowRow2
                    worksheet['G' + str(i)] = entry.find('format').text
                    worksheet['G' + str(i)].font = FontRowRow2
                    worksheet['H' + str(i)] = entry.find('description').text
                    worksheet['H' + str(i)].font = FontRowRow2
                    i += 1
                self.excelCellWidthAdjust(worksheet)
            workbook.save(self.sSheetFile)
    
    def _excelSheetEntryFind(self, entry, key, value):
        if None != value:
            entry.find(key).text = str(value)

    """
    Set endoding
    """

    def _XmlWriteEndoding(self):
        xml = (bytes('<?xml version="1.0" encoding="UTF-8"?>\n', encoding='utf-8') + ET.tostring(self.root))
        xml = xml.decode('utf-8')
        with open(self.sConfigFile, 'w+') as f:
            f.write(xml)   
     
    """
    Creats a new config
    """

    def newXmlVersion(self, product):
        cloneVersion = copy.deepcopy(product.find('Version')[0])
        cloneVersion.set('name', self.sConfig) 
        product.find('Version').append(cloneVersion)

    """
    Removes a config
    """

    def removeXmlConfig(self):
        dataDef = self.root.find('Data')
        for product in dataDef.find('Product'):
            if product.get('name') == self.sProduct:
                break
        if product.get('name') == self.sProduct:
            product.find('Version').remove(self.sConfig)
            self.xmlConfigSave(self.tree, self.root)
        
    """
    Save XML File (in any state)
    """

    def xmlConfigSave(self):
        self.tree.write(self.sConfigFile)
        self._XmlWriteEndoding()   
        del self.tree
        
    """
    Write xml definiton by Excel Sheet
    """

    def excelSheetConfig(self):
        dataDef = self.root.find('Data')
        for product in dataDef.find('Product'):
            if product.get('name') == self.sProduct:
                break
        for version in product.find('Version'):
            if version.get('name') == self.sConfig:
                break
        workbook = openpyxl.load_workbook(self.sSheetFile)
        if workbook:
            if version.get('name') != self.sConfig:
                self.newXmlVersion(product)
                self.xmlConfigSave(self.tree, self.root)
                self.excelSheetConfig()
            else:
                for worksheetName in workbook.sheetnames:
                    name = str(worksheetName).split('@')
                    address = name[1]
                    name = name[0]
                    for page in version.find('Page'):
                        i = 2
                        pageName = page.get('name')
                        pageAddress = hex(int(page.find('pageAddress').text))
                        if name == pageName and pageAddress == address:
                            worksheet = workbook.get_sheet_by_name(worksheetName)
                            for entry in page.find('Entry'):
                                value = str(worksheet['A' + str(i)].value)
                                if None != value:
                                    entry.set('name', value)
                                else:
                                    entry.set('name', "")
                                self._excelSheetEntryFind(entry, 'subAddress', worksheet['B' + str(i)].value)
                                self._excelSheetEntryFind(entry, 'length', worksheet['C' + str(i)].value)
                                self._excelSheetEntryFind(entry, 'readOnly', worksheet['D' + str(i)].value)
                                self._excelSheetEntryFind(entry, 'value', worksheet['E' + str(i)].value)
                                self._excelSheetEntryFind(entry, 'unit', worksheet['F' + str(i)].value)
                                self._excelSheetEntryFind(entry, 'format', worksheet['G' + str(i)].value)
                                self._excelSheetEntryFind(entry, 'description', worksheet['H' + str(i)].value)
                                i += 1
                self.xmlConfigSave(self.tree, self.root)
        
    def xmlPrintVersions(self):
        dataDef = self.root.find('Data')
        for product in dataDef.find('Product'):
            print(product.get('name') + ":")
            for version in product.find('Version'):
                print("   " + version.get('name'))
            
    """
    Read EEPROM to write values in Excel Sheet
    """    

    def excelSheetRead(self):
        pass
    
    """
    Write EEPROM to write values in Excel Sheet
    """    

    def excelSheetWrite(self):
        pass
        
    def newXmlConfig(self, sConfig):
        cloneVersion = copy.deepcopy(self.newXmlVersion(self.tree.find('Config'))[0])
        cloneVersion.set('name', sConfig) 
        self.tree.find('Config').append(cloneVersion)
        self.xmlConfigSave(self.tree, self.root)
        self.vSampleConfigSet(sConfig)
                        
    def run(self, args):
        print(self.args_dict)
        
#         self.xmlPrintVersions()
#         self.excelSheetCreate()
#         input('Please Edit Excel Sheet and press Enter')
#         # newVersion = input('Please Type new Version Name')
#         newVersion = "v2.1.2"
#         self.vConfigSet("STH", newVersion)
#         self.excelSheetConfig()

           
if __name__ == "__main__":
    # (self, log_location, bAcc1, bAcc2, bAcc3, dev, prescaler, aquistionTime, oversampling, runtime):
    watch = myToolItWatch()
    # (sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7], sys.argv[8], sys.argv[9])
    # watch.reset()
    watch.run(sys.argv[1:])
    # watch.bclose()
        
