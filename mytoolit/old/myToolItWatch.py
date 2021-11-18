import argparse
import multiprocessing
import socket
from time import sleep, time
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Optional

from can.interfaces.pcan.basic import PCAN_ERROR_OK, PCAN_ERROR_QOVERRUN
from netaddr import EUI

from mytoolit import __version__
from mytoolit.config import settings
from mytoolit.measurement.acceleration import convert_acceleration_adc_to_g
from mytoolit.measurement.storage import Storage
from mytoolit.old.network import Network
from mytoolit.old.MyToolItNetworkNumbers import MyToolItNetworkNr
from mytoolit.old.MyToolItCommands import (
    AdcAcquisitionTime,
    AdcOverSamplingRate,
    AdcReference,
    AtvcFormat,
    byte_list_to_int,
    calcSamplingRate,
    DataSets,
    int_to_mac_address,
    MyToolItBlock,
    MyToolItStreaming,
    Prescaler,
    SystemCommandBlueTooth,
    SystemCommandRouting,
)
from mytoolit.old.Plotter import vPlotter, tArray2Binary

Watch = {
    "DisplayTimeMax": 10,  # Maximum display time of graphical plot in seconds
    "DisplaySampleRateMs": 1000,  # Maximum Display Time in ms
    "DisplayBlockSize": 100,
    "AliveTimeOutMs":
    4000,  # Time Out after receiving no data in acquiring mode
}


class myToolItWatch():

    def __init__(self, *args, **kwargs):
        # Check if output directory exists and try to create it, if it does not
        # exist already
        try:
            settings.check_output_directory()
        except (NotADirectoryError, OSError) as error:
            raise error

        self.KeyBoardInterrupt = False
        self.bError = False
        self.iMsgLoss = 0
        self.iMsgsTotal = 0
        self.iMsgCounterLast = 0
        self.Can = Network('ICOc.log',
                           FreshLog=True,
                           sender=MyToolItNetworkNr["SPU1"],
                           receiver=MyToolItNetworkNr["STH1"])
        self.vSthAutoConnect(False)
        self.Can.Logger.Info("Start Time: {datetime.now().isoformat()}")
        self.vAccSet(True, False, False, 3)
        self.vDeviceNameSet('')
        self.vDeviceAddressSet("0")
        self.vAdcConfig(2, 8, 64)
        self.vAdcRefVConfig("VDD")
        self.vDisplayTime(10)
        self.vRunTime(0)
        self.vGraphInit(Watch["DisplaySampleRateMs"],
                        Watch["DisplayBlockSize"])
        self.Can.readThreadStop()
        # Set plotter host and port
        self.sPloterSocketHost = settings.gui.host
        self.iPloterSocketPort = settings.gui.port

        self.storage = None
        self.set_output_filename()

    def __exit__(self):
        if self.storage is not None:
            self.storage.close()
        self.guiProcessStop()
        self.Can.ReadThreadReset()
        if self.Can.bConnected:
            self._BlueToothStatistics()
            ReceiveFailCounter = self._RoutingInformation()
            self._statusWords()
            if ReceiveFailCounter > 0:
                self.bError = True
            self.Can.bBlueToothDisconnect(MyToolItNetworkNr["STU1"])
        if self.Can.bConnected:
            self.Can.readThreadStop()
        self.Can.Logger.Info("End Time Stamp")

        if self.bError:
            self.Can.Logger.Info("!!!!Error!!!!")
            print("!!!!Error!!!!")
        else:
            self.Can.Logger.Info("Fin")
        self.Can.__exit__()
        if self.bError:
            raise

    def set_output_filename(self, name: Optional[str] = None) -> None:
        """Set the (base) name of the HDF output file

        Parameters
        ----------

        name:
            A new (base) name for the output file

            If you set this parameter to `None`, then the most recently set
            filename will be used

        """

        filename = Path(settings.measurement.output.filename
                        ) if name is None else Path(name)
        if not filename.suffix:
            filename = filename.with_suffix(".hdf5")

        self.output_filename = filename

    def get_output_filepath(self) -> Path:
        """Get the filepath of the HDF output file

        The filepath returned by this method will always include a current
        timestamp to make sure that there are no conflicts with old output
        files.

        Returns
        -------

        The path to the current HDF file

        """

        directory = settings.output_directory()
        filename = self.output_filename
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filepath = directory.joinpath(
            f"{filename.stem}_{timestamp}{filename.suffix}")

        return filepath

    def _statusWords(self):
        self.Can.Logger.Info("STH Status Word: {}".format(
            self.Can.node_status(MyToolItNetworkNr["STH1"])))
        self.Can.Logger.Info("STU Status Word: {}".format(
            self.Can.node_status(MyToolItNetworkNr["STU1"])))

        status = self.Can.error_status(MyToolItNetworkNr["STH1"])
        if status.adc_overrun():
            self.bError = True
        self.Can.Logger.Info(f"STH Error Word: {status}")

        self.Can.Logger.Info("STU Error Word: {}".format(
            self.Can.error_status(MyToolItNetworkNr["STU1"])))

    def _BlueToothStatistics(self):
        SendCounter = self.Can.BlueToothCmd(
            MyToolItNetworkNr["STH1"], SystemCommandBlueTooth["SendCounter"])
        self.Can.Logger.Info("BlueTooth Send Counter(STH1): " +
                             str(SendCounter))
        Rssi = self.Can.BlueToothRssi(MyToolItNetworkNr["STH1"])
        self.Can.Logger.Info("BlueTooth Rssi(STH1): " + str(Rssi) + "dBm")
        SendCounter = self.Can.BlueToothCmd(
            MyToolItNetworkNr["STU1"], SystemCommandBlueTooth["SendCounter"])
        self.Can.Logger.Info("BlueTooth Send Counter(STU1): " +
                             str(SendCounter))
        ReceiveCounter = self.Can.BlueToothCmd(
            MyToolItNetworkNr["STU1"],
            SystemCommandBlueTooth["ReceiveCounter"])
        self.Can.Logger.Info("BlueTooth Receive Counter(STU1): " +
                             str(ReceiveCounter))
        Rssi = self.Can.BlueToothRssi(MyToolItNetworkNr["STU1"])
        self.Can.Logger.Info("BlueTooth Rssi(STU1): " + str(Rssi) + "dBm")

    def _RoutingInformationSthSend(self):
        self.iSthSendCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STH1"], SystemCommandRouting["SendCounter"],
            MyToolItNetworkNr["STU1"])
        self.Can.Logger.Info("STH1 - Send Counter(Port STU1): " +
                             str(self.iSthSendCounter))
        SendCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STH1"], SystemCommandRouting["SendFailCounter"],
            MyToolItNetworkNr["STU1"])
        self.Can.Logger.Info("STH1 - Send Fail Counter(Port STU1): " +
                             str(SendCounter))
        SendCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STH1"],
            SystemCommandRouting["SendLowLevelByteCounter"],
            MyToolItNetworkNr["STU1"])
        self.Can.Logger.Info("STH1 - Send Byte Counter(Port STU1): " +
                             str(SendCounter))

    def _RoutingInformationSthReceive(self):
        ReceiveCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STH1"], SystemCommandRouting["ReceiveCounter"],
            MyToolItNetworkNr["STU1"])
        self.Can.Logger.Info("STH1 - Receive Counter(Port STU1): " +
                             str(ReceiveCounter))
        ReceiveFailCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STH1"],
            SystemCommandRouting["ReceiveFailCounter"],
            MyToolItNetworkNr["STU1"])
        self.Can.Logger.Info("STH1 - Receive Fail Counter(Port STU1): " +
                             str(ReceiveFailCounter))
        ReceiveCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STH1"],
            SystemCommandRouting["ReceiveLowLevelByteCounter"],
            MyToolItNetworkNr["STU1"])
        self.Can.Logger.Info("STH1 - Receive Byte Counter(Port STU1): " +
                             str(ReceiveCounter))
        return ReceiveFailCounter

    def _RoutingInformationSth(self):
        self._RoutingInformationSthSend()
        ReceiveFailCounter = self._RoutingInformationSthReceive()
        return ReceiveFailCounter

    def _RoutingInformationStuPortSpuSend(self):
        self.iStuSendCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"], SystemCommandRouting["SendCounter"],
            MyToolItNetworkNr["SPU1"])
        self.Can.Logger.Info("STU1 - Send Counter(Port SPU1): " +
                             str(self.iStuSendCounter))
        SendCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"], SystemCommandRouting["SendFailCounter"],
            MyToolItNetworkNr["SPU1"])
        self.Can.Logger.Info("STU1 - Send Fail Counter(Port SPU1): " +
                             str(SendCounter))
        SendCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"],
            SystemCommandRouting["SendLowLevelByteCounter"],
            MyToolItNetworkNr["SPU1"])
        self.Can.Logger.Info("STU1 - Send Byte Counter(Port SPU1): " +
                             str(SendCounter))

    def _RoutingInformationStuPortSpuReceive(self):
        ReceiveCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"], SystemCommandRouting["ReceiveCounter"],
            MyToolItNetworkNr["SPU1"])
        self.Can.Logger.Info("STU1 - Receive Counter(Port SPU1): " +
                             str(ReceiveCounter))
        ReceiveFailCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"],
            SystemCommandRouting["ReceiveFailCounter"],
            MyToolItNetworkNr["SPU1"])
        self.Can.Logger.Info("STU1 - Receive Fail Counter(Port SPU1): " +
                             str(ReceiveFailCounter))
        ReceiveCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"],
            SystemCommandRouting["ReceiveLowLevelByteCounter"],
            MyToolItNetworkNr["SPU1"])
        self.Can.Logger.Info("STU1 - Receive Byte Counter(Port SPU1): " +
                             str(ReceiveCounter))
        return ReceiveFailCounter

    def _RoutingInformationStuPortSpu(self):
        self._RoutingInformationStuPortSpuSend()
        ReceiveFailCounter = self._RoutingInformationStuPortSpuReceive()
        return ReceiveFailCounter

    def _RoutingInformationStuPortSthSend(self):
        iStuSendCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"], SystemCommandRouting["SendCounter"],
            MyToolItNetworkNr["STH1"])
        self.Can.Logger.Info("STU1 - Send Counter(Port STH1): " +
                             str(iStuSendCounter))
        SendCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"], SystemCommandRouting["SendFailCounter"],
            MyToolItNetworkNr["STH1"])
        self.Can.Logger.Info("STU1 - Send Fail Counter(Port STH1): " +
                             str(SendCounter))
        SendCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"],
            SystemCommandRouting["SendLowLevelByteCounter"],
            MyToolItNetworkNr["STH1"])
        self.Can.Logger.Info("STU1 - Send Byte Counter(Port STH1): " +
                             str(SendCounter))

    def _RoutingInformationStuPortSthReceive(self):
        ReceiveCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"], SystemCommandRouting["ReceiveCounter"],
            MyToolItNetworkNr["STH1"])
        self.Can.Logger.Info("STU1 - Receive Counter(Port STH1): " +
                             str(ReceiveCounter))
        ReceiveFailCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"],
            SystemCommandRouting["ReceiveFailCounter"],
            MyToolItNetworkNr["STH1"])
        self.Can.Logger.Info("STU1 - Receive Fail Counter(Port STH1): " +
                             str(ReceiveFailCounter))
        ReceiveCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"],
            SystemCommandRouting["ReceiveLowLevelByteCounter"],
            MyToolItNetworkNr["STH1"])
        self.Can.Logger.Info("STU1 - Receive Byte Counter(Port STH1): " +
                             str(ReceiveCounter))
        return ReceiveFailCounter

    def _RoutingInformationStuPortSth(self):
        self._RoutingInformationStuPortSthSend()
        ReceiveFailCounter = self._RoutingInformationStuPortSthReceive()
        return ReceiveFailCounter

    def _RoutingInformation(self):
        ReceiveFailCounter = self._RoutingInformationSth()
        ReceiveFailCounter += self._RoutingInformationStuPortSth()
        ReceiveFailCounter += self._RoutingInformationStuPortSpu()
        iSendFail = self.iSthSendCounter - self.iStuSendCounter
        if 0 > iSendFail:
            iSendFail = 0
        iSendFail = iSendFail / self.iSthSendCounter
        iSendFail *= 100
        self.Can.Logger.Info("Send fail approximately: " + str(iSendFail) +
                             "%")
        if 0 < iSendFail:
            print("Send fail approximately: " + str(iSendFail) + "%")
        return ReceiveFailCounter

    def sVersion(self):
        """
        version
        """

        return __version__

    def vAccSet(self, bX, bY, bZ, dataSets):
        self.bAccX = bool(bX)
        self.bAccY = bool(bY)
        self.bAccZ = bool(bZ)

        if dataSets in DataSets:
            self.tAccDataFormat = DataSets[dataSets]
        else:
            dataSets = self.Can.dataSetsCan20(bX, bY, bZ)
            self.tAccDataFormat = DataSets[dataSets]

    def vSthAutoConnect(self, bSthAutoConnect):
        self.bSthAutoConnect = bool(bSthAutoConnect)

    def vDeviceNameSet(self, sDevName):
        if 8 < len(sDevName):
            sDevName = sDevName[:8]
        self.sDevName = sDevName
        self.iDevNr = None

    def vDeviceAddressSet(self, iAddress):
        """Set bluetooth device address"""
        iAddress = int(iAddress, base=0)
        if 0 < iAddress and iAddress < 2**48 - 1:
            iAddress = hex(iAddress)
            self.iAddress = iAddress
        else:
            self.iAddress = 0

    def vAdcConfig(self, iPrescaler, iAquistionTime, iOversampling):
        if Prescaler["Min"] > iPrescaler:
            iPrescaler = Prescaler["Min"]
        elif Prescaler["Max"] < iPrescaler:
            iPrescaler = Prescaler["Max"]
        try:
            iAcquisitionTime = AdcAcquisitionTime[iAquistionTime]
            iOversampling = AdcOverSamplingRate[iOversampling]
            self.samplingRate = int(
                calcSamplingRate(iPrescaler, iAcquisitionTime, iOversampling) +
                0.5)
            self.iPrescaler = iPrescaler
            self.iAquistionTime = iAcquisitionTime
            self.iOversampling = iOversampling
        except:
            pass

    def vAdcRefVConfig(self, sAdcRef):
        self.sAdcRef = sAdcRef

    def vDisplayTime(self, iDisplayTime):
        """Set the length of the graphical plot in seconds"""
        self.iDisplayTime = int(min(iDisplayTime, Watch["DisplayTimeMax"]))

    def vRunTime(self, runTime):
        self.iRunTime = int(runTime)

    def vGraphInit(self, sampleInterval=200, blockSize=10):
        """
        sampleInterval in ms
        """

        self.tDataPointTimeStamp = 0  # Time stamp of last data point
        self.iPacketLossTimeStamp = 0
        self.iGraphBlockSize = blockSize
        self.iGraphSampleInterval = sampleInterval
        self.sMsgLoss = "Acceleration(" + str(format(0, '3.3f')) + "%)"
        self.GuiPackage = {"X": [], "Y": [], "Z": []}

    def vStuAddr(self, sStuAddr):
        self.sStuAddr = sStuAddr

    def guiProcessStop(self):
        try:
            self.vGraphSend(["Run", False])
            self.tSocket.close()
            self.guiProcess.terminate()
            self.guiProcess.join()
        except:
            pass

    def vGraphSend(self, data):
        bSend = True
        data = tArray2Binary(data)
        while bSend == True:
            self.tSocket.sendall(data)
            sleep(0.1)
            ack = self.tSocket.recv(2**10)
            self.Can.Logger.Info(
                f"{datetime.now().time()}: Received acknowledgment: {ack}")
            if ack is not None and ack == data:
                bSend = False

    def guiProcessRestart(self):
        self.guiProcessStop()
        if 0 < self.iDisplayTime:
            self.guiProcess = multiprocessing.Process(
                target=vPlotter, args=(self.iPloterSocketPort, ))
            self.guiProcess.start()

            # Wait until socket of GUI application is ready
            connection_established = False
            while not connection_established:
                try:
                    self.tSocket = socket.socket(socket.AF_INET,
                                                 socket.SOCK_STREAM)
                    self.tSocket.connect(
                        (self.sPloterSocketHost, self.iPloterSocketPort))
                    connection_established = True
                except ConnectionError:
                    sleep(0.1)

            self.vGraphSend(["dataBlockSize", self.iGraphBlockSize])
            self.vGraphSend(["sampleInterval", self.iGraphSampleInterval])
            self.vGraphSend(["xDim", self.iDisplayTime])
            self.vGraphPacketLossUpdate(0)
            if False != self.bAccX:
                self.vGraphSend(["lineNameX", "AccX"])
            if False != self.bAccY:
                self.vGraphSend(["lineNameY", "AccY"])
            if False != self.bAccZ:
                self.vGraphSend(["lineNameZ", "AccZ"])
            self.vGraphSend(["Plot", True])

    def vGraphPointNext(self, x, y, z):
        if self.iDisplayTime <= 0:
            return

        if self.guiProcess.is_alive():
            timeStampNow = int(round(time() * 1000))
            elapsed_time_ms = timeStampNow - self.tDataPointTimeStamp
            if (self.iGraphSampleInterval / self.iGraphBlockSize <=
                    elapsed_time_ms):
                self.tDataPointTimeStamp = timeStampNow
                self.GuiPackage["X"].append(x)
                self.GuiPackage["Y"].append(y)
                self.GuiPackage["Z"].append(z)
                if self.iGraphBlockSize <= len(self.GuiPackage["X"]):
                    try:
                        self.tSocket.sendall(
                            tArray2Binary(["data", self.GuiPackage]))
                    except:
                        pass
                    self.GuiPackage = {"X": [], "Y": [], "Z": []}
        else:
            self.aquireEndTime = self.Can.get_elapsed_time()

    def vGraphPacketLossUpdate(self, msgCounter):
        if self.iDisplayTime <= 0:
            return

        self.iMsgCounterLast += 1
        self.iMsgCounterLast %= 256
        if self.iMsgCounterLast != msgCounter:
            iLost = msgCounter - self.iMsgCounterLast
            self.iMsgLoss += iLost
            self.iMsgsTotal += iLost
            if 0 > iLost:
                self.iMsgLoss += 256
                self.iMsgsTotal += 256
            self.iMsgCounterLast = msgCounter
        else:
            self.iMsgsTotal += 1
        iPacketLossTimeStamp = int(round(time() * 1000))
        if 1000 <= (iPacketLossTimeStamp - self.iPacketLossTimeStamp):
            self.iPacketLossTimeStamp = iPacketLossTimeStamp
            sMsgLoss = "Acceleration(" + str(
                format(100 -
                       (100 * self.iMsgLoss / self.iMsgsTotal), '3.3f')) + "%)"
            if sMsgLoss != self.sMsgLoss:
                self.sMsgLoss = sMsgLoss
                self.tSocket.sendall(
                    tArray2Binary(["diagramName", self.sMsgLoss]))
            self.iMsgLoss = 0
            self.iMsgsTotal = 0

    def vParserInit(self):
        self.parser = argparse.ArgumentParser(
            description="Configure and measure data with the ICOtronic system")

        # TODO: Check option arguments for valid inputs with custom type
        # functions. For an example, please take a look at the function
        # `base64_mac_address` and its usage in `mytoolit/scripts/name.py`.

        connection_group = self.parser.add_argument_group(title="Connection")
        connection_group = connection_group.add_mutually_exclusive_group()
        connection_group.add_argument(
            '-b',
            '--bluetooth-address',
            type=str,
            required=False,
            help=("connect to device with specified Bluetooth address "
                  "(e.g. “08:6b:d7:01:de:81”)"))
        connection_group.add_argument(
            '-n',
            '--name',
            type=str,
            required=False,
            help="connect to device with specified name")

        measurement_group = self.parser.add_argument_group(title="Measurement")
        measurement_group.add_argument('-f',
                                       '--filename',
                                       type=str,
                                       required=False,
                                       help="base name of the output file")

        measurement_group.add_argument(
            '-p',
            '--points',
            metavar='XYZ',
            type=int,
            required=False,
            help=
            ("specify the axes for which acceleration data should be acquired "
             "(e.g. “101” to measure data for the x- and z-axis but not for "
             "the y-axis)"))
        measurement_group.add_argument('-r',
                                       '--run-time',
                                       metavar='SECONDS',
                                       type=int,
                                       required=False,
                                       help="run time in seconds")

        adc_group = self.parser.add_argument_group(title="ADC")
        adc_group.add_argument(
            '-a',
            '--adc',
            metavar=('PRESCALER', 'ACQUISITION', 'OVERSAMPLING'),
            nargs=3,
            type=int,
            required=False,
            help=("prescaler, acquisition time and oversampling rate "
                  "(e.g. “2 8 64”)"))

        self.args = self.parser.parse_args()

    def vParserConsoleArgumentsPass(self):
        if self.args.filename is not None:
            self.set_output_filename(self.args.filename)
        if self.args.adc is not None:
            self.vAdcConfig(*self.args.adc)
        iRunTime = self.iRunTime
        if self.args.run_time:
            iRunTime = self.args.run_time
        self.vRunTime(iRunTime)

        if self.args.name is not None:
            self.vDeviceNameSet(self.args.name)
            self.vSthAutoConnect(True)
        elif self.args.bluetooth_address is not None:
            bluetooth_address = EUI(self.args.bluetooth_address)
            self.vDeviceAddressSet(
                str(int.from_bytes(bluetooth_address.packed, 'big')))
            self.vSthAutoConnect(True)

        if self.args.points:
            points = self.args.points[0] & 0x07
            bZ = bool(points & 1)
            bY = bool((points >> 1) & 1)
            bX = bool((points >> 2) & 1)
            self.vAccSet(bX, bY, bZ, -1)

    def reset(self):
        if False == self.KeyBoardInterrupt:
            try:
                self.Can.ReadThreadReset()
                self.Can.reset_node("STU1")
                self.vStuAddr(
                    int_to_mac_address(
                        self.Can.BlueToothAddress(MyToolItNetworkNr["STU1"])))
                self.guiProcessStop()
            except KeyboardInterrupt:
                self.KeyBoardInterrupt = True

    def vDataAquisition(self):
        if self.KeyBoardInterrupt:
            return

        try:
            if self.Can.bConnected:
                self.Can.ConfigAdc(MyToolItNetworkNr["STH1"], self.iPrescaler,
                                   self.iAquistionTime, self.iOversampling,
                                   AdcReference[self.sAdcRef])
                # Initialize HDF output
                self.storage = Storage(self.get_output_filepath())
                # We need the acceleration range later to convert the ADC
                # acceleration values into multiples of g₀
                self.acceleration_range_g = (
                    self.Can.read_acceleration_sensor_range_in_g())
                self.Can.readThreadStop()
                self.guiProcessRestart()
                self.Can.Logger.Info("Start Acquiring Data")
                self.vGetStreamingAccData()
            else:
                self.Can.Logger.Error("Device not allocable")
        except KeyboardInterrupt:
            self.KeyBoardInterrupt = True
        self.__exit__()

    def close(self):
        if False != self.Can.RunReadThread:
            self.__exit__()

    def vGetStreamingAccDataProcess(self):
        startTime = self.Can.get_elapsed_time()
        tAliveTimeStamp = startTime
        tTimeStamp = startTime
        try:
            while tTimeStamp < self.aquireEndTime:
                try:
                    ack = self.ReadMessage()
                    if ack is not None:
                        tAliveTimeStamp = self.Can.get_elapsed_time()
                        if (self.AccAckExpected.ID != ack["CanMsg"].ID
                                and self.VoltageAckExpected.ID !=
                                ack["CanMsg"].ID):
                            self.Can.Logger.Error("CanId bError: " +
                                                  str(ack["CanMsg"].ID))
                        elif (self.AccAckExpected.DATA[0] !=
                              ack["CanMsg"].DATA[0]
                              and self.VoltageAckExpected.DATA[0] !=
                              ack["CanMsg"].DATA[0]):
                            self.Can.Logger.Error(
                                "Wrong Subheader-Format(Acceleration Format): "
                                + str(ack["CanMsg"].ID))
                        elif self.AccAckExpected.ID == ack["CanMsg"].ID:
                            self.GetMessageAcc(ack)
                    else:
                        tTimeStamp = self.Can.get_elapsed_time()
                        if (tAliveTimeStamp +
                                Watch["AliveTimeOutMs"]) < tTimeStamp:
                            self.Can.bConnected = False
                            self.aquireEndTime = tTimeStamp
                            message = ("Not received any streaming package "
                                       "for 4s. Terminated program execution.")
                            self.Can.Logger.Error(message)
                            print(message)
                except KeyboardInterrupt:
                    pass

            # We store the acceleration metadata at the end since, at this time
            # the acceleration table should exist. Otherwise we would not be
            # able to add the metadata to the table.
            sensor_range = self.acceleration_range_g / 2
            self.storage.add_acceleration_meta("Sensor_Range",
                                               f"± {sensor_range} g₀")

            self.__exit__()
        except KeyboardInterrupt:
            self.KeyBoardInterrupt = True
            print("Data acquisition determined")
            self.__exit__()

    def vGetStreamingAccDataAccStart(self):
        if not (self.bAccX or self.bAccY or self.bAccZ):
            return True

        ack = None
        accFormat = AtvcFormat()
        accFormat.asbyte = 0
        accFormat.b.bStreaming = 1
        accFormat.b.bNumber1 = self.bAccX
        accFormat.b.bNumber2 = self.bAccY
        accFormat.b.bNumber3 = self.bAccZ
        accFormat.b.u3DataSets = self.tAccDataFormat
        cmd = self.Can.CanCmd(MyToolItBlock["Streaming"],
                              MyToolItStreaming["Acceleration"], 0, 0)
        self.AccAckExpected = self.Can.CanMessage20(cmd,
                                                    MyToolItNetworkNr["STH1"],
                                                    MyToolItNetworkNr["SPU1"],
                                                    [accFormat.asbyte])
        cmd = self.Can.CanCmd(MyToolItBlock["Streaming"],
                              MyToolItStreaming["Acceleration"], 1, 0)
        message = self.Can.CanMessage20(cmd, MyToolItNetworkNr["SPU1"],
                                        MyToolItNetworkNr["STH1"],
                                        [accFormat.asbyte])
        self.Can.Logger.Info("MsgId/Subpayload(Acc): " + hex(message.ID) +
                             "/" + hex(accFormat.asbyte))
        endTime = self.Can.get_elapsed_time() + 4000
        while ack is None and self.Can.get_elapsed_time() < endTime:
            self.Can.WriteFrame(message)
            readEndTime = self.Can.get_elapsed_time() + 500
            while ack is None and self.Can.get_elapsed_time() < readEndTime:
                ack = self.ReadMessage()
        return ack

    def vGetStreamingAccData(self):
        ack = self.vGetStreamingAccDataAccStart()
        currentTime = self.Can.get_elapsed_time()
        if ack is None:
            self.Can.Logger.Error("No Ack received from Device: " +
                                  str(self.iDevNr))
            self.aquireEndTime = currentTime
        elif self.iRunTime == 0:
            self.aquireEndTime = currentTime + (1 << 32)
        else:
            self.aquireEndTime = currentTime + self.iRunTime * 1000
        self.vGetStreamingAccDataProcess()

    def store_values_single(self, prefix, canMsg):
        timestamp = round(canMsg["PeakCanTime"], 3)
        data = canMsg["CanMsg"].DATA

        counter = data[1]
        values = [
            byte_list_to_int(data[start:start + 2])
            for start in range(2, 8, 2)
        ]
        axis = prefix[-1].lower()

        convert_acceleration = partial(convert_acceleration_adc_to_g,
                                       max_value=self.acceleration_range_g)

        for value in values:
            self.storage.add_acceleration(
                values={axis: convert_acceleration(value)},
                counter=counter,
                timestamp=timestamp)

    def store_values_double(self, prefix1, prefix2, canMsg):
        timestamp = round(canMsg["PeakCanTime"], 3)
        data = canMsg["CanMsg"].DATA

        counter = data[1]
        values = [
            byte_list_to_int(data[start:start + 2])
            for start in range(2, 6, 2)
        ]

        convert_acceleration = partial(convert_acceleration_adc_to_g,
                                       max_value=self.acceleration_range_g)

        axes = [prefix[-1].lower() for prefix in (prefix1, prefix2)]
        values = {
            axis: convert_acceleration(value)
            for axis, value in zip(axes, values)
        }
        self.storage.add_acceleration(values=values,
                                      counter=counter,
                                      timestamp=timestamp)

    def store_values_tripple(self, prefix1, prefix2, prefix3, canMsg):
        timestamp = round(canMsg["PeakCanTime"], 3)
        data = canMsg["CanMsg"].DATA

        counter = data[1]
        values = [
            byte_list_to_int(data[start:start + 2])
            for start in range(2, 8, 2)
        ]

        convert_acceleration = partial(convert_acceleration_adc_to_g,
                                       max_value=self.acceleration_range_g)

        axes = [prefix[-1].lower() for prefix in (prefix1, prefix2, prefix3)]
        values = {
            axis: convert_acceleration(value)
            for axis, value in zip(axes, values)
        }
        self.storage.add_acceleration(values=values,
                                      counter=counter,
                                      timestamp=timestamp)

    def GetMessageAcc(self, canData):
        data = canData["CanMsg"].DATA
        msgCounter = data[1]
        self.vGraphPacketLossUpdate(msgCounter)

        convert_acceleration = partial(convert_acceleration_adc_to_g,
                                       max_value=self.acceleration_range_g)

        value1 = convert_acceleration(byte_list_to_int(data[2:4]))
        if self.tAccDataFormat == DataSets[1]:
            value2 = convert_acceleration(byte_list_to_int(data[4:6]))
            if self.bAccX and self.bAccY and not self.bAccZ:
                self.store_values_double("AccX", "AccY", canData)
                self.vGraphPointNext(value1, value2, 0)
            elif self.bAccX and not self.bAccY and self.bAccZ:
                self.store_values_double("AccX", "AccZ", canData)
                self.vGraphPointNext(value1, 0, value2)
            elif not self.bAccX and self.bAccY and self.bAccZ:
                self.store_values_double("AccY", "AccZ", canData)
                self.vGraphPointNext(0, value1, value2)
            else:
                value3 = convert_acceleration(byte_list_to_int(data[6:8]))
                self.store_values_tripple("AccX", "AccY", "AccZ", canData)
                self.vGraphPointNext(value1, value2, value3)
        elif self.tAccDataFormat == DataSets[3]:
            if self.bAccX:
                self.store_values_single("AccX", canData)
                self.vGraphPointNext(value1, 0, 0)
            elif self.bAccY:
                self.store_values_single("AccY", canData)
                self.vGraphPointNext(0, value1, 0)
            elif self.bAccZ:
                self.store_values_single("AccZ", canData)
                self.vGraphPointNext(0, 0, value1)
        else:
            self.Can.Logger.Error("Wrong Ack format")

    def ReadMessage(self):
        message = None
        result = self.Can.pcan.Read(self.Can.m_PcanHandle)
        if result[0] == PCAN_ERROR_OK:
            peakCanTimeStamp = result[2].millis_overflow * (
                2**32) + result[2].millis + result[2].micros / 1000
            message = {
                "CanMsg": result[1],
                "PcTime": self.Can.get_elapsed_time(),
                "PeakCanTime": peakCanTimeStamp
            }
        elif result[0] == PCAN_ERROR_QOVERRUN:
            self.Can.Logger.Error("RxOverRun")
            print("RxOverRun")
            raise Exception("RxOverRun")
        else:
            sleep(0.001)
        return message

    def _vRunConsoleStartupLoggerPrint(self):
        self.Can.Logger.Info("Log Name: " + str(self.Can.Logger.filepath.name))
        self.Can.Logger.Info("Device Name (to be connected): " +
                             str(self.sDevName))
        self.Can.Logger.Info("Bluetooth address(to be connected): " +
                             str(self.iAddress))  # Todo machen
        self.Can.Logger.Info("AutoConnect?: " + str(self.bSthAutoConnect))
        self.Can.Logger.Info("Run Time: " + str(self.iRunTime) + "s")
        self.Can.Logger.Info("Display Time: " + str(self.iDisplayTime) + "ms")
        self.Can.Logger.Info(
            "Adc Prescaler/AcquisitionTime/OversamplingRate/Reference(Samples/s): "
            + str(self.iPrescaler) + "/" +
            str(AdcAcquisitionTime.inverse[self.iAquistionTime]) + "/" +
            str(AdcOverSamplingRate.inverse[self.iOversampling]) + "/" +
            str(self.sAdcRef) + "(" + str(self.samplingRate) + ")")
        self.Can.Logger.Info("Acc Config(XYZ/DataSets): " +
                             str(int(self.bAccX)) + str(int(self.bAccY)) +
                             str(int(self.bAccZ)) + "/" +
                             str(DataSets.inverse[self.tAccDataFormat]))

    def _vRunConsoleStartup(self):
        self._vRunConsoleStartupLoggerPrint()

    def vRunConsoleAutoConnect(self):
        if "0x0" != self.iAddress and 0 != self.iAddress and "0" != self.iAddress:
            self.Can.bBlueToothConnectPollingAddress(MyToolItNetworkNr["STU1"],
                                                     self.iAddress)
        else:
            self.Can.bBlueToothConnectPollingName(MyToolItNetworkNr["STU1"],
                                                  self.sDevName,
                                                  log=False)
        if False != self.Can.bConnected:
            self.vDataAquisition()

    def vRunConsole(self):
        self._vRunConsoleStartup()
        self.reset()
        if False != self.bSthAutoConnect:
            self.vRunConsoleAutoConnect()
        self.close()


if __name__ == "__main__":
    watch = myToolItWatch()
    watch.vParserInit()
    watch.vParserConsoleArgumentsPass()
    watch.vRunConsole()
