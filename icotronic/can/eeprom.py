"""Read and write EEPROM data of ICOtronic devices"""

# -- Imports ------------------------------------------------------------------

from icotronic.can.message import Message
from icotronic.can.node import NodeId
from icotronic.can.spu import SPU

# -- Classes ------------------------------------------------------------------

# pylint: disable=too-few-public-methods


class EEPROM:
    """Read and write EEPROM data"""

    def __init__(self, spu: SPU, node: NodeId) -> None:
        """Create an EEPROM instance using the given arguments

        Parameters
        ----------

        spu:
            A SPU object used to communicate with the ICOtronic system

        node:
            The node identifier of the node that contains the EEPROM

        """

        self.spu = spu
        self.id = node

    # ==========
    # = EEPROM =
    # ==========

    async def read(self, address: int, offset: int, length: int) -> list[int]:
        """Read EEPROM data

        Parameters
        ----------

        address:
            The page number in the EEPROM

        offset:
            The offset to the base address in the specified page

        length:
            This value specifies how many bytes you want to read

        node:
            The node from which the EEPROM data should be retrieved

        Returns
        -------

        A list containing the EEPROM data at the specified location

        Example
        -------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Read EEPROM data from STU 1

        >>> async def read_eeprom():
        ...     async with Connection() as stu:
        ...         return await stu.eeprom.read(address=0, offset=1, length=8)
        >>> data = run(read_eeprom())
        >>> len(data)
        8
        >>> all((0 <= byte <= 255 for byte in data))
        True

        """

        read_data: list[int] = []
        reserved = [0] * 5
        data_start = 4  # Start index of data in response message

        node = self.id
        while length > 0:
            # Read at most 4 bytes of data at once
            read_length = 4 if length > 4 else length
            message = Message(
                block="EEPROM",
                block_command="Read",
                sender=self.spu.id,
                receiver=node,
                request=True,
                data=[address, offset, read_length, *reserved],
            )

            # pylint: disable=protected-access
            response = await self.spu._request(
                message, description=f"read EEPROM data from “{node}”"
            )
            # pylint: enable=protected-access

            data_end = data_start + read_length
            read_data.extend(response.data[data_start:data_end])
            length -= read_length
            offset += read_length

        return read_data


# pylint: enable=too-few-public-methods

# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import run_docstring_examples

    run_docstring_examples(
        EEPROM.read,
        globals(),
        verbose=True,
    )
