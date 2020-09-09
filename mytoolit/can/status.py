# -- Class --------------------------------------------------------------------


class StatusWord0:
    """Wrapper class for status word 0"""

    def __init__(self, value):
        """Initialize the status word with the given value

        Argument
        --------

        value:
            A 32 bit integer that specifies the value of the status word
        """

        self.value = value

    def __repr__(self):
        """Retrieve the textual representation of the status word

        Returns
        -------

        A string that describes the attributes of the status word

        Example
        -------

        >>> StatusWord0(10)
        10
        """

        return repr(self.value)


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
