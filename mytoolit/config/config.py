# -- Import -------------------------------------------------------------------

from dynaconf import Dynaconf, ValidationError, Validator
from importlib.resources import as_file, files
from os import makedirs
from pathlib import Path
from platformdirs import site_config_dir, user_config_dir
from sys import stderr

from mytoolit.utility.open import open_file

# -- Classes ------------------------------------------------------------------


class ConfigurationUtility:
    """Access configuration data"""

    app_name = "ICOc"
    app_author = "MyTooliT"
    config_filename = "config.yaml"
    site_config_filepath = (
        Path(site_config_dir(app_name, appauthor=app_author)) / config_filename
    )
    user_config_filepath = (
        Path(user_config_dir(app_name, appauthor=app_author)) / config_filename
    )

    @staticmethod
    def open_config_file(filepath: Path):
        """Open configuration file

        Parameters
        ----------

        filepath:
            Path to configuration file

        """

        # Create file, if it does not exist already
        if not filepath.exists():
            filepath.mkdir(parents=True)
            filepath.open("a").close()

        open_file(filepath)

    @classmethod
    def open_user_config(cls):
        """Open the current users configuration file"""

        cls.open_config_file(cls.user_config_filepath)


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


with as_file(
    files("mytoolit.config").joinpath(ConfigurationUtility.config_filename)
) as repo_settings_filepath:
    settings = Settings(
        settings_file=[
            repo_settings_filepath,
            ConfigurationUtility.site_config_filepath,
            ConfigurationUtility.user_config_filepath,
        ],
        merge_enabled=True,
    )
    can_validators = []
    for system in ("linux", "mac", "windows"):
        can_validators.extend(
            [
                Validator(
                    f"can.{system}.bitrate", must_exist=True, is_type_of=int
                ),
                Validator(
                    f"can.{system}.channel", must_exist=True, is_type_of=str
                ),
                Validator(
                    f"can.{system}.interface", must_exist=True, is_type_of=str
                ),
            ]
        )

    settings.validators.register(*can_validators)
    try:
        settings.validators.validate()
    except ValidationError as error:
        config_files_text = "\n".join(
            (
                f"  • {ConfigurationUtility.site_config_filepath}",
                f"  • {ConfigurationUtility.user_config_filepath}",
            )
        )
        print(f"Incorrect configuration: {error}\n", file=stderr)
        print(
            (
                "Please make sure that the configuration files:\n\n"
                f"{config_files_text}\n\n"
                "contain the correct configuration values"
            ),
        )
        exit(1)
