# -- Imports ------------------------------------------------------------------

from argparse import ArgumentParser
from asyncio import run, sleep
from collections import Counter

from netaddr import EUI

from mytoolit.can import Network
from mytoolit.cmdline import byte_value, mac_address

# -- Function -----------------------------------------------------------------


def parse_arguments():
    """Parse the arguments of the EEPROM checker command line tool

    Returns
    -------

    A simple object storing the MAC address (attribute `mac`) of an STH and an
    byte value that should be stored into the cells of the EEPROM (attribute
    `value`)
    """

    parser = ArgumentParser(
        description="Check the integrity of STH EEPROM content"
    )
    parser.add_argument(
        "mac",
        help="MAC address of STH e.g. 08:6b:d7:01:de:81",
        type=mac_address,
    )
    parser.add_argument(
        "--value",
        help="byte value for EEPROM cells (default: %(default)s)",
        type=byte_value,
        default=10,
    )

    return parser.parse_args()


# -- Class --------------------------------------------------------------------


class EEPROMCheck:
    """Write and check the content of a certain page in EEPROM of an STH"""

    def __init__(self, mac: EUI, value):
        """Initialize the EEPROM check with the given arguments

        Parameters
        ----------

        mac
            The MAC address of an STH

        value:
            The value that the EEPROM checker should write into the EEPROM
        """

        self.mac_address = mac
        self.eeprom_address = 1
        self.eeprom_length = 256
        self.eeprom_value = value
        self.network = Network()

    async def __aenter__(self):
        """Initialize the connection to the STU"""

        await self.network.__aenter__()
        await self.network.reset_node("STU 1")
        await sleep(1)  # Wait till reset takes place
        return self

    async def __aexit__(self, exception_type, exception_value, traceback):
        """Disconnect from the STU"""

        await self.network.__aexit__(
            exception_type, exception_value, traceback
        )

    async def connect_bluetooth(self):
        """Connect to the STH"""

        await self.network.connect_sensor_device(self.mac_address)
        print(f"Connected to “{await self.network.read_eeprom_name('STH 1')}”")

    async def reset_sth(self):
        """Reset the (connected) STH"""

        await self.network.reset_node("STH 1")
        await sleep(1)  # Wait till reset takes place

    async def write_eeprom(self):
        """Write a byte value into one page of the EEPROM"""

        print(f"Write value “{self.eeprom_value}” into EEPROM cells")
        await self.network.write_eeprom(
            address=1,
            offset=0,
            data=[self.eeprom_value for _ in range(self.eeprom_length)],
            node="STH 1",
        )

    async def read_eeprom(self):
        """Read a page of the EEPROM

        Returns:

        A list of the byte values stored in the EEPROM page
        """

        return await self.network.read_eeprom(
            address=1, offset=0, length=256, node="STH 1"
        )

    async def print_eeprom_incorrect(self):
        """Print a summary of the incorrect values in the EEPROM page"""

        changed = [
            byte
            for byte in await self.read_eeprom()
            if byte != self.eeprom_value
        ]
        incorrect = len(changed) / self.eeprom_length
        counter = Counter(changed)
        summary = ", ".join(
            f"{value} ({times} time{'' if times == 1 else 's'})"
            for value, times in sorted(
                counter.items(), key=lambda item: item[1], reverse=True
            )
        )
        print(f"{incorrect:.2%} incorrect{': ' if summary else ''}{summary}")

    async def print_eeprom(self):
        """Print the values stored in the EEPROM page"""

        page = await self.read_eeprom()
        bytes_per_line = 8
        for byte in range(0, self.eeprom_length - 1, bytes_per_line):
            print(f"{byte:3}: ", end="")
            byte_representation = " ".join(["{:3}"] * bytes_per_line).format(
                *page[byte : byte + bytes_per_line]
            )
            print(byte_representation)


# -- Functions ----------------------------------------------------------------


async def check_eeprom(arguments):
    async with EEPROMCheck(mac=arguments.mac, value=arguments.value) as check:
        await check.connect_bluetooth()
        await check.write_eeprom()
        await check.print_eeprom_incorrect()
        print()
        for _ in range(5):
            await check.reset_sth()
            await check.connect_bluetooth()
            await check.print_eeprom_incorrect()
            print()
        await check.print_eeprom()


# -- Main ---------------------------------------------------------------------


def main():
    run(check_eeprom(parse_arguments()))


if __name__ == "__main__":
    main()
