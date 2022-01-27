# -- Imports ------------------------------------------------------------------

from os import environ, pathsep
from re import compile
from subprocess import run
from sys import platform

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

        >>> from mytoolit.config import  settings

        >>> commander = Commander(
        ...     serial_number=settings.sth.programming_board.serial_number,
        ...     chip='BGM121A256V2')
        >>> commander.read_power_usage() > 0
        True

        """

        command = [
            "commander", "aem", "measure", "--windowlength",
            str(milliseconds)
        ] + self.identification_arguments

        result = run(command, capture_output=True, text=True)

        if result.returncode != 0:
            error_message = ("Execution of Simplicity Commander power "
                             "measurement command failed with return code "
                             f"“{result.returncode}”")

            combined_output = ("\n".join(
                (result.stdout,
                 result.stderr)) if result.stdout or result.stderr else "")
            if combined_output:
                error_message += f":\n{combined_output}"

            raise CommanderException(error_message)

        regex = compile(r"Power\s*\[mW\]\s*:\s*(?P<milliwatts>\d+\.\d+)")
        pattern_match = regex.search(result.stdout)
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
