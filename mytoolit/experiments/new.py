"""Experiment with some functionality of the „new“ Network class"""

# -- Imports ------------------------------------------------------------------

from asyncio import run
from time import time

from mytoolit.can import Network


# -- Functions ----------------------------------------------------------------


async def test(identifier):
    async with Network() as network:
        start = time()
        await network.connect_sensor_device(identifier)
        print(f"Time until device connection: {time() - start:.3f} seconds")


# -- Main ---------------------------------------------------------------------


def main():
    for _ in range(10):
        start = time()
        run(test(identifier=0))
        print(f"Overall runtime: {time() - start:.3f} seconds")


if __name__ == "__main__":
    main()
