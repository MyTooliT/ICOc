import unittest
import CanFd
import time
import array
import openpyxl
import os
import sys
import struct
import SthLimits
import MyToolItSth
from datetime import date
from shutil import copyfile
from openpyxl.styles import Font
from MyToolItNetworkNumbers import MyToolItNetworkNr 
from MyToolItStu import TestConfig, StuErrorWord

from StuLimits import PcbOnly, RssiStuMin
from MyToolItCommands import *
from openpyxl.descriptors.base import DateTime

sVersion = "v2.1.4"
sLogName = 'ProductionTestStu'
sLogLocation = '../../Logs/ProductionTestStu/'
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
        self.iTestNumber = int(self._testMethodName[4:8])
        self.fileName = sLogLocation + self._testMethodName + ".txt"
        self.fileNameError = sLogLocation + "Error_" + self._testMethodName + ".txt"
        self.sExcelEepromContentFileName = "Stu" + sVersion + ".xlsx"
        if False != bSkip and "test9999StoreTestResults" != self._testMethodName:
            self.skipTest("At least some previous test failed")
        else:
            self.Can = CanFd.CanFd(CanFd.PCAN_BAUD_1M, self.fileName, self.fileNameError, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], 0, 0, 0, FreshLog=True)
            self.Can.Logger.Info("TestCase: " + str(self._testMethodName))
            self.Can.CanTimeStampStart(self._resetStu()["CanTime"])  # This will also reset to STH
            self.sStuAddr = sBlueToothMacAddr(self.Can.BlueToothAddress(MyToolItNetworkNr["STU1"]))
            self.Can.Logger.Info("STU BlueTooth Address: " + self.sStuAddr)
            self.sSerialNumber = sSerialNumber(self.sExcelEepromContentFileName)
            self.sExcelEepromContentReadBackFileName = sLogName + "_" + self.sSerialNumber + "_" + self.sStuAddr.replace(":", "#") + "_ReadBack.xlsx"
            self.sDateClock = sDateClock() 
            self.sTestReport = sLogName + "_" + self.sSerialNumber + "_" + self.sStuAddr.replace(":", "#")
            self.tWorkbookOpenCreate()
            self._statusWords()
            self._SthWDog()
            self.Can.Logger.Info("_______________________________________________________________________________________________________________")
            self.Can.Logger.Info("Start")

    def tearDown(self):
        global bSkip
        self.Can.Logger.Info("Fin")
        self.Can.Logger.Info("_______________________________________________________________________________________________________________")
        if "test9999StoreTestResults" != self._testMethodName:
            self.tWorkbook.save(self.sTestReport + ".xlsx")
        self._statusWords()
        self.Can.Logger.Info("Test Time End Time Stamp")
        self.Can.__exit__()
        if self._outcome.errors[1][1]:
            bSkip = True
        if False != self.bError:
            bSkip = True

    def _resetStu(self, retries=5, log=True):
        self.Can.bConnected = False
        return self.Can.cmdReset(MyToolItNetworkNr["STU1"], retries=retries, log=log)
    
    def _statusWords(self):
        ErrorWord = StuErrorWord()
        psw0 = self.Can.statusWord0(MyToolItNetworkNr["STU1"])
        self.Can.Logger.Info("STU Status Word: " + hex(psw0))
        ErrorWord.asword = self.Can.statusWord1(MyToolItNetworkNr["STU1"])
        self.Can.Logger.Info("STU Error Word: " + hex(ErrorWord.asword))

    def _SthWDog(self):
        WdogCounter = iMessage2Value(self.Can.statisticalData(MyToolItNetworkNr["STU1"], MyToolItStatData["Wdog"])[:4])
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
            self.tWorkSheet = self.tWorkbook.create_sheet(self.sStuAddr.replace(":", "#"))
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
        self.tWorkSheet = self.tWorkbook.get_sheet_by_name(self.sStuAddr.replace(":", "#"))
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
    Test Acknowledgement from STH. Write message and check identifier to be ack (No bError)
    """

    def test0002Ack(self):
        self.tWorkSheetWrite("D", "This test case checks the ability to communicate with the STU")
        cmd = self.Can.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 1, 0)
        expectedData = ActiveState()
        expectedData.asbyte = 0
        expectedData.b.u2NodeState = Node["Application"]
        expectedData.b.u3NetworkState = NetworkState["Operating"]
        msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"], [expectedData.asbyte])
        self.Can.Logger.Info("Write Message")
        self.Can.WriteFrame(msg)
        self.Can.Logger.Info("Wait 200ms")
        time.sleep(0.2)
        cmd = self.Can.CanCmd(MyToolItBlock["System"], MyToolItSystem["ActiveState"], 0, 0)
        msgAckExpected = self.Can.CanMessage20(cmd, MyToolItNetworkNr["STU1"], MyToolItNetworkNr["SPU1"], [0])
        self.Can.Logger.Info("Send ID: " + hex(msg.ID) + "; Expected ID: " + hex(msgAckExpected.ID) + "; Received ID: " + hex(self.Can.getReadMessage(-1).ID))
        self.Can.Logger.Info("Send Data: " + hex(0) + "; Expected Data: " + hex(expectedData.asbyte) + "; Received Data: " + hex(self.Can.getReadMessage(-1).DATA[0]))
        self.tWorkSheetWrite("E", "Test failed")
        self.assertEqual(hex(msgAckExpected.ID), hex(self.Can.getReadMessage(-1).ID))
        self.assertEqual(expectedData.asbyte, self.Can.getReadMessage(-1).DATA[0])
        self.tWorkSheetWrite("E", "Test OK")
        
    """
    Checks that correct Firmware Version has been installed
    """

    def test0040Version(self):
        self.tWorkSheetWrite("D", "Check that the correct firmware version has been installed")
        iIndex = self.Can.cmdSend(MyToolItNetworkNr["STU1"], MyToolItBlock["ProductData"], MyToolItProductData["FirmwareVersion"], [])
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
        self._resetStu()
        self.test0002Ack()
        
    """
    Test that RSSI is good enough
    """

    def test0100Rssi(self):
        self.tWorkSheetWrite("D", "Tests RSSI")
        self.Can.bBlueToothConnectPollingName(MyToolItNetworkNr["STU1"], MyToolItSth.TestConfig["DevName"], log=False)
        time.sleep(1)
        self.sStuAddr = sBlueToothMacAddr(self.Can.BlueToothAddress(MyToolItNetworkNr["STU1"]))
        self.sSthAddr = sBlueToothMacAddr(self.Can.BlueToothAddress(MyToolItNetworkNr["STH1"]))
        self.Can.Logger.Info("STH BlueTooth Address: " + self.sSthAddr)
        iRssiSth = int(self.Can.BlueToothRssi(MyToolItNetworkNr["STH1"]))
        iRssiStu = int(self.Can.BlueToothRssi(MyToolItNetworkNr["STU1"]))
        self.tWorkSheetWrite("E", "RSSI @ STH: " + str(iRssiSth) + "dBm")
        self.tWorkSheetWrite("F", "RSSI @ STU: " + str(iRssiStu) + "dBm")
        self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])
        self.assertGreater(iRssiSth, SthLimits.RssiSthMin)
        self.assertLess(iRssiSth, -20)
        self.assertGreater(iRssiStu, RssiStuMin)
        self.assertLess(iRssiStu, -20)
         
    """
    Write EEPROM
    """

    def test0399Eerpom(self):
        for i in range(0, 100):
            print(str(i))
            self.tWorkSheetWrite("D", "Write EEPROM with data and check that by read")
            # Batch Number
            batchFile = open("BatchNumberStu.txt")
            batchData = batchFile.readlines()
            batchData = batchData[0]
            batchFile.close()
            batchFile = open("BatchNumberStu.txt", "w")
            iBatchNr = int(batchData)
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
                sError = self.sExcelSheetWrite(pageName, MyToolItNetworkNr["STU1"])  
                if None != sError:
                    break      
            # Read Back
            sError = None
            copyfile(self.sExcelEepromContentFileName, self.sExcelEepromContentReadBackFileName)
            for pageName in workSheetNames:
                sError = self.sExcelSheetRead(pageName, MyToolItNetworkNr["STU1"])
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
            for i in range(0, 100):
                sStoreFileName = "./ResultsSth/NOK_" + self.sTestReport + "_nr" + str(i) + ".xlsx"
                if False == os.path.isfile(sStoreFileName):
                    os.rename(self.sTestReport + ".xlsx", sStoreFileName)    
                    break                  
        else:
            self.tWorkSheetWrite("E", "OK")
            self.tWorkbook.save(self.sTestReport + ".xlsx")
            for i in range(0, 100):
                sStoreFileName = "./ResultsSth/OK_" + self.sTestReport + "_nr" + str(i) + ".xlsx"
                if False == os.path.isfile(sStoreFileName):
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
