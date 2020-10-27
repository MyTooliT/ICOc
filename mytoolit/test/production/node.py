# -- Imports ------------------------------------------------------------------

from re import search
from unittest import TestCase

from network import Network
from MyToolItNetworkNumbers import MyToolItNetworkNr
from MyToolItCommands import AdcOverSamplingRate

# -- Class --------------------------------------------------------------------


class TestNode(TestCase):
    """This class contains shared test code for STH and STU"""

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

    def tearDown(self):
        """Clean up after single test case"""

        self._disconnect()
