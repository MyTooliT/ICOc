# -- Imports ------------------------------------------------------------------

from can.interfaces.pcan.basic import PCAN_MESSAGE_EXTENDED, TPCANMsg

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
        self.pcan_message.MSGTYPE = PCAN_MESSAGE_EXTENDED

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
        ...                             request=True, error=False,
        ...                             sender=1, receiver=14).value
        >>> pcan_message.DATA[0] = 0xfe
        >>> pcan_message.DATA[1] = 0xfe
        >>> pcan_message.LEN = 2
        >>> Message(pcan_message) # doctest:+NORMALIZE_WHITESPACE
        0b00000000000000110000001001110 2 0xfe 0xfe
        # [STH1 → STH14, Block: System, Command: Reset, Request]
        """

        identifier = Identifier(self.pcan_message.ID)

        payload_representation = " ".join([
            hex(self.pcan_message.DATA[byte])
            for byte in range(self.pcan_message.LEN)
        ])
        bit_values = [
            f"0b{identifier.value:029b}",
            str(self.pcan_message.LEN), payload_representation
        ]
        # Filter empty string, since otherwise there might be an additional
        # space at the end of the representation for empty payloads
        bit_representation = " ".join(filter(None, bit_values))

        return f"{bit_representation} # {identifier}"

    def acknowledge(self, error=False):
        """Returns an acknowledgment message object for this message

        In the acknowledgment message receiver and sender will be swapped and
        the request (acknowledge) bit will be set to 0 (acknowledge). The
        payload of the acknowledgment message will be empty.

        Returns
        -------

        An acknowledgment message for the current message

        Example
        -------

        >>> identifier = Identifier(block=0, block_command=1, sender=5,
        ...                         receiver=10)
        >>> message = Message(identifier=identifier, payload=[0xaa])
        >>> message.acknowledge() # doctest:+NORMALIZE_WHITESPACE
        0b00000000000000100001010000101 0
        # [STH10 → STH5, Block: System, Command: Reset, Acknowledge]
        """

        identifier = Identifier(self.pcan_message.ID)
        block = identifier.block()
        block_command = identifier.block_command()
        sender = identifier.receiver()
        receiver = identifier.sender()
        acknowledgment_identifier = Identifier(block=block,
                                               block_command=block_command,
                                               request=False,
                                               error=error,
                                               sender=sender,
                                               receiver=receiver)

        return Message(identifier=acknowledgment_identifier, payload=[])


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
