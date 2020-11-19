# -- Class --------------------------------------------------------------------


class EEPROMStatus:
    """This class represents an EEPROM status byte"""

    def __init__(self, value):
        """Create a new status byte from the given argument

        Parameters
        ----------

        value:
            The value of the status byte
        """

        self.value = value

    def __repr__(self):
        """Return the string representation of the status byte

        Returns
        -------

        A string that describes the current value of the status byte

        Examples
        --------

        >>> EEPROMStatus(0xac)
        Initialized (0xac)

        >>> EEPROMStatus(0x13)
        Uninitialized (0x13)

        >>> EEPROMStatus(0xCA)
        Locked (0xca)
        """

        value = self.value

        description = "Initialized" if value == 0xac else (
            "Locked" if self.is_locked() else "Uninitialized")

        return f"{description} (0x{value:02x})"

    def is_locked(self):
        """Check if the EEPROM is locked

        Returns
        -------

        `True` if the status byte represents a locked EEPROM or `False`
        otherwise

        Examples
        --------

        >>> EEPROMStatus(0xca).is_locked()
        True

        >>> EEPROMStatus(0xac).is_locked()
        False

        >>> EEPROMStatus(0x2).is_locked()
        False

        """

        return self.value == 0xca


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod

    testmod()
