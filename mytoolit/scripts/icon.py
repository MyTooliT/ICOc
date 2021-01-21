# -- Imports ------------------------------------------------------------------

from argparse import ArgumentParser, ArgumentTypeError
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

    parser = ArgumentParser()
    parser.add_argument("mac_address",
                        help="MAC address of STH e.g. 08:6b:d7:01:de:81",
                        type=is_mac_address)
    return parser.parse_args()


# -- Class --------------------------------------------------------------------


class EEPROM_Check:

    def __init__(self):
        self.network = Network()
        self.network.reset_node('STU 1')
        self.eeprom_address = 1
        self.eeprom_length = 256
        self.eeprom_value = 10

    def connect_bluetooth(self, mac_address):
        mac_address_hex = hex(int("".join(mac_address.split(":")), 16))
        self.network.bBlueToothConnectPollingAddress(
            Node('STU 1').value, mac_address_hex)

        print(f"Connected to “{self.network.read_eeprom_name()}”")

    def reset_sth(self):
        self.network.reset_node('STH 1')
        self.network.bConnected = False

    def write_eeprom(self):
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
        print(f"{incorrect:.2%} incorrect: {changed}")

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
    mac_address = arguments.mac_address

    check = EEPROM_Check()
    check.connect_bluetooth(mac_address)
    check.write_eeprom()
    check.print_eeprom_incorrect()
    print()
    for _ in range(5):
        check.reset_sth()
        check.connect_bluetooth(mac_address)
        check.print_eeprom_incorrect()
        print()
    check.print_eeprom()
    check.disconnect()


if __name__ == '__main__':
    main()
