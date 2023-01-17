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

        return ", ".join(
            (
                f"M{sensor}: S{value}"
                for sensor, value in enumerate(
                    (self.first, self.second, self.third), start=1
                )
                if value != 0
            )
        )

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

        return ", ".join(
            (
                f"M{sensor}: {f'S{value}' if value != 0 else 'None'}"
                for sensor, value in enumerate(
                    (self.first, self.second, self.third), start=1
                )
            )
        )

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


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import testmod

    testmod()
