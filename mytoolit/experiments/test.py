from asyncio import run

from mytoolit.can import Message, Network


async def test(identifier='Aladdin'):
    async with Network() as network:
        node = 'STH 1'
        await network.connect_sth(identifier)
        name = await network.get_name(node)
        print(f"Connected to “{name}”")

        data = [0b10000000, 0b00000000, 0b00000001, 0b00000010] + 4 * [0]
        message = Message(block='Configuration',
                          block_command=0x01,
                          sender='SPU 1',
                          receiver='STH 1',
                          request=True,
                          data=data)
        print(f"Send message: {message}")
        answer = await network._request(message,
                                        "change channel configuration")
        print(Message(answer))


if __name__ == '__main__':
    run(test())
