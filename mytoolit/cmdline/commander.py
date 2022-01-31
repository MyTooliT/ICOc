# -- Imports ------------------------------------------------------------------

from os import environ, pathsep
from re import compile
from subprocess import run
from sys import platform
from typing import List

from mytoolit.config import settings

# -- Classes ------------------------------------------------------------------


class CommanderException(Exception):
    """Describes problems regarding the execution of Simplicity Commander"""


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
            'incorrect serial':
            f"Serial number of programming board “{serial_number}” incorrect",
            'not connected': "Programming board is not connected to computer"
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
        paths = path.linux if platform == 'Linux' else path.windows
        environ['PATH'] += (pathsep + pathsep.join(paths))

    def _run_command(self, command: List[str], description: str,
                     possible_error_reasons: List[str]) -> str:
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

        Raises
        ------

        An `CommanderException` if the command returned unsuccessfully

        Returns
        -------

        The standard output of the command

        """

        for reason in possible_error_reasons:
            if reason not in self.error_reasons:
                raise ValueError(
                    "“{reason}” is not a valid possible error reason")

        result = run(["commander"] + command, capture_output=True, text=True)
        if result.returncode != 0:
            error_message = ("Execution of Simplicity Commander command to "
                             f"{description} failed with return code "
                             f"“{result.returncode}”")
            combined_output = ("\n".join(
                (result.stdout,
                 result.stderr)) if result.stdout or result.stderr else "")
            if combined_output:
                error_message += f":\n{combined_output.rstrip()}"

            error_reasons = "\n".join([
                f"• {self.error_reasons[reason]}"
                for reason in possible_error_reasons
            ])
            error_message += f"\n\nPossible error reasons:\n\n{error_reasons}"

            raise CommanderException(error_message)

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

        self._run_command(
            command="adapter dbgmode OUT".split() +
            self.identification_arguments,
            description="enable debug mode",
            possible_error_reasons=['not connected', 'incorrect serial'])

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

        command = ["aem", "measure", "--windowlength",
                   str(milliseconds)] + self.identification_arguments

        output = self._run_command(
            command=command,
            description="read power usage",
            possible_error_reasons=['not connected', 'incorrect serial'])

        regex = compile(r"Power\s*\[mW\]\s*:\s*(?P<milliwatts>\d+\.\d+)")
        pattern_match = regex.search(output)
        if pattern_match is None:
            raise CommanderException("Unable to extract power usage "
                                     "from Simplicity Commander output")

        assert pattern_match is not None
        milliwatts = pattern_match['milliwatts']

        return float(milliwatts)


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
