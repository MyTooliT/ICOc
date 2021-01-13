from myToolItWatch import myToolItWatch
from MyToolItCommands import *
from MyToolItNetworkNumbers import *
from MyToolItSth import fVoltageBattery
from time import sleep
import glob
import curses
import os
from network import Network
import subprocess


class mwt(myToolItWatch):
    def __init__(self):
        myToolItWatch.__init__(self)
        self.process = None
        self.bTerminal = False
        self.vNetworkNumberSet(None)

    def close(self):
        if None != self.process:
            self.process.terminate()
        self.vCloseSaveStoreLastConfig()
        self.vTerminalTeardown()
        myToolItWatch.close(self)

    def bLastConfig(self):
        bLoadLastConfig = True
        for key in self.args_dict.keys():
            if None != self.args_dict[key] and False != self.args_dict[key]:
                if 'xml_file_name' != key:
                    bLoadLastConfig = False
        return bLoadLastConfig

    def vOpenLastConfig(self):
        if False != self.bLastConfig():
            lastRun = self.tXmlConfig.tree.find('lastRun')
            self.bLogSet(str(lastRun.find('LogName').text) + ".txt")
            self.vConfigSet(str(lastRun.find('Product').text),
                            str(lastRun.find('Version').text))
            self.vNetworkNumberSet(str(lastRun.find('NetworkNumber').text))
            sFileName = str(lastRun.find('SheetFile').text) + ".xlsx"
            self.vSheetFileSet(sFileName)
            self.bSampleSetupSet(str(lastRun.find('Setup').text))

    def vCloseSaveStoreLastConfig(self):
        lastRun = self.tXmlConfig.tree.find('lastRun')
        sLogName = self.Can.Logger.fileName.split('_')[0]
        sLogName = sLogName.split('.')[0]  # Just to be sure
        lastRun.find('LogName').text = str(sLogName)
        lastRun.find('Product').text = self.sProduct
        lastRun.find('Version').text = self.sConfig
        lastRun.find('NetworkNumber').text = self.sNetworkNumber
        if None != self.sSheetFile:
            sSheetFile = self.sSheetFile.split('.')[0]
        else:
            sSheetFile = self.sSheetFile
        lastRun.find('SheetFile').text = str(sSheetFile)
        lastRun.find('Setup').text = self.sSetupConfig
        self.xmlSave()

    # setter methods
    def vNetworkNumberSet(self, sNetworkNumber):
        if sNetworkNumber in MyToolItNetworkNr:
            self.sNetworkNumber = sNetworkNumber
        elif "0" == sNetworkNumber:
            self.sNetworkNumber = "BroadCast"
        elif "31" == sNetworkNumber:
            self.sNetworkNumber = "BroadCastNoAck"
        else:
            self.sNetworkNumber = None

    def vTerminalHolderConnectCommandsAdcConfig(self):
        self.stdscr.clear()
        self.stdscr.addstr("Prescaler(2-127): ")
        self.stdscr.refresh()
        iPrescaler = self.iTerminalInputNumberIn()
        self.stdscr.addstr("Acquisition Time")
        self.vListKeys(AdcAcquisitionTime)
        self.stdscr.refresh()
        iAquisitionTime = self.iTerminalInputNumberIn()
        self.stdscr.addstr("Oversampling Rate")
        self.vListKeys(AdcOverSamplingRate)
        self.stdscr.refresh()
        iOversamplingRate = self.iTerminalInputNumberIn()
        self.stdscr.addstr("ADC Reference(VDD=3V3)")
        self.vListKeys(AdcReference)
        self.stdscr.refresh()
        sAdcRef = self.sTerminalInputStringIn()
        try:
            self.vAdcConfig(iPrescaler, iAquisitionTime, iOversamplingRate)
            self.vAdcRefVConfig(sAdcRef)
        except:
            pass

    def vTerminalHolderConnectCommandsRunTimeIntervalTime(self):
        self.stdscr.clear()
        self.stdscr.addstr("Run Time(s): ")
        self.stdscr.refresh()
        iRunTime = self.iTerminalInputNumberIn()
        self.stdscr.addstr("Interval Time(s; 0=No Interval Files): ")
        self.stdscr.refresh()
        iIntervalTime = self.iTerminalInputNumberIn()
        self.vRunTime(iRunTime, iIntervalTime)

    def vTerminalHolderConnectCommandsRunTimeDisplayTime(self):
        self.stdscr.clear()
        self.stdscr.addstr("Display Time(1-10s, 0=Off): ")
        self.stdscr.refresh()
        iDisplayTime = self.iTerminalInputNumberIn()
        self.vDisplayTime(iDisplayTime)

    def tTerminalHolderConnectCommandsKeyEvaluation(self):
        keyPress = self.stdscr.getch()
        bRun = True
        bContinue = False
        if (0x03 == keyPress):
            bRun = False
        elif ord('a') == keyPress:
            self.vTerminalHolderConnectCommandsAdcConfig()
        elif ord('d') == keyPress:
            self.vTerminalHolderConnectCommandsRunTimeDisplayTime()
        elif ord('e') == keyPress:
            bRun = False
            bContinue = True
            self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])
        elif ord('f') == keyPress:
            self.stdscr.clear()
            self.stdscr.refresh()
            sOemFreeUse = self.Can.sProductData("OemFreeUse")
            self.stdscr.addstr("OEM Free Use: \n" + sOemFreeUse + "\n")
            self.vTerminalAnyKey()
        elif ord('n') == keyPress:
            self.vTerminalDeviceName()
        elif ord('O') == keyPress:
            self.stdscr.clear()
            self.stdscr.addstr("Are you really sure?\n")
            self.stdscr.addstr("Only charing will leave this state!!!!\n")
            self.stdscr.addstr("Pressing y will trigger standby: ")
            self.stdscr.refresh()
            sYes = self.sTerminalInputStringIn()
            if "y" == sYes:
                self.Can.Standby(MyToolItNetworkNr["STH1"])
                bRun = False
                self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])
                bContinue = True
        elif ord('p') == keyPress:
            self.stdscr.clear()
            self.stdscr.addstr(
                "New sample axis (xyz; 0=off, 1=on; e.g. 100): ")
            iPoints = self.iTerminalInputNumberIn()
            bZ = bool(iPoints & 1)
            bY = bool((iPoints >> 1) & 1)
            bX = bool((iPoints >> 2) & 1)
            self.vAccSet(bX, bY, bZ, -1)
        elif ord('r') == keyPress:
            self.vTerminalHolderConnectCommandsRunTimeIntervalTime()
        elif ord('s') == keyPress:
            self.stdscr.clear()
            if False == self.KeyBoardInterrupt:
                try:
                    self.vDataAquisition()
                except KeyboardInterrupt:
                    self.KeyBoardInterrupt = True
                    self.__exit__()
                bRun = False
        return [bRun, bContinue]

    def bTerminalHolderConnectCommandsShowDataValues(self):
        sGtin = self.Can.sProductData("GTIN", bLog=False)
        sHwRev = self.Can.sProductData("HardwareRevision", bLog=False)
        sSwVersion = self.Can.sProductData("FirmwareVersion", bLog=False)
        sReleaseName = self.Can.sProductData("ReleaseName", bLog=False)
        sSerialNumber = self.Can.sProductData("SerialNumber", bLog=False)
        sName = self.Can.sProductData("Name", bLog=False)
        sSerial = str(sSerialNumber + "-" + sName)
        self.stdscr.addstr("Global Trade Identification Number (GTIN): " +
                           sGtin + "\n")
        self.stdscr.addstr("Hardware Revision(Major.Minor.Build): " + sHwRev +
                           "\n")
        self.stdscr.addstr("Firmware Version(Major.Minor.Build): " +
                           sSwVersion + "\n")
        self.stdscr.addstr("Firmware Release Name: " + sReleaseName + "\n")
        self.stdscr.addstr("Serial: " + sSerial + "\n\n")
        index = self.Can.singleValueCollect(MyToolItNetworkNr["STH1"],
                                            MyToolItStreaming["Voltage"],
                                            1,
                                            0,
                                            0,
                                            log=False)
        iBatteryVoltage = byte_list_to_int(
            self.Can.getReadMessageData(index)[2:4])
        if None != iBatteryVoltage:
            fBatteryVoltage = fVoltageBattery(iBatteryVoltage)
            self.stdscr.addstr("Battery Voltage: " +
                               '{:02.2f}'.format(fBatteryVoltage) + "V\n")
        au8TempReturn = self.Can.calibMeasurement(
            MyToolItNetworkNr["STH1"],
            CalibMeassurementActionNr["Measure"],
            CalibMeassurementTypeNr["Temp"],
            1,
            AdcReference["1V25"],
            log=False)
        iTemperature = float(byte_list_to_int(au8TempReturn[4:]))
        iTemperature /= 1000
        self.Can.calibMeasurement(MyToolItNetworkNr["STH1"],
                                  CalibMeassurementActionNr["None"],
                                  CalibMeassurementTypeNr["Temp"],
                                  1,
                                  AdcReference["VDD"],
                                  log=False,
                                  bReset=True)
        if None != iTemperature:
            self.stdscr.addstr("Internal Chip Temperature: " +
                               '{:02.1f}'.format(iTemperature) + "°C\n\n")

    def bTerminalHolderConnectCommands(self):
        bContinue = True
        bRun = True
        self.vDisplayTime(10)
        while False != bRun:
            self.stdscr.clear()
            self.stdscr.addstr(
                int_to_mac_address(int(self.iAddress, 16)) + "(" +
                str(self.sDevName) + ")\n")
            self.bTerminalHolderConnectCommandsShowDataValues()
            self.stdscr.addstr("Run Time: " + str(self.iRunTime) + "s\n")
            self.stdscr.addstr("Interval Time: " + str(self.iIntervalTime) +
                               "s\n")
            self.stdscr.addstr(
                "Adc Prescaler/AcquisitionTime/OversamplingRate/Reference(Samples/s): "
                + str(self.iPrescaler) + "/" +
                str(AdcAcquisitionTime.inverse[self.iAquistionTime]) + "/" +
                str(AdcOverSamplingRate.inverse[self.iOversampling]) + "/" +
                str(self.sAdcRef) + "(" + str(self.samplingRate) + ")\n")
            self.stdscr.addstr("Acc Config(XYZ/DataSets): " +
                               str(int(self.bAccX)) + str(int(self.bAccY)) +
                               str(int(self.bAccZ)) + "/" +
                               str(DataSets.inverse[self.tAccDataFormat]) +
                               "\n")
            self.stdscr.addstr("\n")
            self.stdscr.addstr("a: Config ADC\n")
            self.stdscr.addstr("d: Display Time\n")
            self.stdscr.addstr("e: Exit and disconnect from holder\n")
            self.stdscr.addstr("f: OEM Free Use\n")
            self.stdscr.addstr("n: Set Device Name\n")
            self.stdscr.addstr("O: Off(Standby)\n")
            self.stdscr.addstr("p: Config Acceleration Points(XYZ)\n")
            self.stdscr.addstr("r: Config run time and interval time\n")
            self.stdscr.addstr("s: Start Data Acquisition\n")
            self.stdscr.refresh()
            [bRun,
             bContinue] = self.tTerminalHolderConnectCommandsKeyEvaluation()
        return bContinue

    def bTerminalHolderConnect(self, iKeyPress):
        iNumber = int(iKeyPress - ord('0'))
        iKeyPress = -1
        bRun = True
        bContinue = False
        devList = None
        while False != bRun:
            devList = self.tTerminalHeaderExtended(devList)
            self.stdscr.addstr(str(iNumber))
            self.stdscr.refresh()
            iKeyPress = self.stdscr.getch()
            if ord('0') <= iKeyPress and ord('9') >= iKeyPress:
                iNumber = self.iTerminalInputNumber(iNumber, iKeyPress)
            elif 0x08 == iKeyPress:
                if 1 < len(str(iNumber)):
                    iNumber = int(str(iNumber)[:-1])
                else:
                    iNumber = 0
            elif 0x0A == iKeyPress or 459 == iKeyPress:
                if 0 < iNumber:
                    self.stdscr.addstr("\nTry to connect to device number " +
                                       str(iNumber) + "\n")
                    self.stdscr.refresh()
                    iNumber -= 1
                    for dev in devList:
                        if dev["DeviceNumber"] == iNumber:
                            self.vDeviceAddressSet(hex(dev["Address"]))
                            self.stdscr.addstr("Connect to " +
                                               hex(dev["Address"]) + "(" +
                                               str(dev["Name"]) + ")\n")
                            self.stdscr.refresh()
                            if False != self.Can.bBlueToothConnectPollingAddress(
                                    MyToolItNetworkNr["STU1"], self.iAddress):
                                bContinue = self.bTerminalHolderConnectCommands(
                                )
                else:
                    bContinue = True
                bRun = False
            elif (0x03 == iKeyPress) or (ord('q') == iKeyPress):
                bRun = False
                bContinue = True
            else:
                devList = None
            iKeyPress = -1
        return bContinue

    def vTerminalEepromChange(self):
        self.stdscr.addstr(
            "Please enter Excel File name for new Excel Sheet(.xlsx will be added): "
        )
        sFileName = self.sTerminalInputStringIn()
        if "" != sFileName:
            sFileName += ".xlsx"
            self.vSheetFileSet(sFileName)

    def bTerminalEepromRead(self, iReceiver):
        self.stdscr.addstr("Read ...\n")
        self.stdscr.refresh()
        pageNames = self.atExcelSheetNames()
        sError = None
        for pageName in pageNames:
            sError = self.sExcelSheetRead(pageName, iReceiver)
            if None != sError:
                break

        if None != sError:
            self.stdscr.addstr(sError + "@ page: " + str(pageName) + "\n")
            self.stdscr.refresh()
            sleep(3)
        return None == sError

    def bTerminalEepromWrite(self, iReceiver):
        self.stdscr.addstr("Write ...\n")
        self.stdscr.refresh()
        sError = None
        pageNames = self.atExcelSheetNames()
        for pageName in pageNames:
            sError = self.sExcelSheetWrite(pageName, iReceiver)
            if None != sError:
                break
        if None != sError:
            self.stdscr.addstr(sError + "@ page: " + str(pageName) + "\n")
            self.stdscr.refresh()
            sleep(3)
        return None == sError

    def tTerminalEepromCreateOpenExcelSheet(self):
        atExcelName = []
        bProductEeprom = ("STU" == self.sProduct) or ("STH" == self.sProduct)
        if None != self.sSheetFile and False != bProductEeprom and None != self.sConfig:
            try:
                atExcelName = self.atExcelSheetNames()
                atXmlList = self.atProductPages()
                bMatch = True
                if len(atExcelName) == len(atXmlList):
                    for i in range(0, len(atExcelName)):
                        if atExcelName[i] != atXmlList[i]["Name"]:
                            bMatch = False
                else:
                    bMatch = False
                if False == bMatch:
                    self.vExcelSheetCreate()
            except:
                try:
                    self.vExcelSheetCreate()
                    atExcelName = self.atExcelSheetNames()
                except:
                    self.stdscr.addstr(
                        "Please close opened Excel File. Can create fresh one(different device)\n"
                    )
                    self.stdscr.refresh()
                    sleep(5)
        return atExcelName

    def tTerminalEepromKeyEvaluation(self):
        keyPress = self.stdscr.getch()
        bRun = True
        bContinue = False
        if 0x03 == keyPress:
            self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])
            bRun = False
        elif ord('d') == keyPress:
            self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])
        elif ord('e') == keyPress:
            self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])
            bRun = False
            bContinue = True
        elif ord('l') == keyPress:
            atList = self.atTerminalXmlProductVersionList()
            self.vTerminalXmlProductVersionChange(atList)
            if None != self.sProduct and None != self.sConfig:
                self.stdscr.addstr("Please enter Network Number(1-14): ")
                iNetworkNumber = self.iTerminalInputNumberIn()
                if 0 < iNetworkNumber and 14 >= iNetworkNumber:
                    self.vNetworkNumberSet(self.sProduct + str(iNetworkNumber))
            else:
                self.vNetworkNumberSet(None)
            self.tTerminalEepromCreateOpenExcelSheet()
        elif ord('R') == keyPress:
            bShowReadWrite = (None != self.sSheetFile)
            bShowReadWrite = bShowReadWrite and ("STU" == self.sProduct
                                                 or "STH" == self.sProduct)
            bShowReadWrite = bShowReadWrite and (None != self.sConfig)
            bShowReadWrite = bShowReadWrite and (None != self.sNetworkNumber)
            if False != bShowReadWrite:
                if False != os.path.isfile(self.sSheetFile):
                    iReceiver = MyToolItNetworkNr[self.sNetworkNumber]
                    if MyToolItNetworkNr[
                            "STH1"] <= iReceiver and MyToolItNetworkNr[
                                "STH14"] >= iReceiver:
                        self.stdscr.clear()
                        self.vConnect()
                    if None != self.process:
                        self.process.terminate()
                    if False != self.Can.bConnected or MyToolItNetworkNr[
                            "STU1"] <= iReceiver:
                        if False != self.bTerminalEepromRead(iReceiver):
                            self.process = subprocess.Popen(
                                ['excel', self.sSheetFile],
                                stdout=subprocess.PIPE)
        elif ord('W') == keyPress:
            bShowReadWrite = (None != self.sSheetFile)
            bShowReadWrite = bShowReadWrite and ("STU" == self.sProduct
                                                 or "STH" == self.sProduct)
            bShowReadWrite = bShowReadWrite and (None != self.sConfig)
            bShowReadWrite = bShowReadWrite and (None != self.sNetworkNumber)
            if False != bShowReadWrite:
                if False != os.path.isfile(self.sSheetFile):
                    iReceiver = MyToolItNetworkNr[self.sNetworkNumber]
                    if MyToolItNetworkNr[
                            "STH1"] <= iReceiver and MyToolItNetworkNr[
                                "STH14"] >= iReceiver:
                        self.stdscr.clear()
                        self.vConnect()
                    if False != self.Can.bConnected or MyToolItNetworkNr[
                            "STU1"] <= iReceiver:
                        self.bTerminalEepromWrite(iReceiver)
        elif ord('I') == keyPress:
            bShowReadWrite = (None != self.sSheetFile)
            bShowReadWrite = bShowReadWrite and ("STU" == self.sProduct
                                                 or "STH" == self.sProduct)
            bShowReadWrite = bShowReadWrite and (None != self.sConfig)
            bShowReadWrite = bShowReadWrite and (None != self.sNetworkNumber)
            if False != bShowReadWrite:
                self.bEepromIgnoreReadErrors = not self.bEepromIgnoreReadErrors
        elif ord('x') == keyPress:
            self.vTerminalEepromChange()
            self.tTerminalEepromCreateOpenExcelSheet()
        return [bRun, bContinue]

    def bTerminalEeprom(self):
        bRun = True
        bContinue = False
        self.bEepromIgnoreReadErrors = False
        self.tTerminalEepromCreateOpenExcelSheet()
        while False != bRun:
            self.stdscr.clear()
            if False != self.Can.bConnected:
                self.stdscr.addstr("Connected: " + str(self.Can.iAddress) +
                                   "(" + str(self.Can.sDevName) + ")" + "\n")
                self.stdscr.addstr("d: Disconnect from device\n")
            self.stdscr.addstr("Device: " + str(self.sProduct) + "\n")
            self.stdscr.addstr("Version: " + str(self.sConfig) + "\n")
            self.stdscr.addstr("Network Number: " + str(self.sNetworkNumber) +
                               "\n")
            self.stdscr.addstr("Excel Sheet Name: " + str(self.sSheetFile) +
                               "\n")
            if False != self.bEepromIgnoreReadErrors:
                self.stdscr.addstr("EEPROM Read Errors will be ignored\n")
            self.stdscr.addstr("e: Escape this menu\n")
            self.stdscr.addstr(
                "l: List devices and versions (an change current device/product)\n"
            )
            self.stdscr.addstr("x: Chance Excel Sheet Name(.xlsx)\n")
            bShowReadWrite = (None != self.sSheetFile)
            bShowReadWrite = bShowReadWrite and ("STU" == self.sProduct
                                                 or "STH" == self.sProduct)
            bShowReadWrite = bShowReadWrite and (None != self.sConfig)
            bShowReadWrite = bShowReadWrite and (None != self.sNetworkNumber)
            if False != bShowReadWrite:
                self.stdscr.addstr("I: Ignore Read Errors\n")
                self.stdscr.addstr("R: Read all from EEPROM to sheet\n")
                self.stdscr.addstr("W: Write all from Sheet to EEPROM\n")
                self.stdscr.refresh()
            [bRun, bContinue] = self.tTerminalEepromKeyEvaluation()
        return bContinue

    def vTerminalLogFileName(self):
        self.stdscr.addstr("Log File Name(" + self.Can.Logger.fileName[0:-4] +
                           "): ")
        sLogFileName = self.sTerminalInputStringIn()
        if "" != sLogFileName:
            self.bLogSet(sLogFileName + '.txt')
        self.stdscr.addstr("" + self.Can.Logger.fileName)
        self.stdscr.refresh()
        sleep(2)

    def vTerminalDeviceName(self):
        self.stdscr.clear()
        self.stdscr.addstr("New Device Name (max. 8 characters): ")
        self.stdscr.refresh()
        sName = self.sTerminalInputStringIn()
        self.vDeviceNameSet(sName)
        self.Can.vBlueToothNameWrite(MyToolItNetworkNr["STH1"], 0, sName)

    def bTerminalTests(self):
        bContinue = True
        self.tTerminalHeaderExtended()
        pyFiles = []
        for file in glob.glob("./VerificationInternal/*.py"):
            file = file.split("\\")
            pyFiles.append(file[-1])
        self.stdscr.addstr("\nVerificationInternal: \n")
        iTestNumber = 1
        for i in range(0, len(pyFiles)):
            self.stdscr.addstr("    " + str(iTestNumber) + ": " + pyFiles[i] +
                               "\n")
            iTestNumber += 1
        self.stdscr.refresh()
        self.stdscr.addstr(
            "Attention! If you want to kill the test press CTRL+Break(STRG+Pause)\n"
        )
        self.stdscr.addstr("Please pick a test number or 0 to escape: ")
        iTestNumberRun = self.iTerminalInputNumberIn()
        if 0 < iTestNumberRun and iTestNumberRun < iTestNumber:
            self.Can.__exit__()
            sDirPath = os.path.dirname(
                os.path.realpath(pyFiles[iTestNumberRun - 1]))
            sDirPath += "\\VerificationInternal\\"
            sDirPath += pyFiles[iTestNumberRun - 1]
            try:
                sString = ""
                self.stdscr.clear()
                atList = self.atXmlProductVersion()
                if -1 != sDirPath.find("Sth"):
                    for key in atList[1]["Versions"]:
                        version = atList[1]["Versions"][key]
                        self.stdscr.addstr(
                            str(key) + ": " + str(version.get('name')) + "\n")
                        self.stdscr.refresh()
                    iVersion = self.iTerminalInputNumberIn()
                    if iVersion in atList[1]["Versions"] or True:
                        version = atList[1]["Versions"][iVersion]
                        sString = "python " + str(
                            sDirPath) + " ../Logs/STH SthAuto.txt " + str(
                                version.get('name'))
                else:
                    for key in atList[2]["Versions"]:
                        version = atList[2]["Versions"][key]
                        self.stdscr.addstr(
                            str(key) + ": " + str(version.get('name')) + "\n")
                        self.stdscr.refresh()
                    iVersion = self.iTerminalInputNumberIn()
                    if iVersion in atList[2]["Versions"] or True:
                        version = atList[2]["Versions"][iVersion]
                    sString = "python " + str(
                        sDirPath) + " ../Logs/STU StuAuto.txt " + str(
                            version.get('name'))
                if "" != sString:
                    os.system(sString)
                    self.iTerminalInputNumberIn()
            except KeyboardInterrupt:
                pass
                #TODO: Kill process
            self.Can = Network("init.txt", "initError.txt",
                               MyToolItNetworkNr["SPU1"],
                               MyToolItNetworkNr["STH1"])
        return bContinue

    def bTerminalUpdateConnectExecute(self, sAddr):
        bDoIt = True
        if "STH" == self.sProduct:
            sSystemCall = "FirmwareUpdates/STH/" + self.sConfig + "/ota-dfu.exe COM6 115200 "
            sSystemCall += "FirmwareUpdates/STH/" + self.sConfig + "/OtaServer.gbl "
        elif "STU" == self.sProduct:
            sSystemCall = "FirmwareUpdates/STU/" + self.sConfig + "/ota-dfu.exe COM6 115200 "
            sSystemCall += "FirmwareUpdates/STU/" + self.sConfig + "/OtaClient.gbl "
        else:
            bDoIt = False

        if False != bDoIt:
            sSystemCall += sAddr + " -> updateLog.txt "
            if os.name == 'nt':
                sSystemCall = sSystemCall.replace("/", "\\")
                os.system(sSystemCall)
            # for mac and linux(here, os.name is 'posix')
            else:
                os.system(sSystemCall)
        return bDoIt

    def bTerminalUpdateConnect(self, iKeyPress):
        iNumber = int(iKeyPress - ord('0'))
        iKeyPress = -1
        bRun = True
        bContinue = False
        devList = None
        sSthOta = ""
        sStuOta = ""
        if "STH" == self.sProduct:
            sSthOta = "FirmwareUpdates\\STH\\" + self.sConfig
        elif "STU" == self.sProduct:
            sStuOta = "FirmwareUpdates\\STU\\" + self.sConfig
        while False != bRun:
            if ((False != os.path.isdir(sSthOta))
                    or (False != os.path.isdir(sStuOta))):
                devList = self.tTerminalHeaderExtended()
            if False != os.path.isdir(sStuOta):
                self.stdscr.addstr(
                    str(BlueToothDeviceNr["Self"]) + "(STU): " +
                    self.sStuAddr + "(" + self.Can.BlueToothNameGet(
                        MyToolItNetworkNr["STU1"], BlueToothDeviceNr["Self"]) +
                    ")\n")
            self.stdscr.addstr(str(iNumber))
            self.stdscr.refresh()
            iKeyPress = self.stdscr.getch()
            if ord('0') <= iKeyPress and ord('9') >= iKeyPress:
                iNumber = self.iTerminalInputNumber(iNumber, iKeyPress)
            elif 0x08 == iKeyPress:
                if 1 < len(str(iNumber)):
                    iNumber = int(str(iNumber)[:-1])
                else:
                    iNumber = 0
            elif 0x0A == iKeyPress or 459 == iKeyPress:
                if 0 < iNumber:
                    self.stdscr.addstr("\nTry to update " + str(iNumber) +
                                       "\n")
                    self.stdscr.refresh()
                    sleep(1)
                    sAddr = ""
                    if BlueToothDeviceNr["Self"] == iNumber:
                        sAddr = self.sStuAddr
                    else:
                        iNumber -= 1
                        for dev in devList:
                            if dev["DeviceNumber"] == iNumber:
                                sAddr = int_to_mac_address(dev["Address"])
                    if "" != sAddr:
                        if BlueToothDeviceNr["Self"] == iNumber:
                            self.Can.bBlueToothDisconnect(
                                MyToolItNetworkNr["STU1"])
                        self.bTerminalUpdateConnectExecute(sAddr)
                        if BlueToothDeviceNr["Self"] == iNumber:
                            self.Can.vBlueToothConnectConnect(
                                MyToolItNetworkNr["STU1"])

                    else:
                        self.stdscr.addstr("Device does not exist")
                        self.stdscr.refresh()
                        sleep(2)
                else:
                    bContinue = True
                bRun = False
            elif (0x03 == iKeyPress) or (ord('q') == iKeyPress):
                bRun = False
                bContinue = True
            else:
                devList = None
            iKeyPress = -1
        return bContinue

    def bTerminalUpdateKeyEval(self):
        bRun = True
        keyPress = self.stdscr.getch()
        if ord('e') == keyPress:
            bRun = False
        elif 0x03 == keyPress:  # CTRL+C
            bRun = False
        elif ord('l') == keyPress:
            atList = self.atTerminalXmlProductVersionList()
            self.vTerminalXmlProductVersionChange(atList)
        elif ord('1') <= keyPress and ord('9') >= keyPress:
            bRun = self.bTerminalUpdateConnect(keyPress)
        return bRun

    def bTerminalUpdate(self):
        bRun = True
        while False != bRun:
            self.stdscr.clear()

            sSthOta = ""
            sStuOta = ""
            if "STH" == self.sProduct:
                sSthOta = "FirmwareUpdates\\STH\\" + self.sConfig
            elif "STU" == self.sProduct:
                sStuOta = "FirmwareUpdates\\STU\\" + self.sConfig

            if ((False != os.path.isdir(sSthOta))
                    or (False != os.path.isdir(sStuOta))):
                self.tTerminalHeaderExtended()
            if False != os.path.isdir(sStuOta):
                self.stdscr.addstr(
                    str(BlueToothDeviceNr["Self"]) + "(STU): " +
                    self.sStuAddr + "(" + self.Can.BlueToothNameGet(
                        MyToolItNetworkNr["STU1"], BlueToothDeviceNr["Self"]) +
                    ")\n")
            self.stdscr.addstr("Device: " + str(self.sProduct) + "\n")
            self.stdscr.addstr("Version: " + str(self.sConfig) + "\n")
            self.stdscr.addstr("\n")
            self.stdscr.addstr("1-9: Update number (ENTER at input end)\n")
            self.stdscr.addstr("e: Exit\n")
            self.stdscr.addstr(
                "l: List devices and versions (and change current device/product)\n"
            )
            bRun = self.bTerminalUpdateKeyEval()

    def vTerminalXmlProductVersionCreate(self, atList):
        self.stdscr.addstr("Device for deriving: ")
        iProduct = self.iTerminalInputNumberIn()
        if iProduct in atList:
            self.stdscr.addstr("Version for deriving: ")
            iVersion = self.iTerminalInputNumberIn()
            if iVersion in atList[iProduct]["Versions"]:
                self.stdscr.addstr("New Version Name: ")
                sVersionName = self.sTerminalInputStringIn()
                self.newXmlVersion(atList[iProduct]["Product"],
                                   atList[iProduct]["Versions"][iVersion],
                                   sVersionName)

    def vTerminalXmlSetupCreate(self, atList):
        self.stdscr.addstr("Version for deriving: ")
        iVersion = self.iTerminalInputNumberIn()
        if iVersion in atList:
            self.stdscr.addstr("New Setup Name: ")
            sSetupName = self.sTerminalInputStringIn()
            self.newXmlSetup(atList[iVersion], sSetupName)

    def vTerminalXmlProductVersionChange(self, atList):
        self.stdscr.addstr("Please chose device: ")
        self.stdscr.refresh()
        iProduct = self.iTerminalInputNumberIn()
        if iProduct in atList:
            self.stdscr.addstr("Please chose version: ")
            self.stdscr.refresh()
            iVersion = self.iTerminalInputNumberIn()
            if iVersion in atList[iProduct]["Versions"]:
                self.vConfigSet(
                    atList[iProduct]["Product"].get('name'),
                    atList[iProduct]["Versions"][iVersion].get('name'))

    def atTerminalXmlProductVersionList(self):
        self.stdscr.clear()
        atList = self.atXmlProductVersion()
        self.stdscr.refresh()
        for key in atList.keys():
            product = atList[key]
            self.stdscr.addstr("Device " + str(key) + ": " +
                               str(product["Product"].get('name')) + "\n")
            for key in product["Versions"].keys():
                version = product["Versions"][key]
                self.stdscr.addstr("         " + str(key) + ": " +
                                   str(version.get('name')) + "\n")
        self.stdscr.refresh()
        return atList

    def atTerminalXmlSetupList(self):
        self.stdscr.clear()
        atSetups = self.atXmlSetup()
        for key in atSetups.keys():
            self.stdscr.addstr(
                str(key) + ": " + atSetups[key].get('name') + "\n")

        self.stdscr.addstr("Choose device to show settings or 0 to escape: ")
        self.stdscr.refresh()
        iSetup = self.iTerminalInputNumberIn()
        if iSetup in atSetups:
            tSetup = atSetups[iSetup]
            self.stdscr.addstr("Device Name: " +
                               tSetup.find('DeviceName').text + "\n")
            self.stdscr.addstr("Acceleration Points(X/Y/Z): " +
                               tSetup.find('Acc').text + "\n")
            self.stdscr.addstr("Prescaler: " + tSetup.find('Prescaler').text +
                               "\n")
            self.stdscr.addstr("Acquisition Time: " +
                               tSetup.find('AcquisitionTime').text + "\n")
            self.stdscr.addstr("Oversampling Rate: " +
                               tSetup.find('OverSamples').text + "\n")
            iAcquisitionTime = AdcAcquisitionTime[int(
                tSetup.find('AcquisitionTime').text)]
            iOversampling = AdcOverSamplingRate[int(
                tSetup.find('OverSamples').text)]
            samplingRate = int(
                calcSamplingRate(int(tSetup.find('Prescaler').text),
                                 iAcquisitionTime, iOversampling) + 0.5)
            self.stdscr.addstr(
                "Derived sampling rate from upper three parameters: " +
                str(samplingRate) + "\n")
            self.stdscr.addstr("ADC Reference Voltage: " +
                               tSetup.find('AdcRef').text + "\n")
            self.stdscr.addstr("Log Name: " + tSetup.find('LogName').text +
                               "\n")
            self.stdscr.addstr("RunTime/IntervalTime: " +
                               tSetup.find('RunTime').text + "/" +
                               tSetup.find('DisplayTime').text + "\n")
            self.stdscr.addstr("Display Time: " +
                               tSetup.find('DisplayTime').text + "\n")
            self.stdscr.refresh()
        return atSetups

    def vTerminalXmlProductVersionRemove(self, atList):
        self.stdscr.addstr("Device for version removing: ")
        iProduct = self.iTerminalInputNumberIn()
        if iProduct in atList:
            self.stdscr.addstr("Version to remove: ")
            iVersion = self.iTerminalInputNumberIn()
            if iVersion in atList[iProduct]["Versions"]:
                self.removeXmlVersion(atList[iProduct]["Product"],
                                      atList[iProduct]["Versions"][iVersion])

    def vTerminalXmlSetupRemove(self, atList):
        self.stdscr.addstr("Chose setup to remove: ")
        iSetup = self.iTerminalInputNumberIn()
        if iSetup in atList and 1 < len(atList):
            self.removeXmlSetup(atList[iSetup])

    def vTerminalXmlSetupChange(self, atList):
        self.stdscr.addstr("Please chose setup: ")
        iSetup = self.iTerminalInputNumberIn()
        if iSetup in atList:
            self.bSampleSetupSet(atList[iSetup].get('name'))
            self.vGetXmlSetup()

    def vTerminalXmlSetupModifyDevName(self):
        self.stdscr.addstr("Please Type in new device Name: ")
        sDevName = self.sTerminalInputStringIn()
        self.vDeviceNameSet(sDevName)

    def vTerminalXmlSetupModifyAcc(self):
        self.stdscr.addstr("Please Type in new acceleration points: ")
        iSamplePoints = str(self.iTerminalInputNumberIn())
        bAccX = int(iSamplePoints[0])
        bAccY = int(iSamplePoints[1])
        bAccZ = int(iSamplePoints[2])
        self.vAccSet(bAccX, bAccY, bAccZ, -1)

    def vTerminalXmlSetupModifyVoltage(self):
        self.stdscr.addstr("Please Type in new voltage points: ")
        iSamplePoints = str(self.iTerminalInputNumberIn())
        bVoltageX = int(iSamplePoints[0])
        bVoltageY = int(iSamplePoints[1])
        bVoltageZ = int(iSamplePoints[2])
        self.vVoltageSet(bVoltageX, bVoltageY, bVoltageZ, -1)

    def vTerminalXmlSetupModifyAdc(self):
        self.stdscr.addstr("Please Type in new prescaler: ")
        iPrescaler = self.iTerminalInputNumberIn()
        self.stdscr.addstr("Please Type in new acquisition time: ")
        iAcquisitionTime = self.iTerminalInputNumberIn()
        self.stdscr.addstr("Please Type in new over sampling rate: ")
        iOversamples = self.iTerminalInputNumberIn()
        self.vAdcConfig(iPrescaler, iAcquisitionTime, iOversamples)

    def vTerminalXmlSetupModifyVRef(self):
        self.stdscr.clear()
        iNumber = 1
        tKeyDict = {}
        for key in AdcReference.keys():
            self.stdscr.addstr(str(iNumber) + ": " + str(key) + "\n")
            tKeyDict[iNumber] = str(key)
            iNumber += 1
        iSelection = self.iTerminalInputNumberIn()
        if iSelection in tKeyDict:
            self.vAdcRefVConfig(tKeyDict[iSelection])

    def vTerminalXmlSetupModifyLogName(self):
        self.vTerminalLogFileName()

    def vTerminalXmlSetupModifyRunIntervalTime(self):
        self.stdscr.addstr("Please Type in new Run Time: ")
        iRunTime = self.iTerminalInputNumberIn()
        self.stdscr.addstr("Please Type in new Interval Time: ")
        iIntervalTime = self.iTerminalInputNumberIn()
        self.vRunTime(iRunTime, iIntervalTime)

    def vTerminalXmlSetupModifyDisplayTime(self):
        self.stdscr.addstr("Please Type in new display time: ")
        iDisplayTime = self.iTerminalInputNumberIn()
        self.vDisplayTime(iDisplayTime)

    def bTerminalXmlSetupModifyKeyEvaluation(self):
        bReturn = True
        iSelection = self.iTerminalInputNumberIn()
        if 0 == iSelection:
            bReturn = False
        elif 1 == iSelection:
            self.vTerminalXmlSetupModifyDevName()
        elif 2 == iSelection:
            self.vTerminalXmlSetupModifyAcc()
        elif 3 == iSelection:
            self.vTerminalXmlSetupModifyVoltage()
        elif 4 == iSelection:
            self.vTerminalXmlSetupModifyAdc()
        elif 5 == iSelection:
            self.vTerminalXmlSetupModifyVRef()
        elif 6 == iSelection:
            self.vTerminalXmlSetupModifyLogName()
        elif 7 == iSelection:
            self.vTerminalXmlSetupModifyRunIntervalTime()
        elif 8 == iSelection:
            self.vTerminalXmlSetupModifyDisplayTime()
        elif 99 == iSelection:
            self.vSetXmlSetup()
            self.xmlSave()
        return bReturn

    def vTerminalXmlSetupModify(self):
        sSetupConfig = self.sSetupConfig
        if None != self.sSetupConfig:
            setup = None
            atSetups = self.atXmlSetup()
            for key in atSetups.keys():
                if atSetups[key].get('name') == self.sSetupConfig:
                    setup = atSetups[key]
            if None != setup:
                bRun = True
                while False != bRun:
                    if sSetupConfig != self.sSetupConfig:
                        bRun = False
                        for key in atSetups.keys():
                            if atSetups[key].get('name') == self.sSetupConfig:
                                setup = atSetups[key]
                                sSetupConfig = self.sSetupConfig
                                bRun = True
                    if False != bRun:
                        self.stdscr.clear()
                        self.stdscr.addstr(self.sSetupConfig + "\n\n")
                        self.stdscr.addstr("0: Exit\n")
                        self.stdscr.addstr("1 : Device Name: " +
                                           self.sDevName + "\n")
                        self.stdscr.addstr(" : XML Device Name: " +
                                           setup.find('DeviceName').text +
                                           "\n")
                        self.stdscr.addstr("2: Acceleration Points(X/Y/Z): " +
                                           str(int(self.bAccX)) +
                                           str(int(self.bAccY)) +
                                           str(int(self.bAccZ)) + "\n")
                        self.stdscr.addstr(
                            " : XML Acceleration Points(X/Y/Z): " +
                            setup.find('Acc').text + "\n")
                        self.stdscr.addstr("3: Voltage Points(X/Y/Z): " +
                                           str(int(self.bVoltageX)) +
                                           str(int(self.bVoltageY)) +
                                           str(int(self.bVoltageZ)) + "\n")
                        self.stdscr.addstr(" : XML Voltage Points(X/Y/Z): " +
                                           setup.find('Voltage').text + "\n")
                        iAcquisitionTime = AdcAcquisitionTime.inverse[
                            self.iAquistionTime]
                        iOversampling = AdcOverSamplingRate.inverse[
                            self.iOversampling]
                        self.stdscr.addstr(
                            "4: Prescaler/AcquisitionTime/OversamplingRate(samples/s): "
                            + str(self.iPrescaler) + "/" +
                            str(iAcquisitionTime) + "/" + str(iOversampling) +
                            "(" + str(self.samplingRate) + ")\n")
                        iPrescaler = int(setup.find('Prescaler').text)
                        iAcquisitionTime = int(
                            setup.find('AcquisitionTime').text)
                        iOversampling = int(setup.find('OverSamples').text)
                        iSamplingRate = int(
                            calcSamplingRate(
                                int(setup.find('Prescaler').text),
                                AdcAcquisitionTime[iAcquisitionTime],
                                AdcOverSamplingRate[iOversampling]) + 0.5)
                        self.stdscr.addstr(
                            " : XML Prescaler/AcquisitionTime/OversamplingRate(samples/s): "
                            + str(iPrescaler) + "/" + str(iAcquisitionTime) +
                            "/" + str(iOversampling) + "(" +
                            str(iSamplingRate) + ")\n")
                        self.stdscr.addstr("5: ADC Reference Voltage: " +
                                           self.sAdcRef + "\n")
                        self.stdscr.addstr(" : XML ADC Reference Voltage: " +
                                           setup.find('AdcRef').text + "\n")
                        self.stdscr.addstr("6: Log Name: " +
                                           self.Can.Logger.fileName + "\n")
                        self.stdscr.addstr(" : XML Log Name: " +
                                           setup.find('LogName').text + "\n")
                        self.stdscr.addstr("7: RunTime/IntervalTime: " +
                                           str(self.iRunTime) + "/" +
                                           str(self.iIntervalTime) + "\n")
                        self.stdscr.addstr(" : XML RunTime/IntervalTime: " +
                                           setup.find('RunTime').text + "/" +
                                           setup.find('DisplayTime').text +
                                           "\n")
                        self.stdscr.addstr("8: Display Time: " +
                                           str(self.iDisplayTime) + "\n")
                        self.stdscr.addstr(" : XML Display Time: " +
                                           setup.find('DisplayTime').text +
                                           "\n")
                        self.stdscr.addstr("99: Save to xml File\n")
                        self.stdscr.addstr("Your selection: ")
                        self.stdscr.refresh()
                        bRun = self.bTerminalXmlSetupModifyKeyEvaluation()

    def vTerminalXmlKeyEvaluation(self):
        bRun = True
        bContinue = False
        keyPress = self.stdscr.getch()
        if 0x03 == keyPress:  # CTRL+C
            bRun = False
        elif ord('c') == keyPress:
            if None != self.sProduct and None != self.sConfig:
                atList = self.atTerminalXmlProductVersionList()
                self.vTerminalXmlProductVersionCreate(atList)
        elif ord('C') == keyPress:
            if None != self.sSetupConfig:
                atList = self.atTerminalXmlSetupList()
                self.vTerminalXmlSetupCreate(atList)
        elif ord('e') == keyPress:
            bRun = False
            bContinue = True
        elif ord('l') == keyPress:
            atList = self.atTerminalXmlProductVersionList()
            self.vTerminalXmlProductVersionChange(atList)
        elif ord('L') == keyPress:
            atList = self.atTerminalXmlSetupList()
            self.vTerminalXmlSetupChange(atList)
        elif ord('r') == keyPress:
            atList = self.atTerminalXmlProductVersionList()
            self.vTerminalXmlProductVersionRemove(atList)
        elif ord('R') == keyPress:
            atList = self.atTerminalXmlSetupList()
            self.vTerminalXmlSetupRemove(atList)
        elif ord('S') == keyPress:
            self.vTerminalXmlSetupModify()
        elif ord('W') == keyPress:
            if None != self.sProduct and None != self.sConfig and None != self.sSheetFile:
                if None != self.process:
                    self.process.terminate()
                self.stdscr.addstr("Write...\n")
                self.stdscr.refresh()
                self.vExcelProductVersion2XmlProductVersion()
        elif ord('x') == keyPress:
            self.vTerminalEepromChange()
        elif ord('X') == keyPress:
            if None != self.sProduct and None != self.sConfig and None != self.sSheetFile:
                try:
                    self.stdscr.addstr("Create...\n")
                    self.stdscr.refresh()
                    if None != self.process:
                        self.process.terminate()
                    self.vExcelSheetCreate()
                    self.process = subprocess.Popen(['excel', self.sSheetFile],
                                                    stdout=subprocess.PIPE)
                except:
                    self.stdscr.addstr(
                        "Please close opened Excel File. Can create fresh one(different device)\n"
                    )
                    self.stdscr.refresh()
                    sleep(5)
        return [bRun, bContinue]

    def bTerminalXml(self):
        bRun = True
        while False != bRun:
            self.stdscr.clear()
            self.stdscr.addstr("Device: " + str(self.sProduct) + "\n")
            self.stdscr.addstr("Version: " + str(self.sConfig) + "\n")
            self.stdscr.addstr("Excel Sheet Name: " + str(self.sSheetFile) +
                               "\n")
            self.stdscr.addstr("Predefined Setup: " + str(self.sSetupConfig) +
                               "\n")
            if None != self.sProduct and None != self.sConfig:
                self.stdscr.addstr("c: Create new Version\n")
            if None != self.sSetupConfig:
                self.stdscr.addstr("C: Create new Setup\n")
            self.stdscr.addstr("e: Exit\n")
            self.stdscr.addstr(
                "l: List devices and versions (and change current device/product)\n"
            )
            self.stdscr.addstr(
                "L: List Setups (and change current device/product)\n")
            self.stdscr.addstr("r: Remove Version\n")
            self.stdscr.addstr("R: Remove Setup\n")
            if None != self.sSetupConfig:
                self.stdscr.addstr(
                    "S: Modify current selected predefined setup\n")
            if None != self.sProduct and None != self.sConfig and None != self.sSheetFile:
                self.stdscr.addstr("W: Write Excel Sheet to Product-Version\n")
            self.stdscr.addstr("x: Chance Excel Sheet Name(.xlsx)\n")
            if None != self.sProduct and None != self.sConfig and None != self.sSheetFile:
                self.stdscr.addstr("X: Write XML Config to Excel Sheet\n")
            self.stdscr.refresh()
            [bRun, bContinue] = self.vTerminalXmlKeyEvaluation()
        return bContinue

    def vConnect(self, devList=None):
        if None == devList:
            devList = self.Can.tDeviceList(MyToolItNetworkNr["STU1"],
                                           bLog=False)
            for dev in devList:
                self.stdscr.addstr(
                    str(dev["DeviceNumber"] + 1) + ": " +
                    int_to_mac_address(dev["Address"]) + "(" +
                    str(dev["Name"]) + ")@" + str(dev["RSSI"]) + "dBm\n")
        if False == self.Can.bConnected:
            self.stdscr.addstr("Pick a device number from the list: ")
            self.stdscr.refresh()
            iDevice = self.iTerminalInputNumberIn()
            if 0 < iDevice:
                iDevice -= 1
                for dev in devList:
                    iDevNumber = int(dev["DeviceNumber"])
                    if iDevNumber == iDevice:
                        self.vDeviceAddressSet(str(dev["Address"]))
                        self.stdscr.addstr("Connect to " +
                                           hex(dev["Address"]) + "(" +
                                           str(dev["Name"]) + ")\n")
                        self.stdscr.refresh()
                        self.Can.bBlueToothConnectPollingAddress(
                            MyToolItNetworkNr["STU1"], self.iAddress)
                        sleep(1)

    def bTerminalMainMenuKeyEvaluation(self, devList):
        bRun = True
        keyPress = self.stdscr.getch()
        if ord('q') == keyPress:
            bRun = False
        elif 0x03 == keyPress:  # CTRL+C
            bRun = False
        elif ord('1') <= keyPress and ord('9') >= keyPress:
            bRun = self.bTerminalHolderConnect(keyPress)
        elif ord('E') == keyPress:
            bRun = self.bTerminalEeprom()
        elif ord('l') == keyPress:  # CTRL+C
            self.vTerminalLogFileName()
        elif ord('n') == keyPress:
            self.vConnect(devList)
            if False != self.Can.bConnected:
                self.vTerminalDeviceName()
                self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])
            else:
                self.stdscr.addstr("Device was not available\n")
                self.stdscr.refresh()
        elif ord('t') == keyPress:
            bRun = self.bTerminalTests()
        elif ord('u') == keyPress:
            bRun = self.bTerminalUpdate()
        elif ord('x') == keyPress:
            bRun = self.bTerminalXml()
        return bRun

    def bTerminalMainMenu(self):
        devList = self.tTerminalHeaderExtended()
        self.stdscr.addstr("\n")
        self.stdscr.addstr("q: Quit program\n")
        self.stdscr.addstr("1-9: Connect to STH number (ENTER at input end)\n")
        self.stdscr.addstr("E: EEPROM (Permanent Storage)\n")
        self.stdscr.addstr("l: Log File Name\n")
        self.stdscr.addstr("n: Change Device Name\n")
        self.stdscr.addstr("t: Test Menu\n")
        self.stdscr.addstr("u: Update Menu\n")
        self.stdscr.addstr("x: Xml Data Base\n")
        self.stdscr.refresh()
        return self.bTerminalMainMenuKeyEvaluation(devList)

    def vListKeys(self, tDict):
        if 0 < len(tDict):
            self.stdscr.addstr("(")
        for key in sorted(tDict):
            if key != sorted(tDict)[-1]:
                self.stdscr.addstr(str(key) + ", ")
            else:
                self.stdscr.addstr(str(key) + "): ")

    def vTerminalAnyKey(self):
        self.stdscr.addstr("\nPress any key to continue\n")
        self.stdscr.refresh()
        iKeyPress = -1
        while -1 == iKeyPress:
            iKeyPress = self.stdscr.getch()

    def sTerminalInputStringIn(self):
        sString = ""
        iKeyPress = -1
        bRun = True
        cursorXPos = self.stdscr.getyx()[1] + 2
        cursorYPos = self.stdscr.getyx()[0]
        while False != bRun:
            self.stdscr.addstr(cursorYPos, cursorXPos, sString)
            self.stdscr.refresh()
            iKeyPress = self.stdscr.getch()

            if 0x03 == iKeyPress:  # CTRL+C
                bRun = False
            elif 0x0A == iKeyPress or 459 == iKeyPress:
                bRun = False
            elif 0x0B == iKeyPress:
                bRun = False
            elif (ord(' ') <= iKeyPress and ord('~') >= iKeyPress):
                sString = sString + chr(iKeyPress)
            elif 0x08 == iKeyPress:
                if 1 < len(sString):
                    sString = sString[:-1]
                else:
                    sString = ""
                self.stdscr.addstr(" ")
                for i in range(0, len(sString) + 1):
                    self.stdscr.addstr(cursorYPos, cursorXPos + i, " ")
                self.stdscr.refresh()
            else:
                pass

        self.stdscr.addstr("\n")
        self.stdscr.refresh()
        return sString

    def iTerminalInputNumberIn(self, iNumber=0):
        iKeyPress = -1
        bRun = True
        cursorXPos = self.stdscr.getyx()[1] + 2
        cursorYPos = self.stdscr.getyx()[0]
        while False != bRun:
            self.stdscr.addstr(cursorYPos, cursorXPos, str(iNumber))
            self.stdscr.refresh()
            iKeyPress = self.stdscr.getch()
            if ord('q') == iKeyPress:
                bRun = False
            elif 0x03 == iKeyPress:  # CTRL+C
                bRun = False
            elif 0x0A == iKeyPress or 459 == iKeyPress:
                bRun = False
            elif ord('0') <= iKeyPress and ord('9') >= iKeyPress:
                iNumber = self.iTerminalInputNumber(iNumber, iKeyPress)
            elif 0x08 == iKeyPress:
                if 1 < len(str(iNumber)):
                    iNumber = int(str(iNumber)[:-1])
                else:
                    iNumber = 0
                self.stdscr.addstr(" ")
                for i in range(0, len(str(iNumber)) + 1):
                    self.stdscr.addstr(cursorYPos, cursorXPos + i, " ")
                self.stdscr.refresh()
            else:
                pass
        self.stdscr.addstr("\n")
        self.stdscr.refresh()
        return iNumber

    def iTerminalInputNumber(self, iNumber, keyPress):
        iDigit = int(keyPress - ord('0'))
        iNumber *= 10
        iNumber += iDigit
        return iNumber

    def vTerminal(self):
        self.vOpenLastConfig()
        self.vTerminalNew()
        self.stdscr.clear()
        bRun = True
        while False != bRun:
            try:
                bRun = self.bTerminalMainMenu()
            except KeyboardInterrupt:
                self.KeyBoardInterrupt = True
                break

    def tTerminalHeaderExtended(self, devList=None):
        self.vTerminalHeader()
        if None == devList:
            devList = self.Can.tDeviceList(MyToolItNetworkNr["STU1"],
                                           bLog=False)
        for dev in devList:
            self.stdscr.addstr(
                str(dev["DeviceNumber"] + 1) + ": " +
                int_to_mac_address(dev["Address"]) + "(" + str(dev["Name"]) +
                ")@" + str(dev["RSSI"]) + "dBm\n")
        return devList

    def vTerminalHeader(self):
        self.stdscr.clear()
        self.stdscr.addstr("MyToolIt Terminal\n\n")

    def vTerminalNew(self):
        self.bTerminal = True
        # create a window object that represents the terminal window
        self.stdscr = curses.initscr()
        # Don't print what I type on the terminal
        curses.noecho()
        # React to every key press, not just when pressing "enter"
        curses.cbreak()
        # Enable easy key codes (will come back to this)
        self.stdscr.keypad(True)
        self.stdscr.nodelay(1)

    def vTerminalTeardown(self):
        if False != self.bTerminal:
            # reverse everything that you changed about the terminal
            curses.nocbreak()
            self.stdscr.keypad(False)
            curses.echo()
            # restore the terminal to its original state
            curses.endwin()
            self.bTerminal = False

    def vRunConsole(self):
        self._vRunConsoleStartup()
        self.reset()
        if False != self.bSthAutoConnect:
            self.vRunConsoleAutoConnect()
        else:
            self.vTerminal()
        self.close()


if __name__ == "__main__":
    mwt = mwt()
    mwt.vParserInit()
    mwt.vParserConsoleArgumentsPass()
    mwt.vRunConsole()
