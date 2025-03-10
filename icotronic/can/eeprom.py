"""Read and write EEPROM data of ICOtronic devices"""

# -- Imports ------------------------------------------------------------------

from struct import unpack

from icotronic.can.message import Message
from icotronic.can.node import NodeId
from icotronic.can.spu import SPU

# -- Classes ------------------------------------------------------------------


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

    # ===========
    # = General =
    # ===========

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

    async def read_float(self, address: int, offset: int) -> float:
        """Read EEPROM data in float format

        Parameters
        ----------

        address:
            The page number in the EEPROM

        offset:
            The offset to the base address in the specified page

        Returns
        -------

        The float number at the specified location of the EEPROM

        Example
        -------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection
        >>> from icotronic.can.sth import STH

        Read slope of acceleration for x-axis of STH 1

        >>> async def read_slope():
        ...     async with Connection() as stu:
        ...         # We assume that at least one sensor device is available
        ...         async with stu.connect_sensor_device(0, STH) as sth:
        ...             return await sth.eeprom.read_float(address=8, offset=0)
        >>> slope = run(read_slope())
        >>> isinstance(slope, float)
        True

        """

        data = await self.read(address, offset, length=4)
        return unpack("<f", bytearray(data))[0]

    async def read_int(
        self,
        address: int,
        offset: int,
        length: int,
        signed: bool = False,
    ) -> int:
        """Read an integer value from the EEPROM

        Parameters
        ----------

        address:
            The page number in the EEPROM

        offset:
            The offset to the base address in the specified page

        length:
            This value specifies how long the number is in bytes

        signed:
            Specifies if `value` is a signed number (`True`) or an
            unsigned number (`False`)

        Returns
        -------

        The number at the specified location of the EEPROM

        Example
        -------

        >>> from asyncio import run
        >>> from icotronic.can.connection import Connection

        Read the operating time (in seconds) of STU 1

        >>> async def read_operating_time():
        ...     async with Connection() as stu:
        ...         return await stu.eeprom.read_int(address=5, offset=8,
        ...                                          length=4)
        >>> operating_time = run(read_operating_time())
        >>> operating_time >= 0
        True

        """

        return int.from_bytes(
            await self.read(address, offset, length),
            "little",
            signed=signed,
        )


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import run_docstring_examples

    run_docstring_examples(
        EEPROM.read_int,
        globals(),
        verbose=True,
    )
