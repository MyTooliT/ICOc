from dynaconf import Dynaconf
from os.path import abspath, dirname, join

repository_root = dirname(dirname(abspath(__file__)))

settings = Dynaconf(
    envvar_prefix="DYNACONF",
    settings_file=[
        join(join(repository_root, 'Configuration'), 'config.yaml')
    ],
)


def acceleration_sensor():
    """Get the settings for the current acceleration sensor

    Returns
    -------

    A configuration object for the currently selected accelerometer sensor
    """

    sensor_settings = settings.STH.Acceleration_Sensor
    if sensor_settings.Sensor == 'ADXL1002':
        return sensor_settings.ADXL1002
    return sensor_settings.ADXL1001
