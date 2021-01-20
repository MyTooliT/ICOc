# -- Imports ------------------------------------------------------------------

from mytoolit.can import Node
from mytoolit.old.network import Network

# -- Class --------------------------------------------------------------------


class EEPROM_Check:

    def __init__(self):
        self.network = Network()
        self.network.reset_node('STU 1')

    def connect_bluetooth(self, mac_address):
        mac_address_hex = hex(int("".join(mac_address.split(":")), 16))
        self.network.bBlueToothConnectPollingAddress(
            Node('STU 1').value, mac_address_hex)

        print(f"Connected to “{self.network.read_eeprom_name()}”")

    def write_eeprom(self):
        self.network.write_eeprom(address=1,
                                  offset=0,
                                  data=[14 for _ in range(256)])

    def read_eeprom(self):
        page1 = self.network.read_eeprom(address=1, offset=0, length=256)
        print("\nContent of EEPROM page 1:\n")
        bytes_per_line = 8
        for byte in range(0, len(page1), bytes_per_line):
            print(f"{byte:3}: ", end='')
            byte_representation = " ".join(["{:3}"] * bytes_per_line).format(
                *page1[byte:byte + bytes_per_line])
            print(byte_representation)

    def disconnect(self):
        self.network.bBlueToothDisconnect(Node('STU 1').value)
        self.network.__exit__()  # Cleanup resources (read thread)


# -- Main ---------------------------------------------------------------------


def main():

    check = EEPROM_Check()
    check.connect_bluetooth("08:6b:d7:01:de:81")
    check.write_eeprom()
    check.read_eeprom()
    check.read_eeprom()
    check.disconnect()


if __name__ == '__main__':
    main()
