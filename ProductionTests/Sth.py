import unittest
import CanFd
import time
import array
import openpyxl
import os
import sys
import math
import struct
from datetime import date
from shutil import copyfile
from openpyxl.styles import Font
from MyToolItNetworkNumbers import MyToolItNetworkNr 
from MyToolItSth import TestConfig, SthErrorWord, fVoltageBattery, fAcceleration
from MyToolItStu import StuErrorWord
from SthLimits import *
from StuLimits import RssiStuMin
from MyToolItCommands import *
from openpyxl.descriptors.base import DateTime

sVersion = "v2.1.5"
sLogName = 'ProductionTestSth'
sLogLocation = '../../Logs/ProductionTestSth/'
sOtaComPort = 'COM6'
sOtaLocation = "../../SimplicityStudio/v4_workspace/server_firmware/builds/"
sResultLocation = '../../ProductionTests/STH/'


def sSerialNumber(sExcelFileName):
    tWorkbook = openpyxl.load_workbook(sExcelFileName)
    tWorkSheet = tWorkbook.get_sheet_by_name("Product Data@0x4")
    value = tWorkSheet['E12'].value
    sSerial = str(value)
    return sSerial


bSkip = False


class TestSth(unittest.TestCase):

    def setUp(self):
        global bSkip
        self.bError = False
        vSthLimitsConfig(1, True)
        self.sOtaLocation = sOtaLocation + sVersion
        self.iTestNumber = int(self._testMethodName[4:8])
        self.fileName = sLogLocation + self._testMethodName + ".txt"
        self.fileNameError = sLogLocation + "Error_" + self._testMethodName + ".txt"
        self.sExcelEepromContentFileName = "Sth" + sVersion + ".xlsx"
        if False != bSkip and "test9999StoreTestResults" != self._testMethodName:
            self.skipTest("At least some previous test failed")
        else:
            self.Can = CanFd.CanFd(CanFd.PCAN_BAUD_1M, self.fileName, self.fileNameError, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], AdcPrescalerReset, AdcAcquisitionTimeReset, AdcAcquisitionOverSamplingRateReset, FreshLog=True)
            self.Can.Logger.Info("TestCase: " + str(self._testMethodName))
            self.Can.CanTimeStampStart(self._resetStu()["CanTime"])  # This will also reset to STH
            self.Can.Logger.Info("Connect to STH")
            self.Can.bBlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"], log=False)
            self.sStuAddr = sBlueToothMacAddr(self.Can.BlueToothAddress(MyToolItNetworkNr["STU1"]))
            self.sSthAddr = sBlueToothMacAddr(self.Can.BlueToothAddress(MyToolItNetworkNr["STH1"]))
            self.Can.Logger.Info("STU BlueTooth Address: " + self.sStuAddr)
            self.Can.Logger.Info("STH BlueTooth Address: " + self.sSthAddr)
            self.sSerialNumber = sSerialNumber(self.sExcelEepromContentFileName)
            self.sExcelEepromContentReadBackFileName = sLogName + "_" + self.sSerialNumber + "_" + self.sSthAddr.replace(":", "#") + "_ReadBack.xlsx"
            self.sDateClock = sDateClock() 
            self.sTestReport = sLogName + "_" + self.sSerialNumber + "_" + self.sSthAddr.replace(":", "#")
            self.tWorkbookOpenCreate()
            self._statusWords()
            self._iSthAdcTemp()
            self._SthWDog()
            self.Can.Logger.Info("_______________________________________________________________________________________________________________")
            self.Can.Logger.Info("Start")

    def tearDown(self):
        global bSkip
        self.Can.Logger.Info("Fin")
        self.Can.Logger.Info("_______________________________________________________________________________________________________________")
        if "test9999StoreTestResults" != self._testMethodName:
            self.tWorkbook.save(self.sTestReport + ".xlsx")
        self.Can.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"])
        self.Can.streamingStop(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"])
        self._statusWords()
        self._iSthAdcTemp()
        self.Can.Logger.Info("Test Time End Time Stamp")
        self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])
        self.Can.__exit__()
        if self._outcome.errors[1][1]:
            bSkip = True
        if False != self.bError:
            bSkip = True

    def _resetStu(self, retries=5, log=True):
        self.Can.bConnected = False
        return self.Can.cmdReset(MyToolItNetworkNr["STU1"], retries=retries, log=log)
    
    def _resetSth(self, retries=5, log=True):
        self.Can.bConnected = False
        return self.Can.cmdReset(MyToolItNetworkNr["STH1"], retries=retries, log=log)
                               
    def _iSthAdcTemp(self):
        ret = self.Can.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["Temp"], 1, AdcReference["1V25"], log=False)
        result = float(iMessage2Value(ret[4:]))
        result /= 1000
        self.Can.Logger.Info("Temperature(Chip): " + str(result) + "°C") 
        self.Can.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["None"], CalibMeassurementTypeNr["Temp"], 1, AdcReference["VDD"], log=False, bReset=True)
        return result

    def _statusWords(self):
        ErrorWordSth = SthErrorWord()
        ErrorWordStu = StuErrorWord()
        psw0 = self.Can.statusWord0(MyToolItNetworkNr["STH1"])
        self.Can.Logger.Info("STH Status Word: " + hex(psw0))
        psw0 = self.Can.statusWord0(MyToolItNetworkNr["STU1"])
        self.Can.Logger.Info("STU Status Word: " + hex(psw0))
        ErrorWordSth.asword = self.Can.statusWord1(MyToolItNetworkNr["STH1"])
        if True == ErrorWordSth.b.bAdcOverRun:
            self.bError = True
        self.Can.Logger.Info("STH Error Word: " + hex(ErrorWordSth.asword))
        ErrorWordStu.asword = self.Can.statusWord1(MyToolItNetworkNr["STU1"])
        self.Can.Logger.Info("STU Error Word: " + hex(ErrorWordStu.asword))

    def _SthWDog(self):
        WdogCounter = iMessage2Value(self.Can.statisticalData(MyToolItNetworkNr["STH1"], MyToolItStatData["Wdog"])[:4])
        self.Can.Logger.Info("WatchDog Counter: " + str(WdogCounter))
        return WdogCounter 
           
    """
    Try to open Excel Sheet. If not able to open, then create a new one
    """

    def tWorkbookOpenCreate(self):
        try:
            self.tWorkbook = openpyxl.load_workbook(self.sTestReport + ".xlsx")
        except:
            self.tWorkbook = openpyxl.Workbook()      
            self.tWorkbook.remove_sheet(self.tWorkbook.get_sheet_by_name('Sheet'))
            self.tWorkSheet = self.tWorkbook.create_sheet(self.sSthAddr.replace(":", "#"))
            tFont = Font(bold=True, size=20)
            self.tWorkSheet['A1'] = 'Test Batch Number'
            self.tWorkSheet['A1'].font = tFont
            self.tWorkSheet['B1'] = 'Test Name'
            self.tWorkSheet['B1'].font = tFont
            self.tWorkSheet['C1'] = 'DateTime'
            self.tWorkSheet['C1'].font = tFont
            self.tWorkSheet['D1'] = 'Description'
            self.tWorkSheet['D1'].font = tFont
            for i in range(0, 16):
                self.tWorkSheet[chr(0x45 + i) + "1"].value = 'Test Case Report ' + str(i)
                self.tWorkSheet[chr(0x45 + i) + "1"].font = tFont
            self.tWorkbook.save(self.sTestReport + ".xlsx")
            self.tWorkbook = openpyxl.load_workbook(self.sTestReport + ".xlsx")
        self.tWorkSheet = self.tWorkbook.get_sheet_by_name(self.sSthAddr.replace(":", "#"))
        self.iTestRow = 1
        while(None != self.tWorkSheet['A' + str(self.iTestRow + 1)].value):
            self.iTestRow += 1
        self.tWorkSheetWrite("A", self.iTestRow)
        self.tWorkSheetWrite("B", self._testMethodName)
        self.tWorkSheetWrite("C", self.sDateClock)
    
    def tWorkSheetWrite(self, sCol, value):
        tFont = Font(bold=False, size=12)
        self.tWorkSheet[sCol + str(self.iTestRow + 1)].value = str(value)
        self.tWorkSheet[sCol + str(self.iTestRow + 1)].font = tFont

    def TurnOffLed(self):
        self.Can.Logger.Info("Turn Off LED")
        cmd = self.Can.CanCmd(MyToolItBlock["Configuration"], MyToolItConfiguration["Hmi"], 1, 0)
        message = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [129, 1, 2, 0, 0, 0, 0, 0])
        self.Can.tWriteFrameWaitAckRetries(message)   

    def au8excelValueToByteArray(self, worksheet, iIndex):
        iLength = int(worksheet['C' + str(iIndex)].value)
        value = worksheet['E' + str(iIndex)].value
        byteArray = [0] * iLength
        if None != value:
            if "UTF8" == worksheet['G' + str(iIndex)].value:
                try:
                    value = str(value).encode('utf-8')
                except Exception as e: 
                    self.Can.Logger.Info(str(e))
                    value = [0] * iLength
                iCopyLength = len(value)
                if iLength < iCopyLength:
                    iCopyLength = iLength
                for i in range(0, iCopyLength):
                    byteArray[i] = value[i]
            elif "ASCII" == worksheet['G' + str(iIndex)].value:
                try:
                    value = str(value).encode('ascii')
                except Exception as e: 
                    self.Can.Logger.Info(str(e))
                    value = [0] * iLength
                iCopyLength = len(value)
                if iLength < iCopyLength:
                    iCopyLength = iLength
                for i in range(0, iCopyLength):
                    byteArray[i] = value[i]                
            elif "unsigned" == worksheet['G' + str(iIndex)].value:
                byteArray = au8Value2Array(int(value), iLength)   
            elif "float" == worksheet['G' + str(iIndex)].value:
                value = float(value)
                value = struct.pack('f', value)
                value = int.from_bytes(value, byteorder='little')
                byteArray = au8Value2Array(int(value), 4)   
            else:
                if "0" == value or 0 == value:
                    value = "[0x0]"
                value = value[1:-1].split(',')
                for i in range(0, len(value)):
                    byteArray[i] = int(value[i], 16)
        return byteArray
    
    def iExcelSheetPageLength(self, worksheet):
        totalLength = 0
        for i in range(2, 256 + 2):
            if None != worksheet['A' + str(i)].value:
                length = int(worksheet['C' + str(i)].value)
                totalLength += length
            else:
                break
        return totalLength 
    
    def sExcelSheetWrite(self, namePage, iReceiver):
        sError = None
        workbook = openpyxl.load_workbook(self.sExcelEepromContentFileName)
        if workbook:
            for worksheetName in workbook.sheetnames:
                name = str(worksheetName).split('@')
                address = int(name[1], base=16)
                name = name[0]
                if namePage == name:
                    worksheet = workbook.get_sheet_by_name(worksheetName)
                    # Prepare Write Data
                    au8WriteData = [0] * 256
                    iByteIndex = 0
                    for i in range(2, 256 + 2, 1):
                        if None != worksheet['A' + str(i)].value:
                            au8ElementData = self.au8excelValueToByteArray(worksheet, i)
                            for j in range(0, len(au8ElementData), 1):
                                au8WriteData[iByteIndex + j] = au8ElementData[j] 
                            iLength = int(worksheet['C' + str(i)].value)
                            iByteIndex += iLength
                        else:
                            break
                    iWriteLength = self.iExcelSheetPageLength(worksheet)  
                    if 0 != iWriteLength % 4:
                        iWriteLength += 4
                        iWriteLength -= (iWriteLength % 4)
                    au8WriteData = au8WriteData[0:iWriteLength] 
                    self.Can.Logger.Info("Write Content: " + payload2Hex(au8WriteData))
                    for offset in range(0, iWriteLength, 4):
                        au8WritePackage = au8WriteData[offset:offset + 4]
                        au8Payload = [address, 0xFF & offset, 4, 0]
                        au8Payload.extend(au8WritePackage)
                        self.Can.cmdSend(iReceiver, MyToolItBlock["Eeprom"], MyToolItEeprom["Write"], au8Payload, log=False)   
            try:
                workbook.close() 
            except Exception as e: 
                sError = "Could not close file: " + str(e)
                self.Can.Logger.Info(sError)
        return sError

    def vUnicodeIllegalRemove(self, value, character):
        while(True):
            try:
                value.remove(character)
            except:
                break  
        return value          
    
    def iExcelSheetPageValue(self, worksheet, aBytes):
        i = 2
        iTotalLength = 0
        while len(aBytes) > iTotalLength:
            if None != worksheet['A' + str(i)].value:
                iLength = worksheet['C' + str(i)].value
                value = aBytes[iTotalLength:iTotalLength + iLength]
                if "UTF8" == worksheet['G' + str(i)].value:
                    try:
                        value = self.vUnicodeIllegalRemove(value, 0)
                        value = self.vUnicodeIllegalRemove(value, 255)
                        value = array.array('b', value).tostring().decode('utf-8', 'replace')
                    except Exception as e:
                        self.Can.Logger.Info(str(e))
                        value = ""
                elif "ASCII" == worksheet['G' + str(i)].value:
                    value = sArray2String(value)
                elif "unsigned" == worksheet['G' + str(i)].value:
                    value = str(iMessage2Value(value))
                elif "float" == worksheet['G' + str(i)].value:
                    if None != value:
                        pass
                        # value = au8ChangeEndianOrder(value)
                    else: 
                        value = 0.0
                    self.Can.Logger.Info("Value from EEPROM: " + str(value))
                    value = bytearray(value)
                    value = struct.unpack('f', value)[0]
                    value = str(value)
                    self.Can.Logger.Info("Value as float: " + str(value))
                else:                    
                    value = payload2Hex(value)
                value = str(value)
                try:
                    worksheet['E' + str(i)] = str(value).encode('utf8')
                except:
                    pass
                iTotalLength += iLength
                i += 1
            else:
                break
        return iTotalLength  

    """
    Read EEPROM page to write values in Excel Sheet
    """    

    def sExcelSheetRead(self, namePage, iReceiver):
        sError = None
        workbook = openpyxl.load_workbook(self.sExcelEepromContentReadBackFileName)
        if workbook:
            for worksheetName in workbook.sheetnames:
                name = str(worksheetName).split('@')
                address = int(name[1], base=16)
                name = name[0]
                if namePage == name:
                    worksheet = workbook.get_sheet_by_name(worksheetName)
                    pageContent = []
                    readLength = self.iExcelSheetPageLength(worksheet)
                    readLengthAlligned = readLength
                    if 0 != readLengthAlligned % 4:
                        readLengthAlligned += 4
                        readLengthAlligned -= (readLengthAlligned % 4)
                    for offset in range(0, readLengthAlligned, 4):
                        payload = [address, 0xFF & offset, 4, 0, 0, 0, 0, 0]
                        index = self.Can.cmdSend(iReceiver, MyToolItBlock["Eeprom"], MyToolItEeprom["Read"], payload, log=False)   
                        readBackFrame = self.Can.getReadMessageData(index)[4:]
                        pageContent.extend(readBackFrame)
                    pageContent = pageContent[0:readLength]
                    self.Can.Logger.Info("Read Data: " + payload2Hex(pageContent))
                    self.iExcelSheetPageValue(worksheet, pageContent)
            try:
                workbook.save(self.sExcelEepromContentReadBackFileName) 
            except Exception as e: 
                sError = "Could not save file(Opened by another application?): " + str(e)
                self.Can.Logger.Info(sError)
        return sError
    
    def tCompareEerpomWriteRead(self):
        tWorkSheetNameError = None
        sCellNumberError = None
        tWorkbookReadBack = openpyxl.load_workbook(self.sExcelEepromContentReadBackFileName)
        tWorkbookWrite = openpyxl.load_workbook(self.sExcelEepromContentFileName)
        if tWorkbookReadBack and tWorkbookWrite:
            for worksheetName in tWorkbookWrite.sheetnames:
                tWorkSheedReadBack = tWorkbookReadBack.get_sheet_by_name(worksheetName)
                tWorkSheedWrite = tWorkbookWrite.get_sheet_by_name(worksheetName)
                for i in range(2, 2 + 256):
                    if None != tWorkSheedWrite['A' + str(i)].value:
                        if str(tWorkSheedWrite['E' + str(i)].value) != str(tWorkSheedReadBack['E' + str(i)].value):
                            tWorkSheetNameError = worksheetName
                            sCellNumberError = 'E' + str(i)
                            break
                    else:
                        if None != tWorkSheedReadBack['A' + str(i)].value:
                            tWorkSheetNameError = worksheetName
                            sCellNumberError = 'A' + str(i)
                        break
                            
        return [tWorkSheetNameError, sCellNumberError]
    
    """
    Change a specific content of an ExcelCell
    """
    
    def vChangeExcelCell(self, sWorkSheetName, sCellName, sContent):
        workSheetNames = []
        workbook = openpyxl.load_workbook(self.sExcelEepromContentFileName)
        if workbook:
            for worksheetName in workbook.sheetnames:
                sName = str(worksheetName).split('@')
                _sAddress = sName[1]
                sName = sName[0]
                workSheetNames.append(sName)
        worksheet = workbook.get_sheet_by_name(sWorkSheetName)    
        worksheet[sCellName] = sContent
        workbook.save(self.sExcelEepromContentFileName)   
    
    
    
    """
    
    """    

    def test0001OverTheAirUpdate(self):
        self.tWorkSheetWrite("D", "Test the over the air update bootloader functionallity")
        self._resetStu()
        time.sleep(1)
        sSystemCall = self.sOtaLocation + "/ota-dfu.exe COM6 115200 " 
        sSystemCall += self.sOtaLocation + "/ServerApplication.gbl "
        sSystemCall += self.sSthAddr + " -> " + sLogLocation 
        sSystemCall += self._testMethodName + "Ota.txt"
        if os.name == 'nt': 
            sSystemCall = sSystemCall.replace("/", "\\")
            os.system(sSystemCall)
        # for mac and linux(here, os.name is 'posix') 
        else: 
            os.system(sSystemCall)            
        tFile = open(sLogLocation + self._testMethodName + "Ota.txt", "r", encoding='utf-8')
        asData = tFile.readlines()
        self.tWorkSheetWrite("E", asData[-2])
        self.tWorkSheetWrite("F", asData[-1])
        self.assertEqual("Finishing DFU block...OK\n", asData[-2])
        self.assertEqual("Closing connection...OK\n", asData[-1])
        self.Can.bBlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"], log=False)
           
    """
    Test Acknowledgement from STH. Write message and check identifier to be ack (No bError)
    """

    def test0002Ack(self):
        self.tWorkSheetWrite("D", "This test case checks the ability to communicate with the STH")
        cmd = self.Can.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 1, 0)
        expectedData = ActiveState()
        expectedData.asbyte = 0
        expectedData.b.u2NodeState = Node["Application"]
        expectedData.b.u3NetworkState = NetworkState["Operating"]
        msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [expectedData.asbyte])
        self.Can.Logger.Info("Write Message")
        self.Can.WriteFrame(msg)
        self.Can.Logger.Info("Wait 200ms")
        time.sleep(0.2)
        cmd = self.Can.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 0, 0)
        msgAckExpected = self.Can.CanMessage20(cmd, MyToolItNetworkNr["STH1"], MyToolItNetworkNr["SPU1"], [0])
        self.Can.Logger.Info("Send ID: " + hex(msg.ID) + "; Expected ID: " + hex(msgAckExpected.ID) + "; Received ID: " + hex(self.Can.getReadMessage(-1).ID))
        self.Can.Logger.Info("Send Data: " + hex(0) + "; Expected Data: " + hex(expectedData.asbyte) + "; Received Data: " + hex(self.Can.getReadMessage(-1).DATA[0]))
        self.tWorkSheetWrite("E", "Test failed")
        self.assertEqual(hex(msgAckExpected.ID), hex(self.Can.getReadMessage(-1).ID))
        self.assertEqual(expectedData.asbyte, self.Can.getReadMessage(-1).DATA[0])
        self.tWorkSheetWrite("E", "Test OK")
        
    def test0010SthTemperature(self):
        self.tWorkSheetWrite("D", "Tests temperature")
        iTemperature = self._iSthAdcTemp()
        self.tWorkSheetWrite("E", "Tests temperature: " + str(iTemperature) + "°C")
        self.assertGreaterEqual(TempInternalProductionMax, iTemperature)
        self.assertLessEqual(TempInternalProductionTestMin, iTemperature)
        
    def test0020SthAccumulatorVoltage(self):
        self.tWorkSheetWrite("D", "Tests accumulator voltage")
        index = self.Can.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], 1, 0, 0)
        iBatteryVoltage = iMessage2Value(self.Can.getReadMessageData(index)[2:4])
        fBatteryVoltage = fVoltageBattery(iBatteryVoltage)
        self.tWorkSheetWrite("E", "Accumulator Voltage: " + str(fBatteryVoltage) + "V")
        self.assertGreaterEqual(VoltMiddleBat + VoltToleranceBat, fBatteryVoltage)
        self.assertLessEqual(VoltMiddleBat - VoltToleranceBat, fBatteryVoltage)
        
    """
    Checks that correct Firmware Version has been installed
    """

    def test0040Version(self):
        self.tWorkSheetWrite("D", "Check that the correct firmware version has been installed")
        iIndex = self.Can.cmdSend(MyToolItNetworkNr["STH1"], MyToolItBlock["ProductData"], MyToolItProductData["FirmwareVersion"], [])
        au8Version = self.Can.getReadMessageData(iIndex)[-3:]
        sVersionRead = "v" + str(au8Version[0]) + "." + str(au8Version[1]) + "." + str(au8Version[2])
        if sVersionRead == sVersion:
            self.tWorkSheetWrite("E", "OK")
        else:
            self.tWorkSheetWrite("E", "NOK")
        self.assertEqual(sVersionRead, sVersion)
    
    """
    Test Reset
    """   

    def test0099Reset(self):
        self.tWorkSheetWrite("D", "Tests Reset Command")
        self._resetSth()
        self.Can.bBlueToothConnectPollingName(MyToolItNetworkNr["STU1"], TestConfig["DevName"], log=False)
        index = self.Can.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], 1, 0, 0)
        iBatteryVoltage = iMessage2Value(self.Can.getReadMessageData(index)[2:4])
        fBatteryVoltage = fVoltageBattery(iBatteryVoltage)
        if 3 < fBatteryVoltage:
            self.tWorkSheetWrite("E", "OK")
        else:
            self.tWorkSheetWrite("E", "NOK")
        self.assertGreaterEqual(VoltMiddleBat + VoltToleranceBat, fBatteryVoltage)
        self.assertLessEqual(VoltMiddleBat - VoltToleranceBat, fBatteryVoltage)
        
    """
    Test that RSSI is good enough
    """

    def test0100Rssi(self):
        self.tWorkSheetWrite("D", "Tests RSSI")
        iRssiSth = int(self.Can.BlueToothRssi(MyToolItNetworkNr["STH1"]))
        iRssiStu = int(self.Can.BlueToothRssi(MyToolItNetworkNr["STU1"]))
        self.tWorkSheetWrite("E", "RSSI @ STH: " + str(iRssiSth) + "dBm")
        self.tWorkSheetWrite("F", "RSSI @ STU: " + str(iRssiStu) + "dBm")
        self.assertGreater(iRssiSth, RssiSthMin)
        self.assertLess(iRssiSth, -20)
        self.assertGreater(iRssiStu, RssiStuMin)
        self.assertLess(iRssiStu, -20)
        
    """
    Checks Acceleration at apparent gravity
    """

    def test0200AccXApparentGravity(self):
        self.tWorkSheetWrite("D", "Acceleration X - Apparent gravity")
        index = self.Can.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 1, 0, 0)
        [val1, _val2, _val3] = self.Can.singleValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 1, 0, 0, index)
        fAccX = fAcceleration(val1[0])
        self.tWorkSheetWrite("E", "Acceleration X - Apparent gravity: " + str(fAccX) + "g")
        self.assertGreaterEqual(AdcMiddleX + AdcToleranceX, fAccX)
        self.assertLessEqual(AdcMiddleX - AdcToleranceX, fAccX)

#     def test0201AccYApparentGravity(self):
#         self.tWorkSheetWrite("D", "Acceleration Y - Apparent gravity")
#         index = self.Can.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 0, 1, 0)
#         [_val1, val2, _val3] = self.Can.singleValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 0, 1, 0, index)
#         fAccY = fAcceleration(val2[0])
#         self.tWorkSheetWrite("E", "Acceleration Y - Apparent gravity: " + str(fAccY) + "V")
#         self.assertGreaterEqual(AdcMiddleY + AdcToleranceY, fAccY)
#         self.assertLessEqual(AdcMiddleY - AdcToleranceY, fAccY)        
# 
#     def test0202AccZApparentGravity(self):
#         self.tWorkSheetWrite("D", "Acceleration Z - Apparent gravity")
#         index = self.Can.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 0, 0, 1)
#         [_val1, _val2, val3] = self.Can.singleValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 0, 0, 1, index)
#         fAccZ = fAcceleration(val3[0])
#         self.tWorkSheetWrite("E", "Acceleration Z - Apparent gravity: " + str(fAccZ) + "V")
#         self.assertGreaterEqual(AdcMiddleY + AdcToleranceY, fAccZ)
#         self.assertLessEqual(AdcMiddleY - AdcToleranceY, fAccZ)  

    """
    Checks AccX SNR
    """

    def test0210AccXSnr(self):
        self.tWorkSheetWrite("D", "Test Acceleration SNR")
        self.TurnOffLed()
        [indexStart, indexEnd] = self.Can.streamingValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 1, 4000)
        [array1, array2, array3] = self.Can.streamingValueArray(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], DataSets[1], 1, 1, 1, indexStart, indexEnd)
        StatisticsNonShaking = self.Can.streamingValueStatistics(array1, array2, array3)
        NonShakingAccXSnrRaw = 20 * math.log((StatisticsNonShaking["Value1"]["StandardDeviation"] / AdcMax), 10)
#         NonShakingAccYSnrRaw = 20 * math.log((StatisticsNonShaking["Value2"]["StandardDeviation"] / AdcMax), 10)
#         NonShakingAccZSnrRaw = 20 * math.log((StatisticsNonShaking["Value3"]["StandardDeviation"] / AdcMax), 10)
        self.tWorkSheetWrite("E", "SNR AccX Raw non shaking: " + str(NonShakingAccXSnrRaw) + "g")
        self.assertGreaterEqual(abs(NonShakingAccXSnrRaw), abs(SigIndAccXSNR))
#         self.assertGreaterEqual(abs(NonShakingAccYSnrRaw), abs(SigIndAccYSNR))
#         self.assertGreaterEqual(abs(NonShakingAccZSnrRaw), abs(SigIndAccZSNR))
        
    """
    Determine correct meassuring via self test 
    """
      
    def test0220AccSelfTest(self): 
        self.tWorkSheetWrite("D", "Acceleration Sensor Self Test")
        self.TurnOffLed()
        kX1ack = self.Can.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["Acc"], 1, AdcReference["VDD"])
        kX1 = iMessage2Value(kX1ack[4:])
        self.Can.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Inject"], CalibMeassurementTypeNr["Acc"], 1, AdcReference["VDD"])
        time.sleep(0.1)
        kX2ack = self.Can.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["Acc"], 1, AdcReference["VDD"])
        kX2 = iMessage2Value(kX2ack[4:])
        self.Can.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Eject"], CalibMeassurementTypeNr["Acc"], 1, AdcReference["VDD"])
        time.sleep(0.1)
        kX3ack = self.Can.calibMeasurement(MyToolItNetworkNr["STH1"], CalibMeassurementActionNr["Measure"], CalibMeassurementTypeNr["Acc"], 1, AdcReference["VDD"])
        kX3 = iMessage2Value(kX3ack[4:])
        k1mVX = (50 * AdcReference["VDD"]) * kX1 / AdcMax
        k2mVX = (50 * AdcReference["VDD"]) * kX2 / AdcMax
        k3mVX = (50 * AdcReference["VDD"]) * kX3 / AdcMax
        self.tWorkSheetWrite("E", "k1 before self test: " + str(k1mVX) + "mV")
        self.tWorkSheetWrite("F", "k2 at self test: " + str(k2mVX) + "mV")
        self.tWorkSheetWrite("G", "k3 at self test: " + str(k3mVX) + "mV")
        iDelta = k2mVX - k1mVX
        self.assertGreater(k2mVX, k1mVX)
        self.assertGreater(k2mVX, k3mVX)  
        self.assertGreater(k1mVX + 20, k3mVX) 
        self.assertGreater(k3mVX + 20, k1mVX)    
        self.assertGreater(iDelta, 50) 
        self.assertLess(iDelta, 150) 
         
    """
    Voltage zero balance
    """   

    def test0300AccCalibrationVoltage(self):
        self.tWorkSheetWrite("D", "Calibrate Battery Voltage i.e. calculate k and get d via zero balance(kx+d)")
        afBatteryVoltage = []
        for _i in range(0, 9):
            index = self.Can.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], 1, 0, 0)
            iBatteryVoltage = iMessage2Value(self.Can.getReadMessageData(index)[2:4])
            fBatteryVoltage = fVoltageBattery(iBatteryVoltage)
            afBatteryVoltage.append(fBatteryVoltage)
        afBatteryVoltage.sort()
        fD = float(3.2 - afBatteryVoltage[4])
        fD = struct.unpack("f", struct.pack("f", fD))[0]
        sD = str(fD)
        fK = float(kBattery)
        fK = struct.unpack("f", struct.pack("f", fK))[0]
        sK = str(fK)
        self.tWorkSheetWrite("E", "k: " + sK)
        self.tWorkSheetWrite("F", "d: " + sD + "V")
        self.vChangeExcelCell("Calibration0@0x8", "E8", sK)
        self.vChangeExcelCell("Calibration0@0x8", "E9", sD)
        
    """
    Acceleration X zero balance
    """

    def test0320AccCalibrationAcceleration(self):
        self.tWorkSheetWrite("D", "Calibrate Acceleration X i.e. calculate k and get d via zero balance(kx+d)")
        afAccelerationX = []
        for _i in range(0, 9):
            index = self.Can.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Acceleration"], 1, 0, 0)
            iAccX = iMessage2Value(self.Can.getReadMessageData(index)[2:4])
            fAccX = fAcceleration(iAccX)
            afAccelerationX.append(fAccX)
        afAccelerationX.sort()
        fD = float(0 - afAccelerationX[4])
        fD += dAccX
        fD = struct.unpack("f", struct.pack("f", fD))[0]
        sD = str(fD)
        fK = float(kAccX)
        fK = struct.unpack("f", struct.pack("f", fK))[0]
        sK = str(fK)
        self.tWorkSheetWrite("E", "k: " + sK)
        self.tWorkSheetWrite("F", "d: " + sD + "g")
        self.vChangeExcelCell("Calibration0@0x8", "E2", sK)
        self.vChangeExcelCell("Calibration0@0x8", "E3", sD)
    
    """
    Write EEPROM with calibration data an read it back to check it as well
    """

    def test0399Eerpom(self):
        self.tWorkSheetWrite("D", "Write EEPROM with data and check that by read")
        # Batch Number
        batchFile = open("BatchNumberSth.txt")
        batchData = batchFile.readlines()
        batchData = batchData[0]
        batchFile.close()
        batchFile = open("BatchNumberSth.txt", "w")
        sStoreFileName = "./ResultsSth/OK_" + self.sTestReport + "_nr1.xlsx"
        iBatchNr = int(batchData)
        if False != os.path.isfile(sStoreFileName):
            iBatchNr += 1
        sBatchNumber = str(iBatchNr)
        batchFile.write(sBatchNumber)
        batchFile.close()
        self.vChangeExcelCell("Statistics@0x5", "E8", sBatchNumber)
        # Write
        workSheetNames = []
        workbook = openpyxl.load_workbook(self.sExcelEepromContentFileName)
        if workbook:
            for worksheetName in workbook.sheetnames:
                sName = str(worksheetName).split('@')
                _sAddress = sName[1]
                sName = sName[0]
                workSheetNames.append(sName)  
        sDate = date.today()
        sDate = str(sDate).replace('-', '')
        self.vChangeExcelCell("Statistics@0x5", "E7", sDate)       
        for pageName in workSheetNames:
            sError = self.sExcelSheetWrite(pageName, MyToolItNetworkNr["STH1"])  
            if None != sError:
                break      
        # Read Back
        sError = None
        copyfile(self.sExcelEepromContentFileName, self.sExcelEepromContentReadBackFileName)
        for pageName in workSheetNames:
            sError = self.sExcelSheetRead(pageName, MyToolItNetworkNr["STH1"])
            if None != sError:
                break
        [tWorkSheetNameError, sCellNumberError] = self.tCompareEerpomWriteRead()
        self.tWorkSheetWrite("E", "Error Worksheet: " + str(tWorkSheetNameError))
        self.tWorkSheetWrite("F", "Error Cell: " + str(sCellNumberError))
        self.assertEqual(tWorkSheetNameError, None)
            
                
    """
    Move Test Report to Results
    """

    def test9999StoreTestResults(self):
        global bSkip
        self.tWorkSheetWrite("D", "Store Results")
        if False != os.path.isfile(self.sExcelEepromContentReadBackFileName):
            tWorkbookContent = openpyxl.load_workbook(self.sExcelEepromContentReadBackFileName)
            for worksheetName in tWorkbookContent.sheetnames:
                tWorkSheet = self.tWorkbook.create_sheet(worksheetName)
                tWorkSheetContent = tWorkbookContent.get_sheet_by_name(worksheetName)
                for row in tWorkSheetContent:
                    for cell in row:
                        tWorkSheet[cell.coordinate].value = cell.value
            tWorkbookContent.close()
            os.remove(self.sExcelEepromContentReadBackFileName)
        if False != bSkip:
            self.tWorkSheetWrite("E", "NOK")   
            self.tWorkbook.save(self.sTestReport + ".xlsx")  
            for i in range(0,100):
                sStoreFileName = "./ResultsSth/NOK_" + self.sTestReport + "_nr" + str(i) + ".xlsx"
                if False == os.path.isfile(sStoreFileName):
                    os.rename(self.sTestReport + ".xlsx", sStoreFileName)    
                    break                  
        else:
            self.tWorkSheetWrite("E", "OK")
            self.tWorkbook.save(self.sTestReport + ".xlsx")
            for i in range(0,100):
                sStoreFileName = "./ResultsSth/OK_" + self.sTestReport + "_nr" + str(i) + ".xlsx"
                if False == os.path.isfile(sStoreFileName):
                    if 2 == i:
                        self.Can.Standby(MyToolItNetworkNr["STH1"])
                    os.rename(self.sTestReport + ".xlsx", sStoreFileName) 
                    break
                
if __name__ == "__main__":
    sLogLocation = sys.argv[1]
    sLogFile = sys.argv[2]
    if '/' != sLogLocation[-1]:
        sLogLocation += '/'
    sLogFileLocation = sLogLocation + sLogFile
    sLogLocation = sLogLocation
    sVersion = sys.argv[3]
    sDirName = os.path.dirname(sLogFileLocation)
    sys.path.append(sDirName)

    if not os.path.exists(sDirName):
        os.makedirs(sDirName)
    with open(sLogFileLocation, "w") as f:    
        runner = unittest.TextTestRunner(f)
        unittest.main(argv=['first-arg-is-ignored'], testRunner=runner)  
