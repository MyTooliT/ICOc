from sys import stderr
from time import sleep
from typing import Callable

from curses import curs_set, wrapper

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
    """ICOc command line & curses interface

    This class can be used to connect to the ICOtronic system and acquire
    measurement data using

    - a command line interface and
    - a menu based curses interface.

    """

    def __init__(self):
        super().__init__()
        self.process = None

    def close(self):
        if self.process is not None:
            self.process.terminate()
        super().close()

    def vTerminalHolderConnectCommandsAdcConfig(self):

        def list_keys(dictionary):
            keys = map(str, dictionary.keys())
            return ', '.join(keys)

        def read_value(description, default):
            self.stdscr.addstr(description)
            self.stdscr.refresh()
            return self.read_number(default)

        self.stdscr.clear()

        iPrescaler = read_value("Prescaler (2–127): ", 2)
        iAquisitionTime = read_value(
            f"Acquisition Time ({list_keys(AdcAcquisitionTime)}): ", 8)
        iOversamplingRate = read_value(
            f"Oversampling Rate ({list_keys(AdcOverSamplingRate)}): ", 64)

        self.stdscr.addstr(
            f"ADC Reference Voltage (VDD=3V3) ({list_keys(AdcReference)}): ")
        self.stdscr.refresh()
        sAdcRef = self.read_text('VDD')

        try:
            self.vAdcConfig(iPrescaler, iAquisitionTime, iOversamplingRate)
            self.vAdcRefVConfig(sAdcRef)
        except KeyError:
            pass

    def change_runtime(self):
        self.stdscr.clear()
        self.stdscr.addstr("Run time of data acquisition "
                           "(in seconds; 0 for infinite runtime): ")
        self.stdscr.refresh()
        iRunTime = self.read_number()
        self.vRunTime(iRunTime)

    def tTerminalHolderConnectCommandsKeyEvaluation(self):
        keyPress = self.stdscr.getch()
        bRun = True
        bContinue = False
        if keyPress == 0x03:  # `Ctrl` + `C`
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
            sYes = self.read_text()
            if "y" == sYes:
                self.Can.Standby(MyToolItNetworkNr["STH1"])
                bRun = False
                self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])
                bContinue = True
        elif ord('p') == keyPress:
            self.stdscr.clear()
            self.stdscr.addstr(
                "Set enabled axes (xyz; 0=off, 1=on; e.g. “100”): ")
            iPoints = self.read_number()
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
        if iBatteryVoltage is not None:
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
        self.stdscr.addstr(
            f"Chip Temperature:{' '*6}{iTemperature:4.1f} °C\n\n")

    def bTerminalHolderConnectCommands(self):
        bContinue = True
        bRun = True
        self.vDisplayTime(10)
        while bRun:
            self.vTerminalHeader()
            address = int_to_mac_address(int(self.iAddress, 16))
            name = self.sDevName
            self.stdscr.addstr(f"STH “{name}” ({address})\n\n")
            self.bTerminalHolderConnectCommandsShowDataValues()
            runtime = '∞' if self.iRunTime == 0 else str(self.iRunTime)
            self.stdscr.addstr(f"Run Time:              {runtime} s\n\n")
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
        while bRun:
            devList = self.tTerminalHeaderExtended(devList)
            self.stdscr.addstr(
                f"\nChoose STH number (Use ⏎ to connect): {iNumber}")
            self.stdscr.refresh()
            iKeyPress = self.stdscr.getch()
            if ord('0') <= iKeyPress and ord('9') >= iKeyPress:
                digit = int(iKeyPress) - ord('0')
                iNumber = iNumber * 10 + digit
            elif 0x08 == iKeyPress:
                if 1 < len(str(iNumber)):
                    iNumber = int(str(iNumber)[:-1])
                else:
                    iNumber = 0
            elif 0x0A == iKeyPress or 459 == iKeyPress:
                # TODO: Handle incorrect device numbers properly
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
                            if self.Can.bBlueToothConnectPollingAddress(
                                    MyToolItNetworkNr["STU1"], self.iAddress):
                                bContinue = (
                                    self.bTerminalHolderConnectCommands())
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
        curs_set(True)  # Enable cursor
        self.stdscr.clear()
        filepath = self.get_output_filepath()
        self.stdscr.addstr(f"Set output file name ({filepath.stem}):")
        self.stdscr.refresh()
        filename = self.read_text()
        if filename != "":
            self.set_output_filename(filename)
        self.stdscr.addstr("New full name (including time stamp): "
                           f"“{self.get_output_filepath()}”")
        self.stdscr.refresh()
        sleep(2)

    def vTerminalDeviceName(self):
        self.stdscr.clear()
        self.stdscr.addstr("New STH name (max. 8 characters):")
        self.stdscr.refresh()
        sName = self.read_text()
        self.vDeviceNameSet(sName)
        self.Can.vBlueToothNameWrite(MyToolItNetworkNr["STH1"], 0, sName)

    def vConnect(self, devList=None):
        if self.Can.bConnected:
            return

        self.stdscr.addstr("Pick a device number from the list: ")
        self.stdscr.refresh()
        iDevice = self.read_number()
        if 0 < iDevice:
            iDevice -= 1
            for dev in devList:
                iDevNumber = int(dev["DeviceNumber"])
                if iDevNumber == iDevice:
                    self.vDeviceAddressSet(str(dev["Address"]))
                    self.stdscr.addstr("Connect to " + hex(dev["Address"]) +
                                       "(" + str(dev["Name"]) + ")\n")
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
            if self.Can.bConnected:
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

        self.stdscr.addstr("  f: Change Output File Name\n")
        self.stdscr.addstr("  n: Change STH Name\n\n")

        self.stdscr.addstr("  q: Quit Program\n")
        self.stdscr.refresh()
        return self.bTerminalMainMenuKeyEvaluation(devList)

    def read_input(self,
                   allowed: Callable[[int], bool],
                   default: str = "") -> str:
        """Read textual input at the current position

        Arguments
        ---------

        allowed:
            A function that specifies if a given input character is allowed to
            occur in the input or not

        default:
            This text will be be used as initial value for the input

        Returns
        -------

        The read input

        """

        y_position, x_position = self.stdscr.getyx()
        ctrl_c = 0x03
        backspace = 0x08
        line_feed = 0x0A
        enter = 459

        text = default
        while True:
            self.stdscr.addstr(y_position, x_position, text)
            self.stdscr.refresh()
            key = self.stdscr.getch()

            if key in {ctrl_c, line_feed, enter}:
                break

            if allowed(key):
                text += chr(key)
            elif key == backspace:
                text = text[:-1] if len(text) > 1 else ''
                self.stdscr.addstr(y_position, x_position + len(text), " ")
                self.stdscr.refresh()

        self.stdscr.addstr("\n")
        self.stdscr.refresh()
        return text

    def read_number(self, default: int = 0) -> int:
        """Read a number at the current position

        Arguments
        ---------

        default:
            A number that will be used as initial value

        Returns
        -------

        The read number, or `0` if there was no user input (apart from
        `Enter`, `Return` or `Ctrl` + `C`)

        """

        number_text = self.read_input(
            allowed=lambda key: ord('0') <= key <= ord('9'),
            default=str(default))

        return int(number_text)

    def read_text(self, default: str = '') -> str:
        """Read a text at the current position


        Parameters
        ----------

        default:
            The initial value for the text

        Returns
        -------

        The read text

        """

        return self.read_input(allowed=lambda key: ord(' ') <= key <= ord('~'),
                               default=default)

    def vTerminal(self, stdscr):
        self.stdscr = stdscr

        # TODO: Do not refresh the whole display constantly
        # Possible Solution:
        # - Spawn two threads
        # - One of them waits for input (blocking)
        # - Other thread refreshes list of devices
        self.stdscr.nodelay(1)
        self.stdscr.clear()

        bRun = True
        while bRun:
            try:
                bRun = self.bTerminalMainMenu()
            except KeyboardInterrupt:
                self.KeyBoardInterrupt = True
                break

    def tTerminalHeaderExtended(self, devList=None):
        self.vTerminalHeader()
        if devList is None:
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

    def vRunConsole(self):
        self._vRunConsoleStartup()
        self.reset()
        if self.bSthAutoConnect:
            self.vRunConsoleAutoConnect()
        else:
            wrapper(self.vTerminal)
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
