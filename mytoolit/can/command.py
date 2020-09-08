# -- Imports ------------------------------------------------------------------

from os.path import abspath, dirname
from sys import path as module_path

# Add path for custom libraries
repository_root = dirname(dirname(dirname(abspath(__file__))))
module_path.append(repository_root)

from MyToolItCommands import MyToolItBlock, blocknumber_to_commands

# -- Class --------------------------------------------------------------------


class Command:
    """This class represents a command including error and acknowledge bits"""

    def __init__(
            self,
            *command,
            block=None,
            block_command=None,
            request=None,
            error=None,
    ):
        """Create a new command from the given arguments

        Usually you will either specify the command directly, or provide
        block, block_command and values for the error and acknowledge/request
        bits. If you decide to specify both the command value and one of the
        keyword arguments, then the keyword arguments will be used to
        overwrite specific parts of the command. For more information, please
        take a look at the examples.


        Arguments
        ---------

        command:
            A 16 bit number that specifies the command including acknowledge
            and error bits (16 bit)

        block:
            A 6 bit number or string that specifies the block of the command

        block_command:
            A 8 bit number that stores the number of the command in the
            specified block

        request:
            A boolean value that specifies if the command is for a request or
            an acknowledgement

        error:
            A boolean value that defines if there was an error or not

        Examples
        --------

        >>> Command(block=0, block_command=0).value
        0

                        block   command A E
        >>> command = 0b001000_00000100_0_0
        >>> bin(Command(command).value)
        '0b10000000010000'

        >>> command = Command(block='System')
        >>> command.block_name()
        'System'
        """

        def set_part(start, width, number):
            """Store bit pattern number at bit start of the identifier"""

            command_ones = 0xffff
            mask = (1 << width) - 1

            # Set all bits for targeted part to 0
            self.value &= (mask << start) ^ command_ones
            # Make sure we use the correct number of bits for number
            number = number & mask
            # Set command bits to given value
            self.value |= number << start

        self.value = command[0] if command else 0

        if isinstance(block, str):
            try:
                block = MyToolItBlock[block]
            except KeyError:
                raise ValueError(f"Unknown block: {block}")

        if block is not None:
            set_part(start=10, width=6, number=block)

        if block_command is not None:
            set_part(start=2, width=8, number=block_command)

        if request is not None:
            set_part(start=1, width=1, number=int(bool(request)))

        if error is not None:
            set_part(start=0, width=1, number=int(bool(error)))

    def __repr__(self):
        """Get a textual representation of the command

        Returns
        -------

        A string that describes the various attributes of the command

        Examples
        --------

                      block   command A E
        >>> Command(0b001000_00000100_0_0)
        Block: StatisticalData, Command: ProductionDate, Acknowledge

                      block   command A E
        >>> Command(block=0, block_command=0x0c, request=True, error=False)
        Block: System, Command: Routing, Request
        """
        error = self.value & 1

        attributes = filter(None, [
            f"Block: {self.block_name()}",
            f"Command: {self.block_command_name()}",
            "Acknowledge" if self.is_acknowledgment() else "Request",
            "Error" if error else None
        ])

        return ', '.join(attributes)

    def block(self):
        """Get the block

        Returns
        -------

        The block number of the command

        Example
        -------

                      block   command A E
        >>> Command(0b000011_00000000_0_0).block()
        3
        """

        return (self.value >> 10) & 0b111111

    def block_name(self):
        """Get a short description of the block

        Returns
        -------

        A short textual representation of the block number

        Examples
        --------
                      block   command A E
        >>> Command(0b101000_00000010_0_0).block_name()
        'Configuration'

                      block   command A E
        >>> Command(0b111101_00000010_0_0).block_name()
        'EEPROM'
        """

        return MyToolItBlock.inverse.get(self.block(), "Unknown")

    def block_command(self):
        """Get the block command number

        Returns
        -------

        The block command number of the command

        Example
        -------

                      block   command A E
        >>> Command(0b001000_00000100_0_0).block_command()
        4
        """

        return (self.value >> 2) & 0xff

    def block_command_name(self):
        """Get the name of the block command

        Returns
        -------

        A short textual representation of the block command

        Examples
        --------

                      block   command A E
        >>> Command(0b101000_00000000_0_0).block_command_name()
        'Acceleration'

                      block   command A E
        >>> Command(0b000000_00001011_0_0).block_command_name()
        'Bluetooth'
        """

        try:
            return blocknumber_to_commands[self.block()].inverse[
                self.block_command()]
        except KeyError:
            return "Unknown"

    def is_acknowledgment(self):
        """Checks if this command represents an acknowledgment

        Returns
        -------

        True if the command is for an acknowledgement, or false otherwise

        Examples
        --------

                      block   command A E
        >>> Command(0b101000_00000000_0_0).is_acknowledgment()
        True

        >>> Command(request=True).is_acknowledgment()
        False
        """

        return bool((self.value >> 1) & 1 == 0)

    def set_acknowledgment(self, value=True):
        """Set the acknowledgment bit to the given value

        Arguments
        ---------

        value:
            A boolean that specifies if the command represents an
            acknowledgment or not

        Examples
        --------

        >>> Command().set_acknowledgment().is_acknowledgment()
        True

        >>> Command().set_acknowledgment(True).is_acknowledgment()
        True

        >>> Command().set_acknowledgment(False).is_acknowledgment()
        False

        Returns
        -------

        The modified command object
        """

        request = not value
        request_bit = 1 << 1

        if request:
            self.value |= request_bit
        else:
            command_ones = 0xff
            self.value &= request_bit ^ command_ones

        return self


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
