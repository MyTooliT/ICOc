# -- Imports ------------------------------------------------------------------

from base64 import b64encode, b64decode
from netaddr import EUI

# -- Functions ----------------------------------------------------------------


def convert_mac_base64(mac: str) -> str:
    """Convert a Bluetooth MAC address to a Base64 encoded text

    Parameters
    ----------

    mac:
        The MAC address

    Returns
    -------

    The MAC address as Base64 encoded string

    Example
    -------

    >>> convert_mac_base64("08:6b:d7:01:de:81")
    'CGvXAd6B'

    """

    return b64encode(EUI(mac).packed).decode()


def convert_base64_mac(name: str) -> str:
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
