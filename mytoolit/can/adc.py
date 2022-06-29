# -- Imports ------------------------------------------------------------------

from typing import List, Optional, Union

# -- Class --------------------------------------------------------------------


class ADCConfiguration:
    """Support for reading and writing the ADC configuration"""

    def __init__(self,
                 *data: Union[bytearray, List[int]],
                 set: Optional[bool] = None):
        """Initialize the ADC configuration using the given arguments

        Positional Parameters
        ---------------------

        data:
            A list containing the (first five) bytes of the ADC configuration

        Keyword Parameters
        ------------------

        set:
            Specifies if we want to set or retrieve (get) the ADC configuration

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

        if set is not None:
            get_set_byte = self.data[0]
            # Set get/set to 0
            get_set_byte &= 0b01111111
            # Set value
            get_set_byte |= int(set) << 7
            self.data[0] = get_set_byte

    def __repr__(self) -> str:
        """Retrieve the textual representation of the ADC configuration

        Returns
        -------

        A string that describes the ADC configuration

        Examples
        --------

        >>> ADCConfiguration()
        Get

        >>> ADCConfiguration(set=True)
        Set

        """

        set = bool(self.data[0] >> 7)
        return "Set" if set else "Get"


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
