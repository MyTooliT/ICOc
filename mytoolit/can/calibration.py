class CalibrationMeasurementFormat:
    """This class stores message data for the calibration measurement command

    See also:
    https://mytoolit.github.io/Documentation/#command-calibration-measurement

    """

    def __init__(self, set: bool) -> None:
        """Initialize the calibration measurement format

        Parameters
        ----------

        set:
            Specifies if we want to set or retrieve (get) calibration
            measurement data

        """

        method_byte = int(set) << 7

        self.data = [method_byte, 0, 0]

    def __repr__(self) -> str:
        """
        Retrieve the textual representation of the calibration format

        Returns
        -------

        A string that describes the calibration measurement format

        Examples
        --------

        >>> CalibrationMeasurementFormat(set=False)
        Get

        >>> CalibrationMeasurementFormat(set=True)
        Set

        """

        method_byte = self.data[0]
        set = method_byte >> 7

        return "Set" if set else "Get"


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
