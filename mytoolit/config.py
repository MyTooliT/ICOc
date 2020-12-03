# -- Import -------------------------------------------------------------------

from dynaconf import Dynaconf
from os.path import abspath, dirname, join

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

repository_root = dirname(dirname(abspath(__file__)))
settings = Settings(
    envvar_prefix="DYNACONF",
    settings_file=[
        join(join(repository_root, 'Configuration'), 'config.yaml')
    ],
)
