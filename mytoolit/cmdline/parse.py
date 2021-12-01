# -- Imports ------------------------------------------------------------------

from argparse import ArgumentTypeError
from re import compile

from netaddr import AddrFormatError, EUI

# -- Functions ----------------------------------------------------------------


def axes_spec(spec: str) -> tuple[bool, bool, bool]:
    """Check if the given text represents a spec for acceleration axes

    An axes spec contains three digits, where each digit is either `0` or `1`.
    Every digit specifies if a certain axis is enabled (`1`) or not (`0`).
    The first digit represents the x-axis, the second one the y-axis and the
    last one the z-axis.

    For example the value `110` specifies that the x-axis and y-axis are
    enabled, while the z-axis is not.

    Throws
    ------

    An argument type error in case the given value does not represent an
    axes specification or if none of the axes is enabled.

    Returns
    -------

    A tuple containing three boolean values that specify if the x-, y- and
    z-axis are enabled or not

    Examples
    --------

    >>> axes_spec("101")
    (True, False, True)

    >>> axes_spec("01") # doctest:+NORMALIZE_WHITESPACE
    Traceback (most recent call last):
       ...
    argparse.ArgumentTypeError: “01” contains not enough digits for an axis
                                specification

    >>> axes_spec("1111") # doctest:+NORMALIZE_WHITESPACE
    Traceback (most recent call last):
       ...
    argparse.ArgumentTypeError: “1111” contains too many digits for an axis
                                specification

    >>> axes_spec("120") # doctest:+NORMALIZE_WHITESPACE
    Traceback (most recent call last):
       ...
    argparse.ArgumentTypeError: The axis specification “120” contains invalid
                                characters (only “0” and “1” are allowed)

    >>> axes_spec("000") # doctest:+NORMALIZE_WHITESPACE
    Traceback (most recent call last):
       ...
    argparse.ArgumentTypeError: At least one axis has to be enabled

    """

    allowed_chars_regex = compile("[01]+$")
    if not allowed_chars_regex.fullmatch(spec):
        raise ArgumentTypeError(
            f"The axis specification “{spec}” contains invalid characters "
            "(only “0” and “1” are allowed)")

    if len(spec) != 3:
        description = "not enough" if len(spec) < 3 else "too many"
        raise ArgumentTypeError(f"“{spec}” contains {description} digits "
                                "for an axis specification")

    if int(spec) == 0:
        raise ArgumentTypeError("At least one axis has to be enabled")

    x, y, z = (bool(int(axis)) for axis in spec)
    return (x, y, z)


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
