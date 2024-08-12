"""Support for streaming (measurement) data in the ICOtronic system"""

# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from asyncio import Queue, wait_for
from ctypes import c_uint8, LittleEndianStructure
from typing import AsyncIterator, Callable, Optional, Sequence, Tuple

from can import Listener, Message

from mytoolit.can.identifier import Identifier

# -- Classes ------------------------------------------------------------------


class StreamingTimeoutError(Exception):
    """Raised if no streaming data was received for a certain amount of time"""


# pylint: disable=too-few-public-methods


class StreamingConfigBits(LittleEndianStructure):
    """Store enable/disabled channels of streaming configuration"""

    _fields_ = [
        ("first", c_uint8, 1),
        ("second", c_uint8, 1),
        ("third", c_uint8, 1),
    ]


# pylint: enable=too-few-public-methods


class StreamingConfiguration:
    """Streaming configuration"""

    def __init__(
        self, first: bool = True, second: bool = False, third: bool = False
    ) -> None:
        """Initialize the streaming configuration with the given values

        Parameters
        ----------

        first:
            Specifies if the first channel is enabled or not

        second:
            Specifies if the second channel is enabled or not

        third:
            Specifies if the third channel is enabled or not

        Raises
        ------

        `ValueError`, if none of the channels is active

        Examples
        --------

        >>> config = StreamingConfiguration()
        >>> config = StreamingConfiguration(
        ...          first=False, second=True, third=True)

        Check invalid configuration

        >>> config = StreamingConfiguration(first=False)
        Traceback (most recent call last):
           ...
        ValueError: At least one channel needs to be active

        >>> config = StreamingConfiguration(
        ...     first=False, second=False, third=False)
        Traceback (most recent call last):
           ...
        ValueError: At least one channel needs to be active

        """

        if sum([first, second, third]) <= 0:
            raise ValueError("At least one channel needs to be active")

        self.channels = StreamingConfigBits(
            first=first, second=second, third=third
        )

    def __repr__(self) -> str:
        """Return the string representation of the streaming configuration

        Examples
        --------

        >>> StreamingConfiguration()
        Channel 1 enabled, Channel 2 disabled, Channel 3 disabled

        >>> StreamingConfiguration(first=False, second=True, third=False)
        Channel 1 disabled, Channel 2 enabled, Channel 3 disabled

        >>> StreamingConfiguration(first=True, second=True, third=True)
        Channel 1 enabled, Channel 2 enabled, Channel 3 enabled

        """

        channels = self.channels

        return ", ".join([
            f"Channel {name} {'en' if status else 'dis'}abled"
            for name, status in enumerate(
                (channels.first, channels.second, channels.third), start=1
            )
        ])

    def data_length(self) -> int:
        """Returns the streaming data length

        This will be either:

        - 2 (when 2 channels are active), or
        - 3 (when 1 or 3 channels are active)

        For more information, please take a look
        [here](https://mytoolit.github.io/Documentation/#command-data)

        Returns
        -------

        The length of the streaming data resulting from this channel
        configuration

        Examples
        --------

        >>> StreamingConfiguration().data_length()
        3

        >>> StreamingConfiguration(
        ...     first=False, second=True, third=False).data_length()
        3

        >>> StreamingConfiguration(
        ...     first=True, second=True, third=True).data_length()
        3

        >>> StreamingConfiguration(
        ...     first=False, second=True, third=True).data_length()
        2

        """

        channels = self.channels

        active_channels = sum(
            [channels.first, channels.second, channels.third]
        )

        return 2 if active_channels == 2 else 3


class AsyncStreamBuffer(Listener):
    """Buffer for streaming data"""

    def __init__(
        self, configuration: StreamingConfiguration, timeout: float
    ) -> None:
        """Initialize object using the given arguments

        Parameters
        ----------

        configuration:
            A streaming configuration that specifies which of the three
            streaming channels should be enabled or not

        timeout:
            The amount of seconds between two consecutive messages, before
            a TimeoutError will be raised

        """

        # Expected identifier of received streaming messages
        self.identifier = Identifier(
            block="Streaming",
            block_command="Data",
            sender="STH 1",
            receiver="SPU 1",
            request=False,
        )
        self.data_length = configuration.data_length()
        self.queue: Queue[Tuple[StreamingData, int]] = Queue()
        self.timeout = timeout
        self.channels = configuration.channels
        self.last_counter = -1
        self.lost_messages = 0

    def __aiter__(self) -> AsyncIterator[Tuple[StreamingData, int]]:
        """Retrieve iterator for collected data

        Returns
        -------

        An iterator over the received streaming data including the number of
        lost messages

        """

        return self

    async def __anext__(self) -> Tuple[StreamingData, int]:
        """Retrieve next stream data object in collected data

        Returns
        -------

        A tuple containing:

        - the data of the streaming message and
        - the number of lost streaming messages right before the returned
          streaming message

        """

        try:
            return await wait_for(self.queue.get(), self.timeout)
        except TimeoutError as error:
            raise StreamingTimeoutError(
                f"No data received for at least {self.timeout} seconds"
            ) from error

    def on_message_received(self, msg: Message) -> None:
        """Handle received messages

        Parameters
        ----------

        msg:
            The received CAN message

        """

        # Ignore messages with wrong id and “Stop Stream” messages
        if msg.arbitration_id != self.identifier.value or len(msg.data) <= 1:
            return

        data = msg.data
        counter = data[1]
        timestamp = msg.timestamp
        data_bytes = (
            (data[2:4], data[4:6], data[6:8])
            if self.data_length == 3
            else (data[2:4], data[4:6])
        )

        values = [
            int.from_bytes(word, byteorder="little") for word in data_bytes
        ]
        assert len(values) == 2 or len(values) == 3

        streaming_data = StreamingData(
            timestamp=timestamp,
            counter=counter,
            values=values,
            channels=self.channels,
        )

        # Calculate amount of lost messages
        if self.last_counter < 0:
            self.last_counter = (counter - 1) % 256
        last_counter = self.last_counter
        lost_messages = (counter - last_counter) % 256 - 1
        self.last_counter = counter
        self.lost_messages += lost_messages

        self.queue.put_nowait((streaming_data, lost_messages))

    def on_error(self, exc: Exception) -> None:
        """This method is called to handle any exception in the receive thread.

        Parameters
        ----------

        exc:
            The exception causing the thread to stop

        """

        raise NotImplementedError()

    def stop(self) -> None:
        """Stop handling new messages"""


class StreamingFormat:
    """Support for specifying the data streaming format

    See also: https://mytoolit.github.io/Documentation/#block-streaming
    """

    # Possible number of data sets
    data_set = [0, 1, 3, 6, 10, 15, 20, 30]

    # pylint: disable=too-many-arguments

    def __init__(
        self,
        *value,
        streaming: Optional[bool] = None,
        width: Optional[int] = 2,
        first: Optional[bool] = None,
        second: Optional[bool] = None,
        third: Optional[bool] = None,
        sets: Optional[int] = None,
        value_explanations: Tuple[str, str, str] = (
            "Value 1",
            "Value 2",
            "Value 3",
        ),
    ) -> None:
        """Initialize the streaming format using the given arguments

        Positional Parameters
        ---------------------

        value:
            The value of the streaming format byte

        Keyword Parameters
        ------------------

        streaming:
            Specifies if this is a request for a stream of data bytes;
            If this value is not set or set to `False`, then the request is
            only for a single value (or set of values).

        width:
            Specifies the width of a single value (either 2 or 3 bytes)

        first:
            Specifies if the first data value should be transmitted or not

        second:
            Specifies if the second data value should be transmitted or not

        third:
            Specifies if the third data value should be transmitted or not

        sets:
            Specifies the number of data sets that should be transmitted

            The value 0 stops the stream. Other possible values for the number
            of sets are 1, 3, 6, 10, 15, 20 and 30.

        value_explanations:
            Three strings used to describe the first, second and third data
            value

        """

        def set_part(start, width, number):
            """Store bit pattern number at bit start of the identifier"""

            streaming_ones = 0xFF
            mask = (1 << width) - 1

            # Set all bits for targeted part to 0
            self.value &= (mask << start) ^ streaming_ones
            # Make sure we use the correct number of bits for number
            number = number & mask
            # Set bits to given value
            self.value |= number << start

        self.value_explanations = value_explanations

        if len(value) > 1:
            raise ValueError("More than one positional argument")

        self.value = value[0] if value else 0

        # =============
        # = Streaming =
        # =============

        if streaming:
            set_part(7, 1, int(streaming))

        # =========
        # = Width =
        # =========

        if width is not None:
            if not (isinstance(width, int) and 2 <= width <= 3):
                raise ValueError(f"Unsupported width value: {width}")

            set_part(6, 1, 1 if width == 3 else 0)

        # =================
        # = Active Values =
        # =================

        for shift, part in enumerate([third, second, first]):
            if part is not None:
                set_part(3 + shift, 1, part)

        # =============
        # = Data Sets =
        # =============

        if sets is not None:
            cls = type(self)

            if sets not in cls.data_set:
                raise ValueError(f"Unsupported number of data sets: {sets}")

            set_part(0, 3, cls.data_set.index(sets))

    # pylint: enable=too-many-arguments

    def __repr__(self) -> str:
        """Retrieve the textual representation of the streaming format

        Returns
        -------

        A string that describes the streaming format

        Examples
        --------

        >>> StreamingFormat(width=3, first=True, sets=15)
        Single Request, 3 Bytes, 15 Data Sets, Read Value 1

        >>> StreamingFormat(0b001, streaming=True)
        Streaming, 2 Bytes, 1 Data Set

        >>> StreamingFormat(0b110111)
        Single Request, 2 Bytes, 30 Data Sets, Read Value 1, Read Value 2

        """

        streaming = self.value >> 7

        data_sets = self.data_sets()
        data_set_explanation = (
            "Stop Stream"
            if data_sets == 0
            else f"{data_sets} Data Set{'' if data_sets == 1 else 's'}"
        )

        parts = [
            "Streaming" if streaming else "Single Request",
            f"{self.data_bytes()} Bytes",
            f"{data_set_explanation}",
        ]

        value_selection = (self.value >> 3) & 0b111

        first = value_selection >> 2
        second = value_selection >> 1 & 1
        third = value_selection & 1

        selected_values = [
            f"Read {value_explanation}"
            for selected, value_explanation in zip(
                (first, second, third), self.value_explanations
            )
            if selected
        ]

        value_explanation = (
            ", ".join(selected_values) if selected_values else ""
        )
        if value_explanation:
            parts.append(value_explanation)

        return ", ".join(parts)

    def data_sets(self) -> int:
        """Get the number of data sets of the streaming format

        Returns
        -------

        The number of data sets

        Examples
        --------

        >>> StreamingFormat(width=3, first=True, sets=15).data_sets()
        15

        >>> StreamingFormat(first=True, second=False, sets=3).data_sets()
        3

        """

        data_set_bits = self.value & 0b111
        cls = type(self)

        return cls.data_set[data_set_bits]

    def data_bytes(self) -> int:
        """Get the number of data bytes used for a single value

        Returns
        -------

        The number of data bytes that represent a single streaming value

        Examples
        --------

        >>> StreamingFormat(width=3, first=True, sets=15).data_bytes()
        3

        >>> StreamingFormat(first=True, second=False, width=2).data_bytes()
        2

        """

        return 3 if (self.value >> 6) & 1 else 2


class StreamingFormatVoltage(StreamingFormat):
    """Support for specifying the streaming format of voltage data"""

    def __init__(self, *arguments, **keyword_arguments) -> None:
        """Initialize the voltage streaming format using the given arguments

        value:
            The value of the streaming format byte

        single:
            Specifies if the request was for a single value or not

        width:
            Specifies the width of a single value (either 2 or 3 bytes)

        first:
            Specifies if the first voltage value should be transmitted or not

        second:
            Specifies if the second voltage value should be transmitted or not

        third:
            Specifies if the third voltage value should be transmitted or not

        sets:
            Specifies the number of data sets that should be transmitted

            The value 0 stops the stream. Other possible values for the number
            of sets are 1, 3, 6, 10, 15, 20 and 30.

        """

        super().__init__(
            *arguments,
            **keyword_arguments,
            value_explanations=("Voltage 1", "Voltage 2", "Voltage 3"),
        )


class StreamingData:
    """Support for storing data of a streaming message"""

    def __init__(
        self,
        counter: int,
        timestamp: float,
        values: Sequence[float],
        channels: StreamingConfigBits,
    ) -> None:
        """Initialize the streaming data with the given arguments

        Parameters
        ----------

        counter:
            The message counter value

        timestamp:
            The message timestamp

        values:
            The streaming values

        channels:
            A bitfield specifying which of the measurement channels was enabled
            when the measurement took place

        """

        self.counter = counter
        self.timestamp = timestamp
        self.values = values
        self.channels = channels

    def apply(
        self,
        function: Callable[[float], float],
    ) -> None:
        """Apply a certain function to the streaming data

        Parameters
        ----------

        function:
            The function that should be applied to the streaming data

        Examples
        --------

        >>> channel3 = StreamingConfigBits(
        ...     first=False, second=False, third=True)
        >>> data = StreamingData(
        ...     values=[1, 2, 3], counter=21, timestamp=1, channels=channel3)
        >>> data.apply(lambda value: value + 10)
        >>> data.values
        [11, 12, 13]

        """

        updated_values = [function(value) for value in self.values]
        assert len(updated_values) == 2 or len(updated_values) == 3
        self.values = updated_values

    def __repr__(self):
        """Get the string representation of the stream data

        Examples
        --------

        >>> all = StreamingConfigBits(
        ...     first=True, second=True, third=True)
        >>> StreamingData(
        ...     values=[1, 2, 3], counter=21, timestamp=1, channels=all)
        [1, 2, 3]@1 #21

        """

        return f"{self.values}@{self.timestamp} #{self.counter}"


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import testmod

    testmod()
