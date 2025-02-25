"""Support for MytooliT protocol calibration commands"""

# -- Imports ------------------------------------------------------------------

from typing import List, Optional, Union

from bidict import bidict

from mytoolit.utility.types import check_list

# pylint: disable=too-few-public-methods

# -- Class --------------------------------------------------------------------


class CalibrationMeasurementFormat:
    """This class stores message data for the calibration measurement command

    See also:
    https://mytoolit.github.io/Documentation/#command-calibration-measurement

    """

    methods = ["Reserved", "Activate", "Deactivate", "Measure"]
    elements = bidict({
        "Data": 0,
        "Temperature": 1,
        "Voltage": 32,
        "VSS": 96,
        "VDD": 97,
        "Internal": 98,
        "OPV": 99,
    })

    def __init__(  # pylint: disable=too-many-arguments
        self,
        *data: Union[bytearray, List[int]],
        # pylint: disable=redefined-builtin
        set: Optional[bool] = None,
        # pylint: enable=redefined-builtin
        element: Optional[str] = None,
        method: Optional[str] = None,
        dimension: Optional[int] = None,
        reference_voltage: Optional[float] = None,
    ) -> None:
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

                - Data
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
            data_bytes = list(data[0])
            check_list(data_bytes, 4)
            self.data = data_bytes[0:4] + [0] * 4
        else:
            self.data = [0, 0, 1, 0] + [0] * 4

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
            self.data[3] = round(reference_voltage * 20) & 0xFF

    def __repr__(self) -> str:
        """
        Retrieve the textual representation of the calibration format

        Returns
        -------

        A string that describes the calibration measurement format

        Examples
        --------

        >>> CalibrationMeasurementFormat(set=False, element='Data')
        Get, Data, Dimension: 1, Reference Voltage: 0.0 V

        >>> CalibrationMeasurementFormat(set=True, method='Measure',
        ...     element='Temperature', dimension=2, reference_voltage=3.3)
        Set, Measure, Temperature, Dimension: 2, Reference Voltage: 3.3 V

        >>> CalibrationMeasurementFormat([10, 20, 30, 40])
        Get, Unknown Element, Dimension: 30, Reference Voltage: 2.0 V

        """

        cls = type(self)

        method_byte = self.data[0]

        set_values = method_byte >> 7
        element = cls.elements.inverse.get(self.data[1], "Unknown Element")
        dimension = self.data[2]
        reference_voltage = round(self.data[3] / 20, 1)

        parts = [
            "Set" if set_values else "Get",
            element,
            f"Dimension: {dimension}",
            f"Reference Voltage: {reference_voltage} V",
        ]
        if set_values:
            method = cls.methods[(method_byte >> 5) & 0b11]
            parts.insert(1, method)

        representation = ", ".join(parts)

        return representation


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import testmod

    testmod()
