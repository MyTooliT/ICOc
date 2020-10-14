from can.interface import Bus
from can import CanError, Message
from mytoolit.can.identifier import Identifier
from platform import system
from time import sleep, time

from network import Network
from MyToolItNetworkNumbers import MyToolItNetworkNr


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


def bytearray_to_text(data):
    return data.decode('ASCII').rstrip('\x00')


def create_connection_network():
    # Configure the CAN hardware
    network = Network()

    # Reset STU (and STH)
    message = network.reset_node("STU 1")
    identifier = Identifier(int(message['ID'], 16))
    print(f"Reset STU 1: {identifier}")
    sleep(1)  # Wait until reset was executed

    # Bluetooth Connect
    message = network.vBlueToothConnectConnect(MyToolItNetworkNr['STU1'])
    identifier = Identifier(int(message['ID'], 16))
    print(f"Bluetooth Connect STU 1: {identifier}")

    # Scan for available devices
    timeout = time() + 10
    available_devices = 0
    while time() < timeout and available_devices == 0:
        available_devices = network.iBlueToothConnectTotalScannedDeviceNr(
            'STU1')
        sleep(0.05)

    print(f"Found {available_devices} available device" +
          "" if available_devices == 1 else "s")

    if available_devices <= 0:
        return

    # Get name of available devices
    names = []
    for device_number in range(0, available_devices):
        name = network.BlueToothNameGet('STU1', device_number)
        print(f"Name of device {device_number}: {name}")
        names.append(name)

    network.__exit__()  # Cleanup resources (read thread)


def create_connection_bus():
    # Configure the CAN hardware
    bus = Bus(bustype='socketcan', channel='can0',
              bitrate=1000000) if system() == "Linux" else Bus(
                  bustype='pcan', channel='PCAN_USBBUS1', bitrate=1000000)

    # Reset STU (and STH)
    send_message(bus, create_id('System', 'Reset'))
    message = bus.recv(2)
    print(f"Reset STU 1: {Identifier(message.arbitration_id)}")
    sleep(1)  # Wait until reset was executed

    # Bluetooth Connect
    send_message(bus, create_id('System', 'Bluetooth'), data=[1] + 7 * [0])
    message = bus.recv(2)
    print(f"Bluetooth Connect STU 1: {Identifier(message.arbitration_id)}")

    # Scan for available devices
    timeout = time() + 10
    available_devices = 0
    while time() < timeout and available_devices == 0:
        send_message(bus, create_id('System', 'Bluetooth'), data=[2] + 7 * [0])
        message = bus.recv(2)
        available_devices = int(bytearray_to_text(message.data[2:]))
        sleep(0.05)

    print(f"Found {available_devices} available device" +
          "" if available_devices == 1 else "s")
    if available_devices <= 0:
        return

    # Get name of available devices
    names = []
    for device_number in range(0, available_devices):
        # Get first part of name
        send_message(bus,
                     create_id('System', 'Bluetooth'),
                     data=[5, device_number] + 6 * [0])
        message = bus.recv(2)
        name_part_1 = bytearray_to_text(message.data[2:])
        # Get second part of name
        send_message(bus,
                     create_id('System', 'Bluetooth'),
                     data=[6, device_number] + 6 * [0])
        message = bus.recv(2)
        name_part_2 = bytearray_to_text(message.data[2:])
        name = name_part_1 + name_part_2
        print(f"Name of device {device_number}: {name}")
        names.append(name)


if __name__ == '__main__':
    create_connection_network()
    print("————")
    create_connection_bus()
