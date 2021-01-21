# -- Imports ------------------------------------------------------------------

from argparse import ArgumentParser, ArgumentTypeError
from collections import Counter
from re import compile

from mytoolit.can import Node
from mytoolit.old.network import Network

# -- Function -----------------------------------------------------------------


def parse_arguments():

    def is_mac_address(mac_address):
        mac_regex = compile("[0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5}$")
        if mac_regex.match(mac_address):
            return mac_address
        raise ArgumentTypeError(f"“{mac_address}” is not a valid MAC address")

    def is_byte_value(value):
        try:
            number = int(value, base=0)
            if number < 0 or number > 255:
                raise ValueError()
            return number
        except ValueError:
            raise ArgumentTypeError(f"“{value}” is not a valid byte value")

    parser = ArgumentParser(
        description="Check the integrity of STH EEPROM content")
    parser.add_argument("mac_address",
                        help="MAC address of STH e.g. 08:6b:d7:01:de:81",
                        type=is_mac_address)
    parser.add_argument("--value",
                        help="byte value for EEPROM cells",
                        type=is_byte_value,
                        default=10)
    return parser.parse_args()


# -- Class --------------------------------------------------------------------


class EEPROM_Check:

    def __init__(self, mac_address, value):
        self.network = Network()
        self.network.reset_node('STU 1')
        self.mac_address = hex(int("".join(mac_address.split(":")), 16))
        self.eeprom_address = 1
        self.eeprom_length = 256
        self.eeprom_value = value

    def connect_bluetooth(self):
        self.network.bBlueToothConnectPollingAddress(
            Node('STU 1').value, self.mac_address)

        print(f"Connected to “{self.network.read_eeprom_name()}”")

    def reset_sth(self):
        self.network.reset_node('STH 1')
        self.network.bConnected = False

    def write_eeprom(self):
        print(f"Write value “{self.eeprom_value}” into EEPROM cells")
        self.network.write_eeprom(
            address=1,
            offset=0,
            data=[self.eeprom_value for _ in range(self.eeprom_length)])

    def read_eeprom(self):
        return self.network.read_eeprom(address=1, offset=0, length=256)

    def print_eeprom_incorrect(self):
        changed = [
            byte for byte in self.read_eeprom() if byte != self.eeprom_value
        ]
        incorrect = len(changed) / self.eeprom_length
        counter = Counter(changed)
        summary = ", ".join(
            f"{value} ({times} time{'' if times == 1 else 's'})"
            for value, times in counter.items())
        print(f"{incorrect:.2%} incorrect{': ' if summary else ''}{summary}")

    def print_eeprom(self):
        page = self.read_eeprom()
        bytes_per_line = 8
        for byte in range(0, self.eeprom_length - 1, bytes_per_line):
            print(f"{byte:3}: ", end='')
            byte_representation = " ".join(["{:3}"] * bytes_per_line).format(
                *page[byte:byte + bytes_per_line])
            print(byte_representation)

    def disconnect(self):
        self.network.bBlueToothDisconnect(Node('STU 1').value)
        self.network.__exit__()  # Cleanup resources (read thread)


# -- Main ---------------------------------------------------------------------


def main():

    arguments = parse_arguments()

    check = EEPROM_Check(mac_address=arguments.mac_address,
                         value=arguments.value)
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
    check.disconnect()


if __name__ == '__main__':
    main()
