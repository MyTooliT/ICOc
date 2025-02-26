"""Support code for Simplicity Commander command line tool

See: https://community.silabs.com/s/article/simplicity-commander

for more information
"""

# -- Imports ------------------------------------------------------------------

from os import environ, pathsep
from pathlib import Path
from platform import system
from re import compile as re_compile
from subprocess import CalledProcessError, run
from sys import byteorder
from typing import List, Optional, Union

from mytoolit.config import settings

# -- Classes ------------------------------------------------------------------


class CommanderException(Exception):
    """Describes problems regarding the execution of Simplicity Commander"""


class CommanderReturnCodeException(CommanderException):
    """A Simplicity Commander command did not return the success status code"""


class CommanderOutputMatchException(CommanderException):
    """The Simplicity Commander output did not contain an expected value"""


class Commander:
    """Wrapper for the Simplicity Commander commandline tool"""

    def __init__(self, serial_number: int, chip: str):
        """Initialize the Simplicity Commander wrapper

        serial_number:
            The serial number of the programming board that is connected to
            the hardware

        chip:
            The identifier of the chip on the PCB e.g. “BGM121A256V2”

        """

        self._add_path_to_environment()
        self.identification_arguments = [
            "--serialno",
            f"{serial_number}",
            "-d",
            chip,
        ]
        self.error_reasons = {
            "incorrect serial": (
                f"Serial number of programming board “{serial_number}”"
                " incorrect"
            ),
            "programmer not connected": (
                "Programming board is not connected to computer"
            ),
            "device not connected": (
                "Programming board is not connected to device"
            ),
        }

    def _add_path_to_environment(self) -> None:
        """Add path to Simplicity Commander (`commander`) to `PATH`

        After calling this method you should be able to call `commander`
        without its path prefix, if you installed it somewhere in the
        locations specified below `COMMANDS` → `PATH` in the configuration.

        Example
        -------

        >>> commander = Commander(
        ...     serial_number=settings.sth.programming_board.serial_number,
        ...     chip='BGM121A256V2')

        >>> from subprocess import run
        >>> result = run("commander --version".split(), capture_output=True)
        >>> result.returncode == 0
        True

        """

        path = settings.commands.path
        operating_system = system()
        paths = (
            path.linux
            if operating_system == "Linux"
            else path.mac if operating_system == "Darwin" else path.windows
        )

        environ["PATH"] += pathsep + pathsep.join(paths)

    def _run_command(
        self,
        command: List[str],
        description: str,
        possible_error_reasons: Optional[List[str]] = None,
        regex_output: Optional[str] = None,
    ) -> str:
        """Run a Simplicity Commander command

        Parameters
        ----------

        command:
            The Simplicity Commander subcommand including all necessary
            arguments

        description:
            A textual description of the purpose of the command
            e.g. “enable debug mode”

        possible_error_reasons:
            A list of dictionary keys that describe why the command might have
            failed

        regex_output:
            An optional regular expression that has to match part of the
            standard output of the command

        Raises
        ------

        A `CommanderException` if

        - the command returned unsuccessfully or
        - the standard output did not match the optional regular expression
          specified in `regex_output`

        Returns
        -------

        The standard output of the command

        """

        if possible_error_reasons:
            for reason in possible_error_reasons:
                if reason not in self.error_reasons:
                    raise ValueError(
                        f"“{reason}” is not a valid possible error reason"
                    )

        try:
            result = run(
                ["commander"] + command,
                capture_output=True,
                check=True,
                text=True,
            )
        except CalledProcessError as error:
            # Since Windows seems to return the exit code as unsigned number we
            # need to convert it first to the “real” signed number.
            returncode = (
                int.from_bytes(
                    error.returncode.to_bytes(4, byteorder),
                    byteorder,
                    signed=True,
                )
                if system() == "Windows"
                else error.returncode
            )
            error_message = (
                "Execution of Simplicity Commander command to "
                f"{description} failed with return code "
                f"“{returncode}”"
            )
            combined_output = (
                "\n".join((error.stdout, error.stderr))
                if error.stdout or error.stderr
                else ""
            )
            if combined_output:
                error_message += (
                    "\n\nSimplicity Commander output:\n\n"
                    f"{combined_output.rstrip()}"
                )

            if possible_error_reasons:
                error_reasons = "\n".join([
                    f"• {self.error_reasons[reason]}"
                    for reason in possible_error_reasons
                ])
                error_message += (
                    f"\n\nPossible error reasons:\n\n{error_reasons}"
                )

            raise CommanderReturnCodeException(error_message) from error

        if (
            regex_output is not None
            and re_compile(regex_output).search(result.stdout) is None
        ):
            error_message = (
                "Output of Simplicity Commander command to "
                f"{description}:\n{result.stdout}\n"
                "did not match the expected regular expression "
                f"“{regex_output}”"
            )
            raise CommanderOutputMatchException(error_message)

        return result.stdout

    def enable_debug_mode(self) -> None:
        """Enable debug mode for external device

        Example
        -------

        Enable debug mode of STH programming board

        >>> from mytoolit.config import settings

        >>> commander = Commander(
        ...     serial_number=settings.sth.programming_board.serial_number,
        ...     chip='BGM121A256V2')
        >>> commander.enable_debug_mode()

        """

        error_reasons = ["programmer not connected", "incorrect serial"]
        self._run_command(
            command="adapter dbgmode OUT".split()
            + self.identification_arguments,
            description="enable debug mode",
            possible_error_reasons=error_reasons,
            regex_output="Setting debug mode to OUT",
        )

    def unlock_device(self) -> None:
        """Unlock device for debugging

        Calling this method will erase the flash of the device!

        """

        self._run_command(
            command="device unlock".split() + self.identification_arguments,
            description="unlock device",
            possible_error_reasons=[
                "device not connected",
                "programmer not connected",
                "incorrect serial",
            ],
            regex_output="Chip successfully unlocked",
        )

    def upload_flash(self, filepath: Union[str, Path]) -> None:
        """Upload code into the flash memory of the device

        Parameters
        ----------

        filepath:
            The filepath of the flash image

        """

        # Set debug mode to out, to make sure we flash the STH (connected via
        # debug cable) and not another microcontroller connected to the
        # programmer board.
        self.enable_debug_mode()

        # Unlock device (triggers flash erase)
        self.unlock_device()

        self._run_command(
            command=["flash", f"{filepath}", "--address", "0x0"]
            + self.identification_arguments,
            description="upload firmware",
        )

    def read_power_usage(self, milliseconds: float = 1000) -> float:
        """Read the power usage of the connected hardware

        Parameters
        ----------

        milliseconds:
            The amount of time the power usage should be measured for

        Returns
        -------

        The measured power usage in milliwatts

        Example
        -------

        Measure power usage of connected STH

        >>> from mytoolit.config import settings

        >>> commander = Commander(
        ...     serial_number=settings.sth.programming_board.serial_number,
        ...     chip='BGM121A256V2')
        >>> commander.read_power_usage() > 0
        True

        """

        command = [
            "aem",
            "measure",
            "--windowlength",
            str(milliseconds),
        ] + self.identification_arguments

        regex = r"Power\s*\[mW\]\s*:\s*(?P<milliwatts>\d+\.\d+)"
        try:
            output = self._run_command(
                command=command,
                description="read power usage",
                possible_error_reasons=[
                    "programmer not connected",
                    "incorrect serial",
                ],
                regex_output=regex,
            )
        except CommanderOutputMatchException as error:
            raise CommanderOutputMatchException(
                "Unable to extract power usage "
                "from Simplicity Commander output"
            ) from error

        pattern_match = re_compile(regex).search(output)
        assert pattern_match is not None
        milliwatts = pattern_match["milliwatts"]

        return float(milliwatts)


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import testmod

    testmod()
