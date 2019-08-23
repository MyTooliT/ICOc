
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
           
    def bTerminalHolderConnectCommands(self):
        bContinue = True
        bRun = True
        iBatteryVoltage = None
        keyPress = -1
        while False != bRun:
            self.stdscr.clear()
            self.stdscr.addstr("Device Name: " + str(self.sDevName) + "\n")
            self.stdscr.addstr("Bluetooth address: " + str(self.iAddress) + "\n")
            self.stdscr.addstr("AutoConnect?: " + str(self.bSthAutoConnect) + "\n")
            self.stdscr.addstr("Run Time: " + str(self.iRunTime) + "s\n")
            self.stdscr.addstr("Inteval Time: " + str(self.iIntervalTime) + "s\n")
            self.stdscr.addstr("Display Time: " + str(self.iDisplayTime) + "s\n")
            self.stdscr.addstr("Adc Prescaler/AcquisitionTime/OversamplingRate/Reference(Samples/s): " + str(self.iPrescaler) + "/" + str(AdcAcquisitionTimeReverse[self.iAquistionTime]) + "/" + str(AdcOverSamplingRateReverse[self.iOversampling]) + "/" + str(self.sAdcRef) + "(" + str(self.samplingRate) + ")\n")
            self.stdscr.addstr("Acc Config(XYZ/DataSets): " + str(int(self.bAccX)) + str(int(self.bAccY)) + str(int(self.bAccZ)) + "/" + str(DataSetsReverse[self.tAccDataFormat]) + "\n")
            self.stdscr.addstr("Voltage Config(XYZ/DataSets): " + str(int(self.bVoltageX)) + str(int(self.bVoltageY)) + str(int(self.bVoltageZ)) + "/" + str(DataSetsReverse[self.tVoltageDataFormat]) + ("(X=Battery)\n"))
            self.stdscr.addstr("a: Config ADC\n")
            self.stdscr.addstr("b: Get battery voltage\n")
            self.stdscr.addstr("d: Config display Time\n")
            self.stdscr.addstr("e: Disconnect from holder\n")
            self.stdscr.addstr("n: Set Device Name\n")
            self.stdscr.addstr("p: Config Acceleration Points(XYZ)\n")
            self.stdscr.addstr("q: Quit\n")
            self.stdscr.addstr("r: Config run time and interval time\n")
            self.stdscr.addstr("s: Start Data Aquisition\n")
            self.stdscr.addstr("v: Activate Battery Voltage Streaming\n")
            self.stdscr.addstr("V: Disable Battery Voltage Streaming\n")
            self.stdscr.addstr("ESC(Top left): Escape from print menus e.g. do not show battery voltage again\n")
            if None != iBatteryVoltage:
                self.stdscr.addstr("Battery Voltage: " + str(iBatteryVoltage) + "V")
            self.stdscr.refresh()
            keyPress = self.stdscr.getch()
            if (0x03 == keyPress) or (ord('q') == keyPress):
                bRun = False
            elif 0x1B == keyPress:
                iBatteryVoltage = None
            elif ord('a') == keyPress:
                self.vTerminalHolderConnectCommandsAdcConfig()
            elif ord('b') == keyPress:
                index = self.PeakCan.singleValueCollect(MyToolItNetworkNr["STH1"], MyToolItStreaming["Voltage"], 1, 0, 0)
                iBatteryVoltage = messageValueGet(self.PeakCan.getReadMessageData(index)[2:4]) / 1000
            elif ord('d') == keyPress:
                self.stdscr.addstr("Display Time(s): ")
                self.stdscr.refresh()            
                iDisplayTime = self.iTerminalInputNumberIn()  
                self.vDisplayTime(iDisplayTime)
            elif ord('n') == keyPress:
                self.vTerminalDeviceName()
            elif ord('e') == keyPress:
                bRun = False
                self.PeakCan.BlueToothDisconnect(MyToolItNetworkNr["STU1"])
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
            elif ord('v') == keyPress:
                self.vVoltageSet(1, 0, 0, -1)
            elif ord('V') == keyPress:
                self.vVoltageSet(0, 0, 0, -1)
        if ord('e') == keyPress:
            bContinue = True
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
                bRun = False
            elif(0x03 == keyPress) or (ord('q') == keyPress):
                bRun = False
                bContinue = True
            else:
                devList = None
            keyPress = -1
        return bContinue
    
    def vTerminalStuEeprom(self):
        self.stdscr.clear()
        if None != self.sSheetFile and None != self.sProduct and None != self.sConfig:
            self.stdscr.clear()
            self.stdscr.addstr("e: Escape(Exit) this menu\n")
            pageNames = self.atExcelSheetNames()
            pageNumber = 0
            for pageName in pageNames:
                self.stdscr.addstr(str(pageNumber) + "1: Read Page " + str(pageName) + "\n")
                pageNumber += 1        
            self.stdscr.refresh()
        
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
    
    def vTerminalTests(self):
        bRun = True
        while False != bRun:
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
            iKeyPress = self.stdscr.getch()
            iDigit = int(iKeyPress - ord('0'))
            if 0 <= iDigit and 9 >= iDigit:
                bRun = False
                iTestNumberRun = self.iTerminalInputNumberIn(iDigit) 
                if 0 == iTestNumberRun:
                    pass
                elif iTestNumberRun < iTestNumber:
                    self.PeakCan.__exit__() 
                    sDirPath = os.path.dirname(os.path.realpath(pyFiles[iTestNumberRun - 1]))
                    sDirPath += "\\VerficationInternal\\"
                    sDirPath += pyFiles[iTestNumberRun - 1]
                    try:
                        os.system("python " + str(sDirPath) + " ../Logs/STH SthAuto.txt")
                    except KeyboardInterrupt:
                        pass
                    self.PeakCan = PeakCanFd.PeakCanFd(PeakCanFd.PCAN_BAUD_1M, "init.txt", "initError.txt", MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"])
                else:
                    pass
           
    def vTerminalXmlProductVersionCreate(self):
        self.stdscr.clear()
        asProductList = self.atXmlProductList()
        number = 0
        for version in asProductList:
            self.stdscr.addstr(str(number) + ": " + version + "\n")
            number += 1
        self.stdscr.addstr("Device for deriving: ")
        self.stdscr.refresh()
        iProduct = self.iTerminalInputNumberIn()
        asVersionList = self.atXmlVersionList(asProductList[iProduct])
        number = 0
        for version in asVersionList:
            self.stdscr.addstr(str(number) + ": " + version + "\n")
            number += 1
        self.stdscr.addstr("Version for deriving: ")
        self.stdscr.refresh()
        if 0 < len(asVersionList):
            iVersion = self.iTerminalInputNumberIn()
            self.stdscr.addstr("New Version Name: ")
            sVersionName = self.sTerminalInputStringIn()
            if iVersion < len(asVersionList):
                dataDef = self.root.find('Data')
                for product in dataDef.find('Product'):
                    if product.get('name') == asProductList[iProduct]:
                        break
                self.newXmlVersion(product, sVersionName)
                self.xmlSave()
    
    def vTerminalXmlProductVersionChange(self):
        self.stdscr.addstr("Please enter product name(STH or STU): ")
        self.stdscr.refresh()
        sProductName = self.sTerminalInputStringIn()
        self.stdscr.addstr("Please enter version: ")
        self.stdscr.refresh()
        sVersion = self.sTerminalInputStringIn()
        self.vConfigSet(sProductName, sVersion)  
                
    def vTerminalXmlProductVersionList(self):
        self.stdscr.clear()
        for product in self.atXmlProductList():
            self.stdscr.addstr("Device: " + str(product) + "\n")
            asVersions = self.atXmlVersionList(product)
            for version in asVersions:
                self.stdscr.addstr("            " + str(version) + "\n")
        self.stdscr.addstr("Press any key to return\n")
        self.stdscr.refresh()
        while -1 == self.stdscr.getch():
            pass
        
    def vTerminalXmlSetupList(self):
        self.stdscr.clear()
        number = 1
        setupArray=[]
        for setup in self.tree.find('Config'):
            self.stdscr.addstr(str(number) + ": " + setup.get('name') + "\n")
            setupArray.append(setup)
            number += 1
        self.stdscr.addstr("Choose device to show settings or 0 to escape: ")
        self.stdscr.refresh()
        iSetup = self.iTerminalInputNumberIn()
        if 0 < iSetup:
            setup = setupArray[iSetup-1]
            self.stdscr.addstr("Device Name: " + setup.find('DeviceName').text + "\n")
            self.stdscr.addstr("Acceleration Points(X/Y/Z): " + setup.find('Acc').text + "\n")
            self.stdscr.addstr("Prescaler: " + setup.find('Prescaler').text + "\n")
            self.stdscr.addstr("Acquisition Time: " + setup.find('AcquisitionTime').text + "\n")
            self.stdscr.addstr("Oversampling Rate: " + setup.find('OverSamples').text + "\n")
            iAcquisitionTime = AdcAcquisitionTime[int(setup.find('AcquisitionTime').text)]
            iOversampling = AdcOverSamplingRate[int(setup.find('OverSamples').text)]
            samplingRate = int(calcSamplingRate(int(setup.find('Prescaler').text), iAcquisitionTime, iOversampling) + 0.5)
            self.stdscr.addstr("Derived samplring rate from upper three parameters: " + str(samplingRate) + "\n")
            self.stdscr.addstr("ADC Reference Voltage: " + setup.find('AdcRef').text + "\n")
            self.stdscr.addstr("Log Name: " + setup.find('LogName').text + "\n")
            self.stdscr.addstr("RunTime/IntervalTime: " + setup.find('RunTime').text + "/" + setup.find('DisplayTime').text + "\n")
            self.stdscr.addstr("Display Time: " + setup.find('DisplayTime').text + "\n")              
            self.stdscr.addstr("Press any key to return\n")
            self.stdscr.refresh()
            while -1 == self.stdscr.getch():
                pass        
        
    def vTerminalXmlProductVersionRemove(self):
        self.stdscr.clear()
        asProductList = self.atXmlProductList()
        number = 0
        for version in asProductList:
            self.stdscr.addstr(str(number) + ": " + version + "\n")
            number += 1
        self.stdscr.addstr("Device for version removing: ")
        self.stdscr.refresh()
        iProduct = self.iTerminalInputNumberIn()
        asVersionList = self.atXmlVersionList(asProductList[iProduct])
        number = 0
        for version in asVersionList:
            self.stdscr.addstr(str(number) + ": " + version + "\n")
            number += 1
        self.stdscr.addstr("Version to remove: ")
        self.stdscr.refresh()
        if 1 < len(asVersionList):
            iVersion = self.iTerminalInputNumberIn()
            if iVersion < len(asVersionList):
                dataDef = self.root.find('Data')
                for product in dataDef.find('Product'):
                    if product.get('name') == asProductList[iProduct]:
                        break
                for version in product.find('Version'):
                    if version.get('name') == asVersionList[iVersion]:
                        break
                self.removeXmlVersion(product.find('Version'), version)
                       
    def vTerminalXmlSetupChange(self):
        self.stdscr.addstr("Please enter setup name: ")
        self.stdscr.refresh()
        sSetupName = self.sTerminalInputStringIn()
        self.bSampleSetupSet(sSetupName)
                    
    def vTerminalXmlExcelChange(self):
        self.stdscr.addstr("Please enter Excel File name for new Excel Sheet")
        self.stdscr.refresh()
        sFileName = self.sTerminalInputStringIn()
        self.vSheetFileSet(sFileName)
    
    def vTerminalXmlKeyEvaluation(self):
        bRun = True
        keyPress = self.stdscr.getch()
        if ord('q') == keyPress:
            bRun = False
        elif 0x03 == keyPress:  # CTRL+C
            bRun = False
        elif ord('c') == keyPress:
            self.vTerminalXmlProductVersionCreate()
        elif ord('d') == keyPress:
            self.vTerminalXmlProductVersionChange()
        elif ord('l') == keyPress:
            self.vTerminalXmlProductVersionList()
        elif ord('L') == keyPress:
            self.vTerminalXmlSetupList()
        elif ord('r') == keyPress:   
            self.vTerminalXmlProductVersionRemove()
        elif ord('s') == keyPress:
            self.vTerminalXmlSetupChange()
        elif ord('x') == keyPress:
            self.vTerminalXmlExcelChange()
        return bRun
      
    def vTerminalXml(self):
        bRun = True
        while False != bRun:
            self.stdscr.clear()
            self.stdscr.addstr("Device: " + str(self.sProduct) + "\n")
            self.stdscr.addstr("Version: " + str(self.sConfig) + "\n")
            self.stdscr.addstr("Configuration: " + str(self.sConfig) + "\n")
            self.stdscr.addstr("Predefined Setup " + str(self.sSetupConfig) + "\n")
            self.stdscr.addstr("Excel Sheet Name(.xlsx): " + str(self.sSheetFile) + "\n")  
            self.stdscr.addstr("c: Create new Version\n")
            self.stdscr.addstr("C: Create new Setup\n")
            self.stdscr.addstr("d: Chance Device(Product) and version\n")
            self.stdscr.addstr("l: List product and versions\n")
            self.stdscr.addstr("L: List Setups\n")
            self.stdscr.addstr("r: Remove Version\n")
            self.stdscr.addstr("s: Change Setup\n")
            self.stdscr.addstr("x: Chance Excel Sheet Name(.xlsx)\n")  
            self.stdscr.refresh()
            bRun = self.vTerminalXmlKeyEvaluation()

 
    def bTerminalMainMenuKeyEvaluation(self, devList):
        bRun = True
        keyPress = self.stdscr.getch()
        if ord('q') == keyPress:
            bRun = False
        elif 0x03 == keyPress:  # CTRL+C
            bRun = False
        elif ord('0') <= keyPress and ord('9') >= keyPress:
            self.PeakCan.Logger.Info("Call bTerminalHolderConnect")
            bRun = self.bTerminalHolderConnect(keyPress)
        elif ord('l') == keyPress:  # CTRL+C    
            self.vTerminalLogFileName()
        elif ord('n') == keyPress:
            self.stdscr.addstr("Pick a device number from the list: ")
            self.stdscr.refresh()            
            iDevice = self.iTerminalInputNumberIn()  
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
        elif ord('s') == keyPress:    
            self.vTerminalStuEeprom() 
        elif ord('t') == keyPress:    
            self.vTerminalTests()              
        elif ord('x') == keyPress:    
            self.vTerminalXml()   
        return bRun 
                  
    def bTerminalMainMenu(self):
        devList = self.tTerminalHeaderExtended()            
        self.stdscr.addstr("\n")
        self.stdscr.addstr("q: Quit program\n")
        self.stdscr.addstr("0-9: Enter Number to connect to STH(ENTER required at the end of the number)\n")
        self.stdscr.addstr("l: Log File Name\n")
        self.stdscr.addstr("n: Change Device Name\n")
        self.stdscr.addstr("s: STU EEPROM Parameters\n")
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
            elif (ord('0') <= iKeyPress and ord('z') >= iKeyPress) or (ord('.') == iKeyPress):                
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
            self.stdscr.addstr("Device Number: " + str(dev["DeviceNumber"]) + "; Name: " + str(dev["Name"]) + "; Address: " + hex(dev["Address"]) + "; RSSI: " + str(dev["RSSI"]) + "\n") 
        return devList    
            
    def vTerminalHeader(self):
        self.stdscr.clear()
        self.stdscr.addstr("MyToolIt Terminal Application\n\n")
        
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
