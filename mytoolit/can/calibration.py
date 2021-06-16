# -- Imports ------------------------------------------------------------------

from bidict import bidict

# -- Class --------------------------------------------------------------------


class CalibrationMeasurementFormat:
    """This class stores message data for the calibration measurement command

    See also:
    https://mytoolit.github.io/Documentation/#command-calibration-measurement

    """

    methods = ['Reserved', 'Activate', 'Deactivate', 'Measure']
    elements = bidict({
        "Acceleration": 0,
        "Temperature": 1,
        "Voltage": 32,
        "VSS": 96,
        "VDD": 97,
        "Internal": 98,
        "OPV": 99,
    })

    def __init__(self,
                 set: bool,
                 element: str,
                 method: str = 'Reserved') -> None:
        """Initialize the calibration measurement format

        Parameters
        ----------

        set:
            Specifies if we want to set or retrieve (get) calibration
            measurement data. If you set this value to false (get), then
            the value of `method` will be ignored

        element:
            Specifies the element that should be measured

            Possible values:

                - Acceleration
                - Temperature
                - Voltage
                - VSS
                - VDD
                - Internal
                - OPV

        method:
            Specifies the calibration method (Activate, Deactivate or Measure)

        """

        cls = type(self)

        if method not in cls.methods:
            raise ValueError(f"Unknown method “{method}”")

        if element not in cls.elements:
            raise ValueError(f"Unknown element “{element}”")

        method_byte = (int(set) << 7) | cls.methods.index(method) << 5
        element_byte = cls.elements[element]
        self.data = [method_byte, element_byte, 0]

    def __repr__(self) -> str:
        """
        Retrieve the textual representation of the calibration format

        Returns
        -------

        A string that describes the calibration measurement format

        Examples
        --------

        >>> CalibrationMeasurementFormat(set=False, element='Acceleration')
        Get, Acceleration

        >>> CalibrationMeasurementFormat(set=True, method='Measure',
        ...     element='Temperature')
        Set, Measure, Temperature

        """

        cls = type(self)

        method_byte = self.data[0]

        set = method_byte >> 7
        element = cls.elements.inverse[self.data[1]]
        parts = ["Set" if set else "Get", element]
        if set:
            method = cls.methods[(method_byte >> 5) & 0b11]
            parts.insert(1, method)

        representation = ", ".join(parts)

        return representation


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
