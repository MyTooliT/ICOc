from can.interface import Bus
from can import CanError, Message
from mytoolit.can.identifier import Identifier
from time import sleep


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


if __name__ == '__main__':
    # Configure the CAN hardware
    bus = Bus(bustype='pcan', channel='PCAN_USBBUS1', bitrate=1000000)

    # Reset STU (and STH)
    send_message(bus, create_id('System', 'Reset'))
    message = bus.recv(2)
    print(f"Reset Acknowledgment: {Identifier(message.arbitration_id)}")
