# -- Imports ------------------------------------------------------------------

from typing import Optional

# -- Classes ------------------------------------------------------------------


class SensorConfig:
    """Used to store the configuration of the three sensor channels"""

    def __init__(self,
                 first: Optional[int] = None,
                 second: Optional[int] = None,
                 third: Optional[int] = None):
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

    def __repr__(self) -> str:
        """The string representation of the sensor configuration

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

        return ", ".join((f"M{sensor}: {'S' if value else ''}{value}"
                          for sensor, value in enumerate(
                              (self.first, self.second, self.third), start=1)))


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
