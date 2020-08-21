# -- Imports ------------------------------------------------------------------

from base64 import b64encode, b64decode

# -- Functions ----------------------------------------------------------------


def convert_mac_base64(mac):
    """Convert a Bluetooth MAC address to a Base64 encoded text

    Arguments
    ---------

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

    Arguments
    ---------

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
