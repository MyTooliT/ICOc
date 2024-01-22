"""Support code for sensors and sensor configuration"""

# -- Imports ------------------------------------------------------------------

from enum import auto, Enum
from statistics import mean
from typing import Iterable, NamedTuple

# -- Classes ------------------------------------------------------------------


class SensorConfig:
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

        """

        self.first = first
        self.second = second
        self.third = third

    def __str__(self) -> str:
        """The string representation of the sensor configuration

        Returns
        -------

        A textual representation of the sensor configuration

        Examples
        --------

        >>> str(SensorConfig(first=1, second=3, third=2))
        'M1: S1, M2: S3, M3: S2'

        >>> str(SensorConfig())
        ''

        >>> str(SensorConfig(second=1))
        'M2: S1'

        """

        return ", ".join((
            f"M{sensor}: S{value}"
            for sensor, value in enumerate(
                (self.first, self.second, self.third), start=1
            )
            if value != 0
        ))

    def __repr__(self) -> str:
        """The textual representation of the sensor configuration

        Returns
        -------

        A textual representation of the sensor configuration

        Examples
        --------

        >>> repr(SensorConfig(first=1, second=3, third=2))
        'M1: S1, M2: S3, M3: S2'

        >>> repr(SensorConfig())
        'M1: None, M2: None, M3: None'

        """

        return ", ".join((
            f"M{sensor}: {f'S{value}' if value != 0 else 'None'}"
            for sensor, value in enumerate(
                (self.first, self.second, self.third), start=1
            )
        ))

    def disable_channel(
        self, first: bool = False, second: bool = False, third: bool = False
    ):
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
            self.first = 0
        if second:
            self.second = 0
        if third:
            self.third = 0


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
