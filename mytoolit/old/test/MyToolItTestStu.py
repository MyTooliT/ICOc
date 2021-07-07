import unittest
import sys
import os
import random
# Required to add peakcan
sDirName = os.path.dirname('')
sys.path.append(sDirName)
file_path = '../'
sDirName = os.path.dirname(file_path)
sys.path.append(sDirName)

# from PCANBasic import *
from random import randint
import time

from mytoolit.old.network import Network
from mytoolit.old.MyToolItCommands import (
    ActiveState,
    BlueToothDeviceNr,
    BluetoothTime,
    byte_list_to_int,
    EepromPage,
    int_to_mac_address,
    MyToolItBlock,
    MyToolItEeprom,
    MyToolItProductData,
    MyToolItStatData,
    MyToolItStreaming,
    MyToolItSystem,
    NodeState,
    NetworkState,
    payload2Hex,
    sArray2String,
    SystemCommandBlueTooth,
)
from mytoolit.old.MyToolItNetworkNumbers import MyToolItNetworkNr
from mytoolit.old.MyToolItStu import TestConfig

sVersion = TestConfig["Version"]
sLogFile = 'TestStu.txt'
sLogLocation = '../../Logs/STU/'
sHomeLocation = "../../SimplicityStudio/v4_workspace/STU/"
sSilabsCommanderLocation = "../../SimplicityStudio/SimplicityCommander/"
sAdapterSerialNo = "440116697"
sBoardType = "BGM111A256V2"
"""
This class is used for automated internal verification of the Stationary Transceiving Unit (STU)
"""


class TestStu(unittest.TestCase):

    def setUp(self):
        self.sHomeLocation = sHomeLocation
        self.sBuildLocation = sHomeLocation + "builds/" + sVersion
        self.sBootloader = sHomeLocation + "builds/" + "BootloaderOtaBgm111.s37"
        self.sAdapterSerialNo = sAdapterSerialNo
        self.sBoardType = sBoardType
        self.sSilabsCommander = sSilabsCommanderLocation + "commander"
        self.fileName = sLogLocation + self._testMethodName + ".txt"
        self.fileNameError = sLogLocation + "Error_" + self._testMethodName + ".txt"
        self.bError = False
        self.Can = Network(self.fileName,
                           self.fileNameError,
                           MyToolItNetworkNr["SPU1"],
                           MyToolItNetworkNr["STU1"],
                           FreshLog=True)
        self.Can.Logger.Info("TestCase: " + str(self._testMethodName))
        self.vSilabsAdapterReset()
        if "test0000FirmwareFlash" != self._testMethodName:
            self.Can.CanTimeStampStart(self._resetStu()["CanTime"])
            self.sStuAddr = int_to_mac_address(
                self.Can.BlueToothAddress(MyToolItNetworkNr["STU1"]))
            self.Can.Logger.Info("STU BlueTooth Address: " + self.sStuAddr)
            self.Can.u32EepromWriteRequestCounter(MyToolItNetworkNr["STU1"])
            self._statusWords()
            self._StuWDog()
        self.Can.Logger.Info(
            "_______________________________________________________________________________________________________________"
        )
        self.Can.Logger.Info("Start")

    def tearDown(self):
        self.Can.Logger.Info("Fin")
        self.Can.Logger.Info(
            "_______________________________________________________________________________________________________________"
        )
        if False == self.Can.bError:
            self.Can.u32EepromWriteRequestCounter(MyToolItNetworkNr["STU1"])
            if "test0000FirmwareFlash" == self._testMethodName:
                self.sStuAddr = hex(
                    self.Can.BlueToothAddress(MyToolItNetworkNr["STU1"]))
                self.Can.Logger.Info("STU BlueTooth Address: " + self.sStuAddr)
                self._StuWDog()
            self._statusWords()
        self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])
        self.Can.Logger.Info("Test Time End Time Stamp")
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
    Checks that a test case has failed or not
    """

    def _test_has_failed(self):
        for _method, error in self._outcome.errors:
            if error:
                return True
        return False

    """
    Reset Stationary Transceiving Unit
    """

    def _resetStu(self, retries=5, log=True):
        self.Can.bConnected = False
        return self.Can.reset_node("STU1", retries=retries, log=log)

    """
    Retrieve Watchdog Counter of ST
    """

    def _StuWDog(self):
        WdogCounter = byte_list_to_int(
            self.Can.statisticalData(MyToolItNetworkNr["STU1"],
                                     MyToolItStatData["Wdog"])[:4])
        self.Can.Logger.Info("WatchDog Counter: " + str(WdogCounter))
        return WdogCounter

    """
    Retrieve all status words
    """

    def _statusWords(self):
        self.Can.Logger.Info("STU Status Word: {}".format(
            self.Can.node_status(MyToolItNetworkNr["STU1"])))
        self.Can.Logger.Info("STU Error Word: {}".format(
            self.Can.error_status(MyToolItNetworkNr["STU1"])))

    """
    Write Page by value
    """

    def vEepromWritePage(self, iPage, value):
        au8Content = [value] * 4
        timeStamp = self.Can.get_elapsed_time()
        for offset in range(0, 256, 4):
            au8Payload = [iPage, 0xFF & offset, 4, 0] + au8Content
            self.Can.cmdSend(MyToolItNetworkNr["STU1"],
                             MyToolItBlock["EEPROM"], MyToolItEeprom["Write"],
                             au8Payload)
        self.Can.Logger.Info("Page Write Time: " +
                             str(self.Can.get_elapsed_time() - timeStamp) +
                             "ms")

    """
    Read page and check content
    """

    def vEepromReadPage(self, iPage, value):
        timeStamp = self.Can.get_elapsed_time()
        for offset in range(0, 256, 4):
            au8Payload = [iPage, 0xFF & offset, 4, 0, 0, 0, 0, 0]
            index = self.Can.cmdSend(MyToolItNetworkNr["STU1"],
                                     MyToolItBlock["EEPROM"],
                                     MyToolItEeprom["Read"], au8Payload)
            dataReadBack = self.Can.getReadMessageData(index)
            for dataByte in dataReadBack[4:]:
                self.assertEqual(dataByte, value)
        self.Can.Logger.Info("Page Read Time: " +
                             str(self.Can.get_elapsed_time() - timeStamp) +
                             "ms")

    """
    Connect to STH1 by device number 1
    """

    def vConnectSth1Dev0(self):
        self.Can.Logger.Info("Connect")
        self.Can.vBlueToothConnectConnect(MyToolItNetworkNr["STU1"])
        self.Can.Logger.Info("Connect to Bluetooth Device")
        for _i in range(0, BluetoothTime["Connect"]):
            time.sleep(1)
            self.Can.Logger.Info("Device Connect to number 0")
            if False != self.Can.bBlueToothConnectDeviceConnect(
                    MyToolItNetworkNr["STU1"], 0):
                break

        for _i in range(0, BluetoothTime["Connect"]):
            self.Can.Logger.Info("Check to be connected")
            if (False != self.Can.bBlueToothCheckConnect(
                    MyToolItNetworkNr["STU1"])):
                break
            time.sleep(1)

    """
    Reset the Silicon Laps Adapter
    """

    def vSilabsAdapterReset(self):
        self.Can.Logger.Info("Reset Adapter " + self.sAdapterSerialNo)
        sSystemCall = self.sSilabsCommander + " adapter reset "
        sSystemCall += "--serialno " + self.sAdapterSerialNo
        sSystemCall += (">>" + sLogLocation + "AdapterReset.txt")
        if os.name == 'nt':
            sSystemCall = sSystemCall.replace("/", "\\")
            os.system(sSystemCall)
        # for mac and linux(here, os.name is 'posix')
        else:
            os.system(sSystemCall)
        time.sleep(4)

    """
    https://www.silabs.com/community/wireless/zigbee-and-thread/knowledge-base.entry.html/2017/12/28/building_firmwareim-1OPr
    commander.exe convert ..\v4_workspace\client_firmware\builds\BootloaderOtaBgm111.s37 ..\v4_workspace\client_firmware\builds\v2.1.4\Client.s37 --patch 0x0fe04000:0x00 --patch 0x0fe041F8:0xFD -o manufacturing_image.hex -d BGM111A256V2
    commander flash manufacturing_image.hex --address 0x0 --serialno 440116697 -d BGM111A256V2
    """

    def test0000FirmwareFlash(self):
        try:
            os.remove(sLogLocation + "ManufacturingCreateResport.txt")
        except:
            pass
        try:
            os.remove(sLogLocation + "ManufacturingFlashResport.txt")
        except:
            pass
        sSystemCall = self.sSilabsCommander + " convert "
        sSystemCall += self.sBootloader + " "
        sSystemCall += self.sBuildLocation + "/firmware_client.s37 "
        sSystemCall += "--patch 0x0fe04000:0x00 --patch 0x0fe041F8:0xFD "
        sSystemCall += "-o " + self.sBuildLocation + "/manufacturingImageStu" + sVersion + ".hex "
        sSystemCall += "-d " + self.sBoardType + " "
        sSystemCall += ">> " + sLogLocation
        sSystemCall += "ManufacturingCreateResport.txt"
        if os.name == 'nt':
            sSystemCall = sSystemCall.replace("/", "\\")
            os.system(sSystemCall)
        # for mac and linux(here, os.name is 'posix')
        else:
            os.system(sSystemCall)
        tFile = open(sLogLocation + "ManufacturingCreateResport.txt",
                     "r",
                     encoding='utf-8')
        asData = tFile.readlines()
        tFile.close()
        self.assertEqual("DONE\n", asData[-1])
        sSystemCall = self.sSilabsCommander + " flash "
        sSystemCall += self.sBuildLocation + "/manufacturingImageStu" + sVersion + ".hex "
        sSystemCall += "--address 0x0 "
        sSystemCall += "--serialno " + self.sAdapterSerialNo + " "
        sSystemCall += "-d " + self.sBoardType + " "
        sSystemCall += ">> " + sLogLocation
        sSystemCall += "ManufacturingFlashResport.txt"
        if os.name == 'nt':
            sSystemCall = sSystemCall.replace("/", "\\")
            os.system(sSystemCall)
        # for mac and linux(here, os.name is 'posix')
        else:
            os.system(sSystemCall)
        tFile = open(sLogLocation + "ManufacturingFlashResport.txt",
                     "r",
                     encoding='utf-8')
        asData = tFile.readlines()
        tFile.close()
        self.assertEqual("range 0x0FE04000 - 0x0FE047FF (2 KB)\n",
                         asData[-2][10:])
        self.assertEqual("DONE\n", asData[-1])
        time.sleep(4)

    """
    Test the over the air update
    """

    def test0001OverTheAirUpdate(self):
        bCreate = os.path.isfile(self.sBuildLocation + "/OtaServer.gbl")
        bCreate = bCreate and os.path.isfile(self.sBuildLocation +
                                             "/OtaApploader.gbl")
        bCreate = bCreate and os.path.isfile(self.sBuildLocation +
                                             "/OtaApploaderServer.gbl")
        bCreate = not bCreate
        if False != bCreate:
            iRuns = 4
            iRuns += 1
            try:
                for i in range(1, iRuns):
                    os.remove(sLogLocation + str(i) + ".txt")
            except:
                pass

            try:
                os.remove(sLogLocation + "CreateReportOta.txt")
            except:
                pass
            try:
                os.remove(self.sBuildLocation + "/OtaClient.gbl")
            except:
                pass
            try:
                os.remove(self.sBuildLocation + "/OtaApploader.gbl")
            except:
                pass
            try:
                os.remove(self.sBuildLocation + "/OtaApploaderClient.gbl")
            except:
                pass

            self._resetStu()
            time.sleep(1)
            sSystemCall = self.sHomeLocation + "/firmware_client/create_bl_files.bat "
            sSystemCall += " -> " + sLogLocation
            sSystemCall += "CreateReportOta.txt"
            if os.name == 'nt':
                sSystemCall = sSystemCall.replace("/", "\\")
                os.system(sSystemCall)
            # for mac and linux(here, os.name is 'posix')
            else:
                os.system(sSystemCall)
            os.rename(
                self.sHomeLocation +
                "/firmware_client/output_gbl/application.gbl",
                self.sBuildLocation + "/OtaClient.gbl")
            os.rename(
                self.sHomeLocation +
                "/firmware_client/output_gbl/apploader.gbl",
                self.sBuildLocation + "/OtaApploader.gbl")
            os.rename(
                self.sHomeLocation + "/firmware_client/output_gbl/full.gbl",
                self.sBuildLocation + "/OtaApploaderClient.gbl")
        for i in range(1, iRuns):
            sSystemCall = self.sBuildLocation + "/ota-dfu.exe COM6 115200 "
            sSystemCall += self.sBuildLocation + "/OtaClient.gbl "
            sSystemCall += self.sStuAddr + " -> " + sLogLocation
            sSystemCall += "Ota" + str(i) + ".txt"
            if os.name == 'nt':
                sSystemCall = sSystemCall.replace("/", "\\")
                os.system(sSystemCall)
            # for mac and linux(here, os.name is 'posix')
            else:
                os.system(sSystemCall)
            tFile = open(sLogLocation + "Ota" + str(i) + ".txt",
                         "r",
                         encoding='utf-8')
            asData = tFile.readlines()
            tFile.close()
            self.assertEqual("Finishing DFU block...OK\n", asData[-2])
            self.assertEqual("Closing connection...OK\n", asData[-1])

    """
    Test Acknowledgement from STU. Write message and check identifier to be ack (No bError)
    """

    def test0005Ack(self):
        cmd = self.Can.CanCmd(MyToolItBlock["System"],
                              MyToolItSystem["Get/Set State"], 1, 0)
        msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                    MyToolItNetworkNr["STU1"], [0])
        self.Can.Logger.Info("Write Message")
        self.Can.WriteFrame(msg)
        self.Can.Logger.Info("Wait 200ms")
        time.sleep(0.25)
        cmd = self.Can.CanCmd(MyToolItBlock["System"],
                              MyToolItSystem["Get/Set State"], 0, 0)
        msgAckExpected = self.Can.CanMessage20(cmd, MyToolItNetworkNr["STU1"],
                                               MyToolItNetworkNr["SPU1"], [0])
        self.Can.Logger.Info("Send ID: " + hex(msg.ID) + "; Expected ID: " +
                             hex(msgAckExpected.ID) + "; Received ID: " +
                             hex(self.Can.getReadMessage(-1).ID))
        expectedData = ActiveState()
        expectedData.asbyte = 0
        expectedData.b.u2NodeState = NodeState["Application"]
        expectedData.b.u3NetworkState = NetworkState["Operating"]
        self.Can.Logger.Info("Send Data: " + hex(0) + "; Expected Data: " +
                             hex(expectedData.asbyte) + "; Received Data: " +
                             hex(self.Can.getReadMessage(-1).DATA[0]))
        self.assertEqual(hex(msgAckExpected.ID),
                         hex(self.Can.getReadMessage(-1).ID))
        self.assertEqual(expectedData.asbyte,
                         self.Can.getReadMessage(-1).DATA[0])

    def test0006FirmwareVersion(self):
        iIndex = self.Can.cmdSend(MyToolItNetworkNr["STU1"],
                                  MyToolItBlock["Product Data"],
                                  MyToolItProductData["FirmwareVersion"], [])
        au8Version = self.Can.getReadMessageData(iIndex)
        au8Version = au8Version[-3:]
        sVersionRead = "v" + str(au8Version[0]) + "." + str(
            au8Version[1]) + "." + str(au8Version[2])
        self.Can.Logger.Info("Version: " + sVersionRead)
        self.assertEqual(sVersion, sVersionRead)

    """ Send Multiple Frames without waiting for an ACK, do ACK after 100 times send flooding to check functionality"""

    def test0052MultiSend(self):
        self.Can.Logger.Info(
            "Send command 100 times, check number of write/reads and do ack test at the end; do that for 100 times"
        )
        for i in range(1, 101):
            self.Can.Logger.Info("Received Index: " +
                                 str(self.Can.GetReadArrayIndex()))
            self.Can.Logger.Info("Run: " + str(i))
            for _j in range(1, 101):
                if (1 == randint(0, 1)):
                    cmd = self.Can.CanCmd(MyToolItBlock["System"],
                                          MyToolItSystem["Get/Set State"], 1,
                                          0)
                    message = self.Can.CanMessage20(cmd,
                                                    MyToolItNetworkNr["SPU1"],
                                                    MyToolItNetworkNr["STU1"],
                                                    [0])
                else:
                    cmd = self.Can.CanCmd(MyToolItBlock["System"],
                                          MyToolItSystem["Bluetooth"], 1, 0)
                    message = self.Can.CanMessage20(
                        cmd, MyToolItNetworkNr["SPU1"],
                        MyToolItNetworkNr["STU1"], [
                            SystemCommandBlueTooth["DeviceCheckConnected"], 0,
                            0, 0, 0, 0, 0, 0
                        ])
                self.Can.WriteFrame(message)
            time.sleep(0.5)
            self.Can.tWriteFrameWaitAckRetries(message, retries=0)

    """ Send Multiple Frames with waiting for an ACK: Send->Ack->Send->Ack"""

    def test0053MultiSendAck(self):
        self.Can.Logger.Info(
            "Send and get ACK for 1000 times AND do it with two messages randomly "
        )
        for i in range(1, 1001):
            self.Can.Logger.Info("Received Index: " +
                                 str(self.Can.GetReadArrayIndex()))
            self.Can.Logger.Info("Run: " + str(i))
            if (1 == randint(0, 1)):
                cmd = self.Can.CanCmd(MyToolItBlock["System"],
                                      MyToolItSystem["Get/Set State"], 1, 0)
                msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                            MyToolItNetworkNr["STU1"], [0])
            else:
                cmd = self.Can.CanCmd(MyToolItBlock["System"],
                                      MyToolItSystem["Bluetooth"], 1, 0)
                msg = self.Can.CanMessage20(
                    cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"],
                    [
                        SystemCommandBlueTooth["DeviceCheckConnected"], 0, 0,
                        0, 0, 0, 0, 0
                    ])
            self.assertNotEqual("bError", self.Can.tWriteFrameWaitAck(msg))
        self.test0005Ack()  # Test that it still works

    """ Send Multiple Frames with waiting for an ACK: Send->Ack->Send->Ack, this also do a retry, tests the test framework - Multiple Messages"""

    def test0054MultiSendMultiAckRetries(self):
        self.Can.Logger.Info(
            "Send and get ACK for 1000 times AND do it with two messages randomly "
        )
        for i in range(1, 1001):
            self.Can.Logger.Info("Received Index: " +
                                 str(self.Can.GetReadArrayIndex()))
            self.Can.Logger.Info("Run: " + str(i))
            if (1 == randint(0, 1)):
                cmd = self.Can.CanCmd(MyToolItBlock["System"],
                                      MyToolItSystem["Get/Set State"], 1, 0)
                msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                            MyToolItNetworkNr["STU1"], [0])
            else:
                cmd = self.Can.CanCmd(MyToolItBlock["System"],
                                      MyToolItSystem["Bluetooth"], 1, 0)
                msg = self.Can.CanMessage20(
                    cmd, MyToolItNetworkNr["SPU1"], MyToolItNetworkNr["STU1"],
                    [
                        SystemCommandBlueTooth["DeviceCheckConnected"], 0, 0,
                        0, 0, 0, 0, 0
                    ])
            self.assertNotEqual(
                "bError", self.Can.tWriteFrameWaitAckRetries(msg, retries=3))
        self.test0005Ack()  # Test that it still works
        """ Send Multiple Frames with waiting for an ACK: Send->Ack->Send->Ack, this also do a retry, tests the test framework - Single Message"""

    def test0055MultiSendSingleAckRetries(self):
        self.Can.Logger.Info(
            "Send and get ACK for 1000 times AND do it with two messages randomly "
        )
        for _i in range(1, 10001):
            self.Can.cmdSend(
                MyToolItNetworkNr["STU1"],
                MyToolItBlock["System"],
                MyToolItSystem["Bluetooth"], [
                    SystemCommandBlueTooth["DeviceCheckConnected"], 0, 0, 0, 0,
                    0, 0, 0
                ],
                retries=0)
        self.test0005Ack()  # Test that it still works

    """
    Send addressing same sender and receiver
    """

    def test0056SenderReceiver(self):
        cmd = self.Can.CanCmd(MyToolItBlock["System"],
                              MyToolItSystem["Get/Set State"], 1, 0)
        msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["STU1"],
                                    MyToolItNetworkNr["STU1"], [0])
        self.assertEqual("Error", self.Can.tWriteFrameWaitAck(msg)[0])
        # Test that it still works
        msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                    MyToolItNetworkNr["STU1"], [0])
        self.Can.tWriteFrameWaitAckRetries(msg, retries=0)

    """
    "Christmas Tree" packages
    """

    def test0057ChristmasTree(self):
        self.Can.Logger.Info("Error Request Frame from STU1 to STU1")
        cmd = self.Can.CanCmd(MyToolItBlock["System"],
                              MyToolItSystem["Get/Set State"], 1, 1)
        msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["STU1"],
                                    MyToolItNetworkNr["STU1"], [0])
        self.assertEqual("Error", self.Can.tWriteFrameWaitAck(msg)[0])
        self.Can.Logger.Info("Error Request Frame from SPU1 to STU1")
        cmd = self.Can.CanCmd(MyToolItBlock["System"],
                              MyToolItSystem["Get/Set State"], 1, 1)
        msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                    MyToolItNetworkNr["STU1"], [0])
        self.assertEqual("Error", self.Can.tWriteFrameWaitAck(msg)[0])
        self.Can.Logger.Info("Error Ack Frame from STU1 to STU1")
        cmd = self.Can.CanCmd(MyToolItBlock["System"],
                              MyToolItSystem["Get/Set State"], 0, 1)
        msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["STU1"],
                                    MyToolItNetworkNr["STU1"], [0])
        self.assertEqual("Error", self.Can.tWriteFrameWaitAck(msg)[0])
        self.Can.Logger.Info("Error Ack Frame from SPU1 to STU1")
        cmd = self.Can.CanCmd(MyToolItBlock["System"],
                              MyToolItSystem["Get/Set State"], 0, 1)
        msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                    MyToolItNetworkNr["STU1"], [0])
        self.assertEqual("Error", self.Can.tWriteFrameWaitAck(msg)[0])
        self.Can.Logger.Info("Ack Frame from STU1 to STU1")
        cmd = self.Can.CanCmd(MyToolItBlock["System"],
                              MyToolItSystem["Get/Set State"], 0, 0)
        msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["STU1"],
                                    MyToolItNetworkNr["STU1"], [0])
        self.assertEqual("Error", self.Can.tWriteFrameWaitAck(msg)[0])
        self.Can.Logger.Info("Ack Frame from SPU1 to STU1")
        cmd = self.Can.CanCmd(MyToolItBlock["System"],
                              MyToolItSystem["Get/Set State"], 0, 0)
        msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                    MyToolItNetworkNr["STU1"], [0])
        self.assertEqual("Error", self.Can.tWriteFrameWaitAck(msg)[0])

        # Test that it still works
        self.Can.Logger.Info("Normal Request to STU1")
        cmd = self.Can.CanCmd(MyToolItBlock["System"],
                              MyToolItSystem["Get/Set State"], 1, 0)
        msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                    MyToolItNetworkNr["STU1"], [0])
        self.Can.tWriteFrameWaitAckRetries(msg, retries=0)

    """
    Connect and disconnect device, check device number after each connect/disconnect to check correctness
    """

    def test0101BlueToothConncectDeviceNr(self):
        self.Can.Logger.Info(
            "Connect and get Device Number, disconnect and get device number")
        for i in range(0, 300):
            self.Can.Logger.Info("Loop Run: " + str(i))
            self.Can.Logger.Info("Connect")
            self.Can.vBlueToothConnectConnect(MyToolItNetworkNr["STU1"])
            for _j in range(0, BluetoothTime["DeviceConnect"]):
                deviceNumbers = self.Can.iBlueToothConnectTotalScannedDeviceNr(
                    MyToolItNetworkNr["STU1"])
                if (0 < deviceNumbers):
                    break
                time.sleep(1)
            self.Can.Logger.Info("Number of available devices: " +
                                 str(deviceNumbers))
            self.assertGreater(deviceNumbers, 0)
            if (False != self.Can.bBlueToothDisconnect(
                    MyToolItNetworkNr["STU1"])):
                self.Can.Logger.Error("Bluetooth STH connected")
                self.assertEqual(False, True)
            deviceNumbers = self.Can.iBlueToothConnectTotalScannedDeviceNr(
                MyToolItNetworkNr["STU1"])
            self.Can.Logger.Info("Number of available devices: " +
                                 str(deviceNumbers))
            self.assertEqual(deviceNumbers, 0)

    """
    Connect and disconnect to device 30 times
    """

    def test0102BlueToothConnectDisconnectDevice(self):
        self.Can.Logger.Info(
            "Bluetooth connect command and check connected command and disconnect command"
        )
        totalConnectDisconnectTime = 0
        totalRuns = 500
        for i in range(0, totalRuns):
            startTime = self.Can.Logger.getTimeStamp()
            self.Can.Logger.Info("Loop Run: " + str(i))
            self.vConnectSth1Dev0()
            if (False != self.Can.bConnected):
                self.Can.Logger.Info("Bluetooth STH connected")
            else:
                self.Can.Logger.Error("Bluetooth STH not Connected")
            self.assertNotEqual(False, self.Can.bConnected)
            self.Can.Logger.Info("Disconnect from Bluetooth Device")
            if (False != self.Can.bBlueToothDisconnect(
                    MyToolItNetworkNr["STU1"])):
                self.Can.Logger.Error("Bluetooth STH connected")
                self.assertEqual(False, True)
            else:
                self.Can.Logger.Info("Bluetooth STH not Connected")
            ConnectDissconnectTime = self.Can.Logger.getTimeStamp() - startTime
            self.Can.Logger.Info("Time to connect and disconnect: " +
                                 str(ConnectDissconnectTime) + "ms")
            totalConnectDisconnectTime += ConnectDissconnectTime
            time.sleep(1)
        totalConnectDisconnectTime /= totalRuns
        self.Can.Logger.Info("Average Time to connect and disconnect: " +
                             str(totalConnectDisconnectTime) + "ms")

    """
    Write name and get name (bluetooth command)
    """

    def test0103BlueToothName(self):
        self.Can.Logger.Info("Bluetooth name command to STH")
        for _i in range(0, 10):
            self.Can.Logger.Info("Loop Run: " + str(_i))
            self.vConnectSth1Dev0()
            time.sleep(1)
            self.Can.Logger.Info("Write Walther0")
            self.Can.vBlueToothNameWrite(MyToolItNetworkNr["STH1"], 0,
                                         "Walther0")
            self.Can.Logger.Info("Check Walther0")
            self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])
            time.sleep(1)
            self.Can.vBlueToothConnectConnect(MyToolItNetworkNr["STU1"])
            time.sleep(2)
            Name = self.Can.BlueToothNameGet(MyToolItNetworkNr["STU1"], 0)
            self.Can.Logger.Info("Received Name: " + Name)
            self.assertEqual("Walther0", Name)
            self.vConnectSth1Dev0()
            time.sleep(1)
            self.Can.Logger.Info("Write " + TestConfig["HolderName"])
            self.Can.vBlueToothNameWrite(MyToolItNetworkNr["STH1"], 0,
                                         TestConfig["HolderName"])
            self.Can.Logger.Info("Check " + TestConfig["HolderName"])
            self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])
            self.Can.vBlueToothConnectConnect(MyToolItNetworkNr["STU1"])
            time.sleep(2)
            time.sleep(BluetoothTime["Disconnect"])
            Name = self.Can.BlueToothNameGet(MyToolItNetworkNr["STU1"], 0)
            self.Can.Logger.Info("Received Name: " + Name)
            self.assertEqual(TestConfig["HolderName"], Name)
            self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])
            time.sleep(2)

    """
    Check that correct Bluetooth addresses are (correctly)  listed
    """

    def test0104BluetoothAddressDevices(self):
        for _i in range(0, 10):
            self.Can.vBlueToothConnectConnect(MyToolItNetworkNr["STU1"])
            endTime = time.time() + 5
            while 0 == self.Can.iBlueToothConnectTotalScannedDeviceNr(
                    MyToolItNetworkNr["STU1"]):
                if time.time() > endTime:
                    break
            time.sleep(0.5)
            devNrs = self.Can.iBlueToothConnectTotalScannedDeviceNr(
                MyToolItNetworkNr["STU1"])
            for devNr in range(0, devNrs):
                self.Can.Logger.Info("Device Number " + str(devNr))
                Address = self.Can.BlueToothAddressGet(
                    MyToolItNetworkNr["STU1"], devNr)
            self.Can.Logger.Info("Address: " + hex(Address))
            self.assertGreater(Address, 0)
            self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])

    """
    Check that correct Bluetooth RSSIs are listed
    """

    def test0105BluetoothRssi(self):
        for _i in range(0, 10):
            self.Can.vBlueToothConnectConnect(MyToolItNetworkNr["STU1"])
            endTime = time.time() + 5
            while 0 == self.Can.iBlueToothConnectTotalScannedDeviceNr(
                    MyToolItNetworkNr["STU1"]):
                if time.time() > endTime:
                    break
            time.sleep(0.5)
            Rssi = self.Can.BlueToothRssiGet(MyToolItNetworkNr["STU1"], 0)
            self.Can.Logger.Info("RSSI: " + str(int(Rssi)))
            self.assertNotEqual(Rssi, 127)
            self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])

    """
    Check that correct Bluetooth RSSIs change
    """

    def test0106BluetoothRssiChange(self):
        self.Can.vBlueToothConnectConnect(MyToolItNetworkNr["STU1"])
        endTime = time.time() + 5
        while 0 == self.Can.iBlueToothConnectTotalScannedDeviceNr(
                MyToolItNetworkNr["STU1"]):
            if time.time() > endTime:
                break
        time.sleep(0.5)
        Rssi = []
        for _i in range(0, 500):
            Rssi.append(self.Can.BlueToothRssiGet(MyToolItNetworkNr["STU1"],
                                                  0))
            self.Can.Logger.Info("RSSI: " + str(int(Rssi[-1])))
            self.assertNotEqual(Rssi, 127)
        self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])
        Rssi.sort()
        self.assertNotEqual(Rssi[1], Rssi[-2])

    """
    Check that correct Bluetooth name, addresses and RSSIs are (correctly) listed
    """

    def test0107BluetoothNameAddressRssi(self):
        self.Can.vBlueToothConnectConnect(MyToolItNetworkNr["STU1"])
        endTime = time.time() + 5
        while 0 == self.Can.iBlueToothConnectTotalScannedDeviceNr(
                MyToolItNetworkNr["STU1"]):
            if time.time() > endTime:
                break
        Name = self.Can.BlueToothNameGet(MyToolItNetworkNr["STU1"], 0)
        Address = self.Can.BlueToothAddressGet(MyToolItNetworkNr["STU1"], 0)
        Rssi = self.Can.BlueToothRssiGet(MyToolItNetworkNr["STU1"], 0)
        self.Can.Logger.Info("Name: " + Name)
        self.Can.Logger.Info("Address: " + hex(Address))
        self.Can.Logger.Info("RSSI: " + str(Rssi))
        self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])

    """
    Connect and disconnect to device 100 times, do it without time out, use connection check
    """

    def test0110BlueToothConnectDisconnectDevicePolling(self):
        self.Can.Logger.Info(
            "Bluetooth connect command and check connected command and disconnect command"
        )
        startTime = self.Can.Logger.getTimeStamp()
        for _i in range(0, 100):
            self.Can.vBlueToothConnectConnect(MyToolItNetworkNr["STU1"], 0)
            while 0 == self.Can.iBlueToothConnectTotalScannedDeviceNr(
                    MyToolItNetworkNr["STU1"]):
                pass
            self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])
        endTime = self.Can.Logger.getTimeStamp()
        ConnectDisconnectTime = endTime - startTime
        ConnectDisconnectTime /= 100
        self.Can.Logger.Info("Average Time for connect and disconnect: " +
                             str(ConnectDisconnectTime) + "ms")

    """
    Get Bluetooth Address
    """

    def test0111BlueToothAddress(self):
        self.Can.Logger.Info("Get Bluetooth Address")
        self.Can.Logger.Info(
            "BlueTooth Address: " +
            hex(self.Can.BlueToothAddress(MyToolItNetworkNr["STU1"])))

    """
    Connect to STH via Bluetooth Address
    """

    def test0112BlueToothConnectMac(self):
        iRssiLimit = -80
        self.Can.Logger.Info("Connect via bluetooth address")
        self.Can.Logger.Info("Connect command")
        self.Can.vBlueToothConnectConnect(MyToolItNetworkNr["STU1"])
        self.Can.Logger.Info("Sleep 4s such that device list is up2date")
        time.sleep(5)
        iRssi = -100
        iRetries = 100
        self.Can.Logger.Info("Rssi of device must be better than: " +
                             str(iRssiLimit))
        iDevPicked = -1
        iAddressReadback = -2
        while iRssiLimit > iRssi and 0 < iRetries:
            iRetries -= 1
            devNrs = self.Can.iBlueToothConnectTotalScannedDeviceNr(
                MyToolItNetworkNr["STU1"])
            self.Can.Logger.Info("Devises Found: " + str(devNrs))
            iDevPicked = randint(0, devNrs - 1)
            self.Can.Logger.Info("Try to pick device: " + str(iDevPicked))
            iRssi = self.Can.BlueToothRssiGet(MyToolItNetworkNr["STU1"],
                                              iDevPicked)
            self.Can.Logger.Info("Rssi: " + str(iRssi))
        if 0 < iRetries:
            iAddress = self.Can.BlueToothAddressGet(MyToolItNetworkNr["STU1"],
                                                    iDevPicked)
            iAddressReadback = self.Can.iBlueToothConnect2MacAddr(
                MyToolItNetworkNr["STU1"], iAddress)
        self.Can.Logger.Info("Try to get Address: " + hex(iAddress))
        self.Can.Logger.Info("Taken Address: " + hex(iAddressReadback))
        self.assertEqual(iAddressReadback, iAddress)
        self.Can.bBlueToothCheckConnect(MyToolItNetworkNr["STU1"])
        self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])

    """
    Change Device Name of STU
    """

    def test0113DeviceNameChangeSTU(self):
        self.Can.Logger.Info("Bluetooth name command to STU")
        for _i in range(0, 10):
            self.Can.Logger.Info("Loop Run: " + str(_i))
            self.Can.Logger.Info("Write Walther0")
            self.Can.vBlueToothNameWrite(MyToolItNetworkNr["STU1"],
                                         BlueToothDeviceNr["Self"], "Walther0")
            self.Can.Logger.Info("Check Walther0")
            Name = self.Can.BlueToothNameGet(MyToolItNetworkNr["STU1"],
                                             BlueToothDeviceNr["Self"])
            self.Can.Logger.Info("Received Name: " + Name)
            self.assertEqual("Walther0", Name)
            self.Can.Logger.Info("Write " + TestConfig["StuName"])
            self.Can.vBlueToothNameWrite(MyToolItNetworkNr["STU1"],
                                         BlueToothDeviceNr["Self"],
                                         TestConfig["StuName"])
            self.Can.Logger.Info("Check " + TestConfig["StuName"])
            self._resetStu()
            Name = self.Can.BlueToothNameGet(MyToolItNetworkNr["STU1"],
                                             BlueToothDeviceNr["Self"])
            self.Can.Logger.Info("Received Name: " + Name)
            self.assertEqual(TestConfig["StuName"], Name)
            time.sleep(1)

    """
    Send Message to STH without connecting. Assumed result = not receiving anything. This especially tests the routing functionality.
    """

    def test0201MyToolItTestNotConnectedAck(self):
        cmd = self.Can.CanCmd(MyToolItBlock["System"],
                              MyToolItSystem["Get/Set State"], 1, 0)
        msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                    MyToolItNetworkNr["STH1"], [0])
        self.Can.Logger.Info("Write Message")
        lastIndex = self.Can.GetReadArrayIndex()
        self.Can.WriteFrame(msg)
        self.Can.Logger.Info("Wait 2000ms")
        time.sleep(2)
        self.assertEqual(self.Can.GetReadArrayIndex(), lastIndex)

    """
    Send Message to STH with connecting. Assumed result = receive correct ack. This especially tests the routing functionality.
    """

    def test0202MyToolItTestAck(self):
        expectedData = ActiveState()
        expectedData.asbyte = 0
        expectedData.b.u2NodeState = NodeState["Application"]
        expectedData.b.u3NetworkState = NetworkState["Operating"]
        self.vConnectSth1Dev0()
        time.sleep(3)
        cmd = self.Can.CanCmd(MyToolItBlock["System"],
                              MyToolItSystem["Get/Set State"], 1, 0)
        msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                    MyToolItNetworkNr["STH1"], [0])
        self.Can.Logger.Info("Write Message")
        self.Can.WriteFrame(msg)
        waitTime = 1
        self.Can.Logger.Info("Wait " + str(waitTime) + "s")
        time.sleep(waitTime)
        cmd = self.Can.CanCmd(MyToolItBlock["System"],
                              MyToolItSystem["Get/Set State"], 0, 0)
        msgAckExpected = self.Can.CanMessage20(cmd, MyToolItNetworkNr["STH1"],
                                               MyToolItNetworkNr["SPU1"],
                                               [expectedData.asbyte])
        self.Can.Logger.Info("Send ID: " + hex(msg.ID) + "; Expected ID: " +
                             hex(msgAckExpected.ID) + "; Received ID: " +
                             hex(self.Can.getReadMessage(-1).ID))
        self.Can.Logger.Info("Send Data: " + hex(0) + "; Expected Data: " +
                             hex(expectedData.asbyte) + "; Received Data: " +
                             hex(self.Can.getReadMessage(-1).DATA[0]))
        self.assertEqual(hex(msgAckExpected.ID),
                         hex(self.Can.getReadMessage(-1).ID))
        self.assertEqual(hex(msgAckExpected.DATA[0]),
                         hex(self.Can.getReadMessage(-1).DATA[0]))
        self.Can.tWriteFrameWaitAckRetries(msg, retries=0)
        self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])

    """
    Send Message to STH with connecting. Assumed result = receive correct ack. This especially tests the routing functionality.
    """

    def test0203MyToolItTestWrongReceiver(self):
        self.Can.vBlueToothConnectConnect(MyToolItNetworkNr["STU1"])
        for _i in range(0, BluetoothTime["Connect"]):
            self.Can.Logger.Info("Device Connect to number 0")
            if False != self.Can.bBlueToothConnectDeviceConnect(
                    MyToolItNetworkNr["STU1"], 0):
                break
            time.sleep(1)
        for _i in range(0, BluetoothTime["Connect"]):
            if (False != self.Can.bBlueToothCheckConnect(
                    MyToolItNetworkNr["STU1"])):
                break
            else:
                time.sleep(1)
        time.sleep(3)
        cmd = self.Can.CanCmd(MyToolItBlock["System"],
                              MyToolItSystem["Get/Set State"], 1, 0)
        for i in range(MyToolItNetworkNr["STH2"], 32):
            if (MyToolItNetworkNr["STU1"] != i):
                msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"], i,
                                            [0])
                ack = self.Can.tWriteFrameWaitAck(msg)
                self.assertEqual("Error", ack[0])

        # Test that it still works
        msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                    MyToolItNetworkNr["STH1"], [0])
        self.Can.tWriteFrameWaitAckRetries(msg, retries=0)

    """ Send Multiple Frames without waiting for an ACK via routing, do ACK after 100 times send flooding to check functionality"""

    def test0204RoutingMultiSend(self):
        self.Can.Logger.Info(
            "Send command 100 times over STU to STH, check number of write/reads and do ack test at the end; do that for 1000 times"
        )
        self.Can.vBlueToothConnectConnect(MyToolItNetworkNr["STU1"])
        for _i in range(0, BluetoothTime["Connect"]):
            self.Can.Logger.Info("Device Connect to number 0")
            if False != self.Can.bBlueToothConnectDeviceConnect(
                    MyToolItNetworkNr["STU1"], 0):
                break
            time.sleep(1)
        for _i in range(0, BluetoothTime["Connect"]):
            if (False != self.Can.bBlueToothCheckConnect(
                    MyToolItNetworkNr["STU1"])):
                break
            else:
                time.sleep(1)
        time.sleep(3)
        for i in range(1, 101):
            self.Can.Logger.Info("Received Index: " +
                                 str(self.Can.GetReadArrayIndex()))
            self.Can.Logger.Info("Run: " + str(i))
            for _j in range(1, 101):
                if (1 == randint(0, 1)):
                    cmd = self.Can.CanCmd(MyToolItBlock["System"],
                                          MyToolItSystem["Get/Set State"], 1,
                                          0)
                    message = self.Can.CanMessage20(cmd,
                                                    MyToolItNetworkNr["SPU1"],
                                                    MyToolItNetworkNr["STH1"],
                                                    [0])
                else:
                    cmd = self.Can.CanCmd(MyToolItBlock["System"],
                                          MyToolItSystem["Node Status"], 1, 0)
                    message = self.Can.CanMessage20(cmd,
                                                    MyToolItNetworkNr["SPU1"],
                                                    MyToolItNetworkNr["STH1"],
                                                    [0, 0, 0, 0, 0, 0, 0, 0])
                self.Can.WriteFrame(message)
            self.Can.reset()
            time.sleep(0.25)
            self.Can.tWriteFrameWaitAckRetries(message, retries=0)

    """ Send Multiple Frames with waiting for an ACK with routing: Send->Ack->Send->Ack"""

    def test0205RoutingMultiSendAck(self):
        self.Can.Logger.Info(
            "Send and get ACK for 10000 times AND do it with two messages randomly "
        )
        self.Can.vBlueToothConnectConnect(MyToolItNetworkNr["STU1"])
        for _i in range(0, BluetoothTime["Connect"]):
            self.Can.Logger.Info("Device Connect to number 0")
            if False != self.Can.bBlueToothConnectDeviceConnect(
                    MyToolItNetworkNr["STU1"], 0):
                break
            time.sleep(1)
        for _i in range(0, BluetoothTime["Connect"]):
            if (False != self.Can.bBlueToothCheckConnect(
                    MyToolItNetworkNr["STU1"])):
                break
            else:
                time.sleep(1)
        time.sleep(3)
        for i in range(1, 1001):
            self.Can.Logger.Info("Received Index: " +
                                 str(self.Can.GetReadArrayIndex()))
            self.Can.Logger.Info("Run: " + str(i))
            if (1 == randint(0, 1)):
                cmd = self.Can.CanCmd(MyToolItBlock["System"],
                                      MyToolItSystem["Get/Set State"], 1, 0)
                msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                            MyToolItNetworkNr["STH1"], [0])
            else:
                cmd = self.Can.CanCmd(MyToolItBlock["System"],
                                      MyToolItSystem["Node Status"], 1, 0)
                msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                            MyToolItNetworkNr["STH1"],
                                            [0, 0, 0, 0, 0, 0, 0, 0])
            self.assertNotEqual("bError", self.Can.tWriteFrameWaitAck(msg))

    """ Send Multiple Frames with waiting for an ACK: Send->Ack->Send->Ack with routing, this also do a retry, tests the test framework - Multiple Messages"""

    def test0206RoutingMultiSendAckRetries(self):
        self.Can.Logger.Info(
            "Send and get ACK for 10000 times AND do it with two messages randomly "
        )
        self.Can.vBlueToothConnectConnect(MyToolItNetworkNr["STU1"])
        for _i in range(0, BluetoothTime["Connect"]):
            self.Can.Logger.Info("Device Connect to number 0")
            if False != self.Can.bBlueToothConnectDeviceConnect(
                    MyToolItNetworkNr["STU1"], 0):
                break
            time.sleep(1)
        for _i in range(0, BluetoothTime["Connect"]):
            if (False != self.Can.bBlueToothCheckConnect(
                    MyToolItNetworkNr["STU1"])):
                break
            else:
                time.sleep(1)
        time.sleep(3)
        for i in range(1, 1001):
            self.Can.Logger.Info("Received Index: " +
                                 str(self.Can.GetReadArrayIndex()))
            self.Can.Logger.Info("Run: " + str(i))
            if (1 == randint(0, 1)):
                cmd = self.Can.CanCmd(MyToolItBlock["System"],
                                      MyToolItSystem["Get/Set State"], 1, 0)
                msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                            MyToolItNetworkNr["STH1"], [0])
            else:
                cmd = self.Can.CanCmd(MyToolItBlock["System"],
                                      MyToolItSystem["Node Status"], 1, 0)
                msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                            MyToolItNetworkNr["STH1"],
                                            [0, 0, 0, 0, 0, 0, 0, 0])
            self.assertNotEqual(
                "bError", self.Can.tWriteFrameWaitAckRetries(msg, retries=0))
        """ Send Multiple Frames with waiting for an ACK: Send->Ack->Send->Ack with routing, this also do a retry, tests the test framework - Single Message"""

    def test0207RoutingMultiSendSingleAckRetries(self):
        self.Can.Logger.Info(
            "Send and get ACK for 10000 times AND do it with two messages randomly "
        )
        self.Can.vBlueToothConnectConnect(MyToolItNetworkNr["STU1"])
        for _i in range(0, BluetoothTime["Connect"]):
            self.Can.Logger.Info("Device Connect to number 0")
            if False != self.Can.bBlueToothConnectDeviceConnect(
                    MyToolItNetworkNr["STU1"], 0):
                break
            time.sleep(1)
        for _i in range(0, BluetoothTime["Connect"]):
            if (False != self.Can.bBlueToothCheckConnect(
                    MyToolItNetworkNr["STU1"])):
                break
            else:
                time.sleep(1)
        time.sleep(3)
        for i in range(1, 1001):
            self.Can.Logger.Info("Received Index: " +
                                 str(self.Can.GetReadArrayIndex()))
            self.Can.Logger.Info("Run: " + str(i))
            cmd = self.Can.CanCmd(MyToolItBlock["System"],
                                  MyToolItSystem["Node Status"], 1, 0)
            msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                        MyToolItNetworkNr["STH1"],
                                        [0, 0, 0, 0, 0, 0, 0, 0])
            self.assertNotEqual(
                "bError", self.Can.tWriteFrameWaitAckRetries(msg, retries=0))

    """
    Send addressing same sender and receiver via Routing
    """

    def test0208RoutingSenderReceiver(self):
        self.Can.Logger.Info(
            "Connect to STH and send message with STH1=sender/receiver")
        self.Can.vBlueToothConnectConnect(MyToolItNetworkNr["STU1"])
        for _i in range(0, BluetoothTime["Connect"]):
            self.Can.Logger.Info("Device Connect to number 0")
            if False != self.Can.bBlueToothConnectDeviceConnect(
                    MyToolItNetworkNr["STU1"], 0):
                break
            time.sleep(1)
        for _i in range(0, BluetoothTime["Connect"]):
            if (False != self.Can.bBlueToothCheckConnect(
                    MyToolItNetworkNr["STU1"])):
                break
            else:
                time.sleep(1)
        time.sleep(3)
        cmd = self.Can.CanCmd(MyToolItBlock["System"],
                              MyToolItSystem["Get/Set State"], 1, 0)
        msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["STH1"],
                                    MyToolItNetworkNr["STH1"], [0])
        self.assertEqual("Error", self.Can.tWriteFrameWaitAck(msg)[0])
        # Test that it still works
        msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                    MyToolItNetworkNr["STH1"], [0])
        self.Can.tWriteFrameWaitAckRetries(msg, retries=0, bErrorExit=False)

    """
    "Christmas Tree" packages via routing
    """

    def test0209RoutingChristmasTree(self):
        self.Can.Logger.Info("Error Request Frame from STH1 to STH1")
        self.Can.vBlueToothConnectConnect(MyToolItNetworkNr["STU1"])
        for _i in range(0, BluetoothTime["Connect"]):
            self.Can.Logger.Info("Device Connect to number 0")
            if False != self.Can.bBlueToothConnectDeviceConnect(
                    MyToolItNetworkNr["STU1"], 0):
                break
            time.sleep(1)
        for _i in range(0, BluetoothTime["Connect"]):
            if (False != self.Can.bBlueToothCheckConnect(
                    MyToolItNetworkNr["STU1"])):
                break
            else:
                time.sleep(1)
        time.sleep(3)
        cmd = self.Can.CanCmd(MyToolItBlock["System"],
                              MyToolItSystem["Get/Set State"], 1, 1)
        msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["STH1"],
                                    MyToolItNetworkNr["STH1"], [0])
        self.assertEqual("Error", self.Can.tWriteFrameWaitAck(msg)[0])
        self.Can.Logger.Info("Error Request Frame from SPU1 to STH1")
        cmd = self.Can.CanCmd(MyToolItBlock["System"],
                              MyToolItSystem["Get/Set State"], 1, 1)
        msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                    MyToolItNetworkNr["STH1"], [0])
        self.assertEqual("Error", self.Can.tWriteFrameWaitAck(msg)[0])
        self.Can.Logger.Info("Error Ack Frame from STH1 to STH1")
        cmd = self.Can.CanCmd(MyToolItBlock["System"],
                              MyToolItSystem["Get/Set State"], 0, 1)
        msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["STH1"],
                                    MyToolItNetworkNr["STH1"], [0])
        self.assertEqual("Error", self.Can.tWriteFrameWaitAck(msg)[0])
        self.Can.Logger.Info("Error Ack Frame from SPU1 to STH1")
        cmd = self.Can.CanCmd(MyToolItBlock["System"],
                              MyToolItSystem["Get/Set State"], 0, 1)
        msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                    MyToolItNetworkNr["STH1"], [0])
        self.assertEqual("Error", self.Can.tWriteFrameWaitAck(msg)[0])
        self.Can.Logger.Info("Ack Frame from STH1 to STH1")
        cmd = self.Can.CanCmd(MyToolItBlock["System"],
                              MyToolItSystem["Get/Set State"], 0, 0)
        msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["STH1"],
                                    MyToolItNetworkNr["STH1"], [0])
        self.assertEqual("Error", self.Can.tWriteFrameWaitAck(msg)[0])
        self.Can.Logger.Info("Ack Frame from SPU1 to STH1")
        cmd = self.Can.CanCmd(MyToolItBlock["System"],
                              MyToolItSystem["Get/Set State"], 0, 0)
        msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                    MyToolItNetworkNr["STH1"], [0])
        self.assertEqual("Error", self.Can.tWriteFrameWaitAck(msg)[0])

        # Test that it still works
        self.Can.Logger.Info("Normal Request to STH1")
        cmd = self.Can.CanCmd(MyToolItBlock["System"],
                              MyToolItSystem["Get/Set State"], 1, 0)
        msg = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                    MyToolItNetworkNr["STH1"], [0])
        self.Can.tWriteFrameWaitAckRetries(msg, retries=0)

    """
    Check Power On and Power Off Counters
    """

    def test0700StatisticsPowerOnCounterPowerOffCounter(self):
        PowerOnOff1 = self.Can.statisticalData(MyToolItNetworkNr["STU1"],
                                               MyToolItStatData["PocPof"])
        PowerOn1 = byte_list_to_int(PowerOnOff1[:4])
        PowerOff1 = byte_list_to_int(PowerOnOff1[4:])
        self._resetStu()
        PowerOnOff2 = self.Can.statisticalData(MyToolItNetworkNr["STU1"],
                                               MyToolItStatData["PocPof"])
        PowerOn2 = byte_list_to_int(PowerOnOff2[:4])
        PowerOff2 = byte_list_to_int(PowerOnOff2[4:])
        self.Can.Logger.Info("PowerOnOff Payload before STU Reset: " +
                             payload2Hex(PowerOnOff1))
        self.Can.Logger.Info("Power On Counter before STU Reset: " +
                             str(PowerOn1))
        self.Can.Logger.Info("Power Off Counter before STU Reset: " +
                             str(PowerOff1))
        self.Can.Logger.Info("PowerOnOff Payload after STU Reset: " +
                             payload2Hex(PowerOnOff2))
        self.Can.Logger.Info("Power On Counter after STU Reset: " +
                             str(PowerOn2))
        self.Can.Logger.Info("Power Off Counter after STU Reset: " +
                             str(PowerOff2))
        self.assertEqual(PowerOn1 + 1, PowerOn2)
        self.assertEqual(PowerOff1, PowerOff2)

    """
    Check Operating Seconds
    """

    def test0701StatisticsOperatingSeconds(self):
        u32EepromWriteRequestCounterTestStart = self.Can.u32EepromWriteRequestCounter(
            MyToolItNetworkNr["STU1"])
        OperatingSeconds = self.Can.statisticalData(
            MyToolItNetworkNr["STU1"], MyToolItStatData["OperatingTime"])
        SecondsReset1 = byte_list_to_int(OperatingSeconds[:4])
        SecondsOveral1 = byte_list_to_int(OperatingSeconds[4:])
        time.sleep(60)
        OperatingSeconds = self.Can.statisticalData(
            MyToolItNetworkNr["STU1"], MyToolItStatData["OperatingTime"])
        SecondsReset2 = byte_list_to_int(OperatingSeconds[:4])
        SecondsOveral2 = byte_list_to_int(OperatingSeconds[4:])
        self._resetStu()
        OperatingSeconds = self.Can.statisticalData(
            MyToolItNetworkNr["STU1"], MyToolItStatData["OperatingTime"])
        SecondsReset3 = byte_list_to_int(OperatingSeconds[:4])
        SecondsOveral3 = byte_list_to_int(OperatingSeconds[4:])
        time.sleep(60 * 31)
        OperatingSeconds = self.Can.statisticalData(
            MyToolItNetworkNr["STU1"], MyToolItStatData["OperatingTime"])
        SecondsReset4 = byte_list_to_int(OperatingSeconds[:4])
        SecondsOveral4 = byte_list_to_int(OperatingSeconds[4:])
        self.Can.Logger.Info("Operating Seconds since Reset: " +
                             str(SecondsReset1))
        self.Can.Logger.Info("Operating Seconds since frist PowerOn: " +
                             str(SecondsOveral1))
        self.Can.Logger.Info("Operating Seconds since Reset(+1 minute): " +
                             str(SecondsReset2))
        self.Can.Logger.Info(
            "Operating Seconds since frist PowerOn(+1minute): " +
            str(SecondsOveral2))
        self.Can.Logger.Info(
            "Operating Seconds since Reset(After Disconnect/Connect): " +
            str(SecondsReset3))
        self.Can.Logger.Info(
            "Operating Seconds since frist PowerOn(After Disconnect/Connect): "
            + str(SecondsOveral3))
        self.Can.Logger.Info("Operating Seconds since Reset(+30 minutes): " +
                             str(SecondsReset4))
        self.Can.Logger.Info(
            "Operating Seconds since frist PowerOn(+30minutes): " +
            str(SecondsOveral4))
        u32EepromWriteRequestCounterTestEnd = self.Can.u32EepromWriteRequestCounter(
            MyToolItNetworkNr["STU1"])
        u32EepromWriteRequsts = u32EepromWriteRequestCounterTestEnd - u32EepromWriteRequestCounterTestStart
        self.Can.Logger.Info("EEPROM Write Requests during tests: " +
                             str(u32EepromWriteRequsts))
        self.assertEqual(1,
                         u32EepromWriteRequsts)  # +1 due to operating seconds
        self.assertLess(SecondsReset1, 10)
        self.assertGreater(SecondsReset2, 60)
        self.assertLess(SecondsReset2, 70)
        self.assertLess(SecondsReset3, 10)
        self.assertGreater(SecondsReset4, 60 * 31 - 20)
        self.assertLess(SecondsReset4, 20 + 60 * 31)
        self.assertEqual(SecondsOveral1, SecondsOveral2)
        self.assertLess(SecondsOveral1 + 58, SecondsOveral3)
        self.assertGreater(SecondsOveral1 + 63, SecondsOveral3)
        self.assertLess(SecondsOveral1 + 58, SecondsOveral3)
        self.assertGreater(SecondsOveral1 + 63, SecondsOveral3)
        self.assertLess(SecondsOveral3 + 30 * 60 - 3, SecondsOveral4)
        self.assertGreater(SecondsOveral3 + 30 * 60 + 4, SecondsOveral4)

    """
    Check Watchdog counter to not increment
    """

    def test0702WdogNotIncrementing(self):
        WDogCounter1 = self._StuWDog()
        self._resetStu()
        WDogCounter2 = self._StuWDog()
        self._resetStu()
        self.Can.Logger.Info("Watchdog Counter at start: " + str(WDogCounter1))
        self.Can.Logger.Info("Watchdog Counter after reset: " +
                             str(WDogCounter2))
        self.assertEqual(WDogCounter1, WDogCounter2)

    """
    Check ProductionDate
    """

    def test0703ProductionDate(self):
        sProductionDate = self.Can.statisticalData(
            MyToolItNetworkNr["STU1"], MyToolItStatData["ProductionDate"])
        sProductionDate = sArray2String(sProductionDate)
        self.Can.Logger.Info("Production Date: " + sProductionDate)
        self.assertEqual(TestConfig["ProductionDate"], sProductionDate)

    """
    Check EEPROM Read/Write - Deterministic data
    """

    def test0750StatisticPageWriteReadDeteministic(self):
        uLoopRuns = 25
        time.sleep(2)
        u32EepromWriteRequestCounterTestStart = self.Can.u32EepromWriteRequestCounter(
            MyToolItNetworkNr["STU1"])
        self.Can.Logger.Info("Save up EEPROM content")
        startData = []
        for offset in range(0, 256, 4):
            index = self.Can.cmdSend(
                MyToolItNetworkNr["STU1"], MyToolItBlock["EEPROM"],
                MyToolItEeprom["Read"],
                [EepromPage["Statistics"], 0xFF & offset, 4, 0, 0, 0, 0, 0])
            dataReadBack = self.Can.getReadMessageData(index)
            startData.extend(dataReadBack[4:])

        # Test it self
        for _i in range(0, uLoopRuns):
            self.Can.Logger.Info("Next Run 12 Writes and Reads")
            self.Can.u32EepromWriteRequestCounter(MyToolItNetworkNr["STU1"])
            self.vEepromWritePage(EepromPage["Statistics"], 0xAA)
            self.vEepromReadPage(EepromPage["Statistics"], 0xAA)
            self.vEepromWritePage(EepromPage["Statistics"], 0xFF)
            self.vEepromReadPage(EepromPage["Statistics"], 0xFF)
            self.vEepromWritePage(EepromPage["Statistics"], 0xAA)
            self.vEepromReadPage(EepromPage["Statistics"], 0xAA)
            self.vEepromWritePage(EepromPage["Statistics"], 0x00)
            self.vEepromReadPage(EepromPage["Statistics"], 0x00)
            self.vEepromWritePage(EepromPage["Statistics"], 0xAA)
            self.vEepromReadPage(EepromPage["Statistics"], 0xAA)
            self.vEepromWritePage(EepromPage["Statistics"], 0x55)
            self.vEepromReadPage(EepromPage["Statistics"], 0x55)
            self.vEepromWritePage(EepromPage["Statistics"], 0xAA)
            self.vEepromReadPage(EepromPage["Statistics"], 0xAA)
            self.vEepromWritePage(EepromPage["Statistics"], 0x55)
            self.vEepromReadPage(EepromPage["Statistics"], 0x55)
            self.vEepromWritePage(EepromPage["Statistics"], 0x00)
            self.vEepromReadPage(EepromPage["Statistics"], 0x00)
            self.vEepromWritePage(EepromPage["Statistics"], 0x55)
            self.vEepromReadPage(EepromPage["Statistics"], 0x55)
            self.vEepromWritePage(EepromPage["Statistics"], 0xFF)
            self.vEepromReadPage(EepromPage["Statistics"], 0xFF)
            self.vEepromWritePage(EepromPage["Statistics"], 0x55)
            self.vEepromReadPage(EepromPage["Statistics"], 0x55)

        # Write Back Page
        timeStamp = self.Can.get_elapsed_time()
        for offset in range(0, 256, 4):
            payload = [EepromPage["Statistics"], 0xFF & offset, 4, 0]
            payload.extend(startData[offset:offset + 4])
            self.Can.cmdSend(MyToolItNetworkNr["STU1"],
                             MyToolItBlock["EEPROM"], MyToolItEeprom["Write"],
                             payload)
        self.Can.Logger.Info("Page Write Time: " +
                             str(self.Can.get_elapsed_time() - timeStamp) +
                             "ms")
        u32EepromWriteRequestCounterTestEnd = self.Can.u32EepromWriteRequestCounter(
            MyToolItNetworkNr["STU1"])
        u32EepromWriteRequsts = u32EepromWriteRequestCounterTestEnd - u32EepromWriteRequestCounterTestStart
        self.Can.Logger.Info("EEPROM Write Requests during tests: " +
                             str(u32EepromWriteRequsts))
        self.assertEqual(u32EepromWriteRequestCounterTestStart + 1,
                         u32EepromWriteRequestCounterTestEnd
                         )  # +1 due to incrementing at first write

    """
    Check EEPROM Read/Write - Deterministic data
    """

    def test0751StatisticPageWriteReadRandom(self):
        uLoopRuns = 100
        u32EepromWriteRequestCounterTestStart = self.Can.u32EepromWriteRequestCounter(
            MyToolItNetworkNr["STU1"])
        self.Can.Logger.Info("Save up EEPROM content")
        startData = []
        for offset in range(0, 256, 4):
            index = self.Can.cmdSend(
                MyToolItNetworkNr["STU1"], MyToolItBlock["EEPROM"],
                MyToolItEeprom["Read"],
                [EepromPage["Product Data"], 0xFF & offset, 4, 0, 0, 0, 0, 0])
            dataReadBack = self.Can.getReadMessageData(index)
            startData.extend(dataReadBack[4:])

        # Test it self
        for _i in range(0, uLoopRuns):
            self.Can.Logger.Info("Next random Writes and Reads")
            self.Can.u32EepromWriteRequestCounter(MyToolItNetworkNr["STU1"])
            au8ReadCheck = []
            for offset in range(0, 256, 4):
                au8Content = []
                for _j in range(0, 4):
                    u8Byte = int(random.random() * 0xFF)
                    au8Content.append(u8Byte)
                au8ReadCheck.extend(au8Content)
                au8Payload = [EepromPage["Product Data"], 0xFF & offset, 4, 0
                              ] + au8Content
                self.Can.cmdSend(MyToolItNetworkNr["STU1"],
                                 MyToolItBlock["EEPROM"],
                                 MyToolItEeprom["Write"], au8Payload)
            for offset in range(0, 256, 4):
                au8Payload = [
                    EepromPage["Product Data"], 0xFF & offset, 4, 0, 0, 0, 0, 0
                ]
                index = self.Can.cmdSend(MyToolItNetworkNr["STU1"],
                                         MyToolItBlock["EEPROM"],
                                         MyToolItEeprom["Read"], au8Payload)
                dataReadBack = self.Can.getReadMessageData(index)
                self.assertEqual(dataReadBack[4:],
                                 au8ReadCheck[offset:offset + 4])
            self.Can.Logger.Info("Fin random Writes and Reads")
            self.Can.u32EepromWriteRequestCounter(MyToolItNetworkNr["STU1"])

        # Write Back Page
        timeStamp = self.Can.get_elapsed_time()
        for offset in range(0, 256, 4):
            payload = [EepromPage["Product Data"], 0xFF & offset, 4, 0]
            payload.extend(startData[offset:offset + 4])
            self.Can.cmdSend(MyToolItNetworkNr["STU1"],
                             MyToolItBlock["EEPROM"], MyToolItEeprom["Write"],
                             payload)
        self.Can.Logger.Info("Page Write Time: " +
                             str(self.Can.get_elapsed_time() - timeStamp) +
                             "ms")
        self.Can.u32EepromWriteRequestCounter(MyToolItNetworkNr["STU1"])
        u32EepromWriteRequestCounterTestEnd = self.Can.u32EepromWriteRequestCounter(
            MyToolItNetworkNr["STU1"])
        u32EepromWriteRequsts = u32EepromWriteRequestCounterTestEnd - u32EepromWriteRequestCounterTestStart
        self.Can.Logger.Info("EEPROM Write Requests during tests: " +
                             str(u32EepromWriteRequsts))
        self.assertEqual(u32EepromWriteRequestCounterTestStart + 1,
                         u32EepromWriteRequestCounterTestEnd
                         )  # +1 due to incrementing at first write

    """
    Check that page switched do not yield to Writing EEPROM
    """

    def test0753EepromWriteRequestCounterPageSwitches(self):
        time.sleep(1)
        uLoopRuns = 5
        u32EepromWriteRequestCounterTestStart = self.Can.u32EepromWriteRequestCounter(
            MyToolItNetworkNr["STU1"])
        for _i in range(0, uLoopRuns):
            for sPage in EepromPage:
                self.Can.Logger.Info("Next Page")
                for offset in range(0, 256, 4):
                    au8Payload = [
                        EepromPage[sPage], 0xFF & offset, 4, 0, 0, 0, 0, 0
                    ]
                    self.Can.cmdSend(MyToolItNetworkNr["STU1"],
                                     MyToolItBlock["EEPROM"],
                                     MyToolItEeprom["Read"], au8Payload)
        u32EepromWriteRequestCounterTestEnd = self.Can.u32EepromWriteRequestCounter(
            MyToolItNetworkNr["STU1"])
        u32EepromWriteRequsts = u32EepromWriteRequestCounterTestEnd - u32EepromWriteRequestCounterTestStart
        self.Can.Logger.Info("EEPROM Write Requests during tests: " +
                             str(u32EepromWriteRequsts))
        self.assertEqual(u32EepromWriteRequestCounterTestStart,
                         u32EepromWriteRequestCounterTestEnd
                         )  # +1 due to incrementing at first write

    """
    Check that page switched with previews writes yield into to Writing EEPROM with the correct number of wirtes
    """

    def test0754EepromWriteRequestCounterPageWriteSwitches(self):
        time.sleep(1)
        uLoopRuns = 5
        uPageStart = 10
        uPageRuns = 6
        u32EepromWriteRequestCounterTestStart = self.Can.u32EepromWriteRequestCounter(
            MyToolItNetworkNr["STU1"])
        for _i in range(0, uLoopRuns):
            for uPageOffset in range(0, uPageRuns):
                self.Can.Logger.Info("Next Page")
                self.Can.u32EepromWriteRequestCounter(
                    MyToolItNetworkNr["STU1"])
                uPage = uPageOffset + uPageStart
                au8Payload = [uPage, 12, 4, 0, 0, 0, 0, 0]
                self.Can.cmdSend(MyToolItNetworkNr["STU1"],
                                 MyToolItBlock["EEPROM"],
                                 MyToolItEeprom["Write"],
                                 au8Payload,
                                 log=False)
                uPage = uPageOffset + 2
                uPage %= uPageRuns
                uPage += uPageStart
                au8Payload = [uPage, 12, 4, 0, 0, 0, 0, 0]
                self.Can.cmdSend(MyToolItNetworkNr["STU1"],
                                 MyToolItBlock["EEPROM"],
                                 MyToolItEeprom["Read"],
                                 au8Payload,
                                 log=False)
        u32EepromWriteRequestCounterTestEnd = self.Can.u32EepromWriteRequestCounter(
            MyToolItNetworkNr["STU1"])
        u32EepromWriteRequsts = u32EepromWriteRequestCounterTestEnd - u32EepromWriteRequestCounterTestStart
        self.Can.Logger.Info("EEPROM Write Requests during tests: " +
                             str(u32EepromWriteRequsts))
        self.assertEqual(uPageRuns * uLoopRuns, u32EepromWriteRequsts)

    """
    Test that nothing happens when sending Command 0x0000 to STU1
    """

    def test0900ErrorCmdVerbotenStu1(self):
        cmd = self.Can.CanCmd(0, 0, 1, 0)
        message = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                        MyToolItNetworkNr["STU1"], [])
        msgAck = self.Can.tWriteFrameWaitAckRetries(message,
                                                    waitMs=1000,
                                                    retries=3,
                                                    bErrorExit=False)
        self.assertEqual("Error", msgAck)
        cmd = self.Can.CanCmd(0, 0, 1, 1)
        message = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                        MyToolItNetworkNr["STU1"], [])
        msgAck = self.Can.tWriteFrameWaitAckRetries(message,
                                                    waitMs=1000,
                                                    retries=3,
                                                    bErrorExit=False)
        self.assertEqual("Error", msgAck)
        cmd = self.Can.CanCmd(0, 0, 0, 0)
        message = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                        MyToolItNetworkNr["STU1"], [])
        msgAck = self.Can.tWriteFrameWaitAckRetries(message,
                                                    waitMs=1000,
                                                    retries=3,
                                                    bErrorExit=False)
        self.assertEqual("Error", msgAck)
        cmd = self.Can.CanCmd(0, 0, 0, 1)
        message = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                        MyToolItNetworkNr["STU1"], [])
        msgAck = self.Can.tWriteFrameWaitAckRetries(message,
                                                    waitMs=1000,
                                                    retries=3,
                                                    bErrorExit=False)
        self.assertEqual("Error", msgAck)

    """
    Test that nothing happens when sending Request(1) and Error(1) to STU1
    """

    def test0901ErrorRequestErrorStu1(self):
        cmd = self.Can.CanCmd(MyToolItBlock["System"], MyToolItSystem["Reset"],
                              1, 1)
        message = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                        MyToolItNetworkNr["STU1"], [])
        msgAck = self.Can.tWriteFrameWaitAckRetries(message,
                                                    waitMs=1000,
                                                    retries=3,
                                                    bErrorExit=False)
        self.assertEqual("Error", msgAck)
        cmd = self.Can.CanCmd(MyToolItBlock["Streaming"],
                              MyToolItStreaming["Acceleration"], 1, 1)
        message = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                        MyToolItNetworkNr["STU1"], [])
        msgAck = self.Can.tWriteFrameWaitAckRetries(message,
                                                    waitMs=1000,
                                                    retries=3,
                                                    bErrorExit=False)
        self.assertEqual("Error", msgAck)


if __name__ == "__main__":
    sLogLocation = sys.argv[1]
    sLogFile = sys.argv[2]
    sVersion = sys.argv[3]
    if '/' != sLogLocation[-1]:
        sLogLocation += '/'
    sLogFileLocation = sLogLocation + sLogFile
    sDirName = os.path.dirname(sLogFileLocation)
    sys.path.append(sDirName)

    if not os.path.exists(sDirName):
        os.makedirs(sDirName)
    with open(sLogFileLocation, "w") as f:
        runner = unittest.TextTestRunner(f)
        unittest.main(argv=['first-arg-is-ignored'], testRunner=runner)