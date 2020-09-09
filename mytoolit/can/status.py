# -- Imports ------------------------------------------------------------------

from enum import Enum
from os.path import abspath, dirname
from sys import path as module_path

# Add path for custom libraries
repository_root = dirname(dirname(dirname(abspath(__file__))))
module_path.append(repository_root)

from MyToolItCommands import NetworkStateName

# -- Classes ------------------------------------------------------------------


class NodeType(Enum):
    """Specifies the type of a node in the network"""
    STH = 1
    STU = 2


class StatusWord0:
    """Wrapper class for status word 0"""

    def __init__(self, value, node=NodeType.STH):
        """Initialize the status using the given arguments

        Arguments
        ---------

        value:
            A 32 bit integer or list of bytes that specifies the value of the
            status word

        node:
            Specifies the network unit the status word belongs to
        """

        # Currently only the first byte (of the little endian version) of
        # status word 0 contains (non-reserved) data
        self.value = value if isinstance(value, int) else value[0]

        self.type = node

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

        >>> StatusWord0(0b1, NodeType.STH)
        State: Network State Failure, Error

        >>> StatusWord0(0b1101010,
        ...             NodeType.STU) # doctest:+NORMALIZE_WHITESPACE
        State: Network State Operating, No Error, Radio Port Disabled,
        CAN Port Enabled, Bluetooth Connected
        """

        error = self.value & 1

        attributes = [
            f"State: {self.state_name()}", f"{'' if error else 'No '}Error"
        ]

        if self.type == NodeType.STU:
            radio_port_enabled = self.value >> 4 & 1
            can_port_enabled = self.value >> 5 & 1
            bluetooth_connected = self.value >> 6 & 1

            attributes.extend([
                "Radio Port {}".format(
                    "Enabled" if radio_port_enabled else "Disabled"),
                "CAN Port {}".format(
                    "Enabled" if can_port_enabled else "Disabled"),
                "Bluetooth {}".format(
                    "Connected" if bluetooth_connected else "Disconnected"),
            ])

        description = ", ".join(attributes)

        return description

    def error(self):
        """Retrieve the status of the error bit

        Returns
        -------

        True if the error bit was set or False otherwise

        Examples
        --------

        >>> StatusWord0(0b0).error()
        False

        >>> StatusWord0(0b1).error()
        True
        """

        return bool(self.value & 1)

    def state_name(self):
        """Get the name of the state represented by the status word

        Returns
        -------

        A textual representation of the current node state

        Examples
        --------

        >>> StatusWord0(0b1010).state_name()
        'Network State Operating'

        >>> StatusWord0(0b1110).state_name()
        'Network State NoChange'
        """

        state = (self.value >> 1) & 0b111
        return NetworkStateName[state]


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
