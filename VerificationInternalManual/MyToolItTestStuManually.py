import unittest
import sys
import os

# Required to add peakcan
sDirName = os.path.dirname('')
sys.path.append(sDirName)
file_path = '../'
sDirName = os.path.dirname(file_path)
sys.path.append(sDirName)
from network import Network
from MyToolItNetworkNumbers import MyToolItNetworkNr
import time
from MyToolItCommands import *

sLogLocation = '../../Logs/STU/'
"""
This class supports the manual tests of the Stationary Transceiving Unit (STU)
"""


class TestSthManually(unittest.TestCase):
    def setUp(self):
        print("TestCase: ", self._testMethodName)
        input('Press Any Key to Continue')
        self.fileName = sLogLocation + self._testMethodName + ".txt"
        self.fileNameError = sLogLocation + "Error_" + self._testMethodName + ".txt"
        self.Can = Network(self.fileName, self.fileNameError,
                           MyToolItNetworkNr["SPU1"],
                           MyToolItNetworkNr["STH1"])
        self.Can.Logger.Info("TestCase: " + str(self._testMethodName))
        self._resetStu()
        self.bError = False
        self.Can.Logger.Info(
            "STU BlueTooth Address: " +
            hex(self.Can.BlueToothAddress(MyToolItNetworkNr["STU1"])))
        self._statusWords()
        print("Start")
        self.Can.Logger.Info("Start")

    def tearDown(self):
        if False != self.Can.bError:
            self.bError = True
        self.Can.__exit__()
        if self._test_has_failed():
            if os.path.isfile(self.fileNameError) and os.path.isfile(
                    self.fileName):
                os.remove(self.fileNameError)
            if os.path.isfile(self.fileName):
                os.rename(self.fileName, self.fileNameError)

    """
    Checks if any test has failed
    """

    def _test_has_failed(self):
        for _method, error in self._outcome.errors:
            if error:
                return True
        if True == self.bError:
            return True
        return False

    """
    Resets the STU
    """

    def _resetStu(self, retries=5, log=True):
        return self.Can.reset_node("STU1",
                                 retries=retries,
                                 log=log)

    """
    Get all status words of the STU
    """

    def _statusWords(self):
        psw0 = self.Can.node_status(MyToolItNetworkNr["STU1"])
        self.Can.Logger.Info("STU Status Word: " + hex(psw0))
        self.Can.Logger.Info("STU Error Word: {}".format(
            self.Can.error_status(MyToolItNetworkNr["STU1"])))

    """
    Test Acknowledgement from STH. Write message and check identifier to be ack (No bError)
    """

    def testManually0001Ack(self):
        cmd = self.Can.CanCmd(MyToolItBlock["System"],
                              MyToolItSystem["ActiveState"], 1, 0)
        msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                    MyToolItNetworkNr["STU1"], [0])
        self.Can.Logger.Info("Write Message")
        self.Can.WriteFrame(msg)
        self.Can.Logger.Info("Wait 200ms")
        time.sleep(0.25)
        cmd = self.Can.CanCmd(MyToolItBlock["System"],
                              MyToolItSystem["ActiveState"], 0, 0)
        msgAckExpected = self.Can.CanMessage20(cmd, MyToolItNetworkNr["STU1"],
                                               MyToolItNetworkNr["SPU1"], [0])
        self.Can.Logger.Info("Send ID: " + hex(msg.ID) + "; Expected ID: " +
                             hex(msgAckExpected.ID) + "; Received ID: " +
                             hex(self.Can.getReadMessage(-1).ID))
        expectedData = ActiveState()
        expectedData.asbyte = 0
        expectedData.b.u2NodeState = Node["Application"]
        expectedData.b.u3NetworkState = NetworkState["Operating"]
        self.Can.Logger.Info("Send Data: " + hex(0) + "; Expected Data: " +
                             hex(expectedData.asbyte) + "; Received Data: " +
                             hex(self.Can.getReadMessage(-1).DATA[0]))
        self.assertEqual(hex(msgAckExpected.ID),
                         hex(self.Can.getReadMessage(-1).ID))
        self.assertEqual(expectedData.asbyte,
                         self.Can.getReadMessage(-1).DATA[0])

    """
    Under Voltage Counter
    """

    def testManually0700PowerOnOffCounter(self):
        PowerOnOff1 = self.Can.statisticalData(MyToolItNetworkNr["STU1"],
                                               MyToolItStatData["PocPof"])
        PowerOn1 = iMessage2Value(PowerOnOff1[:4])
        PowerOff1 = iMessage2Value(PowerOnOff1[4:])
        self.Can.Logger.Info("Power On Counter since first Power On: " +
                             str(PowerOn1))
        self.Can.Logger.Info("Power Off Counter since first Power On: " +
                             str(PowerOff1))
        input(
            'Power Off Device, wait 1s, power on again and then press Any Key to Continue'
        )
        PowerOnOff2 = self.Can.statisticalData(MyToolItNetworkNr["STU1"],
                                               MyToolItStatData["PocPof"])
        PowerOn2 = iMessage2Value(PowerOnOff2[:4])
        PowerOff2 = iMessage2Value(PowerOnOff2[4:])
        self.Can.Logger.Info("Power On Counter since first Power On: " +
                             str(PowerOn2))
        self.Can.Logger.Info("Power Off Counter since first Power On: " +
                             str(PowerOff2))
        self.assertEqual(PowerOn1 + 1, PowerOn2)
        self.assertEqual(PowerOff1 + 1, PowerOff2)


if __name__ == "__main__":
    print(sys.version)
    sLogLocation = sys.argv[1]
    sLogFile = sys.argv[2]
    if '/' != sLogLocation[-1]:
        sLogLocation += '/'
    sLogFileLocation = sLogLocation + sLogFile
    sDirName = os.path.dirname(sLogFileLocation)
    sys.path.append(sDirName)

    print("Log Files will be saved at: " + str(sLogFileLocation))
    if not os.path.exists(sDirName):
        os.makedirs(sDirName)
    with open(sLogFileLocation, "w") as f:
        print(f)
        runner = unittest.TextTestRunner(f)
        unittest.main(argv=['first-arg-is-ignored'], testRunner=runner)
