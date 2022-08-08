# -- Imports ------------------------------------------------------------------

from argparse import ArgumentTypeError
from re import compile

from netaddr import AddrFormatError, EUI

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


def channel_number(value: str):
    """Check if the given string represents a valid channel number (0 –255)

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
    except ValueError:
        raise ArgumentTypeError(f"“{value}” is not a valid channel number")


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
        mac_address = EUI(address)
    except AddrFormatError:
        raise ArgumentTypeError(f"“{address}” is not a valid MAC address")

    return mac_address


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
        name.encode('ascii')
    except UnicodeEncodeError:
        raise ArgumentTypeError(f"“{name}” is not a valid STH name")

    if len(name) > 8:
        raise ArgumentTypeError(f"“{name}” is too long to be a valid STH name")

    return name


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()