# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from asyncio import Queue
from numbers import Real
from typing import (
    AsyncIterator,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)

from can import Listener, Message
from pint import Quantity

from mytoolit.can.identifier import Identifier

# -- Classes ------------------------------------------------------------------


class AsyncStreamBuffer(Listener):
    """Buffer for streaming data"""

    def __init__(self, first: bool, second: bool, third: bool) -> None:
        """Initialize object using the given arguments

        Parameters
        ----------

        first:
            Specifies if the data of the first measurement channel will be
            collected or not

        second:
            Specifies if the data of the second measurement channel will be
            collected or not

        third:
            Specifies if the data of the third measurement channel will be
            collected or not

        """

        # Expected identifier of received streaming messages
        self.identifier = Identifier(
            block="Streaming",
            block_command="Data",
            sender="STH 1",
            receiver="SPU 1",
            request=False,
        )
        self.first = first
        self.second = second
        self.third = third
        self.queue: Queue[StreamingData] = Queue()

    def __aiter__(self) -> AsyncIterator[StreamingData]:
        """Retrieve iterator for collected data

        Returns
        -------

        An iterator over the received streaming data

        """

        return self

    def __anext__(self) -> Awaitable[StreamingData]:
        """Retrieve next stream data object in collected data

        Returns
        -------

        Retrieved streaming data

        """

        return self.queue.get()

    def on_message_received(self, message: Message) -> None:
        """Handle received messages

        Parameters
        ----------

        message:
            The received CAN message

        """

        if message.arbitration_id != self.identifier.value:
            return

        data = message.data
        timestamp = message.timestamp
        raw_values = [
            TimestampedValue(
                value=int.from_bytes(word, byteorder="little"),
                timestamp=timestamp,
                counter=data[1],
            )
            for word in (data[2:4], data[4:6], data[6:8])
        ]

        streaming_data = StreamingData()
        first = self.first
        second = self.second
        third = self.third

        if first and second and third:
            streaming_data.first.append(raw_values[0])
            streaming_data.second.append(raw_values[1])
            streaming_data.third.append(raw_values[2])
        elif first and second:
            streaming_data.first.append(raw_values[0])
            streaming_data.second.append(raw_values[1])
        elif first and third:
            streaming_data.first.append(raw_values[0])
            streaming_data.third.append(raw_values[1])
        elif second and third:
            streaming_data.second.append(raw_values[0])
            streaming_data.third.append(raw_values[1])
        elif first:
            streaming_data.first.extend(raw_values)
        elif second:
            streaming_data.second.extend(raw_values)
        else:
            streaming_data.third.extend(raw_values)

        self.queue.put_nowait(streaming_data)


class StreamingFormat:
    """Support for specifying the data streaming format

    See also: https://mytoolit.github.io/Documentation/#block-streaming
    """

    # Possible number of data sets
    data_set = [0, 1, 3, 6, 10, 15, 20, 30]

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
            else "{} Data Set{}".format(
                data_sets, "" if data_sets == 1 else "s"
            )
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

    def __repr__(self) -> str:
        """Retrieve the textual representation of the voltage streaming format

        Returns
        -------

        A string that describes the voltage streaming format

        Examples
        --------

        >>> StreamingFormatVoltage(streaming=True, width=2, second=True,
        ...                        sets=10)
        Streaming, 2 Bytes, 10 Data Sets, Read Voltage 2

        >>> StreamingFormatVoltage(streaming=False, width=3, first=False,
        ...                        second=True, third=True, sets=3)
        Single Request, 3 Bytes, 3 Data Sets, Read Voltage 2, Read Voltage 3

        """

        return super().__repr__()


class TimestampedValue:
    """Store a single (streaming) value and its timestamp"""

    def __init__(
        self,
        timestamp: float,
        value: Union[float, Quantity],
        counter: int,
    ) -> None:
        """Initialize the timestamped value using the given arguments

        Parameters
        ----------

        timestamp:
            The time when the data value was acquired in seconds since the
            epoch

        value:
            The data value either as
            - raw value or
            - value including a given unit and optional quantity

        counter:
            The message counter of the data

        """

        self.timestamp = timestamp
        self.value = value
        self.counter = counter

    def __repr__(self) -> str:
        """Retrieve the textual representation of the value

        Returns
        -------

        A string that describes the timestamped value

        Examples
        --------

        >>> from mytoolit.measurement import celsius, g0

        >>> TimestampedValue(timestamp=123, value=444, counter=1)
        444@123 (1)
        >>> TimestampedValue(timestamp=20, value=10, counter=10)
        10@20 (10)

        >>> TimestampedValue(timestamp=5, value=g0(10), counter=5)
        10 g_0@5 (5)
        >>> TimestampedValue(timestamp=5, value=celsius(10), counter=20)
        10 °C@5 (20)

        """

        value = (
            f"{self.value:~}"
            if isinstance(self.value, Quantity)
            else str(self.value)
        )

        return f"{value}@{self.timestamp} ({self.counter})"

    def default(self) -> Dict[str, Union[float, int, str]]:
        """Serialize the timestamped value

        Returns
        -------

        An object that can be serialized (into JSON)

        Examples
        --------

        >>> from json import dumps
        >>> from mytoolit.measurement import celsius, g0


        >>> TimestampedValue(timestamp=123, value=11, counter=1).default()
        {'timestamp': 123, 'value': 11, 'counter': 1}

        >>> TimestampedValue(timestamp=123, value=g0(2), counter=1
        ...                 ).default() # doctest:+NORMALIZE_WHITESPACE
        {'timestamp': 123, 'value': 2, 'unit': 'standard_gravity',
         'counter': 1}

        >>> timestamped = TimestampedValue(timestamp=5, value=celsius(10),
        ...                                counter=20)
        >>> dumps(timestamped.default()) # doctest:+NORMALIZE_WHITESPACE
        '{"timestamp": 5, "value": 10, "unit": "degree_Celsius",
          "counter": 20}'

        """

        serialized: Dict[str, Union[float, str]] = {
            "timestamp": self.timestamp
        }
        value = self.value
        if isinstance(value, Quantity):
            serialized["value"] = value.magnitude
            serialized["unit"] = f"{value.units}"
        else:
            serialized["value"] = value
        serialized["counter"] = self.counter

        return serialized


class NotHomogeneousException(Exception):
    """Indicates that a channel of streaming data contains heterogenous data"""


class StreamingData:
    """Auxiliary class to store streaming data"""

    def __init__(
        self,
        first: Optional[List[TimestampedValue]] = None,
        second: Optional[List[TimestampedValue]] = None,
        third: Optional[List[TimestampedValue]] = None,
    ) -> None:
        """Initialize the streaming data using the given arguments

        Parameters
        ----------

        first:
            The data points for the first measurement channel

        second:
            The data points for the second measurement channel

        third:
            The data points for the third measurement channel

        """

        self.first = [] if first is None else first
        self.second = [] if second is None else second
        self.third = [] if third is None else third

    def __iter__(self):
        """Retrieve an iterator for the different measurement channels

        Returns
        -------

        An iterator fir the measurement channels of the streaming data

        Examples
        --------

        >>> value1 = TimestampedValue(timestamp=1, value=1, counter=1)
        >>> value2 = TimestampedValue(timestamp=2, value=2, counter=2)
        >>> value3 = TimestampedValue(timestamp=3, value=3, counter=3)
        >>> data = StreamingData([value1], [], [value2, value3])
        >>> collected = []
        >>> for channel in data:
        ...     collected.extend(channel)
        >>> collected
        [1@1 (1), 2@2 (2), 3@3 (3)]

        """

        return iter([self.first, self.second, self.third])

    def __len__(self) -> int:
        """Retrieve the (combined) length of the streaming data

        Returns
        -------

        The amount of stored streaming values

        """

        return len(self.first) + len(self.second) + len(self.third)

    def __repr__(self) -> str:
        """Retrieve the textual representation of streaming data

        Returns
        -------

        A string that describes the ADC streaming data

        Examples
        --------

        >>> value1 = TimestampedValue(timestamp=1, value=1, counter=1)
        >>> value2 = TimestampedValue(timestamp=2, value=2, counter=2)
        >>> value3 = TimestampedValue(timestamp=3, value=3, counter=3)
        >>> StreamingData([], [], [value1, value2, value3])
        1: []
        2: []
        3: [1@1 (1), 2@2 (2), 3@3 (3)]

        >>> value1 = TimestampedValue(timestamp=1, value=1, counter=10)
        >>> value2 = TimestampedValue(timestamp=2, value=2, counter=11)
        >>> value3 = TimestampedValue(timestamp=3, value=3, counter=12)
        >>> StreamingData([], [], [value1, value2, value3])
        1: []
        2: []
        3: [1@1 (10), 2@2 (11), 3@3 (12)]

        """

        representation = []
        for channel, data in enumerate(
            (self.first, self.second, self.third), start=1
        ):
            representation.append(f"{channel}: {data}")

        return "\n".join(representation)

    def is_homogeneous(self) -> bool:
        """Check if the streaming data for every channel is homogeneous

        The data for a channel is considered homogeneous, if all values have
        the same data type (either `float` or `Quantity`)

        Returns
        -------

        True if the data is homogeneous, false otherwise

        Examples
        --------

        >>> from mytoolit.measurement import celsius

        >>> value1 = TimestampedValue(timestamp=1, value=1, counter=10)
        >>> value2 = TimestampedValue(timestamp=2, value=2, counter=11)
        >>> value3 = TimestampedValue(timestamp=3, value=celsius(3),
        ...                           counter=12)
        >>> value4 = TimestampedValue(timestamp=3, value=celsius(-2),
        ...                           counter=13)

        All values have same data type

        >>> StreamingData([value1], [],
        ...               [value2, value1]).is_homogeneous()
        True

        Values for one channel have different data type

        >>> StreamingData([value1, value3], [], []).is_homogeneous()
        False

        Values of each channel have same data type

        >>> StreamingData([value1, value2], [],
        ...               [value3, value4]).is_homogeneous()
        True

        """

        for channel in self:
            if len(channel) <= 0:
                continue

            value_type_first = type(channel[0].value)
            for timestamped in channel[1:]:
                if type(timestamped.value) != value_type_first:
                    return False

        return True

    def default(
        self, compact: bool = False
    ) -> Union[
        Dict[str, List[Dict[str, Union[float, int, str]]]],
        Dict[str, Dict[str, Union[List[float], List[int], str]]],
    ]:
        """Serialize the streaming data

        Converting streaming data in “compact” form only works for homogenous
        data. If the data of one channel is heterogenous and compact is set to
        true, then this method will throw an `NotHomogeneousException`
        exception.

        Arguments
        ---------

        compact:
            Use a “compact” representation of the streaming data (assumes
            homogenous data)

        Returns
        -------

        An object that can be serialized (into JSON)

        Examples
        --------

        >>> value1 = TimestampedValue(timestamp=1, value=1, counter=10)
        >>> value2 = TimestampedValue(timestamp=2, value=2, counter=11)
        >>> value3 = TimestampedValue(timestamp=3, value=3, counter=12)
        >>> streaming_data = StreamingData([], [], [value1, value2, value3])
        >>> streaming_data.default() # doctest:+NORMALIZE_WHITESPACE
        {'third': [{'timestamp': 1, 'value': 1, 'counter': 10},
                   {'timestamp': 2, 'value': 2, 'counter': 11},
                   {'timestamp': 3, 'value': 3, 'counter': 12}]}
        >>> streaming_data.default(
        ...     compact=True) # doctest:+NORMALIZE_WHITESPACE
        {'third': {'timestamps': [1, 2, 3],
                   'values': [1, 2, 3],
                   'counters': [10, 11, 12]}}

        >>> from mytoolit.measurement import celsius

        >>> value1 = TimestampedValue(timestamp=45, value=celsius(10),
        ...                           counter=10)
        >>> value2 = TimestampedValue(timestamp=67, value=celsius(20),
        ...                           counter=11)
        >>> value3 = TimestampedValue(timestamp=89, value=celsius(30),
        ...                           counter=12)
        >>> streaming_data = StreamingData([value1], [value2, value3], [])
        >>> streaming_data.default(
        ...     compact=True) # doctest:+NORMALIZE_WHITESPACE
        {'first': {'timestamps': [45],
                   'values': [10],
                   'unit': 'degree_Celsius',
                   'counters': [10]},
         'second': {'timestamps': [67, 89],
                    'values': [20, 30],
                    'unit': 'degree_Celsius',
                    'counters': [11, 12]}}

        """

        if compact:
            if not self.is_homogeneous():
                raise NotHomogeneousException(
                    "Unable to serialize data in compact form"
                )

            serializable_compact: Dict[
                str, Dict[str, Union[List[float], List[int], str]]
            ] = {}
            for channel, key in zip(
                (self.first, self.second, self.third),
                ("first", "second", "third"),
            ):
                if len(channel) <= 0:
                    continue

                serializable_compact[key] = {}
                serialized_channel = serializable_compact[key]
                first = channel[0]
                serialized_channel["timestamps"] = [
                    timestamped.timestamp for timestamped in channel
                ]

                values: List[float] = []
                if isinstance(first.value, Quantity):
                    for timestamped in channel:
                        assert isinstance(timestamped.value, Quantity)
                        values.append(timestamped.value.magnitude)
                    serialized_channel["values"] = values
                    serialized_channel["unit"] = f"{first.value.units}"
                else:
                    for timestamped in channel:
                        assert isinstance(timestamped.value, Real)
                        values.append(timestamped.value)
                    serialized_channel["values"] = values

                serialized_channel["counters"] = [
                    timestamped.counter for timestamped in channel
                ]
            return serializable_compact

        # Non “compact” form
        serializable = {}
        for channel, key in zip(
            (self.first, self.second, self.third), ("first", "second", "third")
        ):
            if len(channel) > 0:
                serializable[key] = [
                    timestamped.default() for timestamped in channel
                ]
        return serializable

    def extend(self, data: StreamingData) -> None:
        """Add additional streaming

        Parameters
        ----------

        data:
            The streaming data that should be added to this streaming data
            object

        Examples
        --------

        >>> value11 = TimestampedValue(timestamp=11, value=11, counter=1)
        >>> value12 = TimestampedValue(timestamp=12, value=12, counter=2)
        >>> value13 = TimestampedValue(timestamp=13, value=13, counter=3)
        >>> value14 = TimestampedValue(timestamp=14, value=14, counter=4)
        >>> value21 = TimestampedValue(timestamp=21, value=21, counter=5)
        >>> value22 = TimestampedValue(timestamp=22, value=22, counter=6)
        >>> value31 = TimestampedValue(timestamp=31, value=31, counter=7)
        >>> value32 = TimestampedValue(timestamp=32, value=32, counter=8)
        >>> value33 = TimestampedValue(timestamp=33, value=33, counter=9)
        >>> value34 = TimestampedValue(timestamp=34, value=34, counter=10)

        >>> data = StreamingData([value11, value12], [], [value31, value32])
        >>> other = StreamingData([value13, value14], [value21, value22],
        ...                       [value33, value34])
        >>> data.extend(other)
        >>> data
        1: [11@11 (1), 12@12 (2), 13@13 (3), 14@14 (4)]
        2: [21@21 (5), 22@22 (6)]
        3: [31@31 (7), 32@32 (8), 33@33 (9), 34@34 (10)]
        >>> other
        1: [13@13 (3), 14@14 (4)]
        2: [21@21 (5), 22@22 (6)]
        3: [33@33 (9), 34@34 (10)]

        """

        self.first.extend(data.first)
        self.second.extend(data.second)
        self.third.extend(data.third)

    def empty(self) -> bool:
        """Check if the object contains any streaming data

        Returns
        -------

        `True` if the current streaming data object stores any data, `False`
        otherwise

        Examples
        --------

        >>> StreamingData().empty()
        True
        >>> StreamingData([], [], []).empty()
        True
        >>> StreamingData([], [],
        ...     [TimestampedValue(timestamp=1, value=1, counter=1)]).empty()
        False

        """

        return not (self.first or self.second or self.third)

    def apply(
        self,
        function: Callable[[Union[float, Quantity]], Union[float, Quantity]],
        first: bool = True,
        second: bool = True,
        third: bool = True,
    ) -> None:
        """Apply a certain function to the streaming data

        Parameters
        ----------

        function:
            The function that should be applied to the streaming data

        first:
            Specifies if the function should be applied to the first
            measurement channel or not

        second:
            Specifies if the function should be applied to the second
            measurement channel or not

        third:
            Specifies if the function should be applied to the third
            measurement channel or not

        Examples
        --------

        >>> value11 = TimestampedValue(timestamp=11, value=11, counter=5)
        >>> value12 = TimestampedValue(timestamp=12, value=12, counter=6)
        >>> value13 = TimestampedValue(timestamp=13, value=13, counter=7)
        >>> value14 = TimestampedValue(timestamp=14, value=14, counter=8)

        >>> data = StreamingData([value11, value12], [value13], [value14])
        >>> data
        1: [11@11 (5), 12@12 (6)]
        2: [13@13 (7)]
        3: [14@14 (8)]
        >>> data.apply(lambda value: value + 10)
        >>> data
        1: [21@11 (5), 22@12 (6)]
        2: [23@13 (7)]
        3: [24@14 (8)]

        >>> value11 = TimestampedValue(timestamp=11, value=11, counter=11)
        >>> value12 = TimestampedValue(timestamp=12, value=12, counter=12)
        >>> data = StreamingData([value11, value12])
        >>> data
        1: [11@11 (11), 12@12 (12)]
        2: []
        3: []
        >>> data.apply(lambda value: value*2)
        >>> data
        1: [22@11 (11), 24@12 (12)]
        2: []
        3: []

        """

        def map_list(function, channel):
            return [
                TimestampedValue(
                    timestamped.timestamp,
                    function(timestamped.value),
                    timestamped.counter,
                )
                for timestamped in channel
            ]

        if first:
            self.first = map_list(function, self.first)
        if second:
            self.second = map_list(function, self.second)
        if third:
            self.third = map_list(function, self.third)


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import testmod

    testmod()
