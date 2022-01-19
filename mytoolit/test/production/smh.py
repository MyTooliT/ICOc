# -- Imports ------------------------------------------------------------------

from unittest import main as unittest_main

from mytoolit.config import settings
from mytoolit.test.production import TestNode
from mytoolit.test.unit import ExtendedTestRunner
from mytoolit.utility import add_commander_path_to_environment

# -- Class --------------------------------------------------------------------


class TestSMH(TestNode):
    """This class contains tests for the milling head sensor (PCB)"""

    def _connect(self):
        """Create a connection to the SMH"""

        # Connect to STU
        super()._connect()
        # Connect to sensor hardware
        self.loop.run_until_complete(self.can.connect_sth(settings.smh.name))

    def _read_data(self):
        """Read data from connected SMH"""

        async def read_data():
            """Read data using the new network class"""

            node = 'STH 1'
            cls = type(self)
            cls.bluetooth_mac = await self.can.get_mac_address(node)
            cls.firmware_version = await self.can.get_firmware_version(node)
            cls.release_name = await self.can.get_firmware_release_name(node)

        self.loop.run_until_complete(read_data())

    def test_connection(self):
        """Check connection to SMH"""

        self.loop.run_until_complete(self._test_connection())


# -- Main ---------------------------------------------------------------------


def main():
    add_commander_path_to_environment()
    unittest_main(testRunner=ExtendedTestRunner,
                  module="mytoolit.test.production.smh")


if __name__ == "__main__":
    main()
