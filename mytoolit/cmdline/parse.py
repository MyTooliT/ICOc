# -- Imports ------------------------------------------------------------------

from argparse import ArgumentTypeError
from re import compile

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

    base64_regex = compile("[A-Za-z0-9/+]{8}$")
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

    Examples
    --------

    >>> mac_address("08:6b:d7:01:de:81")
    '08:6b:d7:01:de:81'

    >>> mac_address("08:6b:d7:01:de:8")
    Traceback (most recent call last):
       ...
    argparse.ArgumentTypeError: “08:6b:d7:01:de:8” is not a valid MAC address

    """

    mac_regex = compile("[0-9a-fA-F]{2}(?:[:-][0-9a-fA-F]{2}){5}$")
    if mac_regex.match(address):
        return address
    raise ArgumentTypeError(f"“{address}” is not a valid MAC address")


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
