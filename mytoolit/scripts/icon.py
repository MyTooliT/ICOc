# -- Imports ------------------------------------------------------------------

from time import sleep

from mytoolit.can import Node
from mytoolit.config import settings
from mytoolit.old.network import Network

# -- Functions ----------------------------------------------------------------


def connect():
    network = Network()
    stu1 = Node('STU 1')
    network.reset_node(stu1)
    network.bBlueToothConnectPollingName(stu1.value,
                                         settings.sth_name(),
                                         log=False)
    sleep(1)  # Wait for connection

    print(f"Connected to “{network.read_eeprom_name()}”")

    return network


def disconnect(network):

    network.bBlueToothDisconnect(Node('STU 1').value)
    network.__exit__()  # Cleanup resources (read thread)


# -- Main ---------------------------------------------------------------------


def main():

    network = connect()

    page1 = network.read_eeprom(address=1, offset=0, length=256)
    print("\nContent of EEPROM page 1:\n")
    bytes_per_line = 8
    for byte in range(0, len(page1), bytes_per_line):
        print(f"{byte:3}: ", end='')
        byte_representation = " ".join(["{:3}"] * bytes_per_line).format(
            *page1[byte:byte + bytes_per_line])
        print(byte_representation)

    disconnect(network)


if __name__ == '__main__':
    main()
