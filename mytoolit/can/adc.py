# -- Imports ------------------------------------------------------------------

from math import log2
from typing import List, Optional, Union

# -- Class --------------------------------------------------------------------


class ADCConfiguration:
    """Support for reading and writing the ADC configuration"""

    def __init__(self,
                 *data: Union[bytearray, List[int]],
                 set: Optional[bool] = None,
                 prescaler: int = 2,
                 acquisition_time: int = 8):
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

        acquisition_time:
            The acquisition time in number of cycles
            (1, 2, 3, 4, 8, 16, 32, … , 256)

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
            self.data = [0] * 8

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

        # ====================
        # = Acquisition Time =
        # ====================

        possible_acquisition_times = (list(range(1, 4)) +
                                      [2**value for value in range(3, 9)])
        if acquisition_time not in possible_acquisition_times:
            raise ValueError(
                f"Acquisition time of “{acquisition_time}” out of"
                "range, please use one of the following values: " +
                ", ".join(map(str, possible_acquisition_times)))

        acquisition_time_byte = (acquisition_time - 1 if acquisition_time <= 3
                                 else int(log2(acquisition_time)) + 1)

        self.data[2] = acquisition_time_byte

    def __repr__(self) -> str:
        """Retrieve the textual representation of the ADC configuration

        Returns
        -------

        A string that describes the ADC configuration

        Examples
        --------

        >>> ADCConfiguration()
        Get, Prescaler: 2, Acquisition Time: 8

        >>> ADCConfiguration(set=True, prescaler=64, acquisition_time=128)
        Set, Prescaler: 64, Acquisition Time: 128

        """

        set = bool(self.data[0] >> 7)
        prescaler = self.data[1]
        acquisition_time = (self.data[2] +
                            1 if self.data[2] <= 3 else 2**(self.data[2] - 1))

        parts = [
            "Set" if set else "Get", f"Prescaler: {prescaler}",
            f"Acquisition Time: {acquisition_time}"
        ]

        return ", ".join(parts)


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
