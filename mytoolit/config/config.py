"""Support for changing configuration values

Currently the configuration is mainly used in the hardware (production tests).
"""

# -- Import -------------------------------------------------------------------

from datetime import date, datetime
from functools import partial
from importlib.resources import as_file, files
from numbers import Real
from os import makedirs
from pathlib import Path
from platform import system
from sys import exit as sys_exit, stderr
from typing import List, Optional

from dynaconf import Dynaconf, ValidationError, Validator
from platformdirs import site_config_dir, user_config_dir

from mytoolit.utility.open import open_file, UnableToOpenError

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
            filepath.parent.mkdir(
                exist_ok=True,
                parents=True,
            )

            default_user_config = (
                files("mytoolit.config")
                .joinpath("user.yaml")
                .read_text(encoding="utf-8")
            )

            with filepath.open("w", encoding="utf8") as config_file:
                config_file.write(default_user_config)

        open_file(filepath)

    @classmethod
    def open_user_config(cls):
        """Open the current users configuration file"""

        try:
            cls.open_config_file(cls.user_config_filepath)
        except UnableToOpenError as error:
            print(
                f"Unable to open user configuration: {error}"
                "\nTo work around this problem please open "
                f"“{cls.user_config_filepath}” in your favorite text "
                "editor",
                file=stderr,
            )


class SettingsIncorrectError(Exception):
    """Raised when the configuration is incorrect"""


class Settings(Dynaconf):
    """Small extension of the settings object for our purposes"""

    def __init__(
        self,
        default_settings_filepath,
        *arguments,
        settings_files: Optional[List[str]] = None,
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
            *arguments,
            **keyword_arguments,
        )
        self.validate_settings()

    # pylint: disable=too-many-locals

    def validate_settings(self) -> None:
        """Check settings for errors"""

        def must_exist(*arguments, **keyword_arguments):
            """Return Validator which requires setting to exist"""

            return Validator(*arguments, must_exist=True, **keyword_arguments)

        def element_is_type(
            nodes,
            name: str,
            element_type: type,
        ):
            """Check that all elements of a list have a certain type"""
            if nodes is None:
                return True  # Let parent validator handle wrong type

            for node in nodes:
                if not isinstance(node, element_type):
                    raise ValidationError(
                        f"Element “{node}” of {name} has wrong type "
                        f"“{type(node)}” instead of “{element_type}”"
                    )
            return True

        def element_is_string(nodes, name: str):
            """Check that all elements of a list are strings"""
            return element_is_type(nodes, name, element_type=str)

        def element_is_int(nodes, name: str):
            """Check that all elements of a list are ints"""
            return element_is_type(nodes, name, element_type=int)

        def device_validators(name: str):
            """Return shared validator for ICOtronic device (STH, STU, SMH)"""

            return [
                must_exist(
                    f"{name}.batch_number",
                    f"{name}.gtin",
                    f"{name}.programming_board.serial_number",
                    is_type_of=int,
                ),
                must_exist(
                    f"{name}.firmware.location.flash",
                    f"{name}.firmware.release_name",
                    f"{name}.hardware_version",
                    is_type_of=str,
                ),
                must_exist(
                    f"{name}.oem_data",
                    is_type_of=list,
                    condition=partial(element_is_int, name="{name}.oem_data"),
                ),
                must_exist(
                    f"{name}.production_date",
                    is_type_of=date,
                ),
                must_exist(
                    f"{name}.product_name",
                    is_type_of=str,
                    len_max=128,
                    cast=str,
                ),
                must_exist(
                    f"{name}.serial_number",
                    is_type_of=str,
                    len_max=8,
                    cast=str,
                ),
            ]

        def sensor_device_validators(name: str):
            """Return shared validator for STH or SMH"""

            return device_validators(name) + [
                must_exist(
                    f"{name}.name",
                    is_type_of=str,
                ),
            ]

        def sensor_validators(name: str):
            prefix = "sth.acceleration_sensor"
            return [
                must_exist(
                    f"{prefix}.{name}.acceleration.maximum",
                    f"{prefix}.{name}.acceleration.ratio_noise_to_max_value",
                    f"{prefix}.{name}.acceleration.tolerance",
                    f"{prefix}.{name}.reference_voltage",
                    f"{prefix}.{name}.self_test.voltage.difference",
                    f"{prefix}.{name}.self_test.voltage.tolerance",
                    is_type_of=Real,
                ),
                must_exist(
                    f"{prefix}.{name}.self_test.dimension",
                    is_type_of=str,
                    is_in=("x", "y", "z"),
                ),
            ]

        config_system = "mac" if system() == "Darwin" else system().lower()
        can_validators = [
            must_exist(f"can.{config_system}.bitrate", is_type_of=int),
            must_exist(
                f"can.{config_system}.channel",
                f"can.{config_system}.interface",
                is_type_of=str,
            ),
        ]
        commands_validators = [
            must_exist(
                "commands.path.linux",
                is_type_of=list,
                condition=partial(
                    element_is_string, name="commands.path.linux"
                ),
            ),
            must_exist(
                "commands.path.mac",
                is_type_of=list,
                condition=partial(element_is_string, name="commands.path.mac"),
            ),
            must_exist(
                "commands.path.windows",
                is_type_of=list,
                condition=partial(
                    element_is_string, name="commands.path.windows"
                ),
            ),
        ]
        logger_validators = [
            must_exist(
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
            must_exist("gui.host", is_type_of=str),
            must_exist("gui.port", is_type_of=int),
        ]
        measurement_validators = [
            must_exist(
                "measurement.output.directory",
                "measurement.output.filename",
                is_type_of=str,
            ),
        ]
        operator_validators = [must_exist("operator.name", is_type_of=str)]
        sensory_device_validators = [
            must_exist(
                "sensory_device.bluetooth.advertisement_time_1",
                "sensory_device.bluetooth.advertisement_time_2",
                "sensory_device.bluetooth.sleep_time_1",
                "sensory_device.bluetooth.sleep_time_2",
                is_type_of=int,
            )
        ]
        smh_validators = sensor_device_validators("smh") + [
            must_exist(
                "smh.channels",
                is_type_of=int,
            )
        ]
        sth_validators = (
            sensor_device_validators("sth")
            + sensor_validators("ADXL1001")
            + sensor_validators("ADXL1002")
            + sensor_validators("ADXL356")
        ) + [
            must_exist(
                "sth.acceleration_sensor.sensor",
                is_in=(
                    "ADXL1001",
                    "ADXL1002",
                    "ADXL356",
                ),
            ),
            must_exist(
                "sth.battery_voltage.average",
                "sth.battery_voltage.tolerance",
                is_type_of=Real,
            ),
            must_exist(
                "sth.status",
                is_in=(
                    "Bare PCB",
                    "Epoxied",
                ),
            ),
        ]
        stu_validators = device_validators("stu")

        self.validators.register(
            *can_validators,
            *commands_validators,
            *logger_validators,
            *gui_validators,
            *measurement_validators,
            *operator_validators,
            *sensory_device_validators,
            *smh_validators,
            *sth_validators,
            *stu_validators,
        )

        try:
            self.validators.validate()
        except ValidationError as error:
            config_files_text = "\n".join((
                f"  • {ConfigurationUtility.site_config_filepath}",
                f"  • {ConfigurationUtility.user_config_filepath}",
            ))
            raise SettingsIncorrectError(
                f"Incorrect configuration: {error}\n\n"
                "Please make sure that the configuration files:\n\n"
                f"{config_files_text}\n\n"
                "contain the correct configuration values"
            ) from error

    # pylint: enable=too-many-locals

    def acceleration_sensor(self):
        """Get the settings for the current acceleration sensor

        Returns
        -------

        A configuration object for the currently selected accelerometer sensor
        """

        sensor_settings = self.sth.acceleration_sensor
        return sensor_settings[sensor_settings.sensor]

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

    def get_output_filepath(self) -> Path:
        """Get filepath of HDF measurement file

        The filepath returned by this method will always include a current
        timestamp to make sure that there are no conflicts with old output
        files.

        Returns
        -------

        The path to the current HDF file

        """

        directory = self.output_directory()
        filename = Path(settings.measurement.output.filename)

        if not filename.suffix:
            filename = filename.with_suffix(".hdf5")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filepath = directory.joinpath(
            f"{filename.stem}_{timestamp}{filename.suffix}"
        )

        return filepath

    def check_output_directory(self) -> None:
        """Check the output directory

        If the directory does not already exist, then this function will try to
        create it.

        """

        directory = self.output_directory()

        if directory.exists() and not directory.is_dir():
            raise NotADirectoryError(
                f"The output directory “{directory}” points to an "
                "existing file not a directory"
            )

        if not directory.is_dir():
            try:
                makedirs(str(directory))
            except OSError as error:
                raise OSError(
                    "Unable to create the output directory "
                    f"“{directory}”: {error}"
                ) from error


# -- Attributes ---------------------------------------------------------------


with as_file(
    files("mytoolit.config").joinpath(ConfigurationUtility.config_filename)
) as repo_settings_filepath:
    try:
        settings = Settings(default_settings_filepath=repo_settings_filepath)
    except SettingsIncorrectError as settings_incorrect_error:
        print(f"{settings_incorrect_error}", file=stderr)
        sys_exit(1)
