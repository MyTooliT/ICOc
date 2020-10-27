# -- Imports ------------------------------------------------------------------

from datetime import datetime
from mytoolit.config import settings
from re import search
from types import SimpleNamespace
from unittest import TestCase

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


# -- Class --------------------------------------------------------------------


class TestNode(TestCase):
    """This class contains shared test code for STH and STU"""

    @classmethod
    def setUpClass(cls):
        """Set up data for whole test"""

        # Initialize report
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

    def setUp(self):
        """Set up hardware before a single test case"""

        # The firmware flash does not initiate a connection. The over the air
        # update already terminates the connection itself.
        if search("flash|ota", self._testMethodName):
            return

        self._connect()

        if not type(self).read_attributes:
            # Read data of specific node (STH or STU). Subclasses must
            # implement this method.
            self._read_data()
            type(self).read_attributes = True

    def tearDown(self):
        """Clean up after single test case"""

        self._disconnect()
