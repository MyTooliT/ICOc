# -- Imports ------------------------------------------------------------------

from typing import List, Optional, Union

# -- Class --------------------------------------------------------------------


class ADCConfiguration:
    """Support for reading and writing the ADC configuration"""

    def __init__(self,
                 *data: Union[bytearray, List[int]],
                 set: Optional[bool] = None,
                 prescaler: int = 1):
        """Initialize the ADC configuration using the given arguments

        Positional Parameters
        ---------------------

        data:
            A list containing the (first five) bytes of the ADC configuration

        Keyword Parameters
        ------------------

        set:
            Specifies if we want to set or retrieve (get) the ADC configuration

        prescaler:
            The ADC prescaler value (1 – 127)

        """

        if data:
            data_bytes = list(data[0])
            if not isinstance(data_bytes, list):
                raise ValueError("Unsupported object type for argument data: "
                                 f"“{type(data_bytes)}”")
            required_length = 5
            if len(data_bytes) < required_length:
                raise ValueError(f"Data length of {len(data_bytes)} is too "
                                 "small, at least length of "
                                 f"“{required_length}” required")
            self.data = data_bytes[0:5] + [0] * 3
        else:
            self.data = [0, 1] + [0] * 6

        # ==================
        # = Get/Set Config =
        # ==================

        if set is not None:
            get_set_byte = self.data[0]
            # Set get/set to 0
            get_set_byte &= 0b01111111
            # Set value
            get_set_byte |= int(set) << 7
            self.data[0] = get_set_byte

        # =============
        # = Prescaler =
        # =============

        if not (1 <= prescaler <= 127):
            raise ValueError(f"Prescaler value of “{prescaler}” out of range"
                             ", please use a value between 1 and 127")
        self.data[1] = prescaler

    def __repr__(self) -> str:
        """Retrieve the textual representation of the ADC configuration

        Returns
        -------

        A string that describes the ADC configuration

        Examples
        --------

        >>> ADCConfiguration()
        Get, Prescaler: 1

        >>> ADCConfiguration(set=True, prescaler=64)
        Set, Prescaler: 64

        """

        set = bool(self.data[0] >> 7)
        prescaler = self.data[1]

        parts = ["Set" if set else "Get", f"Prescaler: {prescaler}"]

        return ", ".join(parts)


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
