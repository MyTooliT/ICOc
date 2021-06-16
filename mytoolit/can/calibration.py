class CalibrationMeasurementFormat:
    """This class stores message data for the calibration measurement command

    See also:
    https://mytoolit.github.io/Documentation/#command-calibration-measurement

    """

    methods = ['Reserved', 'Activate', 'Deactivate', 'Measure']

    def __init__(self, set: bool, method: str) -> None:
        """Initialize the calibration measurement format

        Parameters
        ----------

        set:
            Specifies if we want to set or retrieve (get) calibration
            measurement data

        method:
            Specifies the calibration method (Activate, Deactivate or Measure)

        """

        cls = type(self)

        if method not in cls.methods:
            raise ValueError(f"Unknown method “{method}”")

        method_byte = (int(set) << 7) | cls.methods.index(method) << 5

        self.data = [method_byte, 0, 0]

    def __repr__(self) -> str:
        """
        Retrieve the textual representation of the calibration format

        Returns
        -------

        A string that describes the calibration measurement format

        Examples
        --------

        >>> CalibrationMeasurementFormat(set=False, method='Activate')
        Get, Activate

        >>> CalibrationMeasurementFormat(set=True, method='Measure')
        Set, Measure

        """

        cls = type(self)

        method_byte = self.data[0]

        set = method_byte >> 7
        method = cls.methods[(method_byte >> 5) & 0b11]

        representation = ", ".join(["Set" if set else "Get", method])

        return representation


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
