# -- Imports ------------------------------------------------------------------

from argparse import ArgumentTypeError
from re import compile

# -- Functions ----------------------------------------------------------------


def byte_value(value):
    """Check if the given integer like value represents a byte value

    Throws
    ------

    An argument type error in case the given value does not represent a
    (positive) byte value


    Returns
    -------

    An integer representing the given value on success
    """

    try:
        number = int(value, base=0)
        if number < 0 or number > 255:
            raise ValueError()
        return number
    except ValueError:
        raise ArgumentTypeError(f"“{value}” is not a valid byte value")


def mac_address(address):
    """Check if the given text represents a MAC address

    Throws
    ------

    An argument type error in case the given text does not store a MAC
    address of the form `xx:xx:xx:xx:xx:xx`, where `x` represents a
    hexadecimal number.

    Returns
    -------

    The given text on success
    """

    mac_regex = compile("[0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5}$")
    if mac_regex.match(address):
        return address
    raise ArgumentTypeError(f"“{address}” is not a valid MAC address")
