# -- Imports ------------------------------------------------------------------

from mytoolit.can import Node
from mytoolit.old.network import Network

# -- Functions ----------------------------------------------------------------


def connect_network():
    network = Network()
    network.reset_node('STU 1')
    return network


def connect_bluetooth(network, mac_address):
    mac_address_hex = hex(int("".join(mac_address.split(":")), 16))
    network.bBlueToothConnectPollingAddress(
        Node('STU 1').value, mac_address_hex)

    print(f"Connected to “{network.read_eeprom_name()}”")


def read_eeprom_page(network):
    page1 = network.read_eeprom(address=1, offset=0, length=256)
    print("\nContent of EEPROM page 1:\n")
    bytes_per_line = 8
    for byte in range(0, len(page1), bytes_per_line):
        print(f"{byte:3}: ", end='')
        byte_representation = " ".join(["{:3}"] * bytes_per_line).format(
            *page1[byte:byte + bytes_per_line])
        print(byte_representation)


def disconnect(network):

    network.bBlueToothDisconnect(Node('STU 1').value)
    network.__exit__()  # Cleanup resources (read thread)


# -- Main ---------------------------------------------------------------------


def main():

    network = connect_network()
    connect_bluetooth(network, "08:6b:d7:01:de:81")
    read_eeprom_page(network)
    disconnect(network)


if __name__ == '__main__':
    main()
