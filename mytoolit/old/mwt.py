import curses

from sys import stderr
from time import sleep

from mytoolit.old.myToolItWatch import myToolItWatch
from mytoolit.old.MyToolItCommands import (
    AdcAcquisitionTime,
    AdcOverSamplingRate,
    AdcReference,
    byte_list_to_int,
    CalibMeassurementActionNr,
    CalibMeassurementTypeNr,
    DataSets,
    int_to_mac_address,
    MyToolItStreaming,
)
from mytoolit.old.MyToolItNetworkNumbers import MyToolItNetworkNr
from mytoolit.old.MyToolItSth import fVoltageBattery


class mwt(myToolItWatch):

    def __init__(self):
        myToolItWatch.__init__(self)
        self.process = None
        self.bTerminal = False
        self.vNetworkNumberSet(None)

    def close(self):
        if None != self.process:
            self.process.terminate()
        self.vTerminalTeardown()
        myToolItWatch.close(self)

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

    def change_runtime(self):
        self.stdscr.clear()
        self.stdscr.addstr("Run Time (in Seconds): ")
        self.stdscr.refresh()
        iRunTime = self.iTerminalInputNumberIn()
        self.vRunTime(iRunTime)

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
            self.change_runtime()
        elif ord('s') == keyPress:
            self.stdscr.clear()
            if not self.KeyBoardInterrupt:
                try:
                    self.vDataAquisition()
                except KeyboardInterrupt:
                    self.KeyBoardInterrupt = True
                    self.__exit__()
                bRun = False
        return [bRun, bContinue]

    def bTerminalHolderConnectCommandsShowDataValues(self):
        sGtin = self.Can.sProductData("GTIN", bLog=False)
        sHwRev = self.Can.sProductData("Hardware Version", bLog=False)
        sSwVersion = self.Can.sProductData("Firmware Version", bLog=False)
        sReleaseName = self.Can.sProductData("Release Name", bLog=False)
        sSerialNumber = self.Can.sProductData("Serial Number", bLog=False)
        sName = self.Can.sProductData("Product Name", bLog=False)
        sSerial = str(sSerialNumber + "-" + sName)
        self.stdscr.addstr("Global Trade Identification Number (GTIN): " +
                           sGtin + "\n")
        self.stdscr.addstr("Hardware Version(Major.Minor.Build): " + sHwRev +
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
            self.stdscr.addstr("n: Set Device Name\n")
            self.stdscr.addstr("O: Off(Standby)\n")
            self.stdscr.addstr("p: Config Acceleration Points(XYZ)\n")
            self.stdscr.addstr("r: Config run time\n")
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
                            self.sDevName = dev["Name"]
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

    def vTerminalLogFileName(self):
        filepath = self.get_output_filepath()
        self.stdscr.addstr(f"Output File Name ({filepath.stem}): ")
        filename = self.sTerminalInputStringIn()
        if filename != "":
            self.set_output_filename(filename)
        self.stdscr.addstr(str(self.get_output_filepath()))
        self.stdscr.refresh()
        sleep(2)

    def vTerminalDeviceName(self):
        self.stdscr.clear()
        self.stdscr.addstr("New Device Name (max. 8 characters): ")
        self.stdscr.refresh()
        sName = self.sTerminalInputStringIn()
        self.vDeviceNameSet(sName)
        self.Can.vBlueToothNameWrite(MyToolItNetworkNr["STH1"], 0, sName)

    def vConnect(self, devList=None):
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
        elif ord('f') == keyPress:
            self.vTerminalLogFileName()
        elif ord('n') == keyPress:
            self.vConnect(devList)
            if False != self.Can.bConnected:
                self.vTerminalDeviceName()
                self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])
            else:
                self.stdscr.addstr("Device was not available\n")
                self.stdscr.refresh()
        return bRun

    def bTerminalMainMenu(self):
        devList = self.tTerminalHeaderExtended()
        self.stdscr.addstr("\n")
        self.stdscr.addstr("q: Quit program\n")
        self.stdscr.addstr("1-9: Connect to STH number (ENTER at input end)\n")
        self.stdscr.addstr("f: Output File Name\n")
        self.stdscr.addstr("n: Change Device Name\n")
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

        self.stdscr.addstr("     Name     Address            RSSI\n")
        self.stdscr.addstr("    ——————————————————————————————————\n")
        for dev in devList:
            number = dev["DeviceNumber"] + 1
            address = int_to_mac_address(dev["Address"])
            name = dev["Name"]
            rssi = dev["RSSI"]
            self.stdscr.addstr(f"{number:3}: {name:8} {address} {rssi}dBm\n")
        return devList

    def vTerminalHeader(self):
        self.stdscr.clear()
        self.stdscr.addstr("ICOc\n\n")

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


def main():
    try:
        watch_tool = mwt()
        watch_tool.vParserInit()
        watch_tool.vParserConsoleArgumentsPass()
        watch_tool.vRunConsole()
    except Exception as error:
        print(f"Error\n—————\n☹️ {error}\n", file=stderr)
        print("Stack Trace\n———————————", file=stderr)
        raise error


if __name__ == "__main__":
    main()
