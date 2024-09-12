from pathlib import Path
from sys import stderr
from time import sleep
from typing import Callable, Iterable, Tuple

from curses import curs_set, error, wrapper  # type: ignore[attr-defined]

from mytoolit.config import settings
from mytoolit.measurement.sensor import SensorConfiguration
from mytoolit.old.cli import CommandLineInterface
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
from mytoolit.old.network import UnsupportedFeatureException


class Key:
    """Store key constants"""

    CTRL_C = 3
    DELETE = 8
    RETURN = 10

    ZERO = ord("0")
    ONE = ord("1")
    NINE = ord("9")

    A = ord("a")
    C = ord("c")
    F = ord("f")
    N = ord("n")
    P = ord("p")
    Q = ord("q")
    R = ord("r")
    S = ord("s")

    UPPERCASE_O = ord("O")

    ENTER = 459


class UserInterface(CommandLineInterface):
    """ICOc command line & curses interface

    This class can be used to connect to the ICOtronic system and acquire
    measurement data using

    - a command line interface and
    - a menu based curses interface.

    """

    def __init__(self):
        super().__init__()

    def close(self):
        super().close()

    def add_string(self, *arguments) -> None:
        """Add a string to the terminal window

        This is basically a wrapper around the `addstr` method that ignores
        errors (about drawing strings outside the visible area)

        Parameters
        ----------

        arguments:
            A list of argument for the `addstr` method

        """

        try:
            self.stdscr.addstr(*arguments)
        except error:
            # Ignore errors about drawing strings outside terminal window
            pass

    def read_input(
        self,
        allowed_key: Callable[[int], bool],
        allowed_value: Callable[[str], bool],
        default: str = "",
    ) -> Tuple[bool, str]:
        """Read textual input at the current position

        The function will read input until

        - the user enters an allowed value followed by the Enter/Return key, or
        - the user enters `Ctrl` + `C` to stop the input reading.

        Parameters
        ----------

        allowed_key:
            A function that specifies if a given key character is allowed to
            occur in the input or not

        allowed_value:
            A function that specifies if the whole read input is an allowed
            value or not

        default:
            This text will be be used as initial value for the input

        Returns
        -------

        A pair containing:

        - a boolean that specifies if the input is valid according to the
          function `allowed_value`, and
        - the read number.

        """

        y_position, x_position = self.stdscr.getyx()

        text = default
        while True:
            self.add_string(y_position, x_position, text)
            self.stdscr.refresh()
            key = self.stdscr.getch()
            sleep(0.001)  # Sleep a little bit to reduce CPU usage

            if key == Key.CTRL_C:
                break

            if key in {Key.RETURN, Key.ENTER}:
                if allowed_value(text):
                    break
            elif allowed_key(key):
                text += chr(key)
            elif key == Key.DELETE:
                text = text[:-1] if len(text) > 1 else ""
                self.add_string(y_position, x_position + len(text), " ")
                self.stdscr.refresh()

        self.add_string("\n")
        self.stdscr.refresh()
        return (allowed_value(text), text)

    def read_number(
        self,
        default: int = 0,
        allowed: Callable[[int], bool] = lambda value: True,
    ) -> Tuple[bool, int]:
        """Read a number at the current position

        The function will read input until

        - the user enters an allowed number followed by the Enter/Return key,
          or
        - the user enters `Ctrl` + `C` to stop the input reading.

        Parameters
        ----------

        default:
            A number that will be used as initial value

        allowed:
            A function that determines if the current read value is valid or
            not

        Returns
        -------

        A pair containing:

        - a boolean that specifies if the read number is valid according to the
          function `allowed`, and
        - the read number.

        """

        valid, number_text = self.read_input(
            allowed_key=lambda key: ord("0") <= key <= ord("9"),
            allowed_value=lambda value: allowed(int(value)),
            default=str(default),
        )

        return (valid, int(number_text))

    def read_text(
        self,
        default: str = "",
        allowed: Callable[[str], bool] = lambda value: True,
    ) -> Tuple[bool, str]:
        """Read a text at the current position

        The function will read input until

        - the user enters an allowed value followed by the Enter/Return key, or
        - the user enters `Ctrl` + `C` to stop the input reading.

        Parameters
        ----------

        default:
            The initial value for the text

        allowed:
            A function that determines if the current read text is valid or
            not

        Returns
        -------

        A pair containing:

        - a boolean that specifies if the read text is valid according to the
          function `allowed`, and
        - the read number.

        """

        return self.read_input(
            allowed_key=lambda key: ord(" ") <= key <= ord("~"),
            allowed_value=allowed,
            default=default,
        )

    def draw_menu(self, choices: Iterable[str]) -> None:
        """Draw a menu displaying the given choices at the current location

        Parameters
        ----------

        choices:
            A list containing the different choices available

        """

        ruler = "─" * (max(map(len, choices)) + 2)
        max_length_choices = max(map(len, choices))

        self.add_string(f"\n┌{ruler}┐\n")

        for choice in choices:
            fill = max_length_choices - len(choice)
            self.add_string(f"│ {choice}{' ' * fill} │\n")

        self.add_string(f"└{ruler}┘")

        self.stdscr.refresh()

    def change_adc_values_window(self):
        def list_keys(dictionary):
            keys = map(str, dictionary.keys())
            return ", ".join(keys)

        def read_value(description, default, allowed):
            self.add_string(description)
            self.stdscr.refresh()

            valid_input, value = (
                self.read_number(default, allowed)
                if isinstance(default, int)
                else self.read_text(default, allowed)
            )

            if not valid_input:
                self.add_string(
                    f"“{value}” is not a valid value; "
                    f"Using default value “{default}” instead\n"
                )
                value = default

            return value

        curs_set(True)
        self.stdscr.clear()

        prescalar = read_value(
            "Prescaler (2–127): ", 2, lambda value: 2 <= value <= 127
        )
        acquistion_time = read_value(
            f"Acquisition Time ({list_keys(AdcAcquisitionTime)}): ",
            8,
            lambda value: value in AdcAcquisitionTime,
        )
        oversampling_rate = read_value(
            f"Oversampling Rate ({list_keys(AdcOverSamplingRate)}): ",
            64,
            lambda value: value in AdcOverSamplingRate,
        )

        adc_reference = read_value(
            f"ADC Reference Voltage (VDD=3V3) ({list_keys(AdcReference)}): ",
            "VDD",
            lambda value: value in AdcReference,
        )

        self.vAdcConfig(prescalar, acquistion_time, oversampling_rate)
        self.vAdcRefVConfig(adc_reference)

    def change_sensors_window(self):
        """Update sensor configuration"""

        def read_channel_value(channel):
            self.add_string(
                "Sensor number (1 – 255) for measurement "
                f"channel {channel} (0 to disable): "
            )

            value = self.read_input(
                default=str(channel),
                allowed_key=lambda key: ord("0") <= key <= ord("9"),
                allowed_value=lambda value: len(value) <= 3
                and int(value) <= 255,
            )[1]

            return int(value)

        def enable_disable_sensors(channel, default):
            self.add_string(
                f"Enable measurement channel {channel} "
                "(1 to enable, 0 to disable): "
            )

            value = self.read_input(
                default=str(default),
                allowed_key=lambda key: ord("0") <= key <= ord("1"),
                allowed_value=lambda value: len(value) == 1,
            )[1]

            return int(value)

        curs_set(True)
        self.stdscr.clear()

        if self.channel_config_supported:
            sensors = [read_channel_value(channel) for channel in range(1, 4)]
            # We use sensor number 1 for disabled sensors
            self.Can.write_sensor_config(*sensors)
        else:
            enabled_sensors = map(
                lambda channel_number: int(bool(channel_number)),
                (self.sensor.first, self.sensor.second, self.sensor.third),
            )
            sensors = [
                enable_disable_sensors(channel, default_value)
                for channel, default_value in enumerate(
                    enabled_sensors, start=1
                )
            ]

        # Enable/disable axes for transmission
        try:
            self.set_sensors(*sensors)
        except ValueError as error:
            self.add_string(f"\nError: {error}")
            self.stdscr.refresh()
            sleep(2)

    def change_runtime_window(self):
        curs_set(True)
        self.stdscr.clear()

        self.add_string(
            "Run time of data acquisition "
            "(in seconds; 0 for infinite runtime): "
        )
        self.stdscr.refresh()
        runtime = self.read_number()[1]
        self.vRunTime(runtime)

    def sth_window_information(self):
        def read_voltage() -> str:
            index = self.Can.singleValueCollect(
                MyToolItNetworkNr["STH1"],
                MyToolItStreaming["Voltage"],
                1,
                0,
                0,
                log=False,
            )
            iBatteryVoltage = byte_list_to_int(
                self.Can.getReadMessageData(index)[2:4]
            )
            if iBatteryVoltage is not None:
                return f"{fVoltageBattery(iBatteryVoltage):4.2f}"

            return "–"

        def read_temperature() -> float:
            au8TempReturn = self.Can.calibMeasurement(
                MyToolItNetworkNr["STH1"],
                CalibMeassurementActionNr["Measure"],
                CalibMeassurementTypeNr["Temp"],
                1,
                AdcReference["1V25"],
                log=False,
            )
            self.Can.calibMeasurement(
                MyToolItNetworkNr["STH1"],
                CalibMeassurementActionNr["None"],
                CalibMeassurementTypeNr["Temp"],
                1,
                AdcReference["VDD"],
                log=False,
                bReset=True,
            )
            iTemperature = float(byte_list_to_int(au8TempReturn[4:]))
            return iTemperature / 1000

        self.window_header()

        address = int_to_mac_address(int(self.iAddress, 16))
        name = self.sth_name
        device_description = f"STH “{name}” ({address})"
        for value in (
            device_description,
            "\n",
            "—" * len(device_description),
            "\n\n",
        ):
            self.add_string(value)

        hardware_version = self.Can.sProductData(
            "Hardware Version", bLog=False
        )
        software_version = self.Can.sProductData(
            "Firmware Version", bLog=False
        )
        release_name = self.Can.sProductData("Release Name", bLog=False)
        serial_number = self.Can.sProductData("Serial Number", bLog=False)
        product_name = self.Can.sProductData("Product Name", bLog=False)
        serial = f"{serial_number}–{product_name}"
        sensor_range, success = self.read_acceleration_range()
        sensor_range_output = f"± {sensor_range / 2} g"
        if not success:
            sensor_range_output += " (EEPROM Read Error)"

        infos = [
            ("Hardware Version", hardware_version),
            ("Firmware Version", software_version),
            ("Firmware Release Name", release_name),
            ("Serial Number", serial),
            ("Sensor Range", f"{sensor_range_output}\n"),
        ]

        voltage = read_voltage()
        temperature = read_temperature()

        infos.extend([
            ("Supply Voltage", f"{voltage} V"),
            ("Chip Temperature", f"{temperature:4.1f} °C\n"),
        ])

        runtime = "∞" if self.iRunTime == 0 else str(self.iRunTime)
        prescaler = self.iPrescaler
        acquistion_time = AdcAcquisitionTime.inverse[self.iAquistionTime]
        oversampling_rate = AdcOverSamplingRate.inverse[self.iOversampling]
        sampling_rate = self.samplingRate
        adc_reference = self.sAdcRef

        sensor_config_local = (
            self.sensor.first,
            self.sensor.second,
            self.sensor.third,
        )

        if self.channel_config_supported:
            sensor_config_device = self.Can.read_sensor_config()
            sensor_config_device.disable_channel(
                *(not sensor_number for sensor_number in sensor_config_local)
            )
        else:
            sensor_config_device = SensorConfiguration(*[
                number if enabled else 0
                for number, enabled in enumerate(sensor_config_local, start=1)
            ])
        sensors = str(sensor_config_device)

        infos.extend([
            ("Run Time", f"{runtime} s\n"),
            ("Prescaler", prescaler),
            ("Acquisition Time", acquistion_time),
            ("Oversampling Rate", oversampling_rate),
            ("Sampling Rate", sampling_rate),
            ("Reference Voltage", f"{adc_reference}\n"),
            ("Sensors", sensors),
        ])

        max_description_length = max(
            len(description) for description, _ in infos
        )
        for description, value in infos:
            fill = max_description_length - len(description) + 1
            self.add_string(f"{description}{' ' * fill}{value}\n")

    def sth_window_menu(self):
        self.draw_menu([
            "s: Start Data Acquisition",
            "",
            "n: Change STH Name",
            "r: Change Run Time",
            "a: Configure ADC",
            "p: Configure Sensors",
            "O: Set Standby Mode",
            "",
            "q: Disconnect from STH",
        ])

    def sth_window_key_evaluation(self) -> Tuple[bool, bool]:
        """Evaluate key input in the STH window

        Returns
        -------

        A tuple containing boolean values, where

        - the first value specifies if the program should stay in the STH
          window, and
        - the second value specifies if the program execution should continue
          (in the main menu)

        """

        curs_set(False)

        continue_sth_window = True
        continue_program = True

        key = self.stdscr.getch()

        if key == Key.CTRL_C:
            continue_program = False
            continue_sth_window = False
        elif key == Key.A:
            self.change_adc_values_window()
        elif key == Key.P:
            self.change_sensors_window()
        elif key == Key.Q:
            continue_sth_window = False
            self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])
        elif key == Key.N:
            self.change_sth_name_window()
        elif key == Key.UPPERCASE_O:
            self.stdscr.clear()
            self.add_string("Are you really sure?\n")
            self.add_string("Only charing will leave this state!\n")
            self.add_string("Pressing “y” will trigger standby: ")
            curs_set(True)
            self.stdscr.refresh()

            if self.read_text()[1] == "y":
                self.Can.Standby(MyToolItNetworkNr["STH1"])
                self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])
                continue_sth_window = False
        elif key == Key.R:
            self.change_runtime_window()
        elif key == Key.S:
            self.stdscr.clear()
            self.add_string("Collecting measurement data…")
            self.stdscr.refresh()
            if not self.KeyBoardInterrupt:
                try:
                    self.vDataAquisition()
                except KeyboardInterrupt:
                    self.KeyBoardInterrupt = True
                    self.__exit__()
                continue_sth_window = False
                continue_program = False

        return (continue_sth_window, continue_program)

    def sth_window(self):
        continue_main = True
        continue_sth = True

        self.update_sensor_config()

        while continue_sth:
            self.sth_window_information()
            self.sth_window_menu()
            continue_sth, continue_main = self.sth_window_key_evaluation()

        return continue_main

    def connect_sth_window(self, number):
        curs_set(True)

        while True:
            devices = self.main_window_information()

            self.add_string("\n")
            y_position = self.stdscr.getyx()[0]
            self.add_string(
                f"Choose STH number (Use “return” to connect): {number}"
            )
            self.stdscr.refresh()
            key = self.stdscr.getch()

            if ord("0") <= key <= ord("9"):
                digit = int(key) - ord("0")
                number = number * 10 + digit

            elif key == Key.DELETE:
                number = int(str(number)[:-1]) if len(str(number)) > 1 else 0

            elif key in {Key.RETURN, Key.ENTER}:
                curs_set(False)

                device_number = number - 1
                device = None
                for dev in devices:
                    if dev["DeviceNumber"] == device_number:
                        device = dev

                if not device:
                    return False

                name = device["Name"]
                self.add_string(
                    y_position, 0, f"Connecting to device “{name}”…{' ' * 20}"
                )
                self.stdscr.refresh()

                self.vDeviceAddressSet(hex(device["Address"]))
                self.sth_name = name
                self.stdscr.refresh()
                success = self.Can.bBlueToothConnectPollingAddress(
                    MyToolItNetworkNr["STU1"], self.iAddress
                )
                if not success:
                    return False

                # Check if the connected hardware supports channel
                # configuration
                try:
                    self.Can.read_sensor_config()
                    self.channel_config_supported = True
                except UnsupportedFeatureException:
                    self.channel_config_supported = False

                return True

            elif key in {Key.CTRL_C, ord("q")}:
                return False

        return False

    def change_filename_window(self):
        curs_set(True)
        self.stdscr.clear()

        self.add_string("Set base output file name: ")
        self.stdscr.refresh()

        forbidden_characters = set('<>:"/\\|?*')
        input_valid, filename = self.read_text(
            default=str(Path(settings.measurement.output.filename).stem),
            allowed=lambda filename: 1 <= len(filename) <= 200 >= 1
            and not set(filename).intersection(forbidden_characters),
        )

        curs_set(False)
        if input_valid:
            self.set_output_filename(filename)
        self.add_string(
            "New full name (including time stamp): "
            f"“{settings.get_output_filepath()}”"
        )
        self.stdscr.refresh()
        sleep(2)

    def change_sth_name_window(self):
        curs_set(True)
        self.stdscr.clear()
        self.add_string("New STH name (max. 8 characters): ")
        self.stdscr.refresh()
        name_valid, name = self.read_text(
            default=self.sth_name, allowed=lambda text: len(text) <= 8
        )

        if not name_valid:
            return

        self.sth_name = name
        self.Can.vBlueToothNameWrite(MyToolItNetworkNr["STH1"], 0, name)

    def window_header(self):
        self.stdscr.clear()
        self.add_string(f"{' ' * 16}ICOc\n\n")

    def main_window_information(self):
        self.window_header()

        # Removing a disconnected sensor device from the list of displayed
        # sensor devices takes quite some time (about 40 seconds). The first
        # reason for that is probably the function `tDeviceList` below, which
        # takes about 20 seconds before it removes a disconnected sensor from
        # the returned list. It takes about another 20 seconds before the list
        # of displayed sensors is updated afterwords.
        #
        # The reason behind this bug is unclear, especially since updating the
        # list with new values usually takes less than a second. Adding a new
        # or recently disconnected sensor device to the list also seems to work
        # without any perceptible delay.

        devices = self.Can.tDeviceList(MyToolItNetworkNr["STU1"], bLog=False)
        sleep(0.02)  # Sleep a little bit to reduce CPU usage

        header = f"{' ' * 7}Name      Address            RSSI{' ' * 7}"
        ruler = "—" * len(header)
        for line in (header, ruler):
            self.add_string(f"{line}\n")

        for device in devices:
            number = device["DeviceNumber"] + 1
            address = int_to_mac_address(device["Address"])
            name = device["Name"]
            rssi = device["RSSI"]
            self.add_string(f"{number:5}: {name:8}  {address}  {rssi} dBm\n")

        return devices

    def main_window_menu(self):
        self.draw_menu([
            "1-9: Connect to STH",
            "",
            "  f: Change Output File Name",
            "  n: Change STH Name",
            "",
            "  q: Quit ICOc",
        ])

    def main_window_key_evaluation(self) -> bool:
        """Evaluate key input in the main window

        Returns
        -------

        - True, if the execution of the main menu should continue
        - False, if the user interface should be closed

        """

        key = self.stdscr.getch()

        if key in {Key.Q, Key.CTRL_C}:
            return False

        if Key.ONE <= key <= Key.NINE:
            return (
                self.sth_window()
                if self.connect_sth_window(int(key - Key.ZERO))
                else True
            )

        if key == Key.F:
            self.change_filename_window()
            return True

        if key == Key.N:
            if self.connect_sth_window(0):
                self.change_sth_name_window()
                self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])
            else:
                self.add_string("Device was not available\n")
                self.stdscr.refresh()

        return True

    def main_window(self):
        curs_set(False)

        self.main_window_information()
        self.main_window_menu()

        # Refresh display to remove disconnected sensor devices
        self.stdscr.refresh()

        return self.main_window_key_evaluation()

    def user_interface(self, stdscr):
        self.stdscr = stdscr

        # TODO: Do not refresh the whole display constantly
        # Possible Solution:
        # - Spawn two threads
        # - One of them waits for input (blocking)
        # - Other thread refreshes list of devices
        self.stdscr.nodelay(1)
        self.stdscr.clear()

        try:
            while self.main_window():
                pass
        except KeyboardInterrupt:
            self.KeyBoardInterrupt = True

    def run(self):
        self._vRunConsoleStartup()
        self.reset()
        if self.connect:
            self.vRunConsoleAutoConnect()
        else:
            wrapper(self.user_interface)
        self.close()


def main():
    try:
        UserInterface().run()
    except Exception as error:
        print(f"Error\n—————\n☹️ {error}\n", file=stderr)
        print("Stack Trace\n———————————", file=stderr)
        raise error


if __name__ == "__main__":
    main()
