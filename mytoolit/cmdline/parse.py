"""Command Line Parsing support"""

# -- Imports ------------------------------------------------------------------

from argparse import ArgumentParser, ArgumentTypeError
from math import inf
from re import compile as re_compile

from netaddr import AddrFormatError, EUI

from mytoolit.can.adc import ADCConfiguration

# -- Functions ----------------------------------------------------------------


def base64_mac_address(name):
    """Check if the given text represents a Base64 encoded MAC address

    Throws
    ------

    An argument type error in case the given value does not represent a MAC
    address


    Returns
    -------

    The given text on success

    Examples
    --------

    >>> base64_mac_address("CGvXAd6B")
    'CGvXAd6B'

    >>> base64_mac_address("CGvXAd")
    Traceback (most recent call last):
       ...
    argparse.ArgumentTypeError: “CGvXAd” is not a Base64 encoded MAC address

    """

    base64_regex = re_compile("[A-Za-z0-9/+]{8}$")
    if base64_regex.match(name):
        return name
    raise ArgumentTypeError(f"“{name}” is not a Base64 encoded MAC address")


def byte_value(value):
    """Check if the given string represents a byte value

    Throws
    ------

    An argument type error in case the given value does not represent a
    (positive) byte value

    Returns
    -------

    An integer representing the given value on success

    Examples
    --------

    >>> byte_value("0xa")
    10

    >>> byte_value("137")
    137

    >>> byte_value("256")
    Traceback (most recent call last):
       ...
    argparse.ArgumentTypeError: “256” is not a valid byte value

    """

    try:
        number = int(value, base=0)
        if number < 0 or number > 255:
            raise ValueError()
        return number
    except ValueError as error:
        raise ArgumentTypeError(
            f"“{value}” is not a valid byte value"
        ) from error


def channel_number(value: str):
    """Check if the given string represents a valid channel number (0 – 255)

    Throws
    ------

    An argument type error in case the given value does not represent a
    channel number

    Returns
    -------

    An integer representing the given channel number on success

    Examples
    --------

    >>> channel_number("1")
    1

    >>> channel_number("123")
    123

    >>> channel_number("0")
    0

    >>> channel_number("255")
    255

    >>> channel_number("-1")
    Traceback (most recent call last):
       ...
    argparse.ArgumentTypeError: “-1” is not a valid channel number

    >>> channel_number("256")
    Traceback (most recent call last):
       ...
    argparse.ArgumentTypeError: “256” is not a valid channel number

    """

    try:
        number = int(value)
        if number < 0 or number > 255:
            raise ValueError()
        return number
    except ValueError as error:
        raise ArgumentTypeError(
            f"“{value}” is not a valid channel number"
        ) from error


def mac_address(address: str) -> EUI:
    """Check if the given text represents a MAC address

    Throws
    ------

    An argument type error in case the given text does not store a MAC
    address of the form `xx:xx:xx:xx:xx:xx`, where `x` represents a
    hexadecimal number.

    Returns
    -------

    The given text on success

    Examples
    --------

    >>> mac_address("08:6b:d7:01:de:81")
    EUI('08-6B-D7-01-DE-81')

    >>> mac_address("08:6b:d7:01:de:666")
    Traceback (most recent call last):
       ...
    argparse.ArgumentTypeError: “08:6b:d7:01:de:666” is not a valid MAC address

    """

    try:
        eui = EUI(address)
    except AddrFormatError as error:
        raise ArgumentTypeError(
            f"“{address}” is not a valid MAC address"
        ) from error

    return eui


def measurement_time(value: str) -> float:
    """Check if the given number is valid measurement time

    0 will be interpreted as infinite measurement runtime

    Raises
    ------

    An argument type error in case the given text is not a valid measurement
    time value

    Returns
    -------

    A float value representing the measurement time on success

    Examples
    --------

    >>> measurement_time("0")
    inf

    >>> measurement_time("0.1")
    0.1

    >>> measurement_time("12.34")
    12.34

    >>> measurement_time("-1")
    Traceback (most recent call last):
       ...
    argparse.ArgumentTypeError: “-1” is not a valid measurement time

    >>> measurement_time("something")
    Traceback (most recent call last):
       ...
    argparse.ArgumentTypeError: “something” is not a valid measurement time

    """

    try:
        number = float(value)
        if number < 0:
            raise ValueError()
        if number == 0:
            return inf
        return number
    except ValueError as error:
        raise ArgumentTypeError(
            f"“{value}” is not a valid measurement time"
        ) from error


def device_number(value: str) -> int:
    """Check if the given number is valid Bluetooth device number

    Returns
    -------

    An integer representing the given channel number on success

    Examples
    --------

    >>> device_number("0")
    0

    >>> device_number("123")
    123

    >>> device_number("-1")
    Traceback (most recent call last):
       ...
    argparse.ArgumentTypeError: “-1” is not a valid Bluetooth device number

    >>> device_number("hello")
    Traceback (most recent call last):
       ...
    argparse.ArgumentTypeError: “hello” is not a valid Bluetooth device number

    """

    try:
        number = int(value)
        if number < 0:
            raise ValueError()
        return number
    except ValueError as error:
        raise ArgumentTypeError(
            f"“{value}” is not a valid Bluetooth device number"
        ) from error


def sth_name(name: str) -> str:
    """Check if the given text is a valid STH name

    Throws
    ------

    An argument type error in case the given text does not store a valid STH
    name. This is the case, if the name

    - is longer than 8 characters or
    - contains non-ASCII data.

    Returns
    -------

    The given name on success

    Examples
    --------

    >>> sth_name("Blubb")
    'Blubb'

    >>> sth_name("Blübb")
    Traceback (most recent call last):
       ...
    argparse.ArgumentTypeError: “Blübb” is not a valid STH name

    >>> sth_name("123456789")
    Traceback (most recent call last):
       ...
    argparse.ArgumentTypeError: “123456789” is too long to be a valid STH name

    """

    try:
        name.encode("ascii")
    except UnicodeEncodeError as error:
        raise ArgumentTypeError(f"“{name}” is not a valid STH name") from error

    if len(name) > 8:
        raise ArgumentTypeError(f"“{name}” is too long to be a valid STH name")

    return name


def add_identifier_arguments(parser: ArgumentParser) -> None:
    """Add device identifier arguments to given argument parser

    parser:
        The parser which should include the device identifier arguments

    """

    identifier_arg_group = parser.add_argument_group(
        title="Sensor Device Identifier"
    )

    identifier_group = identifier_arg_group.add_mutually_exclusive_group(
        required=True
    )

    identifier_group.add_argument(
        "-n",
        "--name",
        dest="identifier",
        metavar="NAME",
        help="Name of sensor device",
        default="Test-STH",
    )
    identifier_group.add_argument(
        "-m",
        "--mac-address",
        dest="identifier",
        metavar="MAC_ADRESS",
        help="Bluetooth MAC address of sensor device",
        type=mac_address,
    )
    identifier_group.add_argument(
        "-d",
        "--device-number",
        type=device_number,
        dest="identifier",
        metavar="DEVICE_NUMBER",
        help="Bluetooth device number of sensor device",
    )


def add_adc_arguments(parser: ArgumentParser) -> None:
    """Add ADC arguments to given argument parser

    parser:
        The parser which should include the ADC arguments

    """

    adc_group = parser.add_argument_group(title="ADC")
    adc_group.add_argument(
        "-s",
        "--prescaler",
        type=int,
        choices=range(2, 128),
        metavar="2–127",
        default=2,
        required=False,
        help="Prescaler value",
    )
    adc_group.add_argument(
        "-a",
        "--acquisition",
        type=int,
        choices=sorted([2**number for number in range(9)] + [3]),
        default=8,
        required=False,
        help="Acquisition time value",
    )
    adc_group.add_argument(
        "-o",
        "--oversampling",
        type=int,
        choices=[2**number for number in range(13)],
        default=64,
        required=False,
        help="Oversampling rate value",
    )
    adc_group.add_argument(
        "-v",
        "--voltage-reference",
        choices=ADCConfiguration.REFERENCE_VOLTAGES,
        default=3.3,
        required=False,
        help="Reference voltage in V",
    )


def add_channel_arguments(group) -> None:
    """Add channel arguments to given argument parser group

    Parameters
    ----------

    group:
        The parser group to which the channel arguments should be added to

    """

    group.add_argument(
        "-1",
        "--first-channel",
        type=channel_number,
        default=1,
        const=1,
        nargs="?",
        help=(
            "sensor channel number for first measurement channel "
            "(1 - 255; 0 to disable)"
        ),
    )
    group.add_argument(
        "-2",
        "--second-channel",
        type=channel_number,
        default=0,
        const=2,
        nargs="?",
        help=(
            "sensor channel number for second measurement channel "
            "(1 - 255; 0 to disable)"
        ),
    )
    group.add_argument(
        "-3",
        "--third-channel",
        type=channel_number,
        default=0,
        const=3,
        nargs="?",
        help=(
            "sensor channel number for third measurement channel "
            "(1 - 255; 0 to disable)"
        ),
    )


def create_icon_parser() -> ArgumentParser:
    """Create command line parser for icon

    Returns
    -------

    A parser for the CLI arguments of icon

    """

    parser = ArgumentParser(description="ICOtronic CLI tool")

    parser.add_argument(
        "--log",
        choices=("debug", "info", "warning", "error", "critical"),
        default="warning",
        required=False,
        help="minimum log level",
    )

    subparsers = parser.add_subparsers(
        required=True, title="Subcommands", dest="subcommand"
    )

    # ==========
    # = Config =
    # ==========

    subparsers.add_parser(
        "config", help="Open config file in default application"
    )

    # =============
    # = Data Loss =
    # =============

    dataloss_parser = subparsers.add_parser(
        "dataloss", help="Check data loss at different sample rates"
    )
    add_identifier_arguments(dataloss_parser)

    # ========
    # = List =
    # ========

    subparsers.add_parser("list", help="List sensor devices")

    # ===========
    # = Measure =
    # ===========

    measurement_parser = subparsers.add_parser(
        "measure", help="Store measurement data"
    )

    measurement_group = measurement_parser.add_argument_group(
        title="Measurement"
    )

    measurement_group.add_argument(
        "-t",
        "--time",
        type=measurement_time,
        help="measurement time in seconds (0 for infinite runtime)",
        default=10,
    )

    add_channel_arguments(measurement_group)
    add_identifier_arguments(measurement_parser)
    add_adc_arguments(measurement_parser)

    # ==========
    # = Rename =
    # ==========

    rename_parser = subparsers.add_parser(
        "rename", help="Rename a sensor device"
    )
    add_identifier_arguments(rename_parser)
    rename_parser.add_argument(
        "name", type=str, help="New name of STH", nargs="?", default="Test-STH"
    )

    # =======
    # = STU =
    # =======

    stu_parser = subparsers.add_parser(
        "stu", help="Execute commands related to stationary receiver unit"
    )

    stu_subparsers = stu_parser.add_subparsers(
        required=True, title="Subcommands", dest="stu_subcommand"
    )
    stu_subparsers.add_parser(
        "ota", help="Enable “over the air” (OTA) update mode"
    )
    stu_subparsers.add_parser("mac", help="Show Bluetooth MAC address")
    stu_subparsers.add_parser("reset", help="Reset STU")

    return parser


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import testmod

    testmod()
