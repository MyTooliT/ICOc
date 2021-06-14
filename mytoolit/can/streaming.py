# -- Imports ------------------------------------------------------------------

from typing import Optional

# -- Class --------------------------------------------------------------------


class StreamingFormat:
    """Support for specifying the streaming format of a node

    See also: https://mytoolit.github.io/Documentation/#block-streaming
    """

    def __init__(self,
                 *value,
                 first: Optional[bool] = None,
                 second: Optional[bool] = None,
                 third: Optional[bool] = None):
        """Initialize the streaming format using the given arguments

        value:
            The value of the streaming format byte

        first:
            Specifies if the first data value should be transmitted or not

        second:
            Specifies if the second data value should be transmitted or not

        third:
            Specifies if the third data value should be transmitted or not

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

        # =================
        # = Active Values =
        # =================

        for shift, part in enumerate([third, second, first]):
            if part is not None:
                set_part(3 + shift, 1, part)

    def __repr__(self) -> str:
        """Retrieve the textual representation of the streaming format

        Returns
        -------

        A string that describes the streaming format

        Examples
        --------

        >>> StreamingFormat(first=True)
        Streaming, 2 Bytes, Stop Stream, Read Value 1

        >>> StreamingFormat(0b001)
        Streaming, 2 Bytes, 1 Data Set

        >>> StreamingFormat(0b110111)
        Streaming, 2 Bytes, 30 Data Sets, Read Value 1, Read Value 2

        """

        def to_number_data_sets(data_set_bits: int) -> int:
            return [0, 1, 3, 6, 10, 15, 20, 30][data_set_bits]

        single_request = self.value >> 7
        three_bytes = (self.value >> 6) & 1

        data_set_bits = self.value & 0b111
        data_sets = to_number_data_sets(data_set_bits)
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
