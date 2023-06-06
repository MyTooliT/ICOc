# -- Import -------------------------------------------------------------------

from dynaconf import Dynaconf
from importlib.resources import as_file, files
from os import makedirs
from pathlib import Path
from platformdirs import site_config_dir, user_config_dir

# -- Class --------------------------------------------------------------------


class Settings(Dynaconf):
    """Small extension of the settings object for our purposes"""

    def acceleration_sensor(self):
        """Get the settings for the current acceleration sensor

        Returns
        -------

        A configuration object for the currently selected accelerometer sensor
        """

        sensor_settings = self.sth.acceleration_sensor
        if sensor_settings.sensor == "ADXL1001":
            return sensor_settings.adxl1001
        if sensor_settings.sensor == "ADXL1002":
            return sensor_settings.adxl1002
        if sensor_settings.sensor == "ADXL356":
            return sensor_settings.adxl356

        # TODO: Use [validation](https://www.dynaconf.com/validation)
        # to handle incorrect config values after
        #
        # - https://github.com/rochacbruno/dynaconf/issues/486
        #
        # is fixed.
        raise ValueError(
            f"Unsupported sensor: “{sensor_settings.sensor}”\n\n"
            "Please use one of the supported sensor configuration values "
            "“ADXL1001” or “ADXL1002” or “ADXL356”"
        )

    def sth_name(self) -> str:
        """Return the current name of the STH as string

        Returns
        -------

        The name of the STH

        """

        return str(self.sth.name)

    def output_directory(self) -> Path:
        """Get the HDF output directory

        Returns
        -------

        The HDF output directory as path object

        """

        directory = Path(settings.measurement.output.directory)
        return directory if directory.is_absolute() else directory.expanduser()

    def check_output_directory(self) -> None:
        """Check the output directory

        If the directory does not already exist, then this function will try to
        create it.

        """

        directory = self.output_directory()

        if directory.exists() and not directory.is_dir():
            raise NotADirectoryError(
                f"The output directory “{directory}” points to an "
                "existing file not an directory"
            )

        if not directory.is_dir():
            try:
                makedirs(str(directory))
            except OSError as error:
                raise OSError(
                    "Unable to create the output directory "
                    f"“{directory}”: {error}"
                )


# -- Attributes ---------------------------------------------------------------

app_name = "ICOc"
config_filename = "config.yaml"
site_config_filepath = Path(site_config_dir(app_name)) / config_filename
user_config_filepath = Path(user_config_dir(app_name)) / config_filename

with as_file(
    files("mytoolit.config").joinpath(config_filename)
) as repo_settings_filepath:
    settings = Settings(
        settings_file=[
            repo_settings_filepath,
            site_config_filepath,
            user_config_filepath,
        ],
        merge_enabled=True,
    )
