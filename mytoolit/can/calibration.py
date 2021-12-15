# -- Imports ------------------------------------------------------------------

from typing import List, Optional

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
                 *data: List[int],
                 set: Optional[bool] = None,
                 element: Optional[str] = None,
                 method: Optional[str] = None,
                 dimension: Optional[int] = None,
                 reference_voltage: Optional[int] = None) -> None:
        """Initialize the calibration measurement format

        This class allows you to specify the message bytes directly as first
        argument. Alternatively you can use the other arguments of the
        initializer to  either

        - overwrite specific parts of the given message bytes or
        - create a calibration format without specifying the message bytes.

        Parameters
        ----------

        data:
            A list containing the (first four) bytes of the calibration
            measurement format

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

        dimension:
            Specifies the measurement dimension respectively the axis
            (1, 2 or 3)

        reference_voltage:
            The reference voltage in Volt

        """

        cls = type(self)

        if data:
            data_bytes = data[0]
            if not isinstance(data_bytes, list):
                raise ValueError("Unsupported object type for argument data: "
                                 f"“{type(data_bytes)}”")
            required_length = 4
            if len(data_bytes) != required_length:
                raise ValueError(f"Data length has to be “{required_length}” "
                                 f"not “{len(data_bytes)}”")

            self.data = data_bytes
        else:
            self.data = [0, 0, 1, 0]

        if set is not None:
            method_byte = self.data[0]
            # Set get/set to 0
            method_byte &= 0b01111111
            # Set value
            method_byte |= int(set) << 7
            self.data[0] = method_byte

        if method is not None:
            if method not in cls.methods:
                raise ValueError(f"Unknown method “{method}”")
            method_byte = self.data[0]
            # Set method bits to 0
            method_byte &= 0b10011111
            # Set value
            method_byte |= cls.methods.index(method) << 5
            self.data[0] = method_byte

        if element is not None:
            if element not in cls.elements:
                raise ValueError(f"Unknown element “{element}”")
            self.data[1] = cls.elements[element]

        if dimension is not None:
            if dimension not in {1, 2, 3}:
                raise ValueError(f"Unknown dimension “{dimension}”")
            self.data[2] = dimension

        if reference_voltage is not None:
            self.data[3] = round(reference_voltage * 20) & 0xff

    def __repr__(self) -> str:
        """
        Retrieve the textual representation of the calibration format

        Returns
        -------

        A string that describes the calibration measurement format

        Examples
        --------

        >>> CalibrationMeasurementFormat(set=False, element='Acceleration')
        Get, Acceleration, Dimension: 1, Reference Voltage: 0.0 V

        >>> CalibrationMeasurementFormat(set=True, method='Measure',
        ...     element='Temperature', dimension=2, reference_voltage=3.3)
        Set, Measure, Temperature, Dimension: 2, Reference Voltage: 3.3 V

        """

        cls = type(self)

        method_byte = self.data[0]

        set = method_byte >> 7
        element = cls.elements.inverse[self.data[1]]
        dimension = self.data[2]
        reference_voltage = round(self.data[3] / 20, 1)

        parts = [
            "Set" if set else "Get", element, f"Dimension: {dimension}",
            f"Reference Voltage: {reference_voltage} V"
        ]
        if set:
            method = cls.methods[(method_byte >> 5) & 0b11]
            parts.insert(1, method)

        representation = ", ".join(parts)

        return representation


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
