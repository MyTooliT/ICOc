# -- Functions ----------------------------------------------------------------


def bytearray_to_text(data: bytearray) -> str:
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
