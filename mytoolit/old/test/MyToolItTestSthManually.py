import unittest
import sys
import os

# Required to add peakcan
sDirName = os.path.dirname("")
sys.path.append(sDirName)
file_path = "../"
sDirName = os.path.dirname(file_path)
sys.path.append(sDirName)

import time

from mytoolit.old.network import Network
from mytoolit.old.MyToolItNetworkNumbers import MyToolItNetworkNr
from mytoolit.old.SthLimits import SthLimits
from mytoolit.old.MyToolItSth import TestConfig, fAdcRawDat
from mytoolit.old.MyToolItCommands import (
    ActiveState,
    AdcReference,
    byte_list_to_int,
    CalibMeassurementActionNr,
    CalibMeassurementTypeNr,
    DataSets,
    MyToolItBlock,
    MyToolItConfiguration,
    MyToolItStatData,
    MyToolItStreaming,
    MyToolItSystem,
    NodeState,
    NetworkState,
    payload2Hex,
)

sLogLocation = "../../Logs/STH/"

iSensorAxis = 1
bBatteryExternalDcDc = True
uAdc2Acc = 100
iRssiMin = -75
"""
This class supports a manual tests of the Sensory Tool Holder (STH)
"""


class TestSthManually(unittest.TestCase):
    def setUp(self):
        print("TestCase: ", self._testMethodName)
        input("Press Any Key to Continue")
        self.tSthLimits = SthLimits(
            iSensorAxis, bBatteryExternalDcDc, uAdc2Acc, iRssiMin, 20, 35
        )
        self.fileName = sLogLocation + self._testMethodName + ".txt"
        self.fileNameError = (
            sLogLocation + "Error_" + self._testMethodName + ".txt"
        )
        self.Can = Network(
            sender=MyToolItNetworkNr["SPU1"],
            receiver=MyToolItNetworkNr["STH1"],
            prescaler=self.tSthLimits.uSamplingRatePrescalerReset,
            acquisition=self.tSthLimits.uSamplingRateAcqTimeReset,
            oversampling=self.tSthLimits.uSamplingRateOverSamplesReset,
        )
        self.Can.logger.info("TestCase: " + str(self._testMethodName))
        self._resetStu()
        self.Can.logger.info("Connect to STH")
        self.Can.bBlueToothConnectPollingName(
            MyToolItNetworkNr["STU1"], TestConfig["DevName"]
        )
        self._resetSth()
        self.Can.logger.info("Connect to STH")
        self.Can.bBlueToothConnectPollingName(
            MyToolItNetworkNr["STU1"], TestConfig["DevName"]
        )
        self.bError = False
        self.Can.logger.info(
            "STU BlueTooth Address: "
            + hex(self.Can.BlueToothAddress(MyToolItNetworkNr["STU1"]))
        )
        self.Can.logger.info(
            "STH BlueTooth Address: "
            + hex(self.Can.BlueToothAddress(MyToolItNetworkNr["STH1"]))
        )
        self._statusWords()
        temp = self._SthAdcTemp()
        self.assertGreaterEqual(self.tSthLimits.iTemperatureInternalMax, temp)
        self.assertLessEqual(self.tSthLimits.iTemperatureInternalMin, temp)
        print("Start")
        self.Can.logger.info("Start")

    def tearDown(self):
        if False != self.Can.bError:
            self.bError = True
        self.Can.__exit__()
        if self._test_has_failed():
            if os.path.isfile(self.fileNameError) and os.path.isfile(
                self.fileName
            ):
                os.remove(self.fileNameError)
            if os.path.isfile(self.fileName):
                os.rename(self.fileName, self.fileNameError)

    """
    Checks if test case has failed
    """

    def _test_has_failed(self):
        for _method, error in self._outcome.errors:
            if error:
                return True
        if True == self.bError:
            return True
        return False

    """
    Reset the STU
    """

    def _resetStu(self, retries=5, log=True):
        self.Can.bConnected = False
        return self.Can.reset_node("STU1", retries=retries, log=log)

    """
    Reset the STH
    """

    def _resetSth(self, retries=5, log=True):
        self.Can.bConnected = False
        return self.Can.reset_node("STH1", retries=retries, log=log)

    """
    Get the internal BGM113 Chip temeprature in °C
    """

    def _SthAdcTemp(self):
        ret = self.Can.calibMeasurement(
            MyToolItNetworkNr["STH1"],
            CalibMeassurementActionNr["Measure"],
            CalibMeassurementTypeNr["Temp"],
            1,
            AdcReference["1V25"],
            log=False,
        )
        result = float(byte_list_to_int(ret[4:]))
        result /= 1000
        self.Can.logger.info("Temperature(Chip): " + str(result) + "°C")
        self.Can.calibMeasurement(
            MyToolItNetworkNr["STH1"],
            CalibMeassurementActionNr["None"],
            CalibMeassurementTypeNr["Temp"],
            1,
            AdcReference["VDD"],
            log=False,
            bReset=True,
        )
        return result

    """
    Get all status words of STH and STU
    """

    def _statusWords(self):
        psw0 = self.Can.node_status(MyToolItNetworkNr["STH1"])
        self.Can.logger.info("STH Status Word: " + hex(psw0))
        psw0 = self.Can.node_status(MyToolItNetworkNr["STU1"])
        self.Can.logger.info("STU Status Word: " + hex(psw0))

        status = self.Can.error_status(MyToolItNetworkNr["STH1"])
        if status.adc_overrun():
            self.bError = True
        self.Can.logger.info(f"STH Error Word: {status}")

        self.Can.logger.info(
            "STU Error Word: {}".format(
                self.Can.error_status(MyToolItNetworkNr["STU1"])
            )
        )

    """
    Turn off STH LED
    """

    def TurnOffLed(self):
        self.Can.logger.info("Turn Off LED")
        cmd = self.Can.CanCmd(
            MyToolItBlock["Configuration"], MyToolItConfiguration["Hmi"], 1, 0
        )
        message = self.Can.CanMessage20(
            cmd,
            MyToolItNetworkNr["SPU1"],
            MyToolItNetworkNr["STH1"],
            [129, 1, 2, 0, 0, 0, 0, 0],
        )
        self.Can.tWriteFrameWaitAckRetries(message)

    """
    Turn on STH LED
    """

    def TurnOnLed(self):
        self.Can.logger.info("Turn On LED")
        cmd = self.Can.CanCmd(
            MyToolItBlock["Configuration"], MyToolItConfiguration["Hmi"], 1, 0
        )
        message = self.Can.CanMessage20(
            cmd,
            MyToolItNetworkNr["SPU1"],
            MyToolItNetworkNr["STH1"],
            [129, 1, 1, 0, 0, 0, 0, 0],
        )
        self.Can.tWriteFrameWaitAckRetries(message)

    """
    Test Acknowledgement from STH. Write message and check identifier to be ack (No bError)
    """

    def testManually0001Ack(self):
        activeState = ActiveState()
        cmd = self.Can.CanCmd(
            MyToolItBlock["System"], MyToolItSystem["Get/Set State"], 1, 0
        )
        msg = self.Can.CanMessage20(
            cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STH1"], [0]
        )
        self.Can.logger.info("Write Message")
        self.Can.WriteFrame(msg)
        self.Can.logger.info("Wait 200ms")
        time.sleep(0.2)
        cmd = self.Can.CanCmd(
            MyToolItBlock["System"], MyToolItSystem["Get/Set State"], 0, 0
        )
        msgAckExpected = self.Can.CanMessage20(
            cmd, MyToolItNetworkNr["STH1"], MyToolItNetworkNr["SPU1"], [0]
        )
        activeState.asbyte = self.Can.getReadMessage(-1).DATA[0]
        self.Can.logger.info(
            "Send ID: "
            + hex(msg.ID)
            + "; Expected ID: "
            + hex(msgAckExpected.ID)
            + "; Received ID: "
            + hex(self.Can.getReadMessage(-1).ID)
        )
        self.Can.logger.info(
            "Send Data: "
            + hex(0)
            + "; Received Data: "
            + hex(activeState.asbyte)
        )
        self.assertEqual(
            hex(msgAckExpected.ID), hex(self.Can.getReadMessage(-1).ID)
        )
        self.assertEqual(activeState.b.bSetState, 0)
        self.assertEqual(activeState.b.bReserved, 0)
        self.assertEqual(activeState.b.u2NodeState, NodeState["Application"])
        self.assertEqual(activeState.b.bReserved1, 0)
        self.assertEqual(
            activeState.b.u3NetworkState, NetworkState["Operating"]
        )

    """
    Test Standby Command - Run this manually! Only (power on) reset gets out of that (or replay firmware)
    """

    def testManually0010Standby(self):
        failTry = ActiveState()
        receivedData = ActiveState()
        receivedDataFailTry = ActiveState()
        sendData = ActiveState()
        sendData.asbyte = 0
        sendData.b.bSetState = 1
        sendData.b.u2NodeState = 2
        sendData.b.u3NetworkState = 2
        failTry.asbyte = 0
        failTry.b.bSetState = 1
        failTry.b.u2NodeState = 2
        failTry.b.u3NetworkState = 6
        cmd = self.Can.CanCmd(
            MyToolItBlock["System"], MyToolItSystem["Get/Set State"], 1, 0
        )
        message = self.Can.CanMessage20(
            cmd,
            MyToolItNetworkNr["SPU1"],
            MyToolItNetworkNr["STH1"],
            [sendData.asbyte],
        )
        self.Can.logger.info("Send Shut Down Command")
        receivedData.asbyte = self.Can.tWriteFrameWaitAckRetries(message)[
            "Payload"
        ][0]
        self.Can.logger.info("Send try should fail")
        message = self.Can.CanMessage20(
            cmd,
            MyToolItNetworkNr["SPU1"],
            MyToolItNetworkNr["STH1"],
            [failTry.asbyte],
        )
        self.Can.WriteFrame(message)
        self.Can.logger.info("Wait 200ms")
        time.sleep(0.2)
        receivedDataFailTry.asbyte = self.Can.getReadMessage(-1).DATA[0]
        self.Can.logger.info(
            "Fail Try Payload Byte for Active State Command(send): "
            + str(sendData.asbyte)
        )
        self.Can.logger.info(
            "Fail Try Payload Byte for Active State Command(Received): "
            + str(receivedData.asbyte)
        )
        self.Can.logger.info(
            "Fail Try Payload Byte for Active State Command(send with fail): "
            + str(failTry.asbyte)
        )
        self.Can.logger.info(
            "Fail Try Payload Byte for Active State Command(last received): "
            + str(receivedDataFailTry.asbyte)
        )
        self.assertEqual(receivedData.asbyte, sendData.asbyte)
        self.assertEqual(receivedData.asbyte, receivedDataFailTry.asbyte)
        print(
            "Power off device for 1 minute(power consumpiton of the target is"
            " actually REALLY low)"
        )
        input("Press any key to continue")

    """
    Power Consumption - Energy Save Modes
    """

    def testManually0012PowerConsumptionStandby(self):
        self.Can.Standby(MyToolItNetworkNr["STH1"])
        print("Start Simplicty Energy Profiler and connect to target (STH)")
        print("Measure Power Consumption for standby.")
        input("Press any key to continue")
        print(
            "Power off device for 1 minute(power consumpiton of the target is"
            " actually REALLY low)"
        )
        input("Press any key to continue")

    def vComapre(self, iCounterCompare, aiAccCounter, iIndex):
        if iCounterCompare != aiAccCounter[iIndex]:
            iErrorIndex = iIndex
            self.Can.logger.error("Error starts at index: " + str(iIndex))
            if 255 <= iIndex:
                iIndex -= 255
            else:
                iIndex = 0
            iIndexEnd = 255 * 4 + 1
            while iIndex + iIndexEnd > len(aiAccCounter):
                iIndexEnd -= 1
            for i in range(iIndex, iIndex + iIndexEnd):
                self.Can.logger.error(str(aiAccCounter[i]))
            self.assertEqual(iCounterCompare, aiAccCounter[iErrorIndex])

    """
    Power Consumption - Energy Save Modes
    """

    def testManually0300MeasuringInterference(self):
        self.Can.ConfigAdc(
            MyToolItNetworkNr["STH1"],
            self.tSthLimits.uSamplingRatePrescalerReset,
            self.tSthLimits.uSamplingRateAcqTimeReset,
            self.tSthLimits.uSamplingRateOverSamplesReset,
            AdcReference["VDD"],
        )
        print(
            "Please take a smartphone, start scanning Bluetooth devices and"
            " hold it over STU and STH alternately for 10s"
        )
        [indexStart, indexEnd] = self.Can.streamingValueCollect(
            MyToolItNetworkNr["STH1"],
            MyToolItStreaming["Data"],
            DataSets[3],
            1,
            0,
            0,
            30000,
        )
        [
            arrayAccX,
            arrayAccY,
            arrayAccZ,
        ] = self.Can.streamingValueArrayMessageCounters(
            MyToolItNetworkNr["STH1"],
            MyToolItStreaming["Data"],
            DataSets[3],
            1,
            0,
            0,
            indexStart,
            indexEnd,
        )
        self.Can.ValueLog(
            arrayAccX, arrayAccY, arrayAccZ, fAdcRawDat, "AccMsgCounter", ""
        )
        self.assertEqual(0, len(arrayAccY))
        self.assertEqual(0, len(arrayAccZ))
        count = arrayAccX[0]
        self.assertGreaterEqual(count, 0)
        self.assertLessEqual(count, 255)
        bNok = False
        i = 0
        while i < int(len(arrayAccX) / 3):
            if count != arrayAccX[i]:
                bNok = True
            i += 1
            if count != arrayAccX[i]:
                bNok = True
            i += 1
            if count != arrayAccX[i]:
                bNok = True
            i += 1
            count += 1
            count %= 256
        self.assertEqual(bNok, True)

        self.assertGreaterEqual(count, 0)
        self.assertLessEqual(count, 255)
        i = int(2 * len(arrayAccX) / 3)
        while (
            arrayAccX[i] != arrayAccX[i + 1]
            or arrayAccX[i] != arrayAccX[i + 2]
        ):
            i += 1
        self.assertLess(i, int(2 * len(arrayAccX) / 3) + 3)
        count = arrayAccX[i]
        while i < len(arrayAccX) - 3:
            for _j in range(0, 3):
                self.vComapre(count, arrayAccX, i)
                i += 1
            count += 1
            count %= 256

    """
    Under Voltage Counter
    """

    def testManually0700UnderVoltageCounter(self):
        UnderVoltage1 = self.Can.statisticalData(
            MyToolItNetworkNr["STH1"], MyToolItStatData["Uvc"], printLog=True
        )
        UnderVoltagePowerOnFirst1 = byte_list_to_int(UnderVoltage1[:4])
        self.Can.logger.info(
            "Under Voltage Counter since first Power On: "
            + payload2Hex(UnderVoltage1)
        )
        self.Can.logger.info(
            "Under Voltage Counter since first Power On: "
            + str(UnderVoltagePowerOnFirst1)
        )
        input(
            "Power Off Device and wait 1s, power on again and then press Any"
            " Key to Continue"
        )
        self.Can.bBlueToothConnectPollingName(
            MyToolItNetworkNr["STU1"], TestConfig["DevName"]
        )
        UnderVoltage2 = self.Can.statisticalData(
            MyToolItNetworkNr["STH1"], MyToolItStatData["Uvc"], printLog=True
        )
        UnderVoltagePowerOnFirst2 = byte_list_to_int(UnderVoltage2[:4])
        self.Can.logger.info(
            "Under Voltage Counter since first Power On: "
            + payload2Hex(UnderVoltage2)
        )
        self.Can.logger.info(
            "Under Voltage Counter since first Power On: "
            + str(UnderVoltagePowerOnFirst2)
        )
        self.assertEqual(
            0xFFFFFFFF & (UnderVoltagePowerOnFirst1 + 1),
            UnderVoltagePowerOnFirst2,
        )


if __name__ == "__main__":
    print(sys.version)
    sLogLocation = sys.argv[1]
    sLogFile = sys.argv[2]
    if "/" != sLogLocation[-1]:
        sLogLocation += "/"
    sLogFileLocation = sLogLocation + sLogFile
    sDirName = os.path.dirname(sLogFileLocation)
    sys.path.append(sDirName)

    print("Log Files will be saved at: " + str(sLogFileLocation))
    if not os.path.exists(sDirName):
        os.makedirs(sDirName)
    with open(sLogFileLocation, "w") as f:
        print(f)
        runner = unittest.TextTestRunner(f)
        unittest.main(argv=["first-arg-is-ignored"], testRunner=runner)
