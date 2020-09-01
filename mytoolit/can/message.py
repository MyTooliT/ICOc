# -- Imports ------------------------------------------------------------------

from can.interfaces.pcan.basic import TPCANMsg

# Add current path for doctest execution
from os.path import abspath, dirname
from sys import path as module_path
module_path.append(dirname(abspath(__file__)))

from identifier import Identifier

# -- Class --------------------------------------------------------------------


class Message:
    """Wrapper class for CAN messages"""

    def __init__(self, pcan_message):
        """Create a new message based on the data of a PCAN message

        Parameters
        ----------

        pcan_message:
            A PCAN message structure as used by the PCAN Basic API

        Example
        -------

        >>> message = Message(TPCANMsg())
        """

        self.pcan_message = pcan_message

    def __repr__(self):
        """Get a textual representation of the current message

        Returns
        -------

        A text that shows the various attributes of the current message

        Example
        -------

        >>> pcan_message = TPCANMsg()
        >>> pcan_message.ID = Identifier(block=0, block_command=1,
        ...                             request= True, error=False,
        ...                             sender=1, receiver=14).value
        >>> pcan_message.DATA[0] = 0xfe
        >>> pcan_message.DATA[1] = 0xfe
        >>> pcan_message.LEN = 2
        >>> Message(pcan_message)
        [STH1 → STH14, Block: System, Command: Reset, Request] 0xfe, 0xfe
        """

        representation = ", ".join([
            hex(self.pcan_message.DATA[byte])
            for byte in range(self.pcan_message.LEN)
        ])

        return f"{Identifier(self.pcan_message.ID)} {representation}"


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
