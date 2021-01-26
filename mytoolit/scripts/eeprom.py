# -- Imports ------------------------------------------------------------------

from argparse import ArgumentParser
from collections import Counter

from mytoolit.can import Node
from mytoolit.cmdline import byte_value, mac_address
from mytoolit.old.network import Network

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
        description="Check the integrity of STH EEPROM content")
    parser.add_argument("mac",
                        help="MAC address of STH e.g. 08:6b:d7:01:de:81",
                        type=mac_address)
    parser.add_argument(
        "--value",
        help="byte value for EEPROM cells (default: %(default)s)",
        type=byte_value,
        default=10)

    return parser.parse_args()


# -- Class --------------------------------------------------------------------


class EEPROMCheck:
    """Write and check the content of a certain page in EEPROM of an STH"""

    def __init__(self, mac, value):
        """Initialize the EEPROM check with the given arguments

        Arguments
        ---------

        mac
            The MAC address of an STH as text of the form `xx:xx:xx:xx:xx:xx`,
            where `x` represents a hexadecimal number.

        value:
            The value that the EEPROM checker should write into the EEPROM
        """

        self.mac_address = hex(int("".join(mac.split(":")), 16))
        self.eeprom_address = 1
        self.eeprom_length = 256
        self.eeprom_value = value

    def __enter__(self):
        """Initialize the connection to the STU"""

        self.network = Network()
        self.network.reset_node('STU 1')
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """Disconnect from the STU"""

        self.network.bBlueToothDisconnect(Node('STU 1').value)
        self.network.__exit__()  # Cleanup resources (read thread)

    def connect_bluetooth(self):
        """Connect to the STH"""

        self.network.bBlueToothConnectPollingAddress(
            Node('STU 1').value, self.mac_address)

        print(f"Connected to “{self.network.read_eeprom_name()}”")

    def reset_sth(self):
        """Reset the (connected) STH"""

        self.network.reset_node('STH 1')
        self.network.bConnected = False

    def write_eeprom(self):
        """Write a byte value into one page of the EEPROM"""

        print(f"Write value “{self.eeprom_value}” into EEPROM cells")
        self.network.write_eeprom(
            address=1,
            offset=0,
            data=[self.eeprom_value for _ in range(self.eeprom_length)])

    def read_eeprom(self):
        """Read a page of the EEPROM

        Returns:

        A list of the byte values stored in the EEPROM page
        """

        return self.network.read_eeprom(address=1, offset=0, length=256)

    def print_eeprom_incorrect(self):
        """Print a summary of the incorrect values in the EEPROM page"""

        changed = [
            byte for byte in self.read_eeprom() if byte != self.eeprom_value
        ]
        incorrect = len(changed) / self.eeprom_length
        counter = Counter(changed)
        summary = ", ".join(
            f"{value} ({times} time{'' if times == 1 else 's'})"
            for value, times in sorted(
                counter.items(), key=lambda item: item[1], reverse=True))
        print(f"{incorrect:.2%} incorrect{': ' if summary else ''}{summary}")

    def print_eeprom(self):
        """Print the values stored in the EEPROM page"""

        page = self.read_eeprom()
        bytes_per_line = 8
        for byte in range(0, self.eeprom_length - 1, bytes_per_line):
            print(f"{byte:3}: ", end='')
            byte_representation = " ".join(["{:3}"] * bytes_per_line).format(
                *page[byte:byte + bytes_per_line])
            print(byte_representation)


# -- Main ---------------------------------------------------------------------


def main():

    arguments = parse_arguments()

    with EEPROMCheck(mac=arguments.mac,
                     value=arguments.value) as check:
        check.connect_bluetooth()
        check.write_eeprom()
        check.print_eeprom_incorrect()
        print()
        for _ in range(5):
            check.reset_sth()
            check.connect_bluetooth()
            check.print_eeprom_incorrect()
            print()
        check.print_eeprom()


if __name__ == '__main__':
    main()
