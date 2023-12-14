"""Support for ADC CAN commands and configuration

See:
https://mytoolit.github.io/Documentation/#command:Get-Set-ADC-Configuration

for more information
"""

# -- Imports ------------------------------------------------------------------

from collections.abc import Iterator, Mapping
from math import log2
from typing import List, Optional, Union

from mytoolit.utility.types import check_list

# -- Class --------------------------------------------------------------------


class ADCConfiguration(Mapping):
    """Support for reading and writing the ADC configuration"""

    REFERENCE_VOLTAGES = [1.25, 1.65, 1.8, 2.1, 2.2, 2.5, 2.7, 3.3, 5, 6.6]

    # pylint: disable=too-many-branches

    def __init__(  # pylint: disable=too-many-arguments
        self,
        *data: Union[bytearray, List[int]],
        # pylint: disable=redefined-builtin
        set: Optional[bool] = None,
        # pylint: enable=redefined-builtin
        prescaler: Optional[int] = None,
        acquisition_time: Optional[int] = None,
        oversampling_rate: Optional[int] = None,
        reference_voltage: Optional[float] = None,
    ):
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

        oversampling_rate:
            The ADC oversampling rate (1, 2, 4, 8, … , 4096)

        reference_voltage:
            The ADC reference voltage in Volt
            (1.25, 1.65, 1.8, 2.1, 2.2, 2.5, 2.7, 3.3, 5, 6.6)

        """

        if data:
            data_bytes = list(data[0])
            check_list(data_bytes, 5)
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

        if prescaler is not None:
            if not 1 <= prescaler <= 127:
                raise ValueError(
                    f"Prescaler value of “{prescaler}” out of range"
                    ", please use a value between 1 and 127"
                )
            self.data[1] = prescaler
        elif self.data[1] == 0:
            # Make sure default prescaler value makes sense
            self.data[1] = 8

        # ====================
        # = Acquisition Time =
        # ====================

        if acquisition_time is not None:
            possible_acquisition_times = list(range(1, 4)) + [
                2**value for value in range(3, 9)
            ]
            if acquisition_time not in possible_acquisition_times:
                raise ValueError(
                    f"Acquisition time of “{acquisition_time}” out of range"
                    ", please use one of the following values: "
                    + ", ".join(map(str, possible_acquisition_times))
                )

            acquisition_time_byte = (
                acquisition_time - 1
                if acquisition_time <= 3
                else int(log2(acquisition_time)) + 1
            )

            self.data[2] = acquisition_time_byte

        # =====================
        # = Oversampling Rate =
        # =====================

        if oversampling_rate is not None:
            possible_oversampling_rates = [2**value for value in range(13)]
            if oversampling_rate not in possible_oversampling_rates:
                raise ValueError(
                    f"Oversampling rate of “{oversampling_rate}” out of"
                    "range, please use one of the following values: "
                    + ", ".join(map(str, possible_oversampling_rates))
                )

            self.data[3] = int(log2(oversampling_rate))

        # =====================
        # = Reference Voltage =
        # =====================

        cls = type(self)
        if reference_voltage is not None:
            if reference_voltage not in cls.REFERENCE_VOLTAGES:
                raise ValueError(
                    f"Reference voltage of “{oversampling_rate}” out of range"
                    ", please use one of the following values: "
                    + ", ".join(map(str, cls.REFERENCE_VOLTAGES))
                )

            self.data[4] = int(reference_voltage * 20)
        elif self.data[4] == 0:
            # Make sure default reference voltage value makes sense
            supply_voltage = 3.3
            self.data[4] = int(supply_voltage * 20)

        self.attributes = {
            "reference_voltage": self.reference_voltage,
            "prescaler": self.prescaler,
            "acquisition_time": self.acquisition_time,
            "oversampling_rate": self.oversampling_rate,
        }

    # pylint: enable=too-many-branches

    def __getitem__(self, item: str) -> float:
        """Return values of the mapping provided by this class

        Note: This method allow access to the object via the splat
              operators (*, **)

        Parameters
        ----------

        item:
            The attribute for which we want to retrieve the value

        Returns
        -------

        The value of the attribute

        Examples
        --------

        >>> dict(**ADCConfiguration()) # doctest:+NORMALIZE_WHITESPACE
        {'reference_voltage': 3.3,
         'prescaler': 8,
         'acquisition_time': 1,
         'oversampling_rate': 1}

        >>> dict(**ADCConfiguration(oversampling_rate=64)
        ...     ) # doctest:+NORMALIZE_WHITESPACE
        {'reference_voltage': 3.3,
         'prescaler': 8,
         'acquisition_time': 1,
         'oversampling_rate': 64}

        """

        return self.attributes[item]()

    def __iter__(self) -> Iterator:
        """Return an iterator over the mapping provided by this class

        Note: This method allow access to the object via the splat
              operators (*, **)

        Returns
        -------

        The names of the “important” properties of the ADC configuration:

        - reference voltage
        - prescaler
        - acquisition time
        - oversampling rate

        Examples
        --------

        >>> for attribute in ADCConfiguration():
        ...     print(attribute)
        reference_voltage
        prescaler
        acquisition_time
        oversampling_rate

        """

        return iter(self.attributes)

    def __len__(self) -> int:
        """Return the length of the mapping provided by this class

        Note: This method allow access to the object via the splat
              operators (*, **)

        Returns
        -------

        The amount of the “important” properties of the ADC configuration:

        - reference voltage
        - prescaler
        - acquisition time
        - oversampling rate

        Examples
        --------

        >>> len(ADCConfiguration())
        4

        >>> len(ADCConfiguration(reference_voltage=3.3))
        4

        """

        return len(self.attributes)

    def __repr__(self) -> str:
        """Retrieve the textual representation of the ADC configuration

        Returns
        -------

        A string that describes the ADC configuration

        Examples
        --------

        >>> ADCConfiguration(prescaler=1, reference_voltage=3.3
        ... ) # doctest:+NORMALIZE_WHITESPACE
        Get, Prescaler: 1, Acquisition Time: 1, Oversampling Rate: 1,
        Reference Voltage: 3.3 V

        >>> ADCConfiguration(
        ...     set=True,
        ...     prescaler=64,
        ...     acquisition_time=128,
        ...     oversampling_rate=1024,
        ...     reference_voltage=1.8) # doctest:+NORMALIZE_WHITESPACE
        Set, Prescaler: 64, Acquisition Time: 128, Oversampling Rate: 1024,
        Reference Voltage: 1.8 V

        >>> ADCConfiguration([0, 2, 4, 6, 25]) # doctest:+NORMALIZE_WHITESPACE
        Get, Prescaler: 2, Acquisition Time: 8, Oversampling Rate: 64,
        Reference Voltage: 1.25 V

        """

        set_values = bool(self.data[0] >> 7)
        prescaler = self.data[1]
        acquisition_time = (
            self.data[2] + 1 if self.data[2] <= 3 else 2 ** (self.data[2] - 1)
        )
        oversampling_rate = 2 ** self.data[3]
        reference_voltage = self.reference_voltage()

        parts = [
            "Set" if set_values else "Get",
            f"Prescaler: {prescaler}",
            f"Acquisition Time: {acquisition_time}",
            f"Oversampling Rate: {oversampling_rate}",
            f"Reference Voltage: {reference_voltage} V",
        ]

        return ", ".join(parts)

    def reference_voltage(self) -> float:
        """Get the reference voltage

        Returns
        -------

        The reference voltage in Volt

        Examples
        --------

        >>> ADCConfiguration(reference_voltage=3.3).reference_voltage()
        3.3

        >>> ADCConfiguration(reference_voltage=6.6).reference_voltage()
        6.6

        >>> ADCConfiguration(reference_voltage=1.8).reference_voltage()
        1.8

        """

        return self.data[4] / 20

    def prescaler(self) -> int:
        """Get the prescaler value

        Returns
        -------

        The prescaler value

        Examples
        --------

        >>> ADCConfiguration(prescaler=127).prescaler()
        127

        """

        return self.data[1]

    def acquisition_time(self) -> int:
        """Get the acquisition time

        Returns
        -------

        The acquisition time

        Examples
        --------

        >>> ADCConfiguration(acquisition_time=2).acquisition_time()
        2

        """

        acquisition_time_byte = self.data[2]

        return (
            acquisition_time_byte + 1
            if acquisition_time_byte <= 3
            else 2 ** (acquisition_time_byte - 1)
        )

    def oversampling_rate(self) -> int:
        """Get the oversampling rate

        Returns
        -------

        The oversampling rate

        Examples
        --------

        >>> ADCConfiguration(oversampling_rate=128).oversampling_rate()
        128

        """

        oversampling_rate_byte = self.data[3]

        return 2**oversampling_rate_byte

    def sample_rate(self) -> int:
        """Calculate the sampling rate for the current ADC configuration

        Returns
        -------

        The calculated sample rate

        Examples
        --------

        >>> ADCConfiguration(prescaler=2, acquisition_time=8,
        ...                  oversampling_rate=64).sample_rate()
        9524

        >>> ADCConfiguration(prescaler=8, acquisition_time=8,
        ...                  oversampling_rate=64).sample_rate()
        3175

        >>> ADCConfiguration(reference_voltage=5.0,
        ...                  prescaler=16,
        ...                  acquisition_time=8,
        ...                  oversampling_rate=128).sample_rate()
        840

        """

        clock_frequency = 38_400_000

        return round(
            clock_frequency
            / (
                (self.prescaler() + 1)
                * (self.acquisition_time() + 13)
                * self.oversampling_rate()
            )
        )


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import testmod

    testmod()
