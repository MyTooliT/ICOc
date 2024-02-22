"""Test code for stationary transceiver unit (STU)"""

# -- Imports ------------------------------------------------------------------

import sys
import threading

from asyncio import sleep, run
from os import devnull
from sys import stderr
from unittest import main as unittest_main

from mytoolit.can.node import Node
from mytoolit.can.network import CANInitError, Network, NoResponseError
from mytoolit.config import settings
from mytoolit.test.production import TestNode
from mytoolit.report import Report
from mytoolit.test.unit import ExtendedTestRunner

# -- Class --------------------------------------------------------------------


class TestSTU(TestNode):
    """This class contains tests for the Stationary Transceiver Unit (STU)"""

    @classmethod
    def setUpClass(cls):
        """Set up data for whole test"""

        super().setUpClass()
        cls.add_attribute("Serial Number", "{cls.serial_number}", pdf=False)
        cls.report = Report(node="STU")

    def _read_data(self):
        """Read data from connected STU"""

        async def read_data():
            """Read data using the new network class"""

            node = "STU 1"
            cls.bluetooth_mac = await self.can.get_mac_address(node)
            cls.firmware_version = await self.can.get_firmware_version(node)
            cls.release_name = await self.can.get_firmware_release_name(node)

        cls = type(self)
        self.loop.run_until_complete(read_data())

    def test__firmware_flash_disconnected(self):
        """Upload bootloader and application into STU

        Please note the additional underscore in the method name that makes
        sure this test case is executed before all other test cases.

        The text `disconnected` in the method name make sure that the test
        framework does not initialize a connection.

        """

        async def fix_can_connection():
            """Fix possible CAN bus error"""

            # Ignore errors in notifier thread
            old_excepthook = threading.excepthook
            threading.excepthook = lambda *args, **kwargs: print("", end="")

            old_stderr = sys.stderr
            with open(devnull, "w", encoding="utf8") as stream_devnull:
                # Do not print error output
                sys.stderr = stream_devnull

                status_ok = False
                attempt = 1
                while not status_ok and attempt <= 10:
                    print(
                        f"\nTrying to fix CAN connection (Attempt {attempt})",
                        end="",
                    )
                    try:
                        async with Network() as network:
                            await network.reset_node("STU 1")
                        status_ok = True

                    except CANInitError:
                        # Init error only seems to happen on the **first
                        # attempt**, if the CAN adapter is not connected to the
                        # computer.
                        if attempt == 1:
                            print("\nCAN adapter is not connected → Exiting\n")
                            return

                        await sleep(1)
                    except NoResponseError:
                        await sleep(1)

                    attempt += 1
                print()

            # Reenable error output
            sys.stderr = old_stderr
            # Show errors in notifier threads again
            threading.excepthook = old_excepthook

            if not status_ok:
                print("Unable to fix CAN connection", file=stderr)

        self._test_firmware_flash(
            flash_location=settings.stu.firmware.location.flash,
            programmmer_serial_number=(
                settings.stu.programming_board.serial_number
            ),
            chip="BGM111A256V2",
        )
        run(fix_can_connection())

    def test_connection(self):
        """Check connection to STU"""

        self.loop.run_until_complete(self._test_connection("STU 1"))

    def test_eeprom(self):
        """Test if reading and writing the EEPROM works"""

        async def test_eeprom():
            """Test the EERPOM of the STU"""

            cls = type(self)
            receiver = "STU 1"

            # ========
            # = Name =
            # ========

            read_name = await self.can.read_eeprom_name()
            expected_name = "Valerie"
            self.assertEqual(
                read_name,
                expected_name,
                f"Read name “{read_name}” does not match expected name "
                + f"“{expected_name}”",
            )

            cls.name = read_name

            # ================
            # = Product Data =
            # ================

            await self._test_eeprom_product_data(Node(receiver), settings.stu)

            # ==============
            # = Statistics =
            # ==============

            await self._test_eeprom_statistics(
                Node(receiver),
                settings.stu.production_date,
                settings.stu.batch_number,
            )

            # =================
            # = EEPROM Status =
            # =================

            await self._test_eeprom_status(Node(receiver))

        self.loop.run_until_complete(test_eeprom())


# -- Main ---------------------------------------------------------------------


def main():
    """Run production test for Stationary Transceiver Unit (STU)"""

    unittest_main(
        testRunner=ExtendedTestRunner, module="mytoolit.test.production.stu"
    )


if __name__ == "__main__":
    main()
