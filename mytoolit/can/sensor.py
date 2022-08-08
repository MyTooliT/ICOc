# -- Imports ------------------------------------------------------------------

from typing import NamedTuple

# -- Classes ------------------------------------------------------------------


class SensorConfig(NamedTuple):
    """Used to store the configuration of the three sensor channels"""

    x: int
    y: int
    z: int

    def __repr__(self) -> str:
        """The string representation of the sensor configuration

        Returns
        -------

        A textual representation of the sensor configuration

        """

        return f"X: {self.x}, Y: {self.y}, Z: {self.z}"
