"""Data conversion functions"""

# -- Imports ------------------------------------------------------------------

from typing import Iterable

# -- Functions ----------------------------------------------------------------


def convert_bytes_to_text(
    data: Iterable[int], until_null: bool = False
) -> str:
    """Convert byte array data to a string

    Please note, that this function ignores non ASCII data and control
    characters

    Parameters
    ----------

    data:
        The byte array that should be converted

    until_null:
        Ignore data after the first `NULL` byte (`True`) or not `False`

    Returns
    -------

    An string where the (valid) bytes of the input are mapped to an ASCII
    character

    Examples
    --------

    >>> convert_bytes_to_text("test".encode('ASCII'))
    'test'

    >>> input = bytearray([0, 255, 10, 30]) + "something".encode('ASCII')
    >>> convert_bytes_to_text(input)
    'something'

    >>> input = bytearray([0, 255, 10, 30]) + "something".encode('ASCII')
    >>> convert_bytes_to_text(input, until_null=True)
    ''

    """

    ascii_bytes = bytearray()
    for byte in data:
        if byte == 0 and until_null:
            break
        if ord(" ") < byte < 128:
            ascii_bytes.append(byte)

    return ascii_bytes.decode("ASCII")


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import testmod

    testmod()
