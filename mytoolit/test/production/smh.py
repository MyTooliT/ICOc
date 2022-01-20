# -- Imports ------------------------------------------------------------------

from unittest import main as unittest_main

from mytoolit.config import settings
from mytoolit.test.production import TestSensorDevice
from mytoolit.test.unit import ExtendedTestRunner
from mytoolit.utility import add_commander_path_to_environment

# -- Class --------------------------------------------------------------------


class TestSMH(TestSensorDevice):
    """This class contains tests for the milling head sensor (PCB)"""

    def _connect(self):
        """Create a connection to the SMH"""

        super()._connect_device(settings.smh.name)

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
