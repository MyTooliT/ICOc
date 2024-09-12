import argparse
import multiprocessing
import socket

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from time import sleep, time
from functools import partial
from logging import getLogger
from pathlib import Path
from platform import system
from sys import stderr
from typing import Optional, Tuple

# Handle pytest `ModuleNotFoundError` on non-Windows OS
if system() == "Windows":
    from win32event import CreateEvent, WaitForSingleObject, WAIT_OBJECT_0

from can.interfaces.pcan.basic import (
    PCAN_ERROR_OK,
    PCAN_ERROR_QRCVEMPTY,
    PCAN_RECEIVE_EVENT,
)

from mytoolit.can.streaming import StreamingData
from mytoolit.cmdline.parse import (
    add_channel_arguments,
    mac_address,
    sth_name,
)
from mytoolit.config import settings
from mytoolit.measurement.acceleration import convert_raw_to_g
from mytoolit.measurement.storage import Storage
from mytoolit.measurement.sensor import SensorConfiguration
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
from mytoolit.utility.log import get_log_file_handler

Watch = {
    # Time period displayed in the graph in seconds,
    # i.e. “length” of abscissa (“x-coordinate”)
    "DisplayTimeMax": 10,
    # Time after which graph data will be updated again in milliseconds
    "DisplaySampleRateMs": 1 / 5 * 1000,
    # Number of data samples printed in a block,
    # i.e in the time span specified above
    "DisplayBlockSize": 20,
    # Time out after receiving no data in acquiring mode in seconds
    "AliveTimeOutMs": 4000,
}


class CommandLineInterface:
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

        # Check command line arguments
        parser = self.create_parser()
        self.args = parser.parse_args()

        # Init logger
        self.logger = getLogger(__name__)
        self.logger.setLevel(self.args.log.upper())
        self.logger.addHandler(get_log_file_handler("cli.log"))
        self.logger.info("Initialized logger")

        self.KeyBoardInterrupt = False
        self.bError = False
        self.iMsgLoss = 0
        self.iMsgsTotal = 0
        self.iMsgCounterLast = -1
        self.Can = Network(
            sender=MyToolItNetworkNr["SPU1"],
            receiver=MyToolItNetworkNr["STH1"],
            log_destination="network.log",
            log_level=self.args.log.upper(),
        )
        self.logger.info("Initialized CAN class")

        # Set measurement channel mapping
        channels = (
            self.args.first_channel,
            self.args.second_channel,
            self.args.third_channel,
        )
        try:
            self.set_sensors(*channels)
        except ValueError as error:
            self.Can.__exit__()
            parser.error(str(error))

        for channel, value in enumerate(channels, start=1):
            self.logger.info(f"Measurement Channel {channel}: {value}")

        self.connect = (
            True
            if "name" in self.args or "bluetooth_address" in self.args
            else False
        )
        self.sth_name = self.args.name if "name" in self.args else ""
        self.vDeviceAddressSet(
            str(int.from_bytes(self.args.bluetooth_address, "big"))
            if "bluetooth_address" in self.args
            else "0"
        )

        self.vAdcConfig(
            self.args.prescaler, self.args.acquisition, self.args.oversampling
        )
        self.vAdcRefVConfig(self.args.voltage_reference)
        self.vRunTime(0 if self.args.run_time <= 0 else self.args.run_time)
        self.vGraphInit(
            Watch["DisplaySampleRateMs"], Watch["DisplayBlockSize"]
        )
        self.Can.readThreadStop()
        # Set plotter host and port
        self.sPloterSocketHost = settings.gui.host
        self.iPloterSocketPort = settings.gui.port

        self.storage = None
        self.data = None
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
        self.logger.info("Cleanup done")

        if self.bError:
            self.logger.error("An error occurred")

        self.Can.__exit__()
        self.logger.info("Closed CAN connection")
        if self.bError:
            raise RuntimeError("An error occurred")

    def create_parser(self) -> ArgumentParser:
        parser = ArgumentParser(
            description="Configure and measure data with the ICOtronic system",
            argument_default=argparse.SUPPRESS,
            formatter_class=ArgumentDefaultsHelpFormatter,
        )

        connection_group = parser.add_argument_group(title="Connection")
        connection_group = connection_group.add_mutually_exclusive_group()
        connection_group.add_argument(
            "-b",
            "--bluetooth-address",
            type=mac_address,
            required=False,
            help=(
                "connect to device with specified Bluetooth address "
                "(e.g. “08:6b:d7:01:de:81”)"
            ),
        )
        connection_group.add_argument(
            "-n",
            "--name",
            type=sth_name,
            nargs="?",
            const="",
            required=False,
            help="connect to device with specified name",
        )

        measurement_group = parser.add_argument_group(title="Measurement")
        measurement_group.add_argument(
            "-f",
            "--filename",
            type=str,
            default="Measurement",
            required=False,
            help="base name of the output file",
        )

        measurement_group.add_argument(
            "-r",
            "--run-time",
            metavar="SECONDS",
            type=int,
            default=0,
            required=False,
            help=(
                "run time in seconds "
                "(values equal or below “0” specify infinite runtime)"
            ),
        )
        add_channel_arguments(measurement_group)

        adc_group = parser.add_argument_group(title="ADC")

        adc_group.add_argument(
            "-s",
            "--prescaler",
            type=int,
            choices=range(2, 128),
            metavar="2–127",
            default=2,
            required=False,
            help="Prescaler value",
        )
        adc_group.add_argument(
            "-a",
            "--acquisition",
            type=int,
            choices=AdcAcquisitionTime.keys(),
            default=8,
            required=False,
            help="Acquisition time value",
        )
        adc_group.add_argument(
            "-o",
            "--oversampling",
            type=int,
            choices=AdcOverSamplingRate.keys(),
            default=64,
            required=False,
            help="Oversampling rate value",
        )
        adc_group.add_argument(
            "-v",
            "--voltage-reference",
            choices=AdcReference.keys(),
            default="VDD",
            required=False,
            help="Reference voltage",
        )

        logging_group = parser.add_argument_group(title="Logging")
        logging_group.add_argument(
            "--log",
            choices=("debug", "info", "warning", "error", "critical"),
            default="info",
            required=False,
            help="Minimum level of messages written to log",
        )

        return parser

    def set_output_filename(self, name: Optional[str] = None) -> None:
        """Set the (base) name of the HDF output file

        Parameters
        ----------

        name:
            A new (base) name for the output file

            If you set this parameter to `None`, then the most recently set
            filename will be used

        """

        filename = (
            Path(settings.measurement.output.filename)
            if name is None
            else Path(name)
        )
        if not filename.suffix:
            filename = filename.with_suffix(".hdf5")

        settings.measurement.output.filename = str(filename)

    def _statusWords(self):
        self.logger.info(
            "STH Status Word: {}".format(
                self.Can.node_status(MyToolItNetworkNr["STH1"])
            )
        )
        self.logger.info(
            "STU Status Word: {}".format(
                self.Can.node_status(MyToolItNetworkNr["STU1"])
            )
        )

        status = self.Can.error_status(MyToolItNetworkNr["STH1"])
        if status.adc_overrun():
            self.bError = True
        self.logger.info(f"STH Error Word: {status}")

        self.logger.info(
            "STU Error Word: {}".format(
                self.Can.error_status(MyToolItNetworkNr["STU1"])
            )
        )

    def _BlueToothStatistics(self):
        def log_statistics(node, node_description):
            send_counter = self.Can.BlueToothCmd(
                MyToolItNetworkNr[node], SystemCommandBlueTooth["SendCounter"]
            )
            self.logger.info(
                f"Bluetooth send counter of {node_description}: {send_counter}"
            )
            receive_counter = self.Can.BlueToothCmd(
                MyToolItNetworkNr[node],
                SystemCommandBlueTooth["ReceiveCounter"],
            )
            self.logger.info(
                "Bluetooth receive counter of "
                f"{node_description}: {receive_counter}"
            )

            rssi = self.Can.BlueToothRssi(MyToolItNetworkNr[node])
            self.logger.info(f"RSSI of {node_description}: {rssi} dBm")

        log_statistics("STH1", "sensor node")
        log_statistics("STU1", "STU")

    def _RoutingInformationSthSend(self):
        self.iSthSendCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STH1"],
            SystemCommandRouting["SendCounter"],
            MyToolItNetworkNr["STU1"],
        )
        self.logger.info(
            f"Sensor node - Send counter (port STU): {self.iSthSendCounter}"
        )
        SendCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STH1"],
            SystemCommandRouting["SendFailCounter"],
            MyToolItNetworkNr["STU1"],
        )
        self.logger.info(
            f"Sensor node - Send fail counter (port STU): {SendCounter}"
        )
        SendCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STH1"],
            SystemCommandRouting["SendLowLevelByteCounter"],
            MyToolItNetworkNr["STU1"],
        )
        self.logger.info(
            f"Sensor node - Send byte counter (port STU): {SendCounter}"
        )

    def _RoutingInformationSthReceive(self):
        ReceiveCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STH1"],
            SystemCommandRouting["ReceiveCounter"],
            MyToolItNetworkNr["STU1"],
        )
        self.logger.info(
            f"Sensor node - Receive counter (port STU): {ReceiveCounter}"
        )
        ReceiveFailCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STH1"],
            SystemCommandRouting["ReceiveFailCounter"],
            MyToolItNetworkNr["STU1"],
        )
        self.logger.info(
            "Sensor node - Receive fail counter (port STU): "
            f"{ReceiveFailCounter}"
        )
        ReceiveCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STH1"],
            SystemCommandRouting["ReceiveLowLevelByteCounter"],
            MyToolItNetworkNr["STU1"],
        )
        self.logger.info(
            f"Sensor node - Receive byte counter (port STU): {ReceiveCounter}"
        )
        return ReceiveFailCounter

    def _RoutingInformationSth(self):
        self._RoutingInformationSthSend()
        ReceiveFailCounter = self._RoutingInformationSthReceive()
        return ReceiveFailCounter

    def _RoutingInformationStuPortSpuSend(self):
        self.iStuSendCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"],
            SystemCommandRouting["SendCounter"],
            MyToolItNetworkNr["SPU1"],
        )
        self.logger.info(
            "STU1 - Send Counter(Port SPU1): " + str(self.iStuSendCounter)
        )
        SendCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"],
            SystemCommandRouting["SendFailCounter"],
            MyToolItNetworkNr["SPU1"],
        )
        self.logger.info(
            "STU1 - Send Fail Counter(Port SPU1): " + str(SendCounter)
        )
        SendCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"],
            SystemCommandRouting["SendLowLevelByteCounter"],
            MyToolItNetworkNr["SPU1"],
        )
        self.logger.info(
            "STU1 - Send Byte Counter(Port SPU1): " + str(SendCounter)
        )

    def _RoutingInformationStuPortSpuReceive(self):
        ReceiveCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"],
            SystemCommandRouting["ReceiveCounter"],
            MyToolItNetworkNr["SPU1"],
        )
        self.logger.info(
            "STU1 - Receive Counter(Port SPU1): " + str(ReceiveCounter)
        )
        ReceiveFailCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"],
            SystemCommandRouting["ReceiveFailCounter"],
            MyToolItNetworkNr["SPU1"],
        )
        self.logger.info(
            "STU1 - Receive Fail Counter(Port SPU1): "
            + str(ReceiveFailCounter)
        )
        ReceiveCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"],
            SystemCommandRouting["ReceiveLowLevelByteCounter"],
            MyToolItNetworkNr["SPU1"],
        )
        self.logger.info(
            "STU1 - Receive Byte Counter(Port SPU1): " + str(ReceiveCounter)
        )
        return ReceiveFailCounter

    def _RoutingInformationStuPortSpu(self):
        self._RoutingInformationStuPortSpuSend()
        ReceiveFailCounter = self._RoutingInformationStuPortSpuReceive()
        return ReceiveFailCounter

    def _RoutingInformationStuPortSthSend(self):
        iStuSendCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"],
            SystemCommandRouting["SendCounter"],
            MyToolItNetworkNr["STH1"],
        )
        self.logger.info(
            "STU1 - Send Counter(Port STH1): " + str(iStuSendCounter)
        )
        SendCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"],
            SystemCommandRouting["SendFailCounter"],
            MyToolItNetworkNr["STH1"],
        )
        self.logger.info(
            "STU1 - Send Fail Counter(Port STH1): " + str(SendCounter)
        )
        SendCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"],
            SystemCommandRouting["SendLowLevelByteCounter"],
            MyToolItNetworkNr["STH1"],
        )
        self.logger.info(
            "STU1 - Send Byte Counter(Port STH1): " + str(SendCounter)
        )

    def _RoutingInformationStuPortSthReceive(self):
        ReceiveCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"],
            SystemCommandRouting["ReceiveCounter"],
            MyToolItNetworkNr["STH1"],
        )
        self.logger.info(
            "STU1 - Receive Counter(Port STH1): " + str(ReceiveCounter)
        )
        ReceiveFailCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"],
            SystemCommandRouting["ReceiveFailCounter"],
            MyToolItNetworkNr["STH1"],
        )
        self.logger.info(
            "STU1 - Receive Fail Counter(Port STH1): "
            + str(ReceiveFailCounter)
        )
        ReceiveCounter = self.Can.RoutingInformationCmd(
            MyToolItNetworkNr["STU1"],
            SystemCommandRouting["ReceiveLowLevelByteCounter"],
            MyToolItNetworkNr["STH1"],
        )
        self.logger.info(
            "STU1 - Receive Byte Counter(Port STH1): " + str(ReceiveCounter)
        )
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
        self.logger.info("Send fail approximately: " + str(iSendFail) + "%")
        if 0 < iSendFail:
            print("Send fail approximately: " + str(iSendFail) + "%")
        return ReceiveFailCounter

    def set_sensors(self, first: int, second: int, third: int) -> None:
        """Set sensor numbers for measurement channels

        Parameters
        ----------

        first:
            Sensor number for first measurement channel

        second:
            Sensor number for second measurement channel

        third:
            Sensor number for third measurement channel

        Raises
        ------

        ValueError, if none of the measurement channels is enabled

        """

        self.sensor = SensorConfiguration(first, second, third)
        self.sensor.check()

        dataSets = self.Can.data_sets(*map(bool, (first, second, third)))
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
            calcSamplingRate(iPrescaler, iAcquisitionTime, iOversampling) + 0.5
        )
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
        self.sMsgLoss = "Acceleration(" + str(format(0, "3.3f")) + "%)"
        self.GuiPackage = {"X": [], "Y": [], "Z": []}

    def vStuAddr(self, sStuAddr):
        self.sStuAddr = sStuAddr

    def guiProcessStop(self):
        if hasattr(self, "tSocket"):
            try:
                self.vGraphSend(["Run", False])
            except (ConnectionAbortedError, OSError):
                pass
            self.tSocket.close()
        if hasattr(self, "guiProcess"):
            self.guiProcess.terminate()
            self.guiProcess.join()

    def vGraphSend(self, data):
        bSend = True
        data = tArray2Binary(data)
        while bSend:
            self.tSocket.sendall(data)
            sleep(0.1)
            ack = self.tSocket.recv(2**10)
            self.logger.debug(f"Received acknowledgment: {ack}")
            if ack is not None and ack == data:
                bSend = False

    def guiProcessRestart(self):
        self.guiProcessStop()

        self.guiProcess = multiprocessing.Process(
            target=vPlotter,
            args=(self.iPloterSocketPort, self.logger.getEffectiveLevel()),
        )
        self.guiProcess.start()

        # Wait until socket of GUI application is ready
        connection_established = False
        while not connection_established:
            try:
                self.logger.debug("Try to initialize socket")
                self.tSocket = socket.socket(
                    socket.AF_INET, socket.SOCK_STREAM
                )
                self.tSocket.connect(
                    (self.sPloterSocketHost, self.iPloterSocketPort)
                )
                connection_established = True
            except ConnectionError:
                sleep(0.1)

        self.logger.debug("Initialized socket")

        self.vGraphSend(["dataBlockSize", self.iGraphBlockSize])
        self.vGraphSend(["sampleInterval", self.iGraphSampleInterval])
        self.vGraphSend(["xDim", Watch["DisplayTimeMax"]])
        self.update_packet_loss()
        if self.sensor.first:
            self.vGraphSend(["lineNameX", "Signal 1"])
        if self.sensor.second:
            self.vGraphSend(["lineNameY", "Signal 2"])
        if self.sensor.third:
            self.vGraphSend(["lineNameZ", "Signal 3"])
        self.vGraphSend(["Plot", True])

    def update_graph_data(self, x=0, y=0, z=0):
        timeStampNow = int(round(time() * 1000))
        elapsed_time_ms = timeStampNow - self.tDataPointTimeStamp
        # Only add a single data sample for each part of the current block
        if elapsed_time_ms <= self.iGraphSampleInterval / self.iGraphBlockSize:
            return

        self.tDataPointTimeStamp = timeStampNow
        self.GuiPackage["X"].append(x)
        self.GuiPackage["Y"].append(y)
        self.GuiPackage["Z"].append(z)
        # Send the data to the plotter, after we collected all samples for the
        # current block
        if len(self.GuiPackage["X"]) >= self.iGraphBlockSize:
            try:
                self.tSocket.sendall(tArray2Binary(["data", self.GuiPackage]))
            except (ConnectionAbortedError, ConnectionResetError):
                # Closing the plotter window quits the plotter process and
                # there might be not socket to send data to after that
                pass

            self.GuiPackage = {"X": [], "Y": [], "Z": []}

    def update_packet_loss(self, msgCounter=-1):
        if self.iMsgCounterLast == -1:
            self.iMsgCounterLast = msgCounter
        else:
            self.iMsgCounterLast += 1
            self.iMsgCounterLast %= 256
        if self.iMsgCounterLast != msgCounter:
            iLost = (
                msgCounter - self.iMsgCounterLast
                if msgCounter > self.iMsgCounterLast
                else 0xFF - self.iMsgCounterLast + msgCounter
            )
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
            sMsgLoss = f"Signal Quality: {pakets_received:3.2f} %"
            if sMsgLoss != self.sMsgLoss:
                self.sMsgLoss = sMsgLoss
                try:
                    self.tSocket.sendall(
                        tArray2Binary(["diagramName", self.sMsgLoss])
                    )
                except (ConnectionAbortedError, ConnectionResetError):
                    # Closing the plotter window quits the plotter process and
                    # there might be no socket to send data to after that
                    pass

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
                    self.Can.BlueToothAddress(MyToolItNetworkNr["STU1"])
                )
            )
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
                self.Can.read_acceleration_sensor_range_in_g()
            )
            success = True
        except ValueError:
            pass

        return (acceleration_range_g, success)

    def update_sensor_config(self) -> None:
        """Update sensor configuration in the connected sensor device"""

        # We use special sensor channel number `0` (currently defined as “no
        # change to channel number”) as default value.
        #
        # This should not be a problem in connection with the definition in the
        # CLI interface of ICOc, where `0` is defined as disabling the
        # measurement channel. Here we would need to enter the sensor channel
        # number to enable the measurement anyway.
        self.Can.write_sensor_config(*[
            0 if sensor is None or sensor <= 0 else sensor
            for sensor in (
                self.sensor.first,
                self.sensor.second,
                self.sensor.third,
            )
        ])

    def vDataAquisition(self):
        if self.KeyBoardInterrupt:
            return

        try:
            if self.Can.bConnected:
                self.Can.ConfigAdc(
                    MyToolItNetworkNr["STH1"],
                    self.iPrescaler,
                    self.iAquistionTime,
                    self.iOversampling,
                    AdcReference[self.sAdcRef],
                )

                # We need the acceleration range later to convert the ADC
                # acceleration values into multiples of g₀
                (
                    self.acceleration_range_g,
                    success,
                ) = self.read_acceleration_range()
                if not success:
                    print(
                        "Warning: Unable to determine sensor range from "
                        "EEPROM value — Assuming ± 100 g sensor",
                        file=stderr,
                    )
                if self.acceleration_range_g < 1:
                    print(
                        "Warning: Sensor range"
                        f" “{self.acceleration_range_g}” below 1 g — Using"
                        " range 200 instead (± 100 g sensor)",
                        file=stderr,
                    )
                    self.acceleration_range_g = 200

                # Initialize HDF output
                self.storage = Storage(
                    settings.get_output_filepath(),
                    self.sensor.streaming_configuration(),
                )
                self.data = self.storage.open()
                sensor_range = self.acceleration_range_g / 2
                self.data.add_acceleration_meta(
                    "Sensor_Range", f"± {sensor_range} g₀"
                )

                # ICOc does not use the network class to read the streaming
                # data but uses the `Read` method of the PCAN API directly.
                # This means we have to disable the read thread of the CAN
                # class first.
                self.Can.readThreadStop()
                self.guiProcessRestart()
                self.logger.info("Start Acquiring Data")
                self.vGetStreamingAccData()
            else:
                self.logger.error("Device not allocable")
        except KeyboardInterrupt:
            self.KeyBoardInterrupt = True
            self.__exit__()

    def close(self):
        if self.Can.RunReadThread:
            self.__exit__()

    def read_streaming(self):
        """Read streaming messages"""
        self.logger.debug("Add CAN read event")
        receive_event = CreateEvent(None, 0, 0, None)
        status = self.Can.pcan.SetValue(
            self.Can.m_PcanHandle, PCAN_RECEIVE_EVENT, int(receive_event)
        )

        if status != PCAN_ERROR_OK:
            error_message = self.Can.get_can_error_message(
                status, "Unable to set CAN receive event"
            )
            raise Exception(error_message)

        TIMEOUT_SECONDS = 4
        time_last_read = time()
        time_since_read = 0
        self.logger.debug("Wait for CAN data")
        while (
            self.Can.get_elapsed_time() < self.aquireEndTime
            and time_since_read <= TIMEOUT_SECONDS
            and self.guiProcess.is_alive()
        ):
            if WaitForSingleObject(receive_event, 50) == WAIT_OBJECT_0:
                self.read_streaming_messages()
                time_last_read = time()
            time_since_read = time() - time_last_read

        if time_since_read >= TIMEOUT_SECONDS:
            print(
                "Exiting program since no streaming data was received "
                f"in the last {round(time_since_read, 2)} seconds",
                file=stderr,
            )

        self.Can.pcan.SetValue(self.Can.m_PcanHandle, PCAN_RECEIVE_EVENT, 0)

    def read_streaming_messages(self):
        """Read multiple streaming messages"""
        status = PCAN_ERROR_OK

        self.logger.debug("Read streaming messages")

        while status != PCAN_ERROR_QRCVEMPTY:
            status = self.read_streaming_message()
            if status not in {PCAN_ERROR_OK, PCAN_ERROR_QRCVEMPTY}:
                error_message = self.Can.get_can_error_message(
                    status, "Unable to read streaming message"
                )
                raise Exception(error_message)

    def read_streaming_message(self):
        """Read single streaming message"""

        status, message, timestamp = self.Can.pcan.Read(self.Can.m_PcanHandle)
        if status == PCAN_ERROR_OK:
            timestamp_ms = (
                timestamp.millis_overflow * (2**32)
                + timestamp.millis
                + timestamp.micros / 1000
            )
            if message.ID == self.AccAckExpected.ID:
                self.update_packet_loss(message.DATA[1])
                self.update_acceleration_data(message.DATA, timestamp_ms)

        return status

    def vGetStreamingAccDataProcess(self):
        try:
            # Read streaming messages until
            # - plotter window is closed or
            # - runtime is up.
            self.read_streaming()

            self.__exit__()
        except KeyboardInterrupt:
            self.KeyBoardInterrupt = True
            print("Data acquisition terminated")
            self.__exit__()

    def vGetStreamingAccDataAccStart(self):
        if not any((self.sensor.first, self.sensor.second, self.sensor.third)):
            return True

        ack = None
        accFormat = AtvcFormat()
        accFormat.asbyte = 0
        accFormat.b.bStreaming = 1
        accFormat.b.bNumber1 = int(bool(self.sensor.first))
        accFormat.b.bNumber2 = int(bool(self.sensor.second))
        accFormat.b.bNumber3 = int(bool(self.sensor.third))
        accFormat.b.u3DataSets = self.tAccDataFormat
        cmd = self.Can.CanCmd(
            MyToolItBlock["Streaming"], MyToolItStreaming["Data"], 0, 0
        )
        self.AccAckExpected = self.Can.CanMessage20(
            cmd,
            MyToolItNetworkNr["STH1"],
            MyToolItNetworkNr["SPU1"],
            [accFormat.asbyte],
        )
        cmd = self.Can.CanCmd(
            MyToolItBlock["Streaming"], MyToolItStreaming["Data"], 1, 0
        )
        message = self.Can.CanMessage20(
            cmd,
            MyToolItNetworkNr["SPU1"],
            MyToolItNetworkNr["STH1"],
            [accFormat.asbyte],
        )
        self.logger.info(
            "MsgId/Subpayload(Acc): "
            + hex(message.ID)
            + "/"
            + hex(accFormat.asbyte)
        )
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
            self.logger.error(
                f"No acknowledge received from STH “{self.iAddress}”"
            )
            self.aquireEndTime = currentTime
        elif self.iRunTime == 0:
            self.aquireEndTime = currentTime + (1 << 32)
        else:
            self.aquireEndTime = currentTime + self.iRunTime * 1000
        self.vGetStreamingAccDataProcess()

    def update_acceleration_data(self, data, timestamp_ms):
        timestamp = timestamp_ms / 1000
        counter = data[1]

        axes = [
            axis
            for axis, activated in (
                ("x", self.sensor.first),
                ("y", self.sensor.second),
                ("z", self.sensor.third),
            )
            if activated
        ]

        if len(axes) <= 0:
            return

        convert_acceleration = partial(
            convert_raw_to_g, max_value=self.acceleration_range_g
        )
        number_values = 3 if self.tAccDataFormat == DataSets[3] else len(axes)
        values = [
            convert_acceleration(byte_list_to_int(data[start : start + 2]))
            for start in range(2, 2 + number_values * 2, 2)
        ]

        self.data.add_streaming_data(
            StreamingData(values=values, counter=counter, timestamp=timestamp)
        )
        if self.tAccDataFormat == DataSets[1]:
            axis_values = {axis: value for axis, value in zip(axes, values)}
            self.update_graph_data(**axis_values)
        elif self.tAccDataFormat == DataSets[3]:
            axis = axes[0]
            self.update_graph_data(**{axis: values[0]})
        else:
            self.logger.error("Wrong Ack format")

    def ReadMessage(self):
        status, message, timestamp = self.Can.pcan.Read(self.Can.m_PcanHandle)
        if status == PCAN_ERROR_OK:
            peakCanTimeStamp = (
                timestamp.millis_overflow * (2**32)
                + timestamp.millis
                + timestamp.micros / 1000
            )
            result = {
                "CanMsg": message,
                "PcTime": self.Can.get_elapsed_time(),
                "PeakCanTime": peakCanTimeStamp,
            }
            return result

        if status != PCAN_ERROR_QRCVEMPTY:
            error_message = self.Can.get_can_error_message(
                status, "Unexpected CAN status value"
            )
            self.logger.error(error_message)
            print(error_message, file=stderr)
            raise Exception(error_message)

        return None

    def _vRunConsoleStartupLoggerPrint(self):
        self.logger.info(f"STH Name: {self.sth_name}")
        self.logger.info(f"Bluetooth Address: {self.iAddress}")
        self.logger.info(f"Connect to STH: {self.connect}")
        self.logger.info(f"Run Time: {self.iRunTime} s")
        self.logger.info(f"Prescaler: {self.iPrescaler}")
        aqcuisition_time = AdcAcquisitionTime.inverse[self.iAquistionTime]
        oversampling_rate = AdcOverSamplingRate.inverse[self.iOversampling]
        self.logger.info(f"Acquisition Time: {aqcuisition_time}")
        self.logger.info(f"Oversampling Rate: {oversampling_rate}")
        self.logger.info(f"Reference Voltage: {self.sAdcRef}")
        data_sets = DataSets.inverse[self.tAccDataFormat]
        self.logger.info(f"Data Sets: {data_sets}")
        self.logger.info(f"Sensors: {self.sensor}")

    def _vRunConsoleStartup(self):
        self._vRunConsoleStartupLoggerPrint()

    def vRunConsoleAutoConnect(self):
        if self.iAddress not in {0, "0", "0x0"}:
            self.Can.bBlueToothConnectPollingAddress(
                MyToolItNetworkNr["STU1"], self.iAddress
            )
        else:
            self.Can.bBlueToothConnectPollingName(
                MyToolItNetworkNr["STU1"], self.sth_name, log=False
            )
        if self.Can.bConnected:
            self.update_sensor_config()
            self.vDataAquisition()

    def run(self):
        self._vRunConsoleStartup()
        self.reset()
        if self.connect:
            self.vRunConsoleAutoConnect()
        self.close()


if __name__ == "__main__":
    CommandLineInterface().run()
