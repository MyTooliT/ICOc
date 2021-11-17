import curses

from sys import stderr
from time import sleep

from curses import curs_set

from mytoolit.old.myToolItWatch import myToolItWatch
from mytoolit.old.MyToolItCommands import (
    AdcAcquisitionTime,
    AdcOverSamplingRate,
    AdcReference,
    byte_list_to_int,
    CalibMeassurementActionNr,
    CalibMeassurementTypeNr,
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
        self.stdscr.addstr("Prescaler (2-127): ")
        self.stdscr.refresh()
        iPrescaler = self.iTerminalInputNumberIn()
        self.stdscr.addstr("Acquisition Time ")
        self.vListKeys(AdcAcquisitionTime)
        self.stdscr.refresh()
        iAquisitionTime = self.iTerminalInputNumberIn()
        self.stdscr.addstr("Oversampling Rate ")
        self.vListKeys(AdcOverSamplingRate)
        self.stdscr.refresh()
        iOversamplingRate = self.iTerminalInputNumberIn()
        self.stdscr.addstr("ADC Reference Voltage (VDD=3V3) ")
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
        self.stdscr.addstr("Run time of data acquisition (in seconds):")
        self.stdscr.refresh()
        iRunTime = self.iTerminalInputNumberIn()
        self.vRunTime(iRunTime)

    def tTerminalHolderConnectCommandsKeyEvaluation(self):
        keyPress = self.stdscr.getch()
        bRun = True
        bContinue = False
        if (0x03 == keyPress):
            bRun = False
        elif ord('a') == keyPress:
            self.vTerminalHolderConnectCommandsAdcConfig()
        elif ord('q') == keyPress:
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
                "Set enabled axes (xyz; 0=off, 1=on; e.g. “100”): ")
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
        sHwRev = self.Can.sProductData("Hardware Version", bLog=False)
        sSwVersion = self.Can.sProductData("Firmware Version", bLog=False)
        sReleaseName = self.Can.sProductData("Release Name", bLog=False)
        sSerialNumber = self.Can.sProductData("Serial Number", bLog=False)
        sName = self.Can.sProductData("Product Name", bLog=False)
        sSerial = str(sSerialNumber + "-" + sName)
        self.stdscr.addstr(f"Hardware Version:      {sHwRev}\n")
        self.stdscr.addstr(f"Firmware Version:      {sSwVersion}\n")
        self.stdscr.addstr(f"Firmware Release Name: {sReleaseName}\n")
        self.stdscr.addstr(f"Serial Number:         {sSerial}\n\n")

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
            self.stdscr.addstr(
                f"Battery Voltage:{' '*6}{fBatteryVoltage: 4.2f} V\n")
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
            self.stdscr.addstr(
                f"Chip Temperature:{' '*6}{iTemperature:4.1f} °C\n\n")

    def bTerminalHolderConnectCommands(self):
        bContinue = True
        bRun = True
        self.vDisplayTime(10)
        while False != bRun:
            self.vTerminalHeader()
            address = int_to_mac_address(int(self.iAddress, 16))
            name = self.sDevName
            self.stdscr.addstr(f"STH “{name}” ({address})\n\n")
            self.bTerminalHolderConnectCommandsShowDataValues()
            self.stdscr.addstr(f"Run Time:              {self.iRunTime} s\n\n")
            prescaler = self.iPrescaler
            acquistion_time = AdcAcquisitionTime.inverse[self.iAquistionTime]
            oversampling_rate = AdcOverSamplingRate.inverse[self.iOversampling]
            sampling_rate = self.samplingRate
            adc_reference = self.sAdcRef

            self.stdscr.addstr(f"Prescaler:             {prescaler}\n")
            self.stdscr.addstr(f"Acquisition Time:      {acquistion_time}\n")
            self.stdscr.addstr(f"Oversampling Rate:     {oversampling_rate}\n")
            self.stdscr.addstr(f"⇒ Sampling Rate:       {sampling_rate}\n")
            self.stdscr.addstr(f"Reference Voltage:     {adc_reference}\n\n")

            x_enabled = "X" if self.bAccX else ""
            y_enabled = "Y" if self.bAccY else ""
            z_enabled = "Z" if self.bAccZ else ""
            axes = [axis for axis in (x_enabled, y_enabled, z_enabled) if axis]
            last_two_axes = " & ".join(axes[-2:])
            axes = (f"{axes[0]}, {last_two_axes}"
                    if len(axes) >= 3 else last_two_axes)

            self.stdscr.addstr(
                f"Enabled Ax{'i' if len(axes) <= 1 else 'e'}s:{' ' * 10}"
                f"{axes}\n")

            self.stdscr.addstr(f"\n{'—'*30}\n")
            self.stdscr.addstr("s: Start Data Acquisition\n\n")

            self.stdscr.addstr("n: Change Device Name\n")
            self.stdscr.addstr("r: Change Run Time\n")
            self.stdscr.addstr("a: Configure ADC\n")
            self.stdscr.addstr("p: Configure Enabled Axes\n")
            self.stdscr.addstr("O: Set Standby Mode\n\n")

            self.stdscr.addstr("q: Disconnect from STH\n")
            self.stdscr.refresh()
            [bRun,
             bContinue] = self.tTerminalHolderConnectCommandsKeyEvaluation()
        return bContinue

    def bTerminalHolderConnect(self, iKeyPress):
        curs_set(True)  # Enable cursor
        iNumber = int(iKeyPress - ord('0'))
        iKeyPress = -1
        bRun = True
        bContinue = False
        devList = None
        while False != bRun:
            devList = self.tTerminalHeaderExtended(devList)
            self.stdscr.addstr(
                f"\nChoose STH number (Use ⏎ to connect): {iNumber}")
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
                    device_number = iNumber - 1
                    name = devList[device_number]['Name']
                    self.stdscr.addstr(f"\nConnecting to device “{name}” …")
                    self.stdscr.refresh()
                    iNumber -= 1
                    for dev in devList:
                        if dev["DeviceNumber"] == iNumber:
                            self.vDeviceAddressSet(hex(dev["Address"]))
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
        self.stdscr.addstr("New STH name (max. 8 characters):")
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
        curs_set(False)  # Disable cursor

        devList = self.tTerminalHeaderExtended()
        self.stdscr.addstr(f"\n{'—'*30}\n")
        self.stdscr.addstr("1-9: Connect to STH\n\n")

        self.stdscr.addstr("f  : Change Output File Name\n")
        self.stdscr.addstr("n  : Change STH Name\n\n")

        self.stdscr.addstr("q  : Quit Program")
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
        cursorXPos = self.stdscr.getyx()[1] + 1
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
        cursorXPos = self.stdscr.getyx()[1] + 1
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

        self.stdscr.addstr("     Name      Address            RSSI\n")
        self.stdscr.addstr("    ——————————————————————————————————————\n")
        for dev in devList:
            number = dev["DeviceNumber"] + 1
            address = int_to_mac_address(dev["Address"])
            name = dev["Name"]
            rssi = dev["RSSI"]
            self.stdscr.addstr(
                f"{number:3}: {name:8}  {address}  {rssi} dBm\n")
        return devList

    def vTerminalHeader(self):
        self.stdscr.clear()
        self.stdscr.addstr(f"{' '*16}ICOc\n\n")

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

        # TODO: Do not refresh the whole display constantly
        # Possible Solution:
        # - Spawn two threads
        # - One of them waits for input (blocking)
        # - Other thread refresh list of devices
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
