# -- Imports ------------------------------------------------------------------

from time import sleep

from mytoolit.can import Node
from mytoolit.config import settings
from mytoolit.old.network import Network

# -- Main ---------------------------------------------------------------------


def main():
    network = Network()

    stu1 = Node('STU 1')
    network.reset_node(stu1)

    network.bBlueToothConnectPollingName(stu1.value,
                                         settings.sth_name(),
                                         log=False)
    sleep(1)  # Wait for connection

    print(f"Connected to “{network.read_eeprom_name()}”")

    network.bBlueToothDisconnect(stu1.value)
    network.__exit__()  # Cleanup resources (read thread)


if __name__ == '__main__':
    main()
