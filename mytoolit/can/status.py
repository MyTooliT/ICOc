# -- Imports ------------------------------------------------------------------

from os.path import abspath, dirname
from sys import path as module_path

# Add path for custom libraries
repository_root = dirname(dirname(dirname(abspath(__file__))))
module_path.append(repository_root)

from MyToolItCommands import NetworkStateName

# -- Class --------------------------------------------------------------------


class StatusWord0:
    """Wrapper class for status word 0"""

    def __init__(self, value):
        """Initialize the status word with the given value

        Argument
        --------

        value:
            A 32 bit integer or list of bytes that specifies the value of the
            status word
        """

        # Currently only the first byte (of the little endian version) of
        # status word 0 contains (non-reserved) data
        self.value = value if isinstance(value, int) else value[0]

    def __repr__(self):
        """Retrieve the textual representation of the status word

        Returns
        -------

        A string that describes the attributes of the status word

        Examples
        --------

        >>> StatusWord0(0b1010)
        State: Network State Operating, No Error

        >>> StatusWord0([0b1010, 0, 0, 0])
        State: Network State Operating, No Error

        >>> StatusWord0(0b1)
        State: Network State Failure, Error
        """

        error = self.value & 1
        state = (self.value >> 1) & 0b111
        state_name = NetworkStateName[state]

        description = ", ".join(
            [f"State: {state_name}", f"{'' if error else 'No '}Error"])

        return description


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
