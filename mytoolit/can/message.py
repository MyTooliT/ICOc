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
        >>> pcan_message.ID = Identifier(command=0, sender=1, receiver=14
        ...                             ).value
        >>> Message(pcan_message)
        [STH1 → STH14, Block: System, Command: Verboten, Acknowledge, Error]
        """

        return repr(Identifier(self.pcan_message.ID))


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
