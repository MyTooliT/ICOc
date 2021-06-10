class StreamingFormat:
    """Support for specifying the streaming format of a node

    See also: https://mytoolit.github.io/Documentation/#block-streaming
    """

    def __init__(self,
                 *value,
                 first: bool = True,
                 second: bool = False,
                 third: bool = False):
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

        value_selection = int(first) << 2 & int(second) << 1 & int(third)
        set_part(3, 3, value_selection)

    def __repr__(self) -> str:
        """Retrieve the textual representation of the streaming format

        Returns
        -------

        A string that describes the streaming format

        Examples
        --------

        >>> StreamingFormat(0)
        Streaming Format: Stop Stream

        >>> StreamingFormat(0b001)
        Streaming Format: 1 Data Set

        >>> StreamingFormat(0b111)
        Streaming Format: 30 Data Sets

        """

        def to_number_data_sets(data_set_bits: int) -> int:
            return [0, 1, 3, 6, 10, 15, 20, 30][data_set_bits]

        data_set_bits = self.value & 0b111
        data_sets = to_number_data_sets(data_set_bits)
        data_set_explanation = ("Stop Stream"
                                if data_sets == 0 else "{} Data Set{}".format(
                                    data_sets, "" if data_sets == 1 else "s"))

        value_selection = (self.value >> 3) & 0b111
        first = value_selection >> 2
        second = value_selection >> 1 & 1
        third = value_selection & 1

        selected_values = [
            f"Read Value {number}"
            for number, selection in enumerate([first, second, third], start=1)
            if selection
        ]
        value_selection_explanation = ",".join(
            selected_values) if selected_values else ""

        parts = [
            f"Streaming Format: {data_set_explanation}",
        ]
        if value_selection_explanation:
            parts.append(value_selection_explanation)

        return ",".join(parts)


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
