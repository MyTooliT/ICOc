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
