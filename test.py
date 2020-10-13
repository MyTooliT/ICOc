from can.interface import Bus
from can import CanError, Message
from mytoolit.can.identifier import Identifier
from time import sleep
from network import Network


def send_message(bus, identifier, data=None):
    message = Message(arbitration_id=identifier.value,
                      data=data,
                      is_extended_id=True)
    bus.send(message)


def create_id(block,
              block_command,
              sender='SPU 1',
              receiver='STU 1',
              request=True):
    return Identifier(block=block,
                      block_command=block_command,
                      sender=sender,
                      receiver=receiver,
                      request=request)


def create_connection_network():
    network = Network()
    return_message = network.reset_node("STU 1")
    identifier = Identifier(int(return_message['ID'], 16))
    print(f"Reset STU 1: {identifier}")
    sleep(1)  # Wait until reset was executed
    network.__exit__()  # Cleanup resources (read thread)


def create_connection_bus():
    # Configure the CAN hardware
    bus = Bus(bustype='pcan', channel='PCAN_USBBUS1', bitrate=1000000)

    # Reset STU (and STH)
    send_message(bus, create_id('System', 'Reset'))
    message = bus.recv(2)
    print(f"Reset STU 1: {Identifier(message.arbitration_id)}")
    sleep(1)  # Wait until reset was executed


if __name__ == '__main__':
    create_connection_bus()
