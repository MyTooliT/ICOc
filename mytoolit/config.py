# -- Import -------------------------------------------------------------------

from dynaconf import Dynaconf
from pathlib import Path

# -- Class --------------------------------------------------------------------


class Settings(Dynaconf):
    """Small extension of the settings object for our purposes"""

    def acceleration_sensor(self):
        """Get the settings for the current acceleration sensor

        Returns
        -------

        A configuration object for the currently selected accelerometer sensor
        """

        sensor_settings = self.STH.Acceleration_Sensor
        if sensor_settings.Sensor == 'ADXL1002':
            return sensor_settings.ADXL1002
        return sensor_settings.ADXL1001

    def sth_name(self) -> str:
        """Return the current name of the STH as string

        Returns
        -------

        The name of the STH

        """

        return str(self.STH.Name)


# -- Attributes ---------------------------------------------------------------

settings = Settings(
    envvar_prefix="DYNACONF",
    settings_file=[
        Path(__file__).parent.parent.joinpath('Configuration').joinpath(
            'config.yaml')
    ],
)
