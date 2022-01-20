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

    def _read_data(self):
        """Read data from connected SMH"""

        super()._read_data()

        cls = type(self)
        cls.name = settings.smh.name

    def test_connection(self):
        """Check connection to SMH"""

        self.loop.run_until_complete(self._test_connection())

    def test_eeprom(self):
        """Test if reading and writing the EEPROM works"""

        async def test_eeprom():
            """Test the EERPOM of the SMH"""

            cls = type(self)
            receiver = 'STH 1'

            # ========
            # = Name =
            # ========

            name = settings.smh.name

            await self.can.write_eeprom_name(name, receiver)
            read_name = await self.can.read_eeprom_name(receiver)

            self.assertEqual(
                name, read_name,
                f"Written name “{name}” does not match read name “{read_name}”"
            )

            cls.name = read_name

            super_class = super(cls, self)

            # =========================
            # = Sleep & Advertisement =
            # =========================

            await super_class._test_eeprom_sleep_advertisement_times()

        self.loop.run_until_complete(test_eeprom())


# -- Main ---------------------------------------------------------------------


def main():
    add_commander_path_to_environment()
    unittest_main(testRunner=ExtendedTestRunner,
                  module="mytoolit.test.production.smh")


if __name__ == "__main__":
    main()
