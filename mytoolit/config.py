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
        if sensor_settings.Sensor == 'ADXL1001':
            return sensor_settings.ADXL1001
        if sensor_settings.Sensor == 'ADXL1002':
            return sensor_settings.ADXL1002

        # TODO: Use [validation](https://www.dynaconf.com/validation)
        # to handle incorrect config values after
        #
        # - https://github.com/rochacbruno/dynaconf/issues/486
        #
        # is fixed.
        raise ValueError(
            f"Unsupported sensor: “{sensor_settings.Sensor}”\n\n"
            "Please use one of the supported sensor configuration values "
            "“ADXL1001” or “ADXL1002”")

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
