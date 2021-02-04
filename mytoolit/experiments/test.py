from asyncio import run, sleep as asleep
from can.interface import Bus
from can import Message
from pathlib import Path
from platform import system
from sys import path
from time import sleep, time

# Add path for custom libraries
path.append(str(Path(__file__).parent.parent.parent))

from mytoolit.can import Identifier, Network
from mytoolit.old.network import Network as OldNetwork
from mytoolit.old.MyToolItNetworkNumbers import MyToolItNetworkNr
from mytoolit.old.MyToolItCommands import int_to_mac_address


async def create_connection_network_new():
    with Network() as network:
        print("Reset STU 1")
        await network.reset_node('STU 1')  # Reset STU (and STH)

        wait_time = 2
        print(f"Wait {wait_time} seconds for STU 1 reset")
        await asleep(wait_time)

        print("Activate Bluetooth of STU 1")
        await network.activate_bluetooth('STU 1')

        available_devices = 0
        print("Get available Bluetooth devices for STU 1")
        while available_devices <= 0:
            available_devices = await network.get_available_devices_bluetooth(
                'STU 1')
            await asleep(0.1)

        print(f"Available devices: {available_devices}")


def create_connection_network_old():
    # Configure the CAN hardware
    network = OldNetwork()

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

    # Connect to first available device
    device_number = 0
    network.bBlueToothConnectDeviceConnect('STU1', device_number)

    # Check connection to device
    timeout = time() + 10
    connected = False
    while time() < timeout and not connected:
        connected = network.bBlueToothCheckConnect('STU1')
        sleep(0.05)
    if not connected:
        return
    print(f"Connected to {name}")

    # Read MAC address of device
    address = int_to_mac_address(
        network.BlueToothAddress(MyToolItNetworkNr['STH1']))
    print(f"Bluetooth MAC address of {name}: {address}")

    # Disconnect Bluetooth
    connected = network.bBlueToothDisconnect(MyToolItNetworkNr['STU1'])
    if connected:
        return
    print("Disconnected Bluetooth of STU 1")

    network.__exit__()  # Cleanup resources (read thread)


def create_connection_bus():

    def bytearray_to_text(data):
        return bytearray(
            filter(lambda byte: byte > ord(' ') and byte < 128,
                   data)).decode('ASCII')

    def check_bluetooth_connection(bus):
        send_message(bus, create_id('System', 'Bluetooth'), data=[8] + 7 * [0])
        message = bus.recv(2)
        connected = bool(message.data[2])
        return connected

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

    # Connect to first available device
    device_number = 0
    send_message(bus,
                 create_id('System', 'Bluetooth'),
                 data=[7, device_number] + 6 * [0])
    bus.recv(2)

    # Check connection to device
    timeout = time() + 10
    connected = False
    while time() < timeout and not connected:
        connected = check_bluetooth_connection(bus)
        sleep(0.05)
    if not connected:
        return
    print(f"Connected to {name}")

    # Read MAC address of device
    self_addressing = 0xff
    send_message(bus,
                 create_id('System', 'Bluetooth', receiver='STH 1'),
                 data=[17, self_addressing] + 6 * [0])
    bytes_address = reversed(bus.recv(2).data[2:])
    address = ":".join(f"{byte:02x}" for byte in bytes_address)
    print(f"Bluetooth MAC address of {name}: {address}")

    # Disconnect Bluetooth
    send_message(bus, create_id('System', 'Bluetooth'), data=[9] + 7 * [0])
    message = bus.recv(2)
    connected = check_bluetooth_connection(bus)
    if connected:
        return
    print("Disconnected Bluetooth of STU 1")

    # Clean up resources
    bus.shutdown()


if __name__ == '__main__':
    run(create_connection_network_new())
