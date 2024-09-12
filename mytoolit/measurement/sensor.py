"""Support code for sensors and sensor configuration"""

# -- Imports ------------------------------------------------------------------

from collections.abc import Iterator, Mapping
from enum import auto, Enum
from statistics import mean
from typing import Iterable, NamedTuple

from mytoolit.can.streaming import StreamingConfiguration

# -- Classes ------------------------------------------------------------------


class SensorConfiguration(Mapping):
    """Used to store the configuration of the three sensor channels"""

    def __init__(self, first: int = 0, second: int = 0, third: int = 0):
        """Initialize the sensor configuration using the given arguments

        Parameters
        ----------

        first:
            The sensor number for the first measurement channel

        second:
            The sensor number for the second measurement channel

        third:
            The sensor number for the third measurement channel


        Examples
        --------

        >>> SensorConfiguration(first=0, second=1, third=2)
        M1: None, M2: S1, M3: S2

        >>> SensorConfiguration(first=256, second=1, third=2)
        Traceback (most recent call last):
        ...
        ValueError: Incorrect value for first channel: “256”

        >>> SensorConfiguration(first=0, second=1, third=-1)
        Traceback (most recent call last):
        ...
        ValueError: Incorrect value for third channel: “-1”

        """

        self.attributes = {
            "first": first,
            "second": second,
            "third": third,
        }

        for name, channel in self.attributes.items():
            if channel < 0 or channel > 255:
                raise ValueError(
                    f"Incorrect value for {name} channel: “{channel}”"
                )

    def __getitem__(self, item: str) -> int:
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

        >>> dict(**SensorConfiguration()) # doctest:+NORMALIZE_WHITESPACE
        {'first': 0,
         'second': 0,
         'third': 0}

        >>> dict(**SensorConfiguration(first=1, second=2, third=3)
        ...     ) # doctest:+NORMALIZE_WHITESPACE
        {'first': 1,
         'second': 2,
         'third': 3}

        """

        return self.attributes[item]

    def __iter__(self) -> Iterator:
        """Return an iterator over the mapping provided by this class

        Note: This method allow access to the object via the splat
              operators (*, **)

        Returns
        -------

        The names of the “important” properties of the sensor configuration:

        - first
        - second
        - third

        Examples
        --------

        >>> for attribute in SensorConfiguration():
        ...     print(attribute)
        first
        second
        third

        """

        return iter(self.attributes)

    def __len__(self) -> int:
        """Return the length of the mapping provided by this class

        Note: This method allow access to the object via the splat
              operators (*, **)

        Returns
        -------

        The amount of the “important” properties of the sensor configuration:

        - first
        - second
        - third

        Examples
        --------

        >>> len(SensorConfiguration())
        3

        >>> len(SensorConfiguration(second=10))
        3

        """

        return len(self.attributes)

    def __str__(self) -> str:
        """The string representation of the sensor configuration

        Returns
        -------

        A textual representation of the sensor configuration

        Examples
        --------

        >>> str(SensorConfiguration(first=1, second=3, third=2))
        'M1: S1, M2: S3, M3: S2'

        >>> str(SensorConfiguration())
        ''

        >>> str(SensorConfiguration(second=1))
        'M2: S1'

        """

        return ", ".join((
            f"M{sensor}: S{value}"
            for sensor, value in enumerate(self.attributes.values(), start=1)
            if value != 0
        ))

    def __repr__(self) -> str:
        """The textual representation of the sensor configuration

        Returns
        -------

        A textual representation of the sensor configuration

        Examples
        --------

        >>> repr(SensorConfiguration(first=1, second=3, third=2))
        'M1: S1, M2: S3, M3: S2'

        >>> repr(SensorConfiguration())
        'M1: None, M2: None, M3: None'

        """

        return ", ".join((
            f"M{sensor}: {f'S{value}' if value != 0 else 'None'}"
            for sensor, value in enumerate(self.attributes.values(), start=1)
        ))

    @property
    def first(self) -> int:
        """Get the sensor for the first channel

        Returns
        -------

        The sensor number of the first channel


        Examples
        --------

        >>> SensorConfiguration(first=1, second=3, third=2).first
        1

        """

        first = self.attributes["first"]

        return 0 if first is None else first

    @property
    def second(self) -> int:
        """Get the sensor for the second channel

        Returns
        -------

        The sensor number of the second channel


        Examples
        --------

        >>> SensorConfiguration(first=1, second=3, third=2).second
        3

        """

        second = self.attributes["second"]

        return 0 if second is None else second

    @property
    def third(self) -> int:
        """Get the sensor for the third channel

        Returns
        -------

        The sensor number of the third channel


        Examples
        --------

        >>> SensorConfiguration(first=1, second=3, third=2).third
        2

        """

        third = self.attributes["third"]

        return 0 if third is None else third

    def disable_channel(
        self, first: bool = False, second: bool = False, third: bool = False
    ) -> None:
        """Disable certain (measurement) channels

        Parameters
        ----------

        first:
            Specifies if the first measurement channel should be disabled or
            not

        second:
            Specifies if the second measurement channel should be disabled or
            not

        third:
            Specifies if the third measurement channel should be disabled or
            not

        """

        if first:
            self.attributes["first"] = 0
        if second:
            self.attributes["second"] = 0
        if third:
            self.attributes["third"] = 0

    def requires_channel_configuration_support(self) -> bool:
        """Check if the sensor configuration requires channel config support

        Returns
        -------

        - True, if the configuration requires hardware that has support for
          changing the channel configuration
        - False, otherwise

        Examples
        --------

        >>> SensorConfiguration(first=1, second=3, third=2
        ...     ).requires_channel_configuration_support()
        True

        >>> SensorConfiguration(first=1, second=0, third=1
        ...     ).requires_channel_configuration_support()
        False

        >>> SensorConfiguration().requires_channel_configuration_support()
        False

        """

        for value in self.attributes.values():
            if value > 1:
                return True
        return False

    def empty(self) -> bool:
        """Check if the sensor configuration is empty

        In an empty sensor configuration all of the channels are disabled.

        Returns
        -------

        True, if all channels are disabled, False otherwise

        Examples
        --------

        >>> SensorConfiguration(first=3).empty()
        False
        >>> SensorConfiguration().empty()
        True
        >>> SensorConfiguration(third=0).empty()
        True

        """

        return self.first == 0 and self.second == 0 and self.third == 0

    def check(self):
        """Check that at least one measurement channel is enabled

        Raises
        ------

        ValueError, if none of the measurement channels is enabled

        Examples
        --------

        >>> SensorConfiguration(second=1).check()
        >>> SensorConfiguration().check()
        Traceback (most recent call last):
            ...
        ValueError: At least one measurement channel has to be enabled

        """

        if self.empty():
            raise ValueError(
                "At least one measurement channel has to be enabled"
            )

    def streaming_configuration(self) -> StreamingConfiguration:
        """Get a streaming configuration that represents this config

        Returns
        -------

        A stream configuration where

        - every channel that is enabled in the sensor configuration is
          enabled, and
        - every channel that is disables in the sensor configuration is
          disabled.

        Examples
        --------

        >>> SensorConfiguration(second=1).streaming_configuration()
        Channel 1 disabled, Channel 2 enabled, Channel 3 disabled

        >>> SensorConfiguration(first=10, third=2).streaming_configuration()
        Channel 1 enabled, Channel 2 disabled, Channel 3 enabled

        """

        return StreamingConfiguration(**{
            channel: bool(value) for channel, value in self.attributes.items()
        })


class SensorType(Enum):
    """Possible sensor types"""

    BROKEN = auto()
    ACCELERATION = auto()
    TEMPERATURE = auto()
    PIEZO = auto()


class Sensor(NamedTuple):
    """Store information about a sensor"""

    type: SensorType
    mean: float

    def __repr__(self) -> str:
        """Return a string representation of the sensor

        Returns
        -------

        A string that describes the sensor

        Examples
        --------

        >>> Sensor(SensorType.BROKEN, mean=123)
        Broken Sensor (Mean: 123)

        >>> Sensor(SensorType.TEMPERATURE, mean=123)
        Temperature Sensor

        """

        representation = f"{self.type.name.capitalize()} Sensor"
        if self.type == SensorType.BROKEN:
            representation += f" (Mean: {self.mean})"

        return representation

    def works(self) -> bool:
        """Check if the sensor is working or not

        Returns
        -------

        True if the sensor works, false otherwise

        """

        return not self.type == SensorType.BROKEN


# -- Functions ----------------------------------------------------------------


def guess_sensor(values: Iterable[int]) -> Sensor:
    """Guess the sensor type from raw 16 bit ADC values

    Parameters
    ----------

    values:
        Multiple raw 16 bit ADC measurement values

    Returns
    -------

    An object representing the guessed sensor type

    Examples
    --------

    >>> guess_sensor([38024, 38000, 37950])
    Piezo Sensor

    >>> guess_sensor([32500, 32571, 32499])
    Acceleration Sensor

    >>> guess_sensor([10650, 10500, 10780])
    Temperature Sensor

    >>> guess_sensor([123, 10, 50])
    Broken Sensor (Mean: 61)

    """

    mean_raw = mean(values)
    half = 2**15

    tolerance_acceleration = 1000
    min_acceleration = half - tolerance_acceleration
    max_acceleration = half + tolerance_acceleration

    if 10000 <= mean_raw <= 11000:
        return Sensor(SensorType.TEMPERATURE, mean_raw)
    if min_acceleration <= mean_raw <= max_acceleration:
        return Sensor(SensorType.ACCELERATION, mean_raw)
    if 37500 <= mean_raw <= 38500:
        return Sensor(SensorType.PIEZO, mean_raw)

    return Sensor(SensorType.BROKEN, mean_raw)


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import testmod

    testmod()
