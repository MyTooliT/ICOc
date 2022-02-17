import argparse
import multiprocessing
import socket

from argparse import ArgumentDefaultsHelpFormatter
from time import sleep, time
from datetime import datetime
from functools import partial
from pathlib import Path
from sys import stderr
from typing import Optional, Tuple

from can.interfaces.pcan.basic import PCAN_ERROR_OK, PCAN_ERROR_QRCVEMPTY

from mytoolit.cmdline import axes_spec, mac_address, sth_name
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


class CommandLineInterface():
    """ICOc command line interface

    Use this class to connect to the ICOtronic system and acquire measurement
    data using a command line interface.

    """

    def __init__(self, *args, **kwargs):
        # Check if output directory exists and try to create it, if it does not
        # exist already
        try:
            settings.check_output_directory()
        except (NotADirectoryError, OSError) as error:
            raise error

        self.parse_arguments()

        self.KeyBoardInterrupt = False
        self.bError = False
        self.iMsgLoss = 0
        self.iMsgsTotal = 0
        self.iMsgCounterLast = -1
        self.Can = Network('ICOc.log',
                           FreshLog=True,
                           sender=MyToolItNetworkNr["SPU1"],
                           receiver=MyToolItNetworkNr["STH1"])
        self.Can.Logger.Info(f"Start Time: {datetime.now().isoformat()}")

        self.vAccSet(*self.args.points, -1)

        self.connect = (True if 'name' in self.args
                        or 'bluetooth_address' in self.args else False)
        self.sth_name = self.args.name if 'name' in self.args else ""
        self.vDeviceAddressSet(
            str(int.from_bytes(self.args.bluetooth_address, 'big')
                ) if 'bluetooth_address' in self.args else "0")

        self.vAdcConfig(self.args.prescaler, self.args.acquisition,
                        self.args.oversampling)
        self.vAdcRefVConfig("VDD")
        self.vRunTime(0 if self.args.run_time <= 0 else self.args.run_time)
        self.vGraphInit(Watch["DisplaySampleRateMs"],
                        Watch["DisplayBlockSize"])
        self.Can.readThreadStop()
        # Set plotter host and port
        self.sPloterSocketHost = settings.gui.host
        self.iPloterSocketPort = settings.gui.port

        self.storage = None
        self.set_output_filename(self.args.filename)

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

    def parse_arguments(self):
        self.parser = argparse.ArgumentParser(
            description="Configure and measure data with the ICOtronic system",
            argument_default=argparse.SUPPRESS,
            formatter_class=ArgumentDefaultsHelpFormatter)

        connection_group = self.parser.add_argument_group(title="Connection")
        connection_group = connection_group.add_mutually_exclusive_group()
        connection_group.add_argument(
            '-b',
            '--bluetooth-address',
            type=mac_address,
            required=False,
            help=("connect to device with specified Bluetooth address "
                  "(e.g. “08:6b:d7:01:de:81”)"))
        connection_group.add_argument(
            '-n',
            '--name',
            type=sth_name,
            required=False,
            help="connect to device with specified name")

        measurement_group = self.parser.add_argument_group(title="Measurement")
        measurement_group.add_argument('-f',
                                       '--filename',
                                       type=str,
                                       default='Measurement',
                                       required=False,
                                       help="base name of the output file")

        measurement_group.add_argument(
            '-p',
            '--points',
            metavar='XYZ',
            type=axes_spec,
            default='100',
            required=False,
            help=("specify the axes for which acceleration data should be "
                  "acquired (e.g. “101” to measure data for the x- and "
                  "z-axis but not for the y-axis)"))
        measurement_group.add_argument(
            '-r',
            '--run-time',
            metavar='SECONDS',
            type=int,
            default=0,
            required=False,
            help=("run time in seconds "
                  "(values equal or below “0” specify infinite runtime)"))

        adc_group = self.parser.add_argument_group(title="ADC")

        adc_group.add_argument('-s',
                               '--prescaler',
                               type=int,
                               choices=range(2, 128),
                               metavar='2–127',
                               default=2,
                               required=False,
                               help="Prescaler value")
        adc_group.add_argument('-a',
                               '--acquisition',
                               type=int,
                               choices=AdcAcquisitionTime.keys(),
                               default=8,
                               required=False,
                               help="Acquisition time value")
        adc_group.add_argument('-o',
                               '--oversampling',
                               type=int,
                               choices=AdcOverSamplingRate.keys(),
                               default=64,
                               required=False,
                               help="Oversampling rate value")

        self.args = self.parser.parse_args()

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

    def vAccSet(self, bX, bY, bZ, dataSets):
        self.bAccX = bool(bX)
        self.bAccY = bool(bY)
        self.bAccZ = bool(bZ)

        if dataSets in DataSets:
            self.tAccDataFormat = DataSets[dataSets]
        else:
            dataSets = self.Can.dataSetsCan20(bX, bY, bZ)
            self.tAccDataFormat = DataSets[dataSets]

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

        iAcquisitionTime = AdcAcquisitionTime[iAquistionTime]
        iOversampling = AdcOverSamplingRate[iOversampling]
        self.samplingRate = int(
            calcSamplingRate(iPrescaler, iAcquisitionTime, iOversampling) +
            0.5)
        self.iPrescaler = iPrescaler
        self.iAquistionTime = iAcquisitionTime
        self.iOversampling = iOversampling

    def vAdcRefVConfig(self, sAdcRef):
        self.sAdcRef = sAdcRef

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
        if hasattr(self, 'tSocket'):
            try:
                self.vGraphSend(["Run", False])
            except (ConnectionAbortedError, OSError):
                pass
            self.tSocket.close()
        if hasattr(self, 'guiProcess'):
            self.guiProcess.terminate()
            self.guiProcess.join()

    def vGraphSend(self, data):
        bSend = True
        data = tArray2Binary(data)
        while bSend:
            self.tSocket.sendall(data)
            sleep(0.1)
            ack = self.tSocket.recv(2**10)
            self.Can.Logger.Info(
                f"{datetime.now().time()}: Received acknowledgment: {ack}")
            if ack is not None and ack == data:
                bSend = False

    def guiProcessRestart(self):
        self.guiProcessStop()

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
        self.vGraphSend(["xDim", Watch["DisplayTimeMax"]])
        self.vGraphPacketLossUpdate()
        if self.bAccX:
            self.vGraphSend(["lineNameX", "Acceleration X-Axis"])
        if self.bAccY:
            self.vGraphSend(["lineNameY", "Acceleration Y-Axis"])
        if self.bAccZ:
            self.vGraphSend(["lineNameZ", "Acceleration Z-Axis"])
        self.vGraphSend(["Plot", True])

    def vGraphPointNext(self, x=0, y=0, z=0):

        timeStampNow = int(round(time() * 1000))
        elapsed_time_ms = timeStampNow - self.tDataPointTimeStamp
        if (elapsed_time_ms <=
                self.iGraphSampleInterval / self.iGraphBlockSize):
            return

        self.tDataPointTimeStamp = timeStampNow
        self.GuiPackage["X"].append(x)
        self.GuiPackage["Y"].append(y)
        self.GuiPackage["Z"].append(z)
        if self.iGraphBlockSize <= len(self.GuiPackage["X"]):
            self.tSocket.sendall(tArray2Binary(["data", self.GuiPackage]))
            self.GuiPackage = {"X": [], "Y": [], "Z": []}

    def vGraphPacketLossUpdate(self, msgCounter=-1):
        if self.iMsgCounterLast == -1:
            self.iMsgCounterLast = msgCounter
        else:
            self.iMsgCounterLast += 1
            self.iMsgCounterLast %= 256
        if self.iMsgCounterLast != msgCounter:
            iLost = (msgCounter - self.iMsgCounterLast
                     if msgCounter > self.iMsgCounterLast else 0xff -
                     self.iMsgCounterLast + msgCounter)
            self.iMsgLoss += iLost
            self.iMsgsTotal += iLost
            if 0 > iLost:
                self.iMsgLoss += 256
                self.iMsgsTotal += 256
            self.iMsgCounterLast = msgCounter
        else:
            self.iMsgsTotal += 1
        iPacketLossTimeStamp = int(round(time() * 1000))
        time_since_update = iPacketLossTimeStamp - self.iPacketLossTimeStamp
        if time_since_update >= 1000:
            self.iPacketLossTimeStamp = iPacketLossTimeStamp
            pakets_received = (1 - self.iMsgLoss / self.iMsgsTotal) * 100
            sMsgLoss = f"Acceleration (▂▄▇ {pakets_received:3.2f} %)"
            if sMsgLoss != self.sMsgLoss:
                self.sMsgLoss = sMsgLoss
                self.tSocket.sendall(
                    tArray2Binary(["diagramName", self.sMsgLoss]))
            self.iMsgLoss = 0
            self.iMsgsTotal = 0

    def reset(self):
        if self.KeyBoardInterrupt:
            return

        try:
            self.Can.ReadThreadReset()
            self.Can.reset_node("STU1")
            self.vStuAddr(
                int_to_mac_address(
                    self.Can.BlueToothAddress(MyToolItNetworkNr["STU1"])))
            self.guiProcessStop()
        except KeyboardInterrupt:
            self.KeyBoardInterrupt = True

    def read_acceleration_range(self) -> Tuple[int, bool]:
        """Read the range of the acceleration sensor

        Returns
        -------

        A tuple containing

        - the acceleration range in multiples of g₀ or a default value for a ±
          100 g₀ sensor, if reading the EEPROM value was unsuccessful,
        - a boolean that specifies if reading was successful (`True`) or not
          (`False`).

        """

        # Default values
        acceleration_range_g = 200
        success = False

        try:
            acceleration_range_g = int(
                self.Can.read_acceleration_sensor_range_in_g())
            success = True
        except ValueError:
            pass

        return (acceleration_range_g, success)

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
                self.acceleration_range_g, success = (
                    self.read_acceleration_range())
                if not success:
                    print(
                        "Warning: Unable to determine sensor range from "
                        "EEPROM value — Assuming ± 100 g sensor",
                        file=stderr)
                if self.acceleration_range_g < 1:
                    print(
                        f"Warning: Sensor range “{self.acceleration_range_g}” "
                        "below 1 g — Using range 200 instead (± 100 g sensor)",
                        file=stderr)
                    self.acceleration_range_g = 200

                # ICOc does not use the network class to read the streaming
                # data but uses the `Read` method of the PCAN API directly.
                # This means we have to disable the read thread of the CAN
                # class first.
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
        if self.Can.RunReadThread:
            self.__exit__()

    def vGetStreamingAccDataProcess(self):
        startTime = self.Can.get_elapsed_time()
        tAliveTimeStamp = startTime
        tTimeStamp = startTime
        try:
            while tTimeStamp < self.aquireEndTime:
                try:
                    if not self.guiProcess.is_alive():
                        # End program after plotter window was closed
                        break

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
                            self.vGraphPacketLossUpdate(ack["CanMsg"].DATA[1])
                            self.update_acceleration_data(ack)
                    else:
                        tTimeStamp = self.Can.get_elapsed_time()
                        if (tAliveTimeStamp +
                                Watch["AliveTimeOutMs"]) < tTimeStamp:
                            self.Can.bConnected = False
                            self.aquireEndTime = tTimeStamp
                            message = (
                                "Did not receive any streaming data for 4s — "
                                "Terminating program execution")
                            self.Can.Logger.Error(message)
                            print(message, file=stderr)

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
            print("Data acquisition terminated")
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
            self.Can.Logger.Error(
                f"No acknowledge received from STH “{self.iAddress}”")
            self.aquireEndTime = currentTime
        elif self.iRunTime == 0:
            self.aquireEndTime = currentTime + (1 << 32)
        else:
            self.aquireEndTime = currentTime + self.iRunTime * 1000
        self.vGetStreamingAccDataProcess()

    def update_acceleration_data(self, canData):
        data = canData["CanMsg"].DATA
        timestamp = round(canData["PeakCanTime"], 3)
        counter = data[1]

        axes = [
            axis for axis, activated in (('x', self.bAccX), ('y', self.bAccY),
                                         ('z', self.bAccZ)) if activated
        ]

        if len(axes) <= 0:
            return

        convert_acceleration = partial(convert_acceleration_adc_to_g,
                                       max_value=self.acceleration_range_g)
        number_values = 3 if self.tAccDataFormat == DataSets[3] else len(axes)
        values = [
            convert_acceleration(byte_list_to_int(data[start:start + 2]))
            for start in range(2, 2 + number_values * 2, 2)
        ]

        if self.tAccDataFormat == DataSets[1]:
            axis_values = {axis: value for axis, value in zip(axes, values)}
            self.storage.add_acceleration(values=axis_values,
                                          counter=counter,
                                          timestamp=timestamp)
            self.vGraphPointNext(**axis_values)
        elif self.tAccDataFormat == DataSets[3]:
            axis = axes[0]
            for value in values:
                self.storage.add_acceleration(values={axis: value},
                                              counter=counter,
                                              timestamp=timestamp)
            self.vGraphPointNext(**{axis: values[0]})
        else:
            self.Can.Logger.Error("Wrong Ack format")

    def ReadMessage(self):
        status, message, timestamp = self.Can.pcan.Read(self.Can.m_PcanHandle)
        if status == PCAN_ERROR_OK:
            peakCanTimeStamp = timestamp.millis_overflow * (
                2**32) + timestamp.millis + timestamp.micros / 1000
            result = {
                "CanMsg": message,
                "PcTime": self.Can.get_elapsed_time(),
                "PeakCanTime": peakCanTimeStamp
            }
            return result

        if status == PCAN_ERROR_QRCVEMPTY:
            # Sleep a little bit when there are no messages in the buffer
            sleep(0.000_001)
        else:
            explanation = self.Can.pcan.GetErrorText(status)[1].decode()
            error_message = f"Unexpected CAN status value: {explanation}"
            self.Can.Logger.Error(error_message)
            print(error_message, file=stderr)
            raise Exception(error_message)

        return None

    def _vRunConsoleStartupLoggerPrint(self):
        self.Can.Logger.Info(f"Log File: {self.Can.Logger.filepath.name}")
        self.Can.Logger.Info(f"STH Name: {self.sth_name}")
        self.Can.Logger.Info(f"Bluetooth Address: {self.iAddress}")
        self.Can.Logger.Info(f"Connect to STH: {self.connect}")
        self.Can.Logger.Info(f"Run Time: {self.iRunTime} s")
        self.Can.Logger.Info(f"Prescaler: {self.iPrescaler}")
        aqcuisition_time = AdcAcquisitionTime.inverse[self.iAquistionTime]
        oversampling_rate = AdcOverSamplingRate.inverse[self.iOversampling]
        self.Can.Logger.Info(f"Acquisition Time: {aqcuisition_time}")
        self.Can.Logger.Info(f"Oversampling Rate: {oversampling_rate}")
        self.Can.Logger.Info(f"Reference Voltage: {self.sAdcRef}")
        data_sets = DataSets.inverse[self.tAccDataFormat]
        self.Can.Logger.Info(f"Data Sets: {data_sets}")
        axes = "".join([
            axis if active else ""
            for active, axis in ((self.bAccX, "X"), (self.bAccY, "Y"),
                                 (self.bAccZ, "Z"))
        ])
        self.Can.Logger.Info(
            f"Active Ax{'i' if len(axes) == 1 else 'e'}s: {axes}")

    def _vRunConsoleStartup(self):
        self._vRunConsoleStartupLoggerPrint()

    def vRunConsoleAutoConnect(self):
        if self.iAddress not in {0, "0", "0x0"}:
            self.Can.bBlueToothConnectPollingAddress(MyToolItNetworkNr["STU1"],
                                                     self.iAddress)
        else:
            self.Can.bBlueToothConnectPollingName(MyToolItNetworkNr["STU1"],
                                                  self.sth_name,
                                                  log=False)
        if self.Can.bConnected:
            self.vDataAquisition()

    def run(self):
        self._vRunConsoleStartup()
        self.reset()
        if self.connect:
            self.vRunConsoleAutoConnect()
        self.close()


if __name__ == "__main__":
    CommandLineInterface().run()
