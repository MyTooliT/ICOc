"""Test code for a single node in the ICOtronic system

The code below contains shared code for:

- SHA/STH
- SMH
- STU
"""

# -- Imports ------------------------------------------------------------------

from asyncio import new_event_loop, set_event_loop, sleep as async_sleep
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import List, Union
from unittest import TestCase

from dynaconf.utils.boxing import DynaBox
from semantic_version import Version

from mytoolit import __version__
from mytoolit.can import Network, Node, State
from mytoolit.cmdline.commander import Commander
from mytoolit.config import settings
from mytoolit.eeprom import EEPROMStatus
from mytoolit.report import Report

# -- Class --------------------------------------------------------------------


class TestNode(TestCase):
    """This class contains shared test code for STH and STU

    You are not supposed to use this class directly. Instead use it as base
    class for your test class.

    Every subclass of this class has to implement the method `_read_data`,
    which sets the **class** attributes:

    - bluetooth_mac
    - bluetooth_rssi
    - firmware_version

    The method `_read_data` will be called after connection took place (the
    method `_connect` has been called). Please note, that this class only
    connects to the STU. If you also want to connect to a sensor node, please
    overwrite the method `_connect`.

    To add additional test attributes shown in the standard output and
    optionally the PDF, add them as **class** variables to the subclass. Then
    use the **class** method `add_attribute` in the method `setUpClass` and
    use a format string where you reference the class variable as value
    argument. Please do not forget to call `setUpClass` of the superclass
    before you do that.

    The various `_test` methods in this class can be used to run certain tests
    for a device as part of a test method (i.e. a method that starts with the
    string `test`).

    """

    batch_number: int
    eeprom_status: EEPROMStatus
    firmware_version: Version
    gtin: int
    hardware_version: Version
    oem_data: str
    operating_time: int
    power_off_cycles: int
    power_on_cycles: int
    production_date: date
    product_name: str
    release_name: str
    serial_number: str
    under_voltage_counter: int
    watchdog_reset_counter: int

    possible_attributes: List[SimpleNamespace] = []

    @classmethod
    def setUpClass(cls):
        """Set up data for whole test"""

        # Add basic test attributes that all devices share
        cls.add_attribute("EEPROM Status", "{cls.eeprom_status}", pdf=False)
        cls.add_attribute("Name", "{cls.name}")
        cls.add_attribute("Status", "{cls.status}")
        cls.add_attribute(
            "Production Date", "{cls.production_date}", pdf=False
        )
        cls.add_attribute("GTIN", "{cls.gtin}", pdf=False)
        cls.add_attribute("Product Name", "{cls.product_name}", pdf=False)
        cls.add_attribute("Batch Number", "{cls.batch_number}", pdf=False)
        cls.add_attribute("Bluetooth Address", "{cls.bluetooth_mac}")
        cls.add_attribute("RSSI", "{cls.bluetooth_rssi} dBm")
        cls.add_attribute("Hardware Version", "{cls.hardware_version}")
        cls.add_attribute("Firmware Version", "{cls.firmware_version}")
        cls.add_attribute("Release Name", "{cls.release_name}", pdf=False)
        cls.add_attribute("OEM Data", "{cls.oem_data}", pdf=False)
        cls.add_attribute(
            "Power On Cycles", "{cls.power_on_cycles}", pdf=False
        )
        cls.add_attribute(
            "Power Off Cycles", "{cls.power_off_cycles}", pdf=False
        )
        cls.add_attribute(
            "Under Voltage Counter", "{cls.under_voltage_counter}", pdf=False
        )
        cls.add_attribute(
            "Watchdog Reset Counter", "{cls.watchdog_reset_counter}", pdf=False
        )
        cls.add_attribute(
            "Operating Time", "{cls.operating_time} s", pdf=False
        )

        # Add a basic PDF report
        # Subclasses should overwrite this attribute, if you want to change
        # the default arguments of the report class
        cls.report = Report()

        # We store attributes related to the connection, such as MAC address
        # only once. To do that we set `read_attributes` to true after
        # the test class gathered the relevant data.
        cls.read_attributes = False

    @classmethod
    def tearDownClass(cls):
        """Print attributes of tested STH after all successful test cases"""

        cls.__output_general_data()
        cls.__output_node_data()
        cls.report.build()

    @classmethod
    def __output_general_data(cls):
        """Print general information and add it to PDF report"""

        now = datetime.now()

        attributes = [
            SimpleNamespace(
                description="ICOc Version", value=__version__, pdf=True
            ),
            SimpleNamespace(
                description="Date", value=now.strftime("%Y-%m-%d"), pdf=True
            ),
            SimpleNamespace(
                description="Time", value=now.strftime("%H:%M:%S"), pdf=True
            ),
            SimpleNamespace(
                description="Operator", value=settings.operator.name, pdf=True
            ),
        ]

        cls.__output_data(attributes, node_data=False)

    @classmethod
    def __output_node_data(cls):
        """Print node information and add it to PDF report"""

        attributes = []
        for attribute in cls.possible_attributes:
            try:
                attribute.value = str(attribute.value).format(cls=cls)
                attributes.append(attribute)
            except (AttributeError, IndexError):
                pass

        cls.__output_data(attributes)

    @classmethod
    def __output_data(cls, attributes, node_data=True):
        """Output data to standard output and PDF report

        Parameters
        ----------

        attributes:
            An iterable that stores simple name space objects created via
            ``create_attribute``

        node_data:
            Specifies if this method outputs node specific or general data
        """

        # Only output something, if there is at least one attribute
        if not attributes:
            return

        max_length_description = max(
            (len(attribute.description) for attribute in attributes)
        )
        max_length_value = max(
            (len(attribute.value) for attribute in attributes)
        )

        # Print attributes to standard output
        print("\n")
        header = "Attributes" if node_data else "General"
        print(header)
        print("—" * len(header))

        for attribute in attributes:
            print(
                f"{attribute.description:{max_length_description}} "
                + f"{attribute.value:>{max_length_value}}"
            )

        # Add attributes to PDF
        attributes_pdf = [
            attribute for attribute in attributes if attribute.pdf
        ]
        for attribute in attributes_pdf:
            cls.report.add_attribute(
                attribute.description, attribute.value, node_data
            )

    @classmethod
    def add_attribute(cls, name: str, value: object, pdf: bool = True) -> None:
        """Add a test attribute

        Parameters
        ----------

        name:
            The description (name) of the attribute

        value:
            The value of the attribute

        pdf:
            True if the attribute should be added to the PDF report

        """

        cls.possible_attributes.append(
            SimpleNamespace(description=name, value=str(value), pdf=pdf)
        )

    def setUp(self):
        """Set up hardware before a single test case"""

        # All tests methods that contain the text `disconnected` do not
        # initialize a Bluetooth connection
        if self._testMethodName.find("disconnected") >= 0:
            return

        self._connect()

        if not type(self).read_attributes:
            # Read data of specific node (STH or STU). Subclasses must
            # implement this method.
            self._read_data()  # pylint: disable=no-member
            type(self).read_attributes = True

    def tearDown(self):
        """Clean up after single test case"""

        # All tests methods that contain the text `disconnected` do not
        # initialize a Bluetooth connection
        if self._testMethodName.find("disconnected") >= 0:
            return

        self._disconnect()

    def run(self, result=None):
        """Execute a single test

        We override this method to store data about the test outcome.
        """

        super().run(result)
        type(self).report.add_test_result(self.shortDescription(), result)

    def _connect(self):
        """Create a connection to the STU"""

        async def connect():
            """Create connection with new network class"""

            # pylint: disable=attribute-defined-outside-init
            self.can = Network()
            # pylint: enable=attribute-defined-outside-init
            await self.can.reset_node("STU 1")
            # Wait for reset to take place
            await async_sleep(2)

        loop = new_event_loop()
        set_event_loop(loop)
        self.loop = loop
        self.loop.run_until_complete(connect())

    def _disconnect(self):
        """Tear down connection to STU"""

        self.loop.run_until_complete(self.can.shutdown())
        self.loop.close()

    async def _test_connection(self, node: str):
        """Check connection to node

        Parameters
        ----------

        node:
            The node for which the connection should be checked

        """

        # The sensor devices need a little more time to switch from the
        # “Startup” to the “Operating” state
        await async_sleep(1)

        # Just send a request for the state and check if the result matches
        # our expectations. The identifier of the answer will be checked by
        # (the notifier in) the network class already.
        state = await self.can.get_state(node)

        expected_state = State(
            mode="Get", location="Application", state="Operating"
        )

        self.assertEqual(
            expected_state,
            state,
            f"Expected state “{expected_state}” does not match "
            f"received state “{state}”",
        )

    def _test_firmware_flash(
        self,
        flash_location: Union[str, Path],
        programmmer_serial_number: int,
        chip: str,
    ):
        """Upload bootloader and application into node

        Parameters
        ----------

        flash_location:
            The location of the flash image

        programmer_serial_number:
            The serial number of the programming board

        chip:
            The name of the chip that should be flashed

        """

        image_filepath = Path(flash_location).expanduser().resolve()
        self.assertTrue(
            image_filepath.is_file(),
            f"Firmware file {image_filepath} does not exist",
        )

        commander = Commander(
            serial_number=programmmer_serial_number, chip=chip
        )

        commander.upload_flash(image_filepath)

    async def _test_eeprom_product_data(
        self, node: Node, config: DynaBox
    ) -> None:
        """Test if reading and writing the product data EEPROM page works

        Parameters
        ----------

        node:
            The node to which this method writes to and reads from

        config
            A configuration object that stores the various product data
            attributes

        """

        cls = type(self)

        receiver = node

        # ========
        # = GTIN =
        # ========

        gtin = config.gtin
        await self.can.write_eeprom_gtin(gtin, receiver)
        cls.gtin = await self.can.read_eeprom_gtin(receiver)
        self.assertEqual(
            gtin,
            cls.gtin,
            f"Written GTIN “{gtin}” does not match read GTIN “{cls.gtin}”",
        )

        # ====================
        # = Hardware Version =
        # ====================

        hardware_version = config.hardware_version
        await self.can.write_eeprom_hardware_version(
            hardware_version, receiver
        )
        cls.hardware_version = await self.can.read_eeprom_hardware_version(
            receiver
        )
        self.assertEqual(
            hardware_version,
            f"{cls.hardware_version}",
            f"Written hardware version “{hardware_version}” does not "
            + f"match read hardware version “{cls.hardware_version}”",
        )

        # ====================
        # = Firmware Version =
        # ====================

        await self.can.write_eeprom_firmware_version(
            cls.firmware_version, receiver
        )
        firmware_version = await self.can.read_eeprom_firmware_version(
            receiver
        )
        self.assertEqual(
            f"{cls.firmware_version}",
            f"{firmware_version}",
            f"Written firmware version “{cls.firmware_version}” does not "
            + f"match read firmware version “{firmware_version}”",
        )

        # ================
        # = Release Name =
        # ================

        # Originally we assumed that this value would be set by the firmware
        # itself. However, according to tests with an empty EEPROM this is not
        # the case.
        release_name = config.firmware.release_name
        await self.can.write_eeprom_release_name(release_name, receiver)
        cls.release_name = await self.can.read_eeprom_release_name(receiver)
        self.assertEqual(
            release_name,
            cls.release_name,
            f"Written firmware release name “{release_name}” does not "
            + f"match read firmware release name “{cls.release_name}”",
        )

        # =================
        # = Serial Number =
        # =================

        serial_number = config.serial_number
        await self.can.write_eeprom_serial_number(serial_number, receiver)
        cls.serial_number = await self.can.read_eeprom_serial_number(receiver)
        self.assertEqual(
            serial_number,
            cls.serial_number,
            f"Written serial number “{serial_number}” does not "
            + f"match read serial number “{cls.serial_number}”",
        )

        # ================
        # = Product Name =
        # ================

        product_name = config.product_name
        await self.can.write_eeprom_product_name(product_name, receiver)
        cls.product_name = await self.can.read_eeprom_product_name(receiver)
        self.assertEqual(
            product_name,
            cls.product_name,
            f"Written product name “{product_name}” does not "
            + f"match read product name “{cls.product_name}”",
        )

        # ============
        # = OEM Data =
        # ============

        oem_data = config.oem_data
        await self.can.write_eeprom_oem_data(oem_data, receiver)
        oem_data_list = await self.can.read_eeprom_oem_data(receiver)
        self.assertListEqual(
            oem_data,
            oem_data_list,
            f"Written OEM data “{oem_data}” does not "
            + f"match read OEM data “{oem_data_list}”",
        )
        # We currently store the data in text format, to improve the
        # readability of null bytes in the shell. Please notice, that this will
        # not always work (depending on the binary data stored in EEPROM
        # region).
        cls.oem_data = "".join(map(chr, oem_data_list)).replace("\x00", "")

    async def _test_eeprom_statistics(
        self, node: Node, production_date: date, batch_number: int
    ) -> None:
        """Test if reading and writing the statistics EEPROM page works

        For this purpose this method writes (default) values into the EEPROM,
        reads them and then checks if the written and read values are equal.

        Parameters
        ----------

        node:
            The device where the EEPROM statistics page should be updated

        production_date:
            The production date of the node

        batch_number:
            The batch number of the node

        """

        cls = type(self)
        receiver = repr(node)

        # =======================
        # = Power On/Off Cycles =
        # =======================

        power_on_cycles = 0
        await self.can.write_eeprom_power_on_cycles(power_on_cycles, receiver)
        cls.power_on_cycles = await self.can.read_eeprom_power_on_cycles(
            receiver
        )
        self.assertEqual(
            power_on_cycles,
            cls.power_on_cycles,
            f"Written power on cycle value “{power_on_cycles}” "
            + "does not match read power on cycle value "
            + f"“{cls.power_on_cycles}”",
        )

        power_off_cycles = 0
        await self.can.write_eeprom_power_off_cycles(
            power_off_cycles, receiver
        )
        cls.power_off_cycles = await self.can.read_eeprom_power_off_cycles(
            receiver
        )
        self.assertEqual(
            power_off_cycles,
            cls.power_off_cycles,
            f"Written power off cycle value “{power_off_cycles}” "
            + "does not match read power off cycle value "
            + f"“{cls.power_off_cycles}”",
        )

        # ==================
        # = Operating Time =
        # ==================

        operating_time = 0
        await self.can.write_eeprom_operating_time(operating_time, receiver)
        cls.operating_time = await self.can.read_eeprom_operating_time(
            receiver
        )
        self.assertEqual(
            operating_time,
            cls.operating_time,
            f"Written operating time “{operating_time}” "
            + "does not match read operating time “{cls.operating_time}”",
        )

        # =========================
        # = Under Voltage Counter =
        # =========================

        under_voltage_counter = 0
        await self.can.write_eeprom_under_voltage_counter(
            under_voltage_counter, receiver
        )
        cls.under_voltage_counter = (
            await self.can.read_eeprom_under_voltage_counter(receiver)
        )
        self.assertEqual(
            under_voltage_counter,
            cls.under_voltage_counter,
            f"Written under voltage counter value “{under_voltage_counter}” "
            + "does not match read under voltage counter value "
            + f"“{cls.under_voltage_counter}”",
        )

        # ==========================
        # = Watchdog Reset Counter =
        # ==========================

        watchdog_reset_counter = 0
        await self.can.write_eeprom_watchdog_reset_counter(
            watchdog_reset_counter, receiver
        )
        cls.watchdog_reset_counter = (
            await self.can.read_eeprom_watchdog_reset_counter(receiver)
        )
        self.assertEqual(
            watchdog_reset_counter,
            cls.watchdog_reset_counter,
            "Written watchdog reset counter value"
            f" “{watchdog_reset_counter} does not match read watchdog"
            f" reset counter value “{cls.watchdog_reset_counter}”",
        )

        # ===================
        # = Production Date =
        # ===================

        await self.can.write_eeprom_production_date(production_date, receiver)
        cls.production_date = await self.can.read_eeprom_production_date(
            receiver
        )
        self.assertEqual(
            production_date,
            cls.production_date,
            f"Written production date “{production_date}” does not match "
            + f"read production date “{cls.production_date}”",
        )

        # ================
        # = Batch Number =
        # ================

        await self.can.write_eeprom_batch_number(batch_number, receiver)
        cls.batch_number = await self.can.read_eeprom_batch_number(receiver)
        self.assertEqual(
            batch_number,
            cls.batch_number,
            f"Written batch “{batch_number}” does not match "
            + f"read batch number “{cls.batch_number}”",
        )

    async def _test_eeprom_status(self, node: Node) -> None:
        """Test if reading and writing the EEPROM status byte works

        Attributes
        ----------

        node:
            The node where the status byte should be checked

        """

        cls = type(self)

        # =================
        # = EEPROM Status =
        # =================

        await self.can.write_eeprom_status("Initialized", node)
        cls.eeprom_status = await self.can.read_eeprom_status(node)
        self.assertTrue(
            cls.eeprom_status.is_initialized(),
            "Setting EEPROM status to “Initialized” failed. "
            "EEPROM status byte currently stores the value "
            f"“{cls.eeprom_status}”",
        )
