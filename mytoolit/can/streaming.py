class StreamingFormat:
    """Support for specifying the streaming format of a node

    See also: https://mytoolit.github.io/Documentation/#block-streaming
    """

    def __init__(self, *value):
        """Initialize the streaming format using the given arguments


        value:
            The value of the streaming format byte

        """

        self.value = value[0] if value else 0

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

        return f"Streaming Format: {data_set_explanation}"


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
