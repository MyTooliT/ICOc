# -- Imports ------------------------------------------------------------------

from asyncio import run as async_run, sleep as async_sleep
from datetime import date, datetime
from os.path import abspath, isfile, dirname, join
from re import escape
from subprocess import run
from types import SimpleNamespace
from unittest import TestCase

from mytoolit.can import Network, Node, State
from mytoolit.config import settings
from mytoolit import __version__
from mytoolit.report import Report

from mytoolit.old.network import Network as OldNetwork
from mytoolit.old.MyToolItNetworkNumbers import MyToolItNetworkNr
from mytoolit.old.MyToolItCommands import AdcOverSamplingRate

# -- Functions ----------------------------------------------------------------


def create_attribute(description, value, pdf=True):
    """Create a simple object that stores test attributes


    Parameters
    ----------

    description:
        The description (name) of the attribute

    value:
        The value of the attribute

    pdf:
        True if the attribute should be added to the PDF report


    Returns
    -------

    A simple namespace object that stores the specified data
    """

    return SimpleNamespace(description=description, value=str(value), pdf=pdf)


# -- Class --------------------------------------------------------------------


class TestNode(TestCase):
    """This class contains shared test code for STH and STU

    Please note that every subclass of this class has to implement
    the method `_read_data`.
    """

    possible_attributes = [
        create_attribute("EEPROM Status", "{cls.eeprom_status}", pdf=False),
        create_attribute("Name", "{cls.name}"),
        create_attribute("Holder Type", "{cls.holder_type}", pdf=True),
        create_attribute("Status", "{cls.status}"),
        create_attribute("Production Date", "{cls.production_date}",
                         pdf=False),
        create_attribute("GTIN", "{cls.gtin}", pdf=False),
        create_attribute("Product Name", "{cls.product_name}", pdf=False),
        create_attribute("Serial Number", "{cls.serial_number}", pdf=True),
        create_attribute("Batch Number", "{cls.batch_number}", pdf=False),
        create_attribute("Bluetooth Address", "{cls.bluetooth_mac}"),
        create_attribute("RSSI", "{cls.bluetooth_rssi} dBm"),
        create_attribute("Hardware Version", "{cls.hardware_version}"),
        create_attribute("Firmware Version", "{cls.firmware_version}"),
        create_attribute("Release Name", "{cls.release_name}", pdf=False),
        create_attribute("Ratio Noise Maximum",
                         "{cls.ratio_noise_max:.3f} dB"),
        create_attribute("Sleep Time 1", "{cls.sleep_time_1} ms", pdf=False),
        create_attribute("Advertisement Time 1",
                         "{cls.advertisement_time_1} ms",
                         pdf=False),
        create_attribute("Sleep Time 2", "{cls.sleep_time_2} ms", pdf=False),
        create_attribute("Advertisement Time 2",
                         "{cls.advertisement_time_2} ms",
                         pdf=False),
        create_attribute("OEM Data", "{cls.oem_data}", pdf=False),
        create_attribute("Power On Cycles", "{cls.power_on_cycles}",
                         pdf=False),
        create_attribute("Power Off Cycles",
                         "{cls.power_off_cycles}",
                         pdf=False),
        create_attribute("Under Voltage Counter",
                         "{cls.under_voltage_counter}",
                         pdf=False),
        create_attribute("Watchdog Reset Counter",
                         "{cls.watchdog_reset_counter}",
                         pdf=False),
        create_attribute("Operating Time", "{cls.operating_time} s",
                         pdf=False),
        create_attribute("Acceleration Sensor",
                         "{cls.acceleration_sensor}",
                         pdf=True),
        create_attribute("Acceleration Slope",
                         "{cls.acceleration_slope:.5f}",
                         pdf=False),
        create_attribute("Acceleration Offset",
                         "{cls.acceleration_offset:.3f}",
                         pdf=False),
    ]

    @classmethod
    def setUpClass(cls):
        """Set up data for whole test"""

        # We assume that the last three characters of the subclass name
        # specifies the node (STU or STH).
        cls.report = Report(node=cls.__name__[-3:])

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
        date = now.strftime('%Y-%m-%d')
        time = now.strftime("%H:%M:%S")

        operator = settings.operator.name

        attributes = [
            create_attribute("ICOc Version", __version__),
            create_attribute("Date", date),
            create_attribute("Time", time),
            create_attribute("Operator", operator),
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
            except AttributeError:
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
            [len(attribute.description) for attribute in attributes])
        max_length_value = max(
            [len(attribute.value) for attribute in attributes])

        # Print attributes to standard output
        print("\n")
        header = "Attributes" if node_data else "General"
        print(header)
        print("—" * len(header))

        for attribute in attributes:
            print(f"{attribute.description:{max_length_description}} " +
                  f"{attribute.value:>{max_length_value}}")

        # Add attributes to PDF
        node = cls.__name__[-3:]
        # We write the serial number for the STH but do not add it to the
        # PDF report
        attributes_pdf = [
            attribute for attribute in attributes if attribute.pdf and not (
                node == "STU" and attribute.description == "Serial Number")
        ]
        for attribute in attributes_pdf:
            cls.report.add_attribute(attribute.description, attribute.value,
                                     node_data)

    def _connect(self):
        """Create a connection to the STU"""

        def connect_old():
            """Create connection with old network class"""
            # Initialize CAN bus
            log_filepath = f"{self._testMethodName}.txt"
            log_filepath_error = f"{self._testMethodName}_Error.txt"

            cls = type(self)
            node = cls.__name__[-3:]
            receiver = Node(f'{node} 1').value

            self.can = OldNetwork(log_filepath,
                                  log_filepath_error,
                                  MyToolItNetworkNr['SPU1'],
                                  receiver,
                                  oversampling=AdcOverSamplingRate[64])

            # Reset STU (and STH)
            self.can.bConnected = False
            return_message = self.can.reset_node("STU 1")
            self.can.CanTimeStampStart(return_message['CanTime'])

        async def connect_new():
            """Create connection with new network class"""

            self.can = Network()
            await self.can.reset_node("STU 1")
            # Wait for reset to take place
            await async_sleep(2)

        async_run(connect_new()) if (self._testMethodName in {
            'test_connection', 'test_eeprom'
        }) else connect_old()

    def _disconnect(self):
        """Tear down connection to STU"""

        new_network = hasattr(self.can, 'bus')
        async_run(self.can.shutdown()) if new_network else self.can.__exit__()

    async def _test_connection(self):
        """Check connection to node"""

        # The last three characters of the calling subclass (`TestSTU` or
        # `TestSTH`) contain the name of the node (`STU` or `STH`)
        cls = type(self)
        node = cls.__name__[-3:]
        if node == 'STH':
            # The STH needs a little more time to switch from the “Startup” to
            # the “Operating” state
            await async_sleep(1)

        # Just send a request for the state and check if the result matches
        # our expectations. The identifier of the answer will be checked by
        # (the notifier in) the network class already.
        state = await self.can.get_state(f'{node} 1')

        expected_state = State(mode='Get',
                               location='Application',
                               state='Operating')

        self.assertEqual(
            expected_state, state,
            f"Expected state “{expected_state}” does not match "
            f"received state “{state}”")

    def _test_firmware_flash(self):
        """Upload bootloader and application into node"""

        # The last three characters of the calling subclass (`TestSTU` or
        # `TestSTH`) contain the name of the node (`STU` or `STH`)
        cls = type(self)
        node = cls.__name__[-3:]

        programming_board_serial_number = (
            settings.sth.programming_board.serial_number
            if node == 'STH' else settings.stu.programming_board.serial_number)

        chip = "BGM113A256V2" if node == 'STH' else 'BGM111A256V2'

        identification_arguments = (
            f"--serialno {programming_board_serial_number} -d {chip}")

        # Set debug mode to out, to make sure we flash the STH (connected via
        # debug cable) and not another microcontroller connected to the
        # programmer board.
        change_mode_command = (
            f"commander adapter dbgmode OUT {identification_arguments}")
        status = run(change_mode_command, capture_output=True, text=True)
        self.assertEqual(
            status.returncode, 0,
            "Unable to change debug mode of programming board\n\n" +
            "Possible Reasons:\n\n• No programming board connected\n" +
            "• Serial Number of programming board " +
            f"({programming_board_serial_number}) is incorrect")

        # Unlock debug access
        unlock_command = (
            f"commander device unlock {identification_arguments}")
        status = run(unlock_command, capture_output=True, text=True)
        self.assertEqual(
            status.returncode, 0,
            "Unlock command returned non-zero exit code " +
            f"{status.returncode}\n\n" +
            f"Possible Reason:\n\n• {node} not connected to programming board")
        self.assertRegex(status.stdout, "Chip successfully unlocked",
                         "Unable to unlock debug access of chip")

        # Upload bootloader and application data
        flash_location = (settings.sth.firmware.location.flash if node == 'STH'
                          else settings.stu.firmware.location.flash)
        repository_root = dirname(dirname(dirname(dirname(abspath(__file__)))))
        image_filepath = join(repository_root, flash_location)
        self.assertTrue(isfile(image_filepath),
                        f"Firmware file {image_filepath} does not exist")

        flash_command = (f"commander flash {image_filepath} " +
                         f"--address 0x0 {identification_arguments}")
        status = run(flash_command, capture_output=True, text=True)
        self.assertEqual(
            status.returncode, 0,
            "Flash program command returned non-zero exit code " +
            f"{status.returncode}")
        expected_output = "range 0x0FE04000 - 0x0FE047FF (2 KB)"
        self.assertRegex(
            status.stdout, escape(expected_output),
            f"Flash output did not contain expected output “{expected_output}”"
        )
        expected_output = "DONE"
        self.assertRegex(
            status.stdout, expected_output,
            f"Flash output did not contain expected output “{expected_output}”"
        )

    async def _test_eeprom_product_data(self):
        """Test if reading and writing the product data EEPROM page works"""

        cls = type(self)

        # The last three characters of the calling subclass (`TestSTU` or
        # `TestSTH`) contain the name of the node (`STU` or `STH`)
        node = cls.__name__[-3:]
        config = settings.sth if node == 'STH' else settings.stu
        receiver = f"{node} 1"

        # ========
        # = GTIN =
        # ========

        gtin = config.gtin
        await self.can.write_eeprom_gtin(gtin, receiver)
        cls.gtin = await self.can.read_eeprom_gtin(receiver)
        self.assertEqual(
            gtin, cls.gtin,
            f"Written GTIN “{gtin}” does not match read GTIN “{cls.gtin}”")

        # ====================
        # = Hardware Version =
        # ====================

        hardware_version = config.hardware_version
        await self.can.write_eeprom_hardware_version(hardware_version,
                                                     receiver)
        cls.hardware_version = await self.can.read_eeprom_hardware_version(
            receiver)
        self.assertEqual(
            hardware_version, f"{cls.hardware_version}",
            f"Written hardware version “{hardware_version}” does not " +
            f"match read hardware version “{cls.hardware_version}”")

        # ====================
        # = Firmware Version =
        # ====================

        await self.can.write_eeprom_firmware_version(cls.firmware_version,
                                                     receiver)
        firmware_version = await self.can.read_eeprom_firmware_version(receiver
                                                                       )
        self.assertEqual(
            f"{cls.firmware_version}", f"{firmware_version}",
            f"Written firmware version “{cls.firmware_version}” does not " +
            f"match read firmware version “{firmware_version}”")

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
            release_name, cls.release_name,
            f"Written firmware release name “{release_name}” does not " +
            f"match read firmware release name “{cls.release_name}”")

        # =================
        # = Serial Number =
        # =================

        serial_number = str(config.serial_number)
        await self.can.write_eeprom_serial_number(serial_number, receiver)
        cls.serial_number = await self.can.read_eeprom_serial_number(receiver)
        self.assertEqual(
            serial_number, cls.serial_number,
            f"Written serial number “{serial_number}” does not " +
            f"match read serial number “{cls.serial_number}”")

        # ================
        # = Product Name =
        # ================

        product_name = str(config.product_name)
        await self.can.write_eeprom_product_name(product_name, receiver)
        cls.product_name = await self.can.read_eeprom_product_name(receiver)
        self.assertEqual(
            product_name, cls.product_name,
            f"Written product name “{product_name}” does not " +
            f"match read product name “{cls.product_name}”")

        # ============
        # = OEM Data =
        # ============

        oem_data = config.oem_data
        await self.can.write_eeprom_oem_data(oem_data, receiver)
        cls.oem_data = await self.can.read_eeprom_oem_data(receiver)
        self.assertListEqual(
            oem_data, cls.oem_data,
            f"Written OEM data “{oem_data}” does not " +
            f"match read OEM data “{cls.oem_data}”")
        # We currently store the data in text format, to improve the
        # readability of null bytes in the shell. Please notice, that this will
        # not always work (depending on the binary data stored in EEPROM
        # region).
        cls.oem_data = ''.join(map(chr, cls.oem_data)).replace('\x00', '')

    async def _test_eeprom_statistics(self):
        """Test if reading and writing the statistics EEPROM page works"""

        cls = type(self)

        # The last three characters of the calling subclass (`TestSTU` or
        # `TestSTH`) contain the name of the node (`STU` or `STH`)
        node = cls.__name__[-3:]
        config = settings.sth if node == 'STH' else settings.stu
        receiver = f"{node} 1"

        # =======================
        # = Power On/Off Cycles =
        # =======================

        power_on_cycles = 0
        await self.can.write_eeprom_power_on_cycles(power_on_cycles, receiver)
        cls.power_on_cycles = await self.can.read_eeprom_power_on_cycles(
            receiver)
        self.assertEqual(
            power_on_cycles, cls.power_on_cycles,
            f"Written power on cycle value “{power_on_cycles}” " +
            "does not match read power on cycle value " +
            f"“{cls.power_on_cycles}”")

        power_off_cycles = 0
        await self.can.write_eeprom_power_off_cycles(power_off_cycles,
                                                     receiver)
        cls.power_off_cycles = await self.can.read_eeprom_power_off_cycles(
            receiver)
        self.assertEqual(
            power_off_cycles, cls.power_off_cycles,
            f"Written power off cycle value “{power_off_cycles}” " +
            "does not match read power off cycle value " +
            f"“{cls.power_off_cycles}”")

        # ==================
        # = Operating Time =
        # ==================

        operating_time = 0
        await self.can.write_eeprom_operating_time(operating_time, receiver)
        cls.operating_time = (await
                              self.can.read_eeprom_operating_time(receiver))
        self.assertEqual(
            operating_time, cls.operating_time,
            f"Written operating time “{operating_time}” " +
            "does not match read operating time “{cls.operating_time}”")

        # =========================
        # = Under Voltage Counter =
        # =========================

        under_voltage_counter = 0
        await self.can.write_eeprom_under_voltage_counter(
            under_voltage_counter, receiver)
        cls.under_voltage_counter = (
            await self.can.read_eeprom_under_voltage_counter(receiver))
        self.assertEqual(
            under_voltage_counter, cls.under_voltage_counter,
            f"Written under voltage counter value “{under_voltage_counter}” " +
            "does not match read under voltage counter value " +
            f"“{cls.under_voltage_counter}”")

        # ==========================
        # = Watchdog Reset Counter =
        # ==========================

        watchdog_reset_counter = 0
        await self.can.write_eeprom_watchdog_reset_counter(
            watchdog_reset_counter, receiver)
        cls.watchdog_reset_counter = (
            await self.can.read_eeprom_watchdog_reset_counter(receiver))
        self.assertEqual(
            watchdog_reset_counter, cls.watchdog_reset_counter,
            "Written watchdog reset counter value "
            f"“{watchdog_reset_counter} does not match read watchdog reset "
            f"counter value “{cls.watchdog_reset_counter}”")

        # ===================
        # = Production Date =
        # ===================

        production_date = date.fromisoformat(str(config.production_date))
        await self.can.write_eeprom_production_date(production_date, receiver)
        cls.production_date = await self.can.read_eeprom_production_date(
            receiver)
        self.assertEqual(
            production_date, cls.production_date,
            f"Written production date “{production_date}” does not match " +
            f"read production date “{cls.production_date}”")

        # ================
        # = Batch Number =
        # ================

        batch_number = settings.sth.batch_number
        await self.can.write_eeprom_batch_number(batch_number, receiver)
        cls.batch_number = await self.can.read_eeprom_batch_number(receiver)
        self.assertEqual(
            batch_number, cls.batch_number,
            f"Written batch “{batch_number}” does not match " +
            f"read batch number “{cls.batch_number}”")

    async def _test_eeprom_status(self):
        """Test if reading and writing the EEPROM status byte works"""

        cls = type(self)
        # The last three characters of the calling subclass (`TestSTU` or
        # `TestSTH`) contain the name of the node (`STU` or `STH`)
        node = cls.__name__[-3:]
        receiver = f"{node} 1"

        # =================
        # = EEPROM Status =
        # =================

        await self.can.write_eeprom_status('Initialized', receiver)
        cls.eeprom_status = await self.can.read_eeprom_status(receiver)
        self.assertTrue(
            cls.eeprom_status.is_initialized(),
            f"Setting EEPROM status to “Initialized” failed. "
            "EEPROM status byte currently stores the value "
            f"“{cls.eeprom_status}”")

    def setUp(self):
        """Set up hardware before a single test case"""

        # We do not need a CAN connection for the firmware flash test
        if self._testMethodName == 'test__firmware_flash':
            return

        self._connect()

        if not type(self).read_attributes:
            # Read data of specific node (STH or STU). Subclasses must
            # implement this method.
            self._read_data()
            type(self).read_attributes = True

    def tearDown(self):
        """Clean up after single test case"""

        # The firmware flash does not initiate a connection.
        if self._testMethodName.find("flash") >= 0:
            return

        self._disconnect()

    def run(self, result=None):
        """Execute a single test

        We override this method to store data about the test outcome.
        """

        super().run(result)
        type(self).report.add_test_result(self.shortDescription(), result)
