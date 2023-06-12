# -- Import -------------------------------------------------------------------

from dynaconf import Dynaconf, ValidationError, Validator
from functools import partial
from importlib.resources import as_file, files
from os import makedirs
from pathlib import Path
from platform import system
from platformdirs import site_config_dir, user_config_dir
from sys import stderr
from typing import List, Optional

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


class SettingsIncorrectError(Exception):
    """Raised when the configuration is incorrect"""


class Settings(Dynaconf):
    """Small extension of the settings object for our purposes"""

    def __init__(
        self,
        default_settings_filepath,
        settings_files: Optional[List[str]] = None,
        *arguments,
        **keyword_arguments,
    ) -> None:
        """Initialize the settings using the given arguments

        Parameters
        ----------

        default_settings_filepath:
            Filepath to default settings file

        setting_files:
            A list containing setting files in ascending order according to
            importance (most important last).

        arguments:
            All positional arguments

        keyword_arguments:
            All keyword arguments

        """

        if settings_files is None:
            settings_files = []

        settings_files = [
            default_settings_filepath,
            ConfigurationUtility.site_config_filepath,
            ConfigurationUtility.user_config_filepath,
        ] + settings_files

        super().__init__(
            settings_files=settings_files,
            merge_enabled=True,  # Combine settings
            *arguments,
            **keyword_arguments,
        )
        self.validate_settings()

    def validate_settings(self) -> None:
        """Check settings for errors"""

        def element_is_string(nodes, name: str):
            if nodes is None:
                return True  # Let parent validator handle wrong type

            for node in nodes:
                if not isinstance(node, str):
                    raise ValidationError(
                        f"Element “{node}” of {name} has wrong type "
                        f"“{type(node)}” instead of string"
                    )
            return True

        config_system = "mac" if system() == "Darwin" else system().lower()
        can_validators = [
            Validator(
                f"can.{config_system}.bitrate", must_exist=True, is_type_of=int
            ),
            Validator(
                f"can.{config_system}.channel", must_exist=True, is_type_of=str
            ),
            Validator(
                f"can.{config_system}.interface",
                must_exist=True,
                is_type_of=str,
            ),
        ]
        commands_validators = [
            Validator(
                "commands.path.linux",
                is_type_of=list,
                condition=partial(
                    element_is_string, name="commands.path.linux"
                ),
            ),
            Validator(
                "commands.path.mac",
                is_type_of=list,
                condition=partial(element_is_string, name="commands.path.mac"),
            ),
            Validator(
                "commands.path.windows",
                is_type_of=list,
                condition=partial(
                    element_is_string, name="commands.path.windows"
                ),
            ),
        ]
        logger_validators = [
            Validator(
                "logger.can.level",
                is_type_of=str,
                is_in=(
                    "CRITICAL",
                    "ERROR",
                    "WARNING",
                    "INFO",
                    "DEBUG",
                    "NOTSET",
                ),
            )
        ]
        gui_validators = [
            Validator("gui.host", is_type_of=str),
            Validator("gui.port", is_type_of=int),
        ]
        measurement_validators = [
            Validator(
                "measurement.output.directory",
                "measurement.output.filename",
                is_type_of=str,
            ),
        ]
        operator_validators = [
            Validator("operator.name", is_type_of=str, must_exist=True)
        ]

        self.validators.register(
            *can_validators,
            *commands_validators,
            *logger_validators,
            *gui_validators,
            *measurement_validators,
            *operator_validators,
        )

        try:
            self.validators.validate()
        except ValidationError as error:
            config_files_text = "\n".join(
                (
                    f"  • {ConfigurationUtility.site_config_filepath}",
                    f"  • {ConfigurationUtility.user_config_filepath}",
                )
            )
            raise SettingsIncorrectError(
                f"Incorrect configuration: {error}\n\n"
                "Please make sure that the configuration files:\n\n"
                f"{config_files_text}\n\n"
                "contain the correct configuration values"
            ) from error

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
    try:
        settings = Settings(default_settings_filepath=repo_settings_filepath)
    except SettingsIncorrectError as error:
        print(f"{error}", file=stderr)
        exit(1)
