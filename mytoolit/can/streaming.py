# -- Imports ------------------------------------------------------------------

from typing import Optional

# -- Class --------------------------------------------------------------------


class StreamingFormat:
    """Support for specifying the data streaming format

    See also: https://mytoolit.github.io/Documentation/#block-streaming
    """

    # Possible number of data sets
    data_set = [0, 1, 3, 6, 10, 15, 20, 30]

    def __init__(self,
                 *value,
                 single: Optional[bool] = None,
                 width: Optional[int] = 2,
                 first: Optional[bool] = None,
                 second: Optional[bool] = None,
                 third: Optional[bool] = None,
                 sets: Optional[int] = None) -> None:
        """Initialize the streaming format using the given arguments

        value:
            The value of the streaming format byte

        single:
            Specifies if the request was for a single value or not

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

        self.value = value[0] if value else 0

        # ==================
        # = Single Request =
        # ==================

        if single:
            set_part(7, 1, int(single))

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
        Streaming, 3 Bytes, 15 Data Sets, Read Value 1

        >>> StreamingFormat(0b001, single=True)
        Single Request, 2 Bytes, 1 Data Set

        >>> StreamingFormat(0b110111)
        Streaming, 2 Bytes, 30 Data Sets, Read Value 1, Read Value 2

        """

        single_request = self.value >> 7
        three_bytes = (self.value >> 6) & 1

        data_set_bits = self.value & 0b111
        cls = type(self)
        data_sets = cls.data_set[data_set_bits]
        data_set_explanation = ("Stop Stream"
                                if data_sets == 0 else "{} Data Set{}".format(
                                    data_sets, "" if data_sets == 1 else "s"))

        parts = [
            "Single Request" if single_request else "Streaming",
            "{} Bytes".format(3 if three_bytes else 2),
            f"{data_set_explanation}",
        ]

        value_selection = (self.value >> 3) & 0b111
        first = value_selection >> 2
        second = value_selection >> 1 & 1
        third = value_selection & 1
        selected_values = [
            f"Read Value {number}"
            for number, selection in enumerate([first, second, third], start=1)
            if selection
        ]
        value_selection_explanation = ", ".join(
            selected_values) if selected_values else ""
        if value_selection_explanation:
            parts.append(value_selection_explanation)

        return ", ".join(parts)


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
