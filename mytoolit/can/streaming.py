# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from typing import List, Optional, Tuple

# -- Class --------------------------------------------------------------------


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
        value_explanations: Tuple[str, str,
                                  str] = ("Value 1", "Value 2", "Value 3")
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

            streaming_ones = 0xff
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
        data_set_explanation = ("Stop Stream"
                                if data_sets == 0 else "{} Data Set{}".format(
                                    data_sets, "" if data_sets == 1 else "s"))

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
            for selected, value_explanation in zip((
                first, second, third), self.value_explanations) if selected
        ]

        value_explanation = (", ".join(selected_values)
                             if selected_values else "")
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

        super().__init__(*arguments,
                         **keyword_arguments,
                         value_explanations=("Voltage 1", "Voltage 2",
                                             "Voltage 3"))

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


class StreamingData:
    """Auxiliary class to store streaming data"""

    def __init__(self,
                 first: Optional[List[float]] = None,
                 second: Optional[List[float]] = None,
                 third: Optional[List[float]] = None) -> None:
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

    def __repr__(self) -> str:
        """Retrieve the textual representation of streaming data

        Returns
        -------

        A string that describes the ADC streaming data

        Examples
        --------

        >>> StreamingData([], [], [1, 2, 3])
        1: []
        2: []
        3: [1, 2, 3]

        """

        representation = []
        for channel, data in enumerate((self.first, self.second, self.third),
                                       start=1):
            representation.append(f"{channel}: {data}")

        return "\n".join(representation)

    def extend(self, data: StreamingData) -> None:
        """Add additional streaming

        Parameters
        ----------

        data:
            The streaming data that should be added to this streaming data
            object

        Examples
        --------

        >>> data = StreamingData([11, 12], [], [31, 32])
        >>> other = StreamingData([13, 14], [21, 22], [33, 34])
        >>> data.extend(other)
        >>> data
        1: [11, 12, 13, 14]
        2: [21, 22]
        3: [31, 32, 33, 34]
        >>> other
        1: [13, 14]
        2: [21, 22]
        3: [33, 34]

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
        >>> StreamingData([], [], [3]).empty()
        False

        """

        return not (self.first or self.second or self.third)


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
