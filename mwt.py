
from myToolItWatch import myToolItWatch
from MyToolItCommands import *
from MyToolItNetworkNumbers import *
from time import sleep
import glob
import curses
import os
import PeakCanFd


class mwt(myToolItWatch):

    def __init__(self):
        myToolItWatch.__init__(self)
        self.bTerminal = False
        
    def close(self):
        self.PeakCan.Logger.Info("Close Terminal")
        self.vTerminalTeardown()            
        myToolItWatch.close(self) 
        
    def vTerminalHolderConnectCommandsAdcConfig(self):
        self.stdscr.addstr("Prescaler(2-127): ")
        self.stdscr.refresh()
        iPrescaler = self.iTerminalInputNumberIn()
        self.stdscr.addstr("Aquisition Time")
        self.vListKeys(AdcAcquisitionTime)
        self.stdscr.refresh()
        iAquisitionTime = self.iTerminalInputNumberIn()
        self.stdscr.addstr("Oversampling Rate")
        self.vListKeys(AdcOverSamplingRate)
        self.stdscr.refresh()
        iOversamplingRate = self.iTerminalInputNumberIn()
        self.stdscr.addstr("ADC Reference")
        self.vListKeys(AdcReference)
        self.stdscr.refresh()     
        sAdcRef = self.sTerminalInputStringIn()        
        try:
            self.vAdcConfig(iPrescaler, iAquisitionTime, iOversamplingRate)
            self.vAdcRefVConfig(sAdcRef)
        except:
            pass
    
    def vTerminalHolderConnectCommandsRunTimeIntervalTime(self):
        self.stdscr.addstr("Run Time(s): ")
        self.stdscr.refresh()            
        iRunTime = self.iTerminalInputNumberIn()   
        self.stdscr.addstr("Interval Time(s; 0=No Interval Files): ")
        self.stdscr.refresh()            
        iIntervalTime = self.iTerminalInputNumberIn() 
        self.vRunTime(iRunTime, iIntervalTime)
    
    
    def tTerminalHolderConnectCommandsKeyEvaluation(self):
        keyPress = self.stdscr.getch()
        bRun = True
        bContinue = False
        if (0x03 == keyPress):
            bRun = False
        elif ord('a') == keyPress:
            self.vTerminalHolderConnectCommandsAdcConfig()
        elif ord('d') == keyPress:
            self.stdscr.addstr("Display Time(s): ")
            self.stdscr.refresh()            
            iDisplayTime = self.iTerminalInputNumberIn()  
            self.vDisplayTime(iDisplayTime)
        elif ord('e') == keyPress:
            bRun = False
            bContinue = True 
            self.PeakCan.BlueToothDisconnect(MyToolItNetworkNr["STU1"])
        elif ord('f') == keyPress:
            self.stdscr.clear()
            self.stdscr.refresh()
            sOemFreeUse = self.PeakCan.sProductData("OemFreeUse")  
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
                self.PeakCan.Standby(MyToolItNetworkNr["STH1"])
                bRun = False
                self.PeakCan.bConnected = False
                bContinue = True
        elif ord('p') == keyPress:
            self.stdscr.addstr("New sample axis (xyz; 0=off, 1=on; e.g. 100): ")
            iPoints = self.iTerminalInputNumberIn() 
            bZ = bool(iPoints & 1)
            bY = bool((iPoints >> 1) & 1)
            bX = bool((iPoints >> 2) & 1)
            self.vAccSet(bX, bY, bZ, -1)
        elif ord('r') == keyPress:
            self.vTerminalHolderConnectCommandsRunTimeIntervalTime()
        elif ord('s') == keyPress:
            self.vDataAquisition()
            bRun = False
        elif ord('S') == keyPress: 
            self.stdscr.clear()
            self.stdscr.refresh()
            sSerialNumber = self.PeakCan.sProductData("SerialNumber")  
            sName = self.PeakCan.sProductData("Name")  
            self.stdscr.addstr("Serial: " + sSerialNumber + " " + sName + "\n")  
            self.vTerminalAnyKey()
        elif ord('v') == keyPress:
            self.vVoltageSet(1, 0, 0, -1)
        elif ord('V') == keyPress:
            self.vVoltageSet(0, 0, 0, -1)             
        return [bRun, bContinue]      
     
    def bTerminalHolderConnectCommandsShowDataValues(self):
        sGtin = self.PeakCan.sProductData("GTIN")  
        sHwRev = self.PeakCan.sProductData("HardwareRevision")  
        sSwVersion = self.PeakCan.sProductData("FirmwareVersion")  
        sReleaseName = self.PeakCan.sProductData("ReleaseName")  
        self.stdscr.addstr("Global Trad Identifcation Number (GTIN): " + sGtin + "\n")
        self.stdscr.addstr("Hardware Revision(Major.Minor.Build): " + sHwRev + "\n")
        self.stdscr.addstr("Firmware Version(Major.Minor.Build): " + sSwVersion + "\n")
        self.stdscr.addstr("Firmware Release Name: " + sReleaseName + "\n")
        index = self.PeakCan.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], 1, 0, 0)
        iBatteryVoltage = messageValueGet(self.PeakCan.getReadMessageData(index)[2:4]) / 1000
        if None != iBatteryVoltage:
            self.stdscr.addstr("Battery Voltage: " + str(iBatteryVoltage) + "V\n")   

        
                  
    def bTerminalHolderConnectCommands(self):
        bContinue = True
        bRun = True
        
        while False != bRun:
            self.stdscr.clear()
            self.stdscr.addstr("Device Name: " + str(self.sDevName) + "\n")
            self.stdscr.addstr("Bluetooth address: " + str(self.iAddress) + "\n")
            self.bTerminalHolderConnectCommandsShowDataValues()
            self.stdscr.addstr("AutoConnect?: " + str(self.bSthAutoConnect) + "\n")
            self.stdscr.addstr("Run Time: " + str(self.iRunTime) + "s\n")
            self.stdscr.addstr("Inteval Time: " + str(self.iIntervalTime) + "s\n")
            self.stdscr.addstr("Display Time: " + str(self.iDisplayTime) + "s\n")
            self.stdscr.addstr("Adc Prescaler/AcquisitionTime/OversamplingRate/Reference(Samples/s): " + str(self.iPrescaler) + "/" + str(AdcAcquisitionTimeReverse[self.iAquistionTime]) + "/" + str(AdcOverSamplingRateReverse[self.iOversampling]) + "/" + str(self.sAdcRef) + "(" + str(self.samplingRate) + ")\n")
            self.stdscr.addstr("Acc Config(XYZ/DataSets): " + str(int(self.bAccX)) + str(int(self.bAccY)) + str(int(self.bAccZ)) + "/" + str(DataSetsReverse[self.tAccDataFormat]) + "\n")
            self.stdscr.addstr("Voltage Config(XYZ/DataSets): " + str(int(self.bVoltageX)) + str(int(self.bVoltageY)) + str(int(self.bVoltageZ)) + "/" + str(DataSetsReverse[self.tVoltageDataFormat]) + ("(X=Battery)\n"))
            self.stdscr.addstr("a: Config ADC\n")
            self.stdscr.addstr("d: Config display Time\n")
            self.stdscr.addstr("e: Exit and disconnect from holder\n")
            self.stdscr.addstr("f: OEM Free Use\n")
            self.stdscr.addstr("n: Set Device Name\n")
            self.stdscr.addstr("O: Off(Standby)\n")
            self.stdscr.addstr("p: Config Acceleration Points(XYZ)\n")
            self.stdscr.addstr("r: Config run time and interval time\n")
            self.stdscr.addstr("s: Start Data Aquisition\n")
            self.stdscr.addstr("S: Serial Number(and Name)\n")
            self.stdscr.addstr("v: Activate Battery Voltage Streaming\n")
            self.stdscr.addstr("V: Disable Battery Voltage Streaming\n")
            self.stdscr.refresh()

            [bRun, bContinue] = self.tTerminalHolderConnectCommandsKeyEvaluation()
        return bContinue
                                
    def bTerminalHolderConnect(self, keyPress):
        self.PeakCan.Logger.Info("Start bTerminalHolderConnect")
        iNumber = int(keyPress - ord('0'))
        keyPress = -1
        self.PeakCan.Logger.Info("Start Loop")
        bRun = True
        bContinue = False
        devList = None
        while False != bRun:
            devList = self.tTerminalHeaderExtended(devList)
            self.stdscr.addstr(str(iNumber))
            self.stdscr.refresh()
            keyPress = self.stdscr.getch()
            if ord('0') <= keyPress and ord('9') >= keyPress:         
                iNumber = self.iTerminalInputNumber(iNumber, keyPress)   
            elif 0x08 == keyPress:
                if 1 < len(str(iNumber)):
                    iNumber = int(str(iNumber)[:-1])
                else:
                    iNumber = 0
            elif 0x0A == keyPress:
                if 0 < iNumber:
                    iNumber-=1
                    self.stdscr.addstr("\nTry to connect to device number " + str(iNumber) + "\n")
                    self.stdscr.refresh()
                    self.PeakCan.Logger.Info("Device List: " + str(devList))
                    for dev in devList:
                        iDevNumber = int(dev["DeviceNumber"])
                        if iDevNumber == iNumber:
                            self.vDeviceAddressSet(str(dev["Address"]))
                            self.stdscr.addstr("Connect to " + hex(dev["Address"]) + "(" + str(dev["Name"]) + ")\n")
                            self.stdscr.refresh()
                            self.PeakCan.BlueToothConnectPollingAddress(MyToolItNetworkNr["STU1"], self.iAddress)
                            bContinue = self.bTerminalHolderConnectCommands()
                else:
                    bContinue = True
                bRun = False
            elif(0x03 == keyPress) or (ord('q') == keyPress):
                bRun = False
                bContinue = True
            else:
                devList = None
            keyPress = -1
        return bContinue
    
    def vTerminalEepromExcelChange(self):
        self.stdscr.addstr("Please enter Excel File name for new Excel Sheet")
        sFileName = self.sTerminalInputStringIn()
        if ".xlsx" == sFileName[-5:]:
            self.vSheetFileSet(sFileName)
        else:
            self.stdscr.addstr(".xlsx file ending required")
            self.stdscr.refresh()
            sleep(1)
        
    def tTerminalEepromKeyEvaluation(self):
        keyPress = self.stdscr.getch()
        bRun = True
        bContinue = False
        if 0x03 == keyPress:
            bRun = False
        elif ord('x') == keyPress:
            self.vTerminalEepromExcelChange()
        elif ord('l') == keyPress:
            atList = self.atTerminalXmlProductVersionList()
            self.vTerminalXmlProductVersionChange(atList)
        elif ord('e') == keyPress:
            bRun = False
            bContinue = True
        
            
        return [bRun, bContinue]
            
    def bTerminalEeprom(self):
        bRun = True
        bContinue = False
        while False != bRun:
            self.stdscr.clear()
            self.stdscr.addstr("Device: " + str(self.sProduct) + "\n")
            self.stdscr.addstr("Version: " + str(self.sConfig) + "\n")
            self.stdscr.addstr("Excel Sheet Name(.xlsx): " + str(self.sSheetFile) + "\n")    
            self.stdscr.addstr("e: Escape(Exit) this menu\n")
            self.stdscr.addstr("l: List devices and versions (an change current device/product)\n")
            self.stdscr.addstr("x: Chance Excel Sheet Name(.xlsx)\n")          
            if None != self.sSheetFile and "STU" == self.sProduct and None != self.sConfig:
                try:
                    pageNames = self.atExcelSheetNames()
                    pageNumber = 0
                    for pageName in pageNames:
                        self.stdscr.addstr(str(pageNumber) + ": Read Page " + str(pageName) + "\n")
                        pageNumber += 1  
                except:
                    self.excelSheetCreate()
                self.stdscr.refresh()

            [bRun, bContinue] = self.tTerminalEepromKeyEvaluation()
        return bContinue
        
        
    def vTerminalLogFileName(self):
        self.stdscr.addstr("Log File Name(" + self.PeakCan.Logger.fileName + "): ")  
        sLogFileName = self.sTerminalInputStringIn()       
        self.bLogSet(sLogFileName)
        self.stdscr.addstr("" + self.PeakCan.Logger.fileName)
        self.stdscr.refresh()
        sleep(2)
        
    def vTerminalDeviceName(self):
        self.stdscr.addstr("New Device Name (max. 8 characters): ")
        self.stdscr.refresh()   
        sName = self.sTerminalInputStringIn()         
        self.vDeviceNameSet(sName)
        self.PeakCan.BlueToothNameWrite(0, sName)
    
    def bTerminalTests(self):
        bContinue = True
        self.tTerminalHeaderExtended() 
        pyFiles = []
        for file in glob.glob("./VerficationInternal/*.py"):
            file = file.split("\\")
            pyFiles.append(file[-1])
        self.stdscr.addstr("\nVerficationInternal: \n")
        iTestNumber = 1
        for i in range(0, len(pyFiles)):
            self.stdscr.addstr("    " + str(iTestNumber) + ": " + pyFiles[i] + "\n")
            iTestNumber += 1
        self.stdscr.refresh()
        self.stdscr.addstr("Attention! If you want to kill the test press CTRL+Break(STRG+Pause)\n")
        self.stdscr.addstr("Please pick a test number or 0 to escape: ")
        iTestNumberRun = self.iTerminalInputNumberIn() 
        if 0 < iTestNumberRun and iTestNumberRun < iTestNumber:
            self.PeakCan.__exit__() 
            sDirPath = os.path.dirname(os.path.realpath(pyFiles[iTestNumberRun - 1]))
            sDirPath += "\\VerficationInternal\\"
            sDirPath += pyFiles[iTestNumberRun - 1]
            try:
                os.system("python " + str(sDirPath) + " ../Logs/STH SthAuto.txt")
            except KeyboardInterrupt:
                pass
            self.PeakCan = PeakCanFd.PeakCanFd(PeakCanFd.PCAN_BAUD_1M, "init.txt", "initError.txt", MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"])
        return bContinue
                
           
    def vTerminalXmlProductVersionCreate(self, atList):
        self.stdscr.addstr("Device for deriving: ")
        iProduct = self.iTerminalInputNumberIn()
        if iProduct in atList:
            self.stdscr.addstr("Version for deriving: ")
            iVersion = self.iTerminalInputNumberIn()
            if iVersion in atList[iProduct]["Versions"]:
                self.stdscr.addstr("New Version Name: ")
                sVersionName = self.sTerminalInputStringIn()
                self.newXmlVersion(atList[iProduct]["Product"], atList[iProduct]["Versions"][iVersion], sVersionName)
                
                    
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
                self.vConfigSet(atList[iProduct]["Product"].get('name'), atList[iProduct]["Versions"][iVersion].get('name'))  
                    
    def atTerminalXmlProductVersionList(self):
        self.stdscr.clear()
        atList = self.atXmlProductVersion()
        self.stdscr.refresh()
        for key in atList.keys(): 
            product = atList[key]          
            self.stdscr.addstr("Device " + str(key) + ": " + str(product["Product"].get('name')) + "\n")
            for key in product["Versions"].keys():
                version = product["Versions"][key]
                self.stdscr.addstr("         " + str(key) + ": " + str(version.get('name')) + "\n")
        self.stdscr.refresh()
        return atList
    
    def atTerminalXmlSetupList(self):
        self.stdscr.clear()
        atSetups = self.atXmlSetup()
        for key in atSetups.keys(): 
            self.stdscr.addstr(str(key) + ": " + atSetups[key].get('name') + "\n")
            
        self.stdscr.addstr("Choose device to show settings or 0 to escape: ")
        self.stdscr.refresh()
        iSetup = self.iTerminalInputNumberIn()
        if iSetup in atSetups:
            tSetup = atSetups[iSetup]
            self.stdscr.addstr("Device Name: " + tSetup.find('DeviceName').text + "\n")
            self.stdscr.addstr("Acceleration Points(X/Y/Z): " + tSetup.find('Acc').text + "\n")
            self.stdscr.addstr("Prescaler: " + tSetup.find('Prescaler').text + "\n")
            self.stdscr.addstr("Acquisition Time: " + tSetup.find('AcquisitionTime').text + "\n")
            self.stdscr.addstr("Oversampling Rate: " + tSetup.find('OverSamples').text + "\n")
            iAcquisitionTime = AdcAcquisitionTime[int(tSetup.find('AcquisitionTime').text)]
            iOversampling = AdcOverSamplingRate[int(tSetup.find('OverSamples').text)]
            samplingRate = int(calcSamplingRate(int(tSetup.find('Prescaler').text), iAcquisitionTime, iOversampling) + 0.5)
            self.stdscr.addstr("Derived samplring rate from upper three parameters: " + str(samplingRate) + "\n")
            self.stdscr.addstr("ADC Reference Voltage: " + tSetup.find('AdcRef').text + "\n")
            self.stdscr.addstr("Log Name: " + tSetup.find('LogName').text + "\n")
            self.stdscr.addstr("RunTime/IntervalTime: " + tSetup.find('RunTime').text + "/" + tSetup.find('DisplayTime').text + "\n")
            self.stdscr.addstr("Display Time: " + tSetup.find('DisplayTime').text + "\n")              
            self.stdscr.refresh()
        return atSetups  
        
    def vTerminalXmlProductVersionRemove(self, atList):
        self.stdscr.addstr("Device for version removing: ")
        iProduct = self.iTerminalInputNumberIn()
        if iProduct in atList:
            self.stdscr.addstr("Version to remove: ")
            iVersion = self.iTerminalInputNumberIn()
            if iVersion in atList[iProduct]["Versions"]:
                self.removeXmlVersion(atList[iProduct]["Product"], atList[iProduct]["Versions"][iVersion])
     
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
        self.stdscr.addstr("Please Type in new overer sampling rate: ")
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
        
    def vTerminalXmlSetupModifyRunIntervalTime (self):   
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
                        self.stdscr.addstr("1 : Device Name: " + self.sDevName + "\n")
                        self.stdscr.addstr(" : XML Device Name: " + setup.find('DeviceName').text + "\n")
                        self.stdscr.addstr("2: Acceleration Points(X/Y/Z): " + str(int(self.bAccX)) + str(int(self.bAccY)) + str(int(self.bAccZ)) + "\n")
                        self.stdscr.addstr(" : XML Acceleration Points(X/Y/Z): " + setup.find('Acc').text + "\n")
                        self.stdscr.addstr("3: Voltage Points(X/Y/Z): " + str(int(self.bVoltageX)) + str(int(self.bVoltageY)) + str(int(self.bVoltageZ)) + "\n")
                        self.stdscr.addstr(" : XML Voltage Points(X/Y/Z): " + setup.find('Voltage').text + "\n")
                        iAcquisitionTime = AdcAcquisitionTimeReverse[self.iAquistionTime]
                        iOversampling = AdcOverSamplingRateReverse[self.iOversampling]
                        self.stdscr.addstr("4: Prescaler/AcquisitionTime/OversamplingRate(samples/s): " + str(self.iPrescaler) + "/" + str(iAcquisitionTime) + "/" + str(iOversampling) + "(" + str(self.samplingRate) + ")\n") 
                        iPrescaler = int(setup.find('Prescaler').text)
                        iAcquisitionTime = int(setup.find('AcquisitionTime').text)
                        iOversampling = int(setup.find('OverSamples').text)
                        iSamplingRate = int(calcSamplingRate(int(setup.find('Prescaler').text), AdcAcquisitionTime[iAcquisitionTime], AdcOverSamplingRate[iOversampling]) + 0.5)
                        self.stdscr.addstr(" : XML Prescaler/AcquisitionTime/OversamplingRate(samples/s): " + str(iPrescaler) + "/" + str(iAcquisitionTime) + "/" + str(iOversampling) + "(" + str(iSamplingRate) + ")\n")               
                        self.stdscr.addstr("5: ADC Reference Voltage: " + self.sAdcRef + "\n")
                        self.stdscr.addstr(" : XML ADC Reference Voltage: " + setup.find('AdcRef').text + "\n")
                        self.stdscr.addstr("6: Log Name: " + self.PeakCan.Logger.fileName + "\n")
                        self.stdscr.addstr(" : XML Log Name: " + setup.find('LogName').text + "\n")
                        self.stdscr.addstr("7: RunTime/IntervalTime: " + str(self.iRunTime) + "/" + str(self.iIntervalTime) + "\n")
                        self.stdscr.addstr(" : XML RunTime/IntervalTime: " + setup.find('RunTime').text + "/" + setup.find('DisplayTime').text + "\n")
                        self.stdscr.addstr("8: Display Time: " + str(self.iDisplayTime) + "\n")
                        self.stdscr.addstr(" : XML Display Time: " + setup.find('DisplayTime').text + "\n")
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
            atList = self.atTerminalXmlProductVersionList()
            self.vTerminalXmlProductVersionCreate(atList)
        elif ord('C') == keyPress:
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
        return [bRun, bContinue]
      
    def bTerminalXml(self):
        bRun = True
        while False != bRun:
            self.stdscr.clear()
            self.stdscr.addstr("Device: " + str(self.sProduct) + "\n")
            self.stdscr.addstr("Version: " + str(self.sConfig) + "\n")
            self.stdscr.addstr("Predefined Setup: " + str(self.sSetupConfig) + "\n")
            self.stdscr.addstr("c: Create new Version\n")
            self.stdscr.addstr("C: Create new Setup\n")
            self.stdscr.addstr("e: Exit\n")
            self.stdscr.addstr("l: List devices and versions (an change current device/product)\n")
            self.stdscr.addstr("L: List Setups (an change current device/product)\n")
            self.stdscr.addstr("r: Remove Version\n")
            self.stdscr.addstr("R: Remove Setup\n")
            self.stdscr.addstr("S: Modyfiy current selected predefined setup\n")  
            self.stdscr.refresh()
            [bRun, bContinue] = self.vTerminalXmlKeyEvaluation()
        return bContinue
    
    
    def bTerminalMainMenuKeyEvaluation(self, devList):
        bRun = True
        keyPress = self.stdscr.getch()
        if ord('q') == keyPress:
            bRun = False
        elif 0x03 == keyPress:  # CTRL+C
            bRun = False
        elif ord('1') <= keyPress and ord('9') >= keyPress:
            self.PeakCan.Logger.Info("Call bTerminalHolderConnect")
            bRun = self.bTerminalHolderConnect(keyPress)
        elif ord('E') == keyPress:    
            bRun = self.bTerminalEeprom() 
        elif ord('l') == keyPress:  # CTRL+C    
            self.vTerminalLogFileName()
        elif ord('n') == keyPress:
            self.stdscr.addstr("Pick a device number from the list: ")
            self.stdscr.refresh()            
            iDevice = self.iTerminalInputNumberIn()  
            if 0 < iDevice:
                iDevice-=1
                bConnected = False
                for dev in devList:
                    iDevNumber = int(dev["DeviceNumber"])
                    if iDevNumber == iDevice:
                        self.vDeviceAddressSet(str(dev["Address"]))
                        self.stdscr.addstr("Connect to " + hex(dev["Address"]) + "(" + str(dev["Name"]) + ")\n")
                        self.stdscr.refresh()
                        self.PeakCan.BlueToothConnectPollingAddress(MyToolItNetworkNr["STU1"], self.iAddress)
                        self.vTerminalDeviceName()
                        self.PeakCan.BlueToothDisconnect(MyToolItNetworkNr["STU1"])
                        bConnected = True        
                if False == bConnected:
                    self.stdscr.addstr("Device was not available\n")
                    self.stdscr.refresh()    
        elif ord('t') == keyPress:    
            bRun = self.bTerminalTests()              
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
        self.stdscr.addstr("Press any key to continue\n")
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
            elif 0x0A == iKeyPress:
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
            elif 0x0A == iKeyPress:
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
        self.vTerminalNew()
        self.stdscr.clear()
        bRun = True
        while False != bRun:
            try:
                bRun = self.bTerminalMainMenu()
            except KeyboardInterrupt:
                self.KeyBoadInterrupt = True
                break

    def tTerminalHeaderExtended(self, devList=None):
        self.vTerminalHeader()
        if None == devList:
            devList = self.PeakCan.tDeviceList(MyToolItNetworkNr["STU1"])
        for dev in devList:
            self.stdscr.addstr("Device Number: " + str(dev["DeviceNumber"]+1) + "; Name: " + str(dev["Name"]) + "; Address: " + hex(dev["Address"]) + "; RSSI: " + str(dev["RSSI"]) + "\n") 
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
