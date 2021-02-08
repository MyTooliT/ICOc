# -- Imports ------------------------------------------------------------------

from base64 import b64encode, b64decode

# -- Functions ----------------------------------------------------------------


def bytearray_to_text(data):
    """Convert byte array data to a string

    Please note, that this function ignores non ASCII data and control
    characters

    Parameters
    ----------

    data
        The byte array that should be converted

    Returns
    -------

    An string where each (valid) byte of the input is mapped to an ASCII
    character

    Examples
    --------

    >>> bytearray_to_text("test".encode('ASCII'))
    'test'

    >>> input = bytearray([0, 255, 10, 30]) + "something".encode('ASCII')
    >>> bytearray_to_text(input)
    'something'

    """

    return bytearray(filter(lambda byte: byte > ord(' ') and byte < 128,
                            data)).decode('ASCII')


def convert_mac_base64(mac):
    """Convert a Bluetooth MAC address to a Base64 encoded text

    Parameters
    ----------

    mac:
        The MAC address as an iterable of 8 byte sized integer values

    Returns
    -------

    The MAC address as Base64 encoded string

    Example
    -------

    >>> convert_mac_base64([0x08, 0x6b, 0xd7, 0x01, 0xde, 0x81])
    'CGvXAd6B'

    """

    return b64encode(bytes(mac)).decode()


def convert_base64_mac(name):
    """Convert a Base64 encoded MAC address into a readable MAC address

    Parameters
    ----------

    mac:
        A Base64 encoded text that stores a (Bluetooth) MAC address

    Returns
    -------

    A MAC address as Base64 encoded string

    Example
    -------

    >>> convert_base64_mac('CGvXAd6B')
    '08:6b:d7:01:de:81'

    """

    mac = list(b64decode(name))
    return ":".join([f"{byte:02x}" for byte in mac])


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
