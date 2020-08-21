# -- Imports ------------------------------------------------------------------

from base64 import b64encode

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


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
