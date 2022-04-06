from asyncio import run
from time import time

from mytoolit.can import Message, Network


async def test(identifier="Aladdin"):
    async with Network() as network:
        node = 'STH 1'
        start_time = time()

        await network.connect_sensor_device(identifier)
        name = await network.get_name(node)
        mac_address = await network.get_mac_address(node)
        print(f"Connected to sensor device “{name}” with MAC "
              f"address “{mac_address}”")

        # Byte 1 (Silicon Labs Channel Number)
        channel_number = 0
        # Byte 2 (Type; 253: pn9, 254: CW)
        signal_type = 253
        # Byte 3 (Time till the RF is turned on in seconds)
        wait_time_seconds = 0
        # Byte 4–5 (Duration the RF is turned on in seconds; Big Endian)
        duration_rf_seconds = 0
        # Byte 6 (RF Power; Max = 32))
        power = 0
        # Byte 7 (Physical antenna chosen; default = 1)
        antenna = 1
        # Byte 8 (Length of an RF packet; default = 37)
        packet_length = 37

        data = [
            channel_number,
            signal_type,
            wait_time_seconds,
            *list((duration_rf_seconds).to_bytes(2, byteorder='big')),
            power,
            antenna,
            packet_length,
        ]
        message = Message(block='Test',
                          block_command=0x69,
                          sender='SPU 1',
                          receiver='STH 1',
                          request=True,
                          data=data)
        print(f"Send message: {message}")
        answer = await network._request(message, "“Pfeifferl” test command")

        print(Message(answer))

        print("\nExecution took {:.3} seconds".format(time() - start_time))


if __name__ == '__main__':
    run(test())
