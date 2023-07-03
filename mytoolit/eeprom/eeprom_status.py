"""Support for reading EEPROM status"""

# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from typing import Union

# -- Class --------------------------------------------------------------------


class EEPROMStatus:
    """This class represents an EEPROM status byte"""

    def __init__(self, status: Union[int, str, EEPROMStatus]) -> None:
        """Create a new status byte from the given argument

        Parameters
        ----------

        status:
            The value of the status byte

        Examples
        --------

        >>> EEPROMStatus(0xca)
        Locked (0xca)

        >>> EEPROMStatus(0)
        Uninitialized (0x00)

        >>> EEPROMStatus('Initialized')
        Initialized (0xac)

        >>> EEPROMStatus('Uninitialized')
        Uninitialized (0x00)

        >>> EEPROMStatus('Locked').value == 0xca
        True

        >>> EEPROMStatus(EEPROMStatus('Locked'))
        Locked (0xca)

        >>> EEPROMStatus('Something')
        Traceback (most recent call last):
           ...
        ValueError: Unknown EEPROM status “Something”

        """

        if isinstance(status, str):
            if status == "Initialized":
                self.value = 0xAC
                return

            if status == "Locked":
                self.value = 0xCA
                return

            if status == "Uninitialized":
                self.value = 0
                return

            raise ValueError(f"Unknown EEPROM status “{status}”")

        if isinstance(status, EEPROMStatus):
            self.value = status.value
            return

        self.value = status

    def __repr__(self) -> str:
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

        description = (
            "Initialized"
            if self.is_initialized()
            else ("Locked" if self.is_locked() else "Uninitialized")
        )

        return f"{description} (0x{value:02x})"

    def is_locked(self) -> bool:
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

        return self.value == 0xCA

    def is_initialized(self) -> bool:
        """Check if the EEPROM is initialized

        Returns
        -------

        `True` if the status byte represents an initialized EEPROM or `False`
        otherwise

        Examples
        --------

        >>> EEPROMStatus(0xca).is_initialized()
        False

        >>> EEPROMStatus(0xac).is_initialized()
        True

        >>> EEPROMStatus(0x2).is_initialized()
        False

        """

        return self.value == 0xAC


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import testmod

    testmod()
