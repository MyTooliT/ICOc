"""Read name of STH with device number 0"""

# -- Imports ------------------------------------------------------------------

from asyncio import run

from mytoolit.can import Network

# -- Functions ----------------------------------------------------------------


async def read_name(identifier):
    async with Network() as network:
        await network.connect_sensor_device(identifier)
        name = await network.get_name("STH 1")
        print(f"Connected to sensor device “{name}”")


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    # Possible Identifiers:
    # - Name:          e.g. `"Test-STH"`
    # - Device Number: e.g. `1`
    # - MAC Address:   e.g. `netaddr.EUI('08-6B-D7-01-DE-81')`
    run(read_name(identifier=0))
