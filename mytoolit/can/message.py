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

    def __init__(self, *pcan_message, identifier=None, payload=None):
        """Create a new message based on the given attributes

        Usually you will either specify the Peak CAN message directly, or
        provide identifier and payload. If, you decide to specify both
        the Peak CAN message and one of the keyword arguments, then the
        keyword arguments will be used to overwrite specific parts of the
        Peak CAN message.

        Parameters
        ----------

        pcan_message:
            A PCAN message structure as used by the PCAN Basic API

        identifier:
            A 29 bit CAN identifier

        payload:
            An iterable over 8 bit values that stores the payload of the
            message

        Examples
        --------

        >>> message = Message(TPCANMsg())

        >>> identifier = Identifier(block=0, block_command=1)
        >>> payload = [0xab, 0xcd]
        >>> message = Message(identifier=identifier, payload=payload)

        """
        self.pcan_message = pcan_message[0] if pcan_message else TPCANMsg()

        if identifier:
            self.pcan_message.ID = identifier if isinstance(
                identifier, int) else identifier.value

        if payload:
            for byte, data in enumerate(payload):
                self.pcan_message.DATA[byte] = data
            self.pcan_message.LEN = len(payload)

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
        >>> Message(pcan_message) # doctest:+NORMALIZE_WHITESPACE
        [STH1 → STH14, Block: System, Command: Reset, Request]
        0b00000000000000110000001001110 2 0xfe 0xfe
        """

        identifier = Identifier(self.pcan_message.ID)

        payload_representation = " ".join([
            hex(self.pcan_message.DATA[byte])
            for byte in range(self.pcan_message.LEN)
        ])
        bit_representation = " ".join([
            f"0b{identifier.value:029b}",
            str(self.pcan_message.LEN), payload_representation
        ])

        return f"{identifier}\n{bit_representation}"


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
