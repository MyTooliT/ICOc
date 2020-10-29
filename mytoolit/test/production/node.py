# -- Imports ------------------------------------------------------------------

from datetime import datetime
from os.path import abspath, isfile, dirname, join
from mytoolit.config import settings
from re import escape, search
from subprocess import run
from types import SimpleNamespace
from unittest import TestCase

from mytoolit.config import settings
from mytoolit import __version__
from mytoolit.report import Report

from network import Network
from MyToolItNetworkNumbers import MyToolItNetworkNr
from MyToolItCommands import AdcOverSamplingRate

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


def filter_undefined_attributes(cls, possible_attributes):
    """Get all defined attributes for a certain class

    The attributes (specified in possible_attributes) have to be created
    with the function create_attribute.

    Parameters
    ----------

    cls:
        The class that might store the attributes specified in
        possible_attributes

    possible_attributes:
        An iterable of possible attributes stored in the class cls

    Returns
    -------

    A list of defined attributes for the class
    """

    # Check available read hardware attributes
    attributes = []
    for attribute in possible_attributes:
        try:
            attribute.value = str(attribute.value).format(cls=cls)
            attributes.append(attribute)
        except AttributeError:
            pass

    return attributes


# -- Class --------------------------------------------------------------------


class TestNode(TestCase):
    """This class contains shared test code for STH and STU

    Please note that every subclass of this class has to implement

    - the **class** method `_collect_node_data` and
    - the method `_read_data`.
    """

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

        operator = settings.Operator.Name

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

        # The method _collect_node_data has to be implemented by the subclass
        attributes = cls._collect_node_data()
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
        attributes_pdf = [
            attribute for attribute in attributes if attribute.pdf
        ]
        for attribute in attributes_pdf:
            cls.report.add_attribute(attribute.description, attribute.value,
                                     node_data)

    def run(self, result=None):
        """Execute a single test

        We override this method to store data about the test outcome.
        """

        super().run(result)
        type(self).report.add_test_result(self.shortDescription(), result)

    def _connect(self):
        """Create a connection to the STU"""

        # Initialize CAN bus
        log_filepath = f"{self._testMethodName}.txt"
        log_filepath_error = f"{self._testMethodName}_Error.txt"

        self.can = Network(log_filepath,
                           log_filepath_error,
                           MyToolItNetworkNr['SPU1'],
                           MyToolItNetworkNr['STH1'],
                           oversampling=AdcOverSamplingRate[64])

        # Reset STU (and STH)
        self.can.bConnected = False
        return_message = self.can.reset_node("STU 1")
        self.can.CanTimeStampStart(return_message['CanTime'])

    def _disconnect(self):
        """Tear down connection to STU"""

        self.can.__exit__()

    def _test_firmware_flash(self, node):
        """Upload bootloader and application into node

        Please note the additional underscore in the method name that makes
        sure this test case is executed before all other test cases.
        """

        programming_board_serial_number = (
            settings.STH.Programming_Board.Serial_Number
            if node == 'STH' else settings.STU.Programming_Board.Serial_Number)

        chip = "BGM113A256V2" if node == 'STH' else 'BGM111A256V2'

        identification_arguments = (
            f"--serialno {programming_board_serial_number} -d {chip}")

        # Set debug mode to out, to make sure we flash the STH (connected via
        # debug cable) and not another microcontroller connected to the
        # programmer board.
        change_mode_command = (
            f"commander adapter dbgmode OUT {identification_arguments}")
        status = run(change_mode_command, capture_output=True, text=True)
        self.assertEqual(status.returncode, 0,
                         f"Unable to change debug mode of programming board")

        # Unlock debug access
        unlock_command = (
            f"commander device unlock {identification_arguments}")
        status = run(unlock_command, capture_output=True, text=True)
        self.assertEqual(
            status.returncode, 0,
            f"Unlock command returned non-zero exit code {status.returncode}")
        self.assertRegex(status.stdout, "Chip successfully unlocked",
                         "Unable to unlock debug access of chip")

        # Upload bootloader and application data
        flash_location = (settings.STH.Firmware.Location.Flash if node == 'STH'
                          else settings.STU.Firmware.Location.Flash)
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

        # The firmware flash does not initiate a connection. The over the air
        # update already terminates the connection itself.
        if search("flash|ota", self._testMethodName):
            return

        self._disconnect()
