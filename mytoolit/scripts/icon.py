# -- Imports ------------------------------------------------------------------

from mytoolit.can import Node
from mytoolit.old.network import Network

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

    mac_address = "08:6b:d7:01:de:81"
    check = EEPROM_Check()
    check.connect_bluetooth(mac_address)
    check.write_eeprom()
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
