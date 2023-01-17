from asyncio import run
from time import time

from mytoolit.can import Message, Network


async def pfeifferl(
    identifier,
    channel_number=0,
    signal_type="cw",
    wait_time_seconds=0,
    duration_rf_seconds=0,
    power=0,
    antenna=1,
    packet_length=37,
    myprint=print,
):
    """exclusively broadcast RF test signals (cw/pn9),
    inherently prevents BLE/MYT operations during execution,
    STH is disconnected and advertising afterwards

    Byte_nr, arg : descr (type)
    - *,   identifier: STH-name (str)
    - 1,   channel_number: silabs BLE CH nr, 0-39 (uint8)
    - 2,   signal_type: cw/pn9 (str)
    - 3,   wait_time_seconds (till rf is turned on) (uint8)
    - 4-5, duration_rf_seconds (how long is RF turned on) (int)
    - 6,   RF power 0-32, default = 0 (uint8)
    - 7,   physical antenna, default = 1 (uint8)
    - 8,   length of RF packet, default = 37 (uint8)
    - *,   myprint redirector, default = print (fct_ptr)

    returns: execution_time
    """
    # # map signal_type to byte id # #
    if signal_type == "pn9":
        signal_type = 253
    elif signal_type == "cw":
        signal_type = 254
    else:
        raise Exception("signal type {} unknown - typo?".format(signal_type))

    # # open MYT network, send, return  # #
    async with Network() as network:
        node = "STH 1"
        start_time = time()

        await network.connect_sensor_device(identifier)
        name = await network.get_name(node)
        mac_address = await network.get_mac_address(node)
        myprint(
            f"Connected to sensor device “{name}” with MAC "
            f"address “{mac_address}”"
        )

        data = [
            channel_number,
            signal_type,
            wait_time_seconds,
            *list((duration_rf_seconds).to_bytes(2, byteorder="big")),
            power,
            antenna,
            packet_length,
        ]
        message = Message(
            block="Test",
            block_command=0x69,
            sender="SPU 1",
            receiver="STH 1",
            request=True,
            data=data,
        )
        myprint(f"Send message: {message}")
        answer = await network._request(message, "“Pfeifferl” test command")

        myprint(Message(answer))

        exec_time = time() - start_time
        myprint("\nExecution took {:.3} seconds".format(exec_time))

        return exec_time


if __name__ == "__main__":
    # call async fct via asyncio.run
    run(pfeifferl(identifier="Aladdin"))
