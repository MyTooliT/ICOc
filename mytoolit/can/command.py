# -- Imports ------------------------------------------------------------------

from os.path import abspath, dirname
from sys import path as module_path

# Add path for custom libraries
repository_root = dirname(dirname(dirname(abspath(__file__))))
module_path.append(repository_root)

from MyToolItCommands import MyToolItBlock

# -- Class --------------------------------------------------------------------


class Command:
    """This class represents a command including error and acknowledge bits"""

    def __init__(
            self,
            *command,
            block=None,
            block_command=None,
            request=True,
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
            A 6 bit number that specifies the block of the command

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

        >>> command = Command(block=0, block_command=0)

        """

        def set_part(start, width, number):
            """Store bit pattern number at bit start of the identifier"""

            command_ones = 0xffff
            mask = 2**width - 1

            # Set all bits for targeted part to 0
            self.value &= (mask << start) ^ command_ones
            # Make sure we use the correct number of bits for number
            number = number & mask
            # Set command bits to given value
            self.value |= number << start

        self.value = command[0] if command else 0

        if block:
            set_part(start=10, width=6, number=block)

        if block_command:
            set_part(start=2, width=8, number=block_command)

        if request:
            set_part(start=1, width=1, number=int(bool(request)))

        if error:
            set_part(start=0, width=1, number=int(not (error)))

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


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
