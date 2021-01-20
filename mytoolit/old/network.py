from array import array
from ctypes import c_byte
from logging import getLogger, FileHandler, Formatter
from math import log
from struct import pack, unpack
from sys import stderr
from threading import Lock, Thread
from time import time, sleep

from can.interfaces.pcan.basic import (PCAN_BAUD_1M, PCAN_BUSOFF_AUTORESET,
                                       PCAN_ERROR_OK, PCAN_ERROR_QOVERRUN,
                                       PCAN_PARAMETER_ON, PCAN_USBBUS1,
                                       PCANBasic)
from semantic_version import Version

from mytoolit.can import (Command, ErrorStatusSTH, ErrorStatusSTU, Identifier,
                          Message, Node, NodeStatusSTH, NodeStatusSTU)
from mytoolit.eeprom import EEPROMStatus
from mytoolit.config import settings
from mytoolit.old.Logger import Logger
from mytoolit.old.MyToolItNetworkNumbers import MyToolItNetworkName
from mytoolit.old.MyToolItCommands import (
    AdcAcquisitionTimeName,
    AdcOverSamplingRateName,
    AdcMax,
    ActiveState,
    AsciiStringWordLittleEndian,
    AtvcFormat,
    BluetoothTime,
    byte_list_to_int,
    calcSamplingRate,
    CalibrationMeassurement,
    CalibMeassurementActionName,
    CalibMeassurementTypeName,
    DataSets,
    int_to_byte_list,
    int_to_mac_address,
    MyToolItBlock,
    MyToolItConfiguration,
    MyToolItEeprom,
    MyToolItProductData,
    MyToolItStreaming,
    MyToolItSystem,
    NodeState,
    NetworkState,
    payload2Hex,
    sArray2String,
    sDateClock,
    SystemCommandBlueTooth,
    VRefName,
)


class Network(object):
    """A class used to communicate over CAN

    Objects of this class will create a thread that reads data from the CAN
    bus. The thread will store the read data into a list, appending the latest
    data at the end.

    """

    def __init__(self,
                 testMethodName='unknown_test_method.txt',
                 testMethodNameError='unknown_test_method_error.txt',
                 sender=Node('SPU 1').value,
                 receiver=Node('STH 1').value,
                 prescaler=2,
                 acquisition=8,
                 oversampling=64,
                 FreshLog=False):
        # Start with disconnected Bluetooth connection
        self.bConnected = False
        # Set default sender (number) for CAN bus
        self.sender = sender
        # Set default receiver (number) for CAN bus
        self.receiver = receiver
        self.Logger = Logger(testMethodName,
                             testMethodNameError,
                             FreshLog=FreshLog)
        self.Logger.Info(str(sDateClock()))
        self.start_time = int(round(time() * 1000))
        self.pcan = PCANBasic()
        self.m_PcanHandle = PCAN_USBBUS1
        self.bError = False
        self.RunReadThread = False
        self.CanTimeStampStart(0)
        self.AdcConfig = {
            "Prescaler": prescaler,
            "AquisitionTime": acquisition,
            "OverSamplingRate": oversampling
        }
        # Configuration for acceleration streaming
        # - Single Request
        # - Do not collect any data (axes inactive)
        self.AccConfig = AtvcFormat()
        self.AccConfig.asbyte = 0
        self.AccConfig.b.bStreaming = 1
        # Configuration for voltage streaming
        # - Single Request
        # - Do not collect any data (voltages inactive)
        self.VoltageConfig = AtvcFormat()
        self.VoltageConfig.asbyte = 0
        self.VoltageConfig.b.bStreaming = 1
        result = self.pcan.Initialize(self.m_PcanHandle, PCAN_BAUD_1M)
        if result != PCAN_ERROR_OK:
            raise Exception(
                self.__get_error_message("Unable to initialize CAN hardware",
                                         result))

        # Reset the CAN controller if a bus-off state is detected
        result = self.pcan.SetValue(self.m_PcanHandle, PCAN_BUSOFF_AUTORESET,
                                    PCAN_PARAMETER_ON)
        if result != PCAN_ERROR_OK:
            print(self.__get_error_message(
                "Unable to set auto reset on CAN bus-off state", result),
                  file=stderr)
        self.tCanReadWriteMutex = Lock()
        self.reset()
        self.ReadThreadReset()

        logger = getLogger('can')
        # We use `Logger` in the code below, since the `.logger` attribute
        # stores internal DynaConf data
        logger.setLevel(settings.Logger.can.level)
        handler = FileHandler('can.log', 'w', 'utf-8', delay=True)
        handler.setFormatter(Formatter('{asctime} {message}', style='{'))
        logger.addHandler(handler)

    def __exit__(self):
        try:
            if not self.bError:
                if self.RunReadThread:
                    self.readThreadStop()
                else:
                    self.Logger.Error("Peak CAN Message Over Run")
                    self.bError = True
            self.reset()
            self.tCanReadWriteMutex.acquire()  # Insane
            self.pcan.Uninitialize(self.m_PcanHandle)
            self.tCanReadWriteMutex.release()
            sleep(1)
            [_iDs, cmds] = self.ReadMessageStatistics()
            for cmd, value in cmds.items():
                block_command = Identifier(command=cmd).block_command_name()
                self.Logger.Info(f"{block_command} received {value} times")
            self.Logger.__exit__()
        except:
            pass

    def __exitError(self, sErrorMessage):
        try:
            self.Logger.ErrorFlag = True
            self.__exit__()
            self.bError = True
        except Exception:
            self.pcan.Uninitialize(self.m_PcanHandle)
            print("Error: " + sErrorMessage)
        raise Exception(sErrorMessage)

    def __close__(self):
        try:
            self.__exit__()
        except:
            pass

    def __get_error_message(self, description, error_code):
        """Return an error message for a given error code

        Parameters
        ----------

        description:
            A textual description of the current error condition
        error_code:
            A PCAN error code

        Returns
        -------

        A error message consisting of description and the textual
        representation of the given error code
        """

        translated_error_code = self.pcan.GetErrorText(error_code)[1].decode()
        return f"{description}: {translated_error_code}"

    def vLogNameChange(self, testMethodName, testMethodNameError):
        self.Logger.vRename(testMethodName, testMethodNameError)

    def vLogNameCloseInterval(self, testMethodName, testMethodNameError):
        self.Logger.vClose()
        self.Logger = Logger(testMethodName, testMethodNameError)

    def vLogDel(self):
        self.Logger.vDel()

    def vSetReceiver(self, receiver):
        self.receiver = receiver

    def readThreadStop(self):
        try:
            if self.RunReadThread:
                self.RunReadThread = False
                self.readThread.terminate()
                self.readThread.join()
        except:
            pass

    def ReadThreadReset(self):
        try:
            self.readThreadStop()
            self.readArray = []
            sleep(0.2)
            self.RunReadThread = True
            self.readThread = Thread(target=self.ReadMessage,
                                     name="CanReadThread")
            self.readThread.start()
            self.reset()
            sleep(0.2)
        except:
            pass

    def reset(self):
        with self.tCanReadWriteMutex:
            self.pcan.Reset(self.m_PcanHandle)

    def CanTimeStampStart(self, CanTimeStampStart):
        self.PeakCanTimeStampStart = CanTimeStampStart

    def WriteFrame(self, CanMsg):
        returnMessage = CanMsg
        if returnMessage == "Error":
            return returnMessage

        with self.tCanReadWriteMutex:
            status = self.pcan.Write(self.m_PcanHandle, CanMsg)
        if status != PCAN_ERROR_OK:
            error_message = self.__get_error_message(
                "Unable to write CAN message", status)
            self.Logger.Error(error_message)
            self.__exitError(error_message)

        # Only log message, if writing was successful
        getLogger('can').debug(f"{Message(CanMsg)}")

        return status

    def WriteFrameWaitAckOk(self, message):
        payload = list(message["CanMsg"].DATA)
        returnMessage = {
            "ID": hex(message["CanMsg"].ID),
            "Payload": payload,
            "PcTime": message["PcTime"],
            "CanTime": message["PeakCanTime"]
        }
        return returnMessage

    def WriteFrameWaitAckError(self, message, bError, printLog):
        identifier = Identifier(message["CanMsg"].ID)
        payload = payload2Hex(message["CanMsg"].DATA)
        info = (f"Error acknowledgement received: {identifier}; "
                if bError else
                f"Acknowledgement received (error assumed): {identifier}; ")
        info += f"Payload: {payload}"
        self.Logger.Error(info)
        if printLog:
            print(info)
        return self.WriteFrameWaitAckOk(message)

    def WriteFrameWaitAckTimeOut(self, CanMsg, printLog):
        identifier = Identifier(CanMsg.ID)
        payload = payload2Hex(CanMsg.DATA)
        message = (f"No (error) acknowledgement received: {identifier}; " +
                   f"Payload: {payload}")
        self.Logger.Warning(message)
        if printLog:
            print(message)
        return "Error"

    def tWriteFrameWaitAck(self,
                           CanMsg,
                           waitMs=1000,
                           currentIndex=None,
                           printLog=False,
                           assumedPayload=None,
                           bError=False,
                           sendTime=None,
                           notAckIdleWaitTimeMs=0.001):
        if waitMs < 200:
            self.__exitError(
                f"Meantime between send retry to low ({waitMs} ms)")
        if sendTime is None:
            sendTime = self.get_elapsed_time()
        if currentIndex is None or currentIndex >= self.GetReadArrayIndex():
            currentIndex = self.GetReadArrayIndex() - 1

        if printLog:
            print(f"Message ID Send: {Identifier(CanMsg.ID)}")
            print(f"Message DATA Send: {payload2Hex(CanMsg.DATA)}")
        status = self.WriteFrame(CanMsg)

        if status == "Error":
            return (status, currentIndex)

        waitTimeMax = self.get_elapsed_time() + waitMs
        CanMsgAck = Message(CanMsg).acknowledge(error=bError).to_pcan()
        CanMsgAckError = Message(CanMsg).acknowledge(
            error=not bError).to_pcan()

        while True:
            # Check timeout
            if self.get_elapsed_time() > waitTimeMax:
                return (self.WriteFrameWaitAckTimeOut(CanMsg,
                                                      printLog), currentIndex)

            # Get read message
            if currentIndex < self.GetReadArrayIndex() - 1:
                currentIndex += 1
                message = self.readArray[currentIndex]
            else:
                # No new message ready yet
                sleep(notAckIdleWaitTimeMs)
                continue

            # Message was received before sent message
            if sendTime > message["PcTime"]:
                continue

            if CanMsgAck.ID == message["CanMsg"].ID and (
                    assumedPayload is None
                    or list(message["CanMsg"].DATA) == assumedPayload):
                return (self.WriteFrameWaitAckOk(message), currentIndex)

            if CanMsgAckError.ID == message["CanMsg"].ID:
                return (self.WriteFrameWaitAckError(message, bError,
                                                    printLog), currentIndex)

    def tWriteFrameWaitAckRetries(self,
                                  CanMsg,
                                  retries=10,
                                  waitMs=1000,
                                  printLog=False,
                                  bErrorAck=False,
                                  assumedPayload=None,
                                  bErrorExit=True,
                                  notAckIdleWaitTimeMs=0.001):
        try:
            currentIndex = self.GetReadArrayIndex() - 1
            sendTime = self.get_elapsed_time()
            for _ in range(retries + 1):
                returnMessage, currentIndex = self.tWriteFrameWaitAck(
                    CanMsg,
                    waitMs=waitMs,
                    currentIndex=currentIndex,
                    printLog=printLog,
                    assumedPayload=assumedPayload,
                    bError=bErrorAck,
                    sendTime=sendTime,
                    notAckIdleWaitTimeMs=notAckIdleWaitTimeMs)
                if returnMessage != "Error":
                    return returnMessage

            identifier = Identifier(CanMsg.ID)
            payload = payload2Hex(CanMsg.DATA)
            text = (f"Message request failed: {identifier}; " +
                    f"Payload: {payload}")
            self.Logger.Error(text)
            if printLog:
                print(text)
            if bErrorExit:
                self.__exitError(f"Too many retries ({retries})")
        except KeyboardInterrupt:
            self.RunReadThread = False

    def cmdSend(self,
                receiver,
                blockCmd,
                subCmd,
                payload,
                log=True,
                retries=10,
                bErrorAck=False,
                printLog=False,
                bErrorExit=True,
                notAckIdleWaitTimeMs=0.001):
        message = Message(block=blockCmd,
                          block_command=subCmd,
                          request=True,
                          sender=self.sender,
                          receiver=receiver,
                          data=payload)
        index = self.GetReadArrayIndex()
        msgAck = self.tWriteFrameWaitAckRetries(
            message.to_pcan(),
            retries=retries,
            waitMs=1000,
            bErrorAck=bErrorAck,
            printLog=printLog,
            bErrorExit=bErrorExit,
            notAckIdleWaitTimeMs=notAckIdleWaitTimeMs)
        if msgAck == "Error" and bErrorExit:
            self.__exitError("Unable to send command")
        if log:
            can_time_stamp = msgAck["CanTime"] - self.PeakCanTimeStampStart
            prefix = "Unable to send message: " if msgAck == "Error" else ""
            log_message = f"{prefix}{message} (CAN time: {can_time_stamp})"
            self.Logger.Info(log_message)
            self.Logger.Info(f"Assumed receive message number: {index}")
        # sleep(0.2)  # synch to read thread TODO: Really kick it out?
        return index

    def cmdSendData(self,
                    receiver,
                    blockCmd,
                    subCmd,
                    payload,
                    log=True,
                    retries=10,
                    bErrorAck=False,
                    printLog=False,
                    bErrorExit=True):
        """
        Send cmd and return Ack
        """
        message = Message(block=blockCmd,
                          block_command=subCmd,
                          sender=self.sender,
                          receiver=receiver,
                          request=True,
                          data=payload).to_pcan()
        index = self.GetReadArrayIndex()
        msgAck = self.tWriteFrameWaitAckRetries(message,
                                                retries=retries,
                                                waitMs=1000,
                                                bErrorAck=bErrorAck,
                                                printLog=printLog,
                                                bErrorExit=bErrorExit)
        if msgAck != "Error" and False == bErrorExit:
            self.__exitError("Retries exceeded(" + str(retries) + " Retries)")
        if False != log:
            canCmd = self.CanCmd(blockCmd, subCmd, 1, 0)
            if "Error" != msgAck:
                self.Logger.Info(
                    MyToolItNetworkName[self.sender] + "->" +
                    MyToolItNetworkName[receiver] + "(CanTimeStamp: " +
                    str(msgAck["CanTime"] - self.PeakCanTimeStampStart) +
                    "ms): " + Identifier(command=canCmd).block_command_name() +
                    " - " + payload2Hex(payload))
            else:
                self.Logger.Info(MyToolItNetworkName[self.sender] + "->" +
                                 MyToolItNetworkName[receiver] + ": " +
                                 Identifier(
                                     command=canCmd).block_command_name() +
                                 " - " + "Error")
            self.Logger.Info("Assumed receive message number: " + str(index))
        # sleep(0.2)  # synch to read thread TODO: Really kick it out?
        return msgAck

    def reset_node(self, receiver, retries=5, log=True):
        identifier = Identifier(block='System',
                                block_command='Reset',
                                sender=self.sender,
                                receiver=receiver,
                                request=True)
        if log:
            self.Logger.Info(f"Reset {identifier.receiver_name()}")

        return_message = self.tWriteFrameWaitAckRetries(
            Message(identifier=identifier).to_pcan(), retries=retries)
        sleep(2)
        return return_message

    def u32EepromWriteRequestCounter(self, receiver):
        """
        Get EEPROM Write Request Counter, please note that the count start is
        power on
        """
        index = self.cmdSend(receiver, MyToolItBlock["EEPROM"],
                             MyToolItEeprom["WriteRequest"], [0] * 8)
        dataReadBack = self.getReadMessageData(index)[4:]
        u32WriteRequestCounter = byte_list_to_int(dataReadBack)
        self.Logger.Info("EEPROM Write Request Counter: " +
                         str(u32WriteRequestCounter))
        return u32WriteRequestCounter

    def singleValueCollect(self,
                           receiver,
                           subCmd,
                           b1,
                           b2,
                           b3,
                           log=True,
                           printLog=False):
        accFormat = AtvcFormat()
        accFormat.asbyte = 0
        accFormat.b.bNumber1 = b1
        accFormat.b.bNumber2 = b2
        accFormat.b.bNumber3 = b3
        accFormat.b.u3DataSets = DataSets[1]
        return self.cmdSend(receiver,
                            MyToolItBlock["Streaming"],
                            subCmd, [accFormat.asbyte],
                            log=log,
                            printLog=printLog)

    def ValueDataSet1(self, data, b1, b2, b3, array1, array2, array3):
        count = 0
        if False != b1:
            Acc = byte_list_to_int(data[2:4])
            array1.append(Acc)
            count += 1
        if False != b2:
            if 0 == count:
                Acc = byte_list_to_int(data[2:4])
            else:
                Acc = byte_list_to_int(data[4:6])
            array2.append(Acc)
            count += 1
        if False != b3:
            if 0 == count:
                Acc = byte_list_to_int(data[2:4])
            elif 1 == count:
                Acc = byte_list_to_int(data[4:6])
            else:
                Acc = byte_list_to_int(data[6:8])
            array3.append(Acc)
        return [array1, array2, array3]

    def ValueDataSet3(self, data, b1, b2, b3, array1, array2, array3):
        Acc1 = byte_list_to_int(data[2:4])
        Acc2 = byte_list_to_int(data[4:6])
        Acc3 = byte_list_to_int(data[6:8])
        if False != b1:
            array1.append(Acc1)
            array1.append(Acc2)
            array1.append(Acc3)
        if False != b2:
            array2.append(Acc1)
            array2.append(Acc2)
            array2.append(Acc3)
        if False != b3:
            array3.append(Acc1)
            array3.append(Acc2)
            array3.append(Acc3)
        return [array1, array2, array3]

    def singleValueArray(self, receiver, subCmd, b1, b2, b3, index):
        cmdFilter = self.CanCmd(MyToolItBlock["Streaming"], subCmd, 0, 0)
        messageIdFilter = Identifier(command=cmdFilter,
                                     sender=receiver,
                                     receiver=self.sender).value
        messageIdFilter = hex(messageIdFilter)
        data = self.getReadMessageData(index)
        messageId = self.getReadMessageId(index)
        array1 = []
        array2 = []
        array3 = []
        if messageId == messageIdFilter:
            self.ValueDataSet1(data, b1, b2, b3, array1, array2, array3)
        else:
            identifier_received = Identifier(command=int(messageId, 16))
            identifier_filtered = Identifier(command=int(messageIdFilter, 16))

            cmdRec = identifier_received.command()
            cmdFiltered = identifier_filtered.command()

            receivedCmdBlk = identifier_received.block()
            receivedCmdSub = identifier_received.command_number()
            filterCmdBlk = identifier_filtered.block()
            filterCmdSub = identifier_filtered.command_number()
            self.Logger.Error("Assumed message ID: " + str(messageIdFilter) +
                              "(" + str(cmdRec) + "); Received message ID: " +
                              str(messageId) + "(" + str(cmdFiltered) + ")")
            self.Logger.Error("Assumed command block: " + str(filterCmdBlk) +
                              f"; Received command block: {receivedCmdBlk}")
            self.Logger.Error("Assumed sub command: " + str(filterCmdSub) +
                              "; Received sub command: " + str(receivedCmdSub))
            self.__exitError("Wrong Filter ID")
        if 0 < len(array1):
            array1 = [array1[0]]
        if 0 < len(array2):
            array2 = [array2[0]]
        if 0 < len(array3):
            array3 = [array3[0]]
        return [array1, array2, array3]

    def streamingStart(self, receiver, subCmd, dataSets, b1, b2, b3, log=True):
        streamingFormat = AtvcFormat()
        streamingFormat.asbyte = 0
        streamingFormat.b.bStreaming = 1
        streamingFormat.b.bNumber1 = b1
        streamingFormat.b.bNumber2 = b2
        streamingFormat.b.bNumber3 = b3
        streamingFormat.b.u3DataSets = dataSets

        if MyToolItStreaming["Acceleration"] == subCmd:
            self.AccConfig = streamingFormat
        elif MyToolItStreaming["Voltage"] == subCmd:
            self.VoltageConfig = streamingFormat
        else:
            self.__exitError(f"Streaming unknown at streaming start: {subCmd}")
        if False != log:
            self.Logger.Info("CAN Bandwidth(Lowest, may be more): "
                             f"{self.canBandwith()} bit/s")
            self.Logger.Info("Bluetooth Bandwidth(Lowest, may be more): "
                             f"{self.bluetoothBandwidth()} bit/s")

        message = Message(block="Streaming",
                          block_command=subCmd,
                          request=True,
                          sender=self.sender,
                          receiver=receiver,
                          data=[streamingFormat.asbyte])

        if log:
            block_command = Identifier(message.id()).block_command_name()
            self.Logger.Info(f"Start sending {block_command}; "
                             f"Subpayload: {hex(streamingFormat.asbyte)}")

        indexStart = self.GetReadArrayIndex()
        self.tWriteFrameWaitAckRetries(message.to_pcan())
        return indexStart

    def streamingStop(self,
                      receiver,
                      subCmd,
                      bErrorExit=True,
                      notAckIdleWaitTimeMs=0.00005):
        streamingFormat = AtvcFormat()
        streamingFormat.asbyte = 0
        streamingFormat.b.bStreaming = 1
        streamingFormat.b.u3DataSets = DataSets[0]

        if MyToolItStreaming["Acceleration"] == subCmd:
            self.AccConfig = streamingFormat
        elif MyToolItStreaming["Voltage"] == subCmd:
            self.VoltageConfig = streamingFormat
        else:
            self.__exitError(f"Streaming unknown at streaming stop: {subCmd}")

        message = Message(block="Streaming",
                          block_command=subCmd,
                          request=True,
                          sender=self.sender,
                          receiver=receiver,
                          data=[streamingFormat.asbyte])

        self.Logger.Info(
            "_____________________________________________________________")
        self.Logger.Info(
            f"Stop Streaming - {Identifier(message.id()).block_command_name()}"
        )
        ack = self.tWriteFrameWaitAckRetries(
            message.to_pcan(),
            retries=20,
            printLog=False,
            assumedPayload=[streamingFormat.asbyte, 0, 0, 0, 0, 0, 0, 0],
            bErrorExit=bErrorExit,
            notAckIdleWaitTimeMs=notAckIdleWaitTimeMs)
        self.Logger.Info(
            "_____________________________________________________________")
        return ack

    def streamingValueCollect(self,
                              receiver,
                              subCmd,
                              dataSets,
                              b1,
                              b2,
                              b3,
                              testTimeMs,
                              log=True,
                              StartupTimeMs=0):
        if log:
            self.Logger.Info(f"Test Time: {testTimeMs} ms")
        indexStart = self.streamingStart(receiver,
                                         subCmd,
                                         dataSets,
                                         b1,
                                         b2,
                                         b3,
                                         log=log)
        if log:
            self.Logger.Info(f"indexStart: {indexStart}")
        testTimeMs += StartupTimeMs
        sleep(testTimeMs / 1000)
        self.streamingStop(receiver, subCmd)
        sleep(2)  # synch to read thread
        indexEnd = self.GetReadArrayIndex() - 180  # do not catch stop command
        countDel = 0
        while testTimeMs < self.getReadMessageTimeMs(indexStart,
                                                     indexEnd) - 0.5:
            countDel += 1
            indexEnd -= 1
        if log:
            self.Logger.Info(
                f"Deleted {countDel + 180} messages to achieve {testTimeMs} ms"
            )
            self.Logger.Info(f"indexEnd: {indexEnd}")
        if 0.2 * (indexEnd - indexStart) < countDel:
            self.Logger.Warning(
                f"Deleted {countDel + 180} messages to achieve {testTimeMs} ms"
            )

        return [indexStart, indexEnd]

    def streamingValueArray(self, receiver, streamingCmd, dataSets, b1, b2, b3,
                            indexStart, indexEnd):
        messageIdFilter = self.CanCmd(MyToolItBlock["Streaming"], streamingCmd,
                                      0, 0)
        messageIdFilter = Identifier(command=messageIdFilter,
                                     sender=receiver,
                                     receiver=self.sender).value
        messageIdFilter = hex(messageIdFilter)
        runIndex = indexStart
        array1 = []
        array2 = []
        array3 = []
        while runIndex <= indexEnd:
            data = self.getReadMessageData(runIndex)
            messageId = self.getReadMessageId(runIndex)
            if messageId == messageIdFilter:
                if DataSets[1] == dataSets:
                    [array1, array2,
                     array3] = self.ValueDataSet1(data, b1, b2, b3, array1,
                                                  array2, array3)
                elif DataSets[3] == dataSets:
                    [array1, array2,
                     array3] = self.ValueDataSet3(data, b1, b2, b3, array1,
                                                  array2, array3)
                else:
                    self.__exitError("Wrong Data Set(:" + str(dataSets) + ")")
            runIndex += 1
        return [array1, array2, array3]

    def ValueDataSet1MsgCounter(self, data, b1, b2, b3, array1, array2,
                                array3):
        if False != b1:
            array1.append(data[1])
        if False != b2:
            array2.append(data[1])
        if False != b3:
            array3.append(data[1])
        return [array1, array2, array3]

    def ValueDataSet3MsgCounter(self, data, b1, b2, b3, array1, array2,
                                array3):
        if False != b1:
            array1.append(data[1])
            array1.append(data[1])
            array1.append(data[1])
        elif False != b2:
            array2.append(data[1])
            array2.append(data[1])
            array2.append(data[1])
        elif False != b3:
            array3.append(data[1])
            array3.append(data[1])
            array3.append(data[1])
        return [array1, array2, array3]

    def streamingValueArrayMessageCounters(self, receiver, streamingCmd,
                                           dataSets, b1, b2, b3, indexStart,
                                           indexEnd):
        messageIdFilter = self.CanCmd(MyToolItBlock["Streaming"], streamingCmd,
                                      0, 0)
        messageIdFilter = Identifier(command=messageIdFilter,
                                     sender=receiver,
                                     receiver=self.sender).value
        messageIdFilter = hex(messageIdFilter)
        runIndex = indexStart
        array1 = []
        array2 = []
        array3 = []
        while runIndex <= indexEnd:
            data = self.getReadMessageData(runIndex)
            messageId = self.getReadMessageId(runIndex)
            if messageId == messageIdFilter:
                if DataSets[1] == dataSets:
                    [array1, array2, array3
                     ] = self.ValueDataSet1MsgCounter(data, b1, b2, b3, array1,
                                                      array2, array3)
                elif DataSets[3] == dataSets:
                    [array1, array2, array3
                     ] = self.ValueDataSet3MsgCounter(data, b1, b2, b3, array1,
                                                      array2, array3)
                else:
                    self.__exitError("Data Sets not available(Data Sets: " +
                                     str(dataSets) + ")")
            runIndex += 1
        return [array1, array2, array3]

    def samplingPoints(self, array1, array2, array3):
        samplingPoints = len(array1)
        samplingPoints += len(array2)
        samplingPoints += len(array3)
        return samplingPoints

    def ValueLog(self, array1, array2, array3, fCbfRecalc, preFix, postFix):
        samplingPointMax = len(array1)
        if (len(array2) > samplingPointMax):
            samplingPointMax = len(array2)
        if (len(array3) > samplingPointMax):
            samplingPointMax = len(array3)

        samplingPoints = self.samplingPoints(array1, array2, array3)
        self.Logger.Info("Received Sampling Points: " + str(samplingPoints))

        for i in range(0, samplingPointMax):
            if 0 < len(array1):
                self.Logger.Info(preFix + "X: " + str(fCbfRecalc(array1[i])) +
                                 postFix)
            if 0 < len(array2):
                self.Logger.Info(preFix + "Y: " + str(fCbfRecalc(array2[i])) +
                                 postFix)
            if 0 < len(array3):
                self.Logger.Info(preFix + "Z: " + str(fCbfRecalc(array3[i])) +
                                 postFix)
        return samplingPoints

    def streamingValueStatisticsArithmeticAverage(self, sortArray):
        arithmeticAverage = 0
        if None != arithmeticAverage:
            for Value in sortArray:
                arithmeticAverage += Value
            arithmeticAverage /= len(sortArray)
        return arithmeticAverage

    def streamingValueStatisticsSort(self, sortArray):
        if None != sortArray:
            sortArray.sort()
        return sortArray

    def streamingValueStatisticsQuantile(self, sortArray, quantil):
        if None != sortArray:
            sortArray.sort()
            samplingPoints = len(sortArray)
            if (samplingPoints % 2 == 0):
                quantilSet = sortArray[int(samplingPoints * quantil)]
                quantilSet += sortArray[int(samplingPoints * quantil - 1)]
                quantilSet /= 2
            else:
                quantilSet = sortArray[int(quantil * samplingPoints)]
        else:
            quantilSet = None
        return quantilSet

    def streamingValueStatisticsVariance(self, sortArray):
        variance = 0
        arithmeticAverage = self.streamingValueStatisticsArithmeticAverage(
            sortArray)
        if None != sortArray:
            for Value in sortArray:
                Value = (Value - arithmeticAverage)**2
                variance += Value
            variance /= len(sortArray)
        return variance

    def streamingValueStatisticsMomentOrder(self, sortArray, order):
        momentOrder = 0
        arithmeticAverage = self.streamingValueStatisticsArithmeticAverage(
            sortArray)
        standardDeviation = self.streamingValueStatisticsVariance(
            sortArray)**0.5
        if None != sortArray:
            for Value in sortArray:
                Value = (Value - arithmeticAverage) / standardDeviation
                Value = Value**order
                momentOrder += Value
            momentOrder /= len(sortArray)
        return momentOrder

    def streamingValueStatisticsValue(self, sortArray):
        statistics = {}
        statistics["Minimum"] = sortArray[0]
        statistics["Quantil1"] = self.streamingValueStatisticsQuantile(
            sortArray, 0.01)
        statistics["Quantil5"] = self.streamingValueStatisticsQuantile(
            sortArray, 0.05)
        statistics["Quantil25"] = self.streamingValueStatisticsQuantile(
            sortArray, 0.25)
        statistics["Median"] = self.streamingValueStatisticsQuantile(
            sortArray, 0.5)
        statistics["Quantil75"] = self.streamingValueStatisticsQuantile(
            sortArray, 0.75)
        statistics["Quantil95"] = self.streamingValueStatisticsQuantile(
            sortArray, 0.95)
        statistics["Quantil99"] = self.streamingValueStatisticsQuantile(
            sortArray, 0.99)
        statistics["Maximum"] = sortArray[-1]
        statistics[
            "ArithmeticAverage"] = self.streamingValueStatisticsArithmeticAverage(
                sortArray)
        statistics[
            "StandardDeviation"] = self.streamingValueStatisticsVariance(
                sortArray)**0.5
        statistics["Variance"] = self.streamingValueStatisticsVariance(
            sortArray)
        statistics["Skewness"] = self.streamingValueStatisticsMomentOrder(
            sortArray, 3)
        statistics["Kurtosis"] = self.streamingValueStatisticsMomentOrder(
            sortArray, 4)
        statistics["Data"] = sortArray
        statistics["InterQuartialRange"] = statistics[
            "Quantil75"] - statistics["Quantil25"]
        statistics[
            "90PRange"] = statistics["Quantil95"] - statistics["Quantil5"]
        statistics[
            "98PRange"] = statistics["Quantil99"] - statistics["Quantil1"]
        statistics["TotalRange"] = sortArray[-1] - sortArray[0]
        return statistics

    def streamingValueStatistics(self, Array1, Array2, Array3):
        sortArray1 = Array1.copy()
        sortArray2 = Array2.copy()
        sortArray3 = Array3.copy()
        sortArray1 = self.streamingValueStatisticsSort(sortArray1)
        sortArray2 = self.streamingValueStatisticsSort(sortArray2)
        sortArray3 = self.streamingValueStatisticsSort(sortArray3)

        statistics = {"Value1": None, "Value2": None, "Value3": None}
        if 0 < len(sortArray1):
            statistics["Value1"] = self.streamingValueStatisticsValue(
                sortArray1)
        if 0 < len(sortArray2):
            statistics["Value2"] = self.streamingValueStatisticsValue(
                sortArray2)
        if 0 < len(sortArray3):
            statistics["Value3"] = self.streamingValueStatisticsValue(
                sortArray3)
        return statistics

    def signalIndicators(self, array1, array2, array3):
        statistics = self.streamingValueStatistics(array1, array2, array3)
        for key, stat in statistics.items():
            if None != stat:
                self.Logger.Info(
                    "____________________________________________________")
                self.Logger.Info(key)
                self.Logger.Info("Minimum: " + str(stat["Minimum"]))
                self.Logger.Info("Quantil 1%: " + str(stat["Quantil1"]))
                self.Logger.Info("Quantil 5%: " + str(stat["Quantil5"]))
                self.Logger.Info("Quantil 25%: " + str(stat["Quantil25"]))
                self.Logger.Info("Median: " + str(stat["Median"]))
                self.Logger.Info("Quantil 75%: " + str(stat["Quantil75"]))
                self.Logger.Info("Quantil 95%: " + str(stat["Quantil95"]))
                self.Logger.Info("Quantil 99%: " + str(stat["Quantil99"]))
                self.Logger.Info("Maximum: " + str(stat["Maximum"]))
                self.Logger.Info("Arithmetic Average: " +
                                 str(stat["ArithmeticAverage"]))
                self.Logger.Info("Standard Deviation: " +
                                 str(stat["StandardDeviation"]))
                self.Logger.Info("Variance: " + str(stat["Variance"]))
                self.Logger.Info("Skewness: " + str(stat["Skewness"]))
                self.Logger.Info("Kurtosis: " + str(stat["Kurtosis"]))
                self.Logger.Info("Inter Quartial Range: " +
                                 str(stat["InterQuartialRange"]))
                self.Logger.Info("90%-Range: " + str(stat["90PRange"]))
                self.Logger.Info("98%-Range: " + str(stat["98PRange"]))
                self.Logger.Info("Total Range: " + str(stat["TotalRange"]))
                SNR = 20 * log((stat["StandardDeviation"] / AdcMax), 10)
                self.Logger.Info("SNR: " + str(SNR))
                self.Logger.Info(
                    "____________________________________________________")
        return statistics

    def dataPointsTotal(self, b1, b2, b3):
        return [bool(b1), bool(b2), bool(b3)].count(True)

    def dataSetsCan20(self, b1, b2, b3):
        dataSets = [bool(b1), bool(b2), bool(b3)].count(True)
        if 0 == dataSets:
            pass
        elif 1 == dataSets:
            dataSets = 3
        else:
            dataSets = 1
        return dataSets

    def bandwith(self):
        samplingRate = calcSamplingRate(self.AdcConfig["Prescaler"],
                                        self.AdcConfig["AquisitionTime"],
                                        self.AdcConfig["OverSamplingRate"])
        dataSetsAcc = self.dataSetsCan20(self.AccConfig.b.bNumber1,
                                         self.AccConfig.b.bNumber2,
                                         self.AccConfig.b.bNumber3)
        dataSetsVoltage = self.dataSetsCan20(self.VoltageConfig.b.bNumber1,
                                             self.VoltageConfig.b.bNumber2,
                                             self.VoltageConfig.b.bNumber3)
        dataPointsAcc = self.dataPointsTotal(self.AccConfig.b.bNumber1,
                                             self.AccConfig.b.bNumber2,
                                             self.AccConfig.b.bNumber3)
        dataPointsVoltage = self.dataPointsTotal(self.VoltageConfig.b.bNumber1,
                                                 self.VoltageConfig.b.bNumber2,
                                                 self.VoltageConfig.b.bNumber3)
        totalDataPoints = dataPointsAcc + dataPointsVoltage
        msgAcc = samplingRate / totalDataPoints
        if 0 < dataSetsAcc:
            msgAcc /= dataSetsAcc
        else:
            msgAcc = 0
        msgVoltage = samplingRate / totalDataPoints
        if 0 < dataSetsVoltage:
            msgVoltage /= dataSetsVoltage
        else:
            msgVoltage = 0
        return [msgAcc, msgVoltage, dataSetsAcc, dataSetsVoltage]

    def canBandwith(self):
        [msgAcc, msgVoltage, dataSetsAcc, dataSetsVoltage] = self.bandwith()
        # (Header + Subheader(Message Counter) + data)*msg/s
        bitsAcc = (67 + 16 + dataSetsAcc * 16) * msgAcc
        bitsVoltage = (67 + 16 + dataSetsVoltage * 16) * msgVoltage
        return (bitsAcc + bitsVoltage)

    def bluetoothBandwidth(self):
        [msgAcc, msgVoltage, dataSetsAcc, dataSetsVoltage] = self.bandwith()
        # (Header + Subheader(Message Counter) + data)/samples
        bitsAcc = (32 + 16 + dataSetsAcc * 16) * msgAcc
        bitsVoltage = (32 + 16 + dataSetsVoltage * 16) * msgVoltage

        return (bitsAcc + bitsVoltage)

    def ConfigAdc(self,
                  receiver,
                  preq,
                  aquistionTime,
                  oversampling,
                  adcRef,
                  log=True):
        self.AdcConfig = {
            "Prescaler": preq,
            "AquisitionTime": aquistionTime,
            "OverSamplingRate": oversampling
        }
        if False != log:
            self.Logger.Info("Config ADC - Prescaler: " + str(preq) + "/" +
                             str(AdcAcquisitionTimeName[aquistionTime]) + "/" +
                             str(AdcOverSamplingRateName[oversampling]) + "/" +
                             str(VRefName[adcRef]))
            self.Logger.Info(
                "Calculated Sampling Rate: " +
                str(calcSamplingRate(preq, aquistionTime, oversampling)))
        byte1 = 1 << 7  # Set Sampling Rate
        cmd = self.CanCmd(MyToolItBlock["Configuration"],
                          MyToolItConfiguration["Acceleration"], 1, 0)
        message = self.CanMessage20(
            cmd, self.sender, receiver,
            [byte1, preq, aquistionTime, oversampling, adcRef, 0, 0, 0])
        return self.tWriteFrameWaitAckRetries(message, retries=5)["Payload"]

    def calibMeasurement(self,
                         receiver,
                         u2Action,
                         signal,
                         dimension,
                         vRef,
                         log=True,
                         retries=3,
                         bSet=True,
                         bErrorAck=False,
                         bReset=False,
                         printLog=False):

        messageIdFilter = hex(
            Identifier(command=Command(block="Configuration",
                                       block_command="CalibrateMeasurement",
                                       error=bErrorAck),
                       sender=receiver,
                       receiver=self.sender).value)
        byte1 = CalibrationMeassurement()
        byte1.asbyte = 0
        byte1.b.bReset = bReset
        byte1.b.u2Action = u2Action
        byte1.b.bSet = bSet
        if False != log:
            self.Logger.Info(CalibMeassurementActionName[u2Action])
            self.Logger.Info(CalibMeassurementTypeName[signal] +
                             str(dimension))
            self.Logger.Info(VRefName[vRef])
        calibPayload = [byte1.asbyte, signal, dimension, vRef, 0, 0, 0, 0]
        indexAssumed = self.cmdSend(
            receiver,
            MyToolItBlock["Configuration"],
            MyToolItConfiguration["CalibrateMeasurement"],
            calibPayload,
            log=log,
            retries=retries,
            bErrorAck=bErrorAck,
            printLog=printLog)
        indexRun = indexAssumed
        indexEnd = self.GetReadArrayIndex()
        returnAck = []
        while indexRun < indexEnd:
            if messageIdFilter == self.getReadMessageId(indexRun):
                returnAck = self.getReadMessageData(indexRun)
                break
            indexRun += indexRun
        if indexRun != indexAssumed:
            self.Logger.Warning(
                "Calibration Measurement Index Miss (Assumed/Truly): " +
                str(indexAssumed) + "/" + str(indexRun))
        if indexRun == indexEnd:
            self.Logger.Error("Calibration Measurement Fail Request")
        return returnAck

    def statisticalData(self,
                        receiver,
                        subCmd,
                        log=True,
                        retries=3,
                        bErrorAck=False,
                        printLog=False):
        msgAck = self.cmdSendData(receiver,
                                  MyToolItBlock["StatisticalData"],
                                  subCmd, [],
                                  log=log,
                                  retries=retries,
                                  bErrorAck=bErrorAck,
                                  printLog=printLog)
        return msgAck["Payload"]

    def node_status(self, receiver):
        message = Message(block='System',
                          block_command='Node Status',
                          request=True,
                          sender=self.sender,
                          receiver=receiver,
                          data=[0] * 8)
        psw0 = self.tWriteFrameWaitAckRetries(message.to_pcan(),
                                              retries=5)["Payload"]

        if Node(receiver).is_sth():
            return NodeStatusSTH(psw0[0:4])
        return NodeStatusSTU(psw0[0:4])

    def error_status(self, receiver):
        message = Message(block='System',
                          block_command='Error Status',
                          request=True,
                          sender=self.sender,
                          receiver=receiver,
                          data=[0] * 8)

        payload = self.tWriteFrameWaitAckRetries(message.to_pcan(),
                                                 retries=5)["Payload"]
        status_word_1_bytes = payload[0:4]
        if Node(receiver).is_sth():
            return ErrorStatusSTH(status_word_1_bytes)
        return ErrorStatusSTU(status_word_1_bytes)

    def get_elapsed_time(self):
        """Return the time since the initialization of the CAN object

        Returns
        -------

        The time in milliseconds since the initialization

        Example
        -------

        >>> network = Network()
        >>> elapsed_time = network.get_elapsed_time()
        >>> 0 <= elapsed_time < 1000
        True
        >>> network.__exit__()
        """

        return int(round(time() * 1000)) - int(self.start_time)

    def CanMessage20(self, command=0, sender=0, receiver=0, data=[]):
        if len(data) > 8:
            return "Error"

        return Message(command=command,
                       sender=sender,
                       receiver=receiver,
                       data=data).to_pcan()

    def CanCmd(self, block, cmd, request=1, error=0):
        """Return the binary representation of a MyTooliT CAN command

        Parameters
        ----------

        block:
            The block that contains the command
        cmd:
            The command inside the block that should be issued
        request:
            Specifies if you want to request (`1`) or acknowledge (`0`) the
            command
        error:
            Specifies if you want to set the error bit (`1`) or not (`0`).
            Please note that the values above are swapped according to the old
            documentation. According to the usage in the tool, it makes sense
            that the value are correct, since most calls of this function use
            `0` as argument for the error value.

        Returns
        -------

        A 16 bit integer number representing the requested command
        """

        # TODO: This method does not use `self` at all. Maybe it makes sense to
        # remove this code from the class and use a standalone function
        # instead.
        return Command(block=block,
                       block_command=cmd,
                       request=request,
                       error=error).value

    def cTypesArrayToArray(self, dataArray, Offset, end):
        counter = 0
        Array = []
        for item in dataArray:
            if Offset <= counter:
                Array.append(chr(item))
            if end <= counter:
                break
            counter += 1

        return Array

    def ReadMessageStatistics(self):
        iDs = {}
        cmds = {}

        # We start at index 1, since the first entry contains a spurious
        # message inserted by the method `ReadThreadReset`
        for i in range(1, self.GetReadArrayIndex()):
            msg = self.readArray[i]["CanMsg"]
            if msg.ID in iDs:
                iDs[msg.ID] += 1
            else:
                iDs[msg.ID] = 1

        for iD in iDs:
            command = Identifier(iD).command()
            cmds[command] = iDs[iD]

        return [iDs, cmds]

    def ReadMessage(self):
        while self.RunReadThread:
            try:
                self.tCanReadWriteMutex.acquire()
                status, message, timestamp = self.pcan.Read(self.m_PcanHandle)
                self.tCanReadWriteMutex.release()
                if status == PCAN_ERROR_OK:
                    peakCanTimeStamp = (timestamp.millis_overflow * 2**32 +
                                        timestamp.millis +
                                        timestamp.micros / 1000)
                    self.readArray.append({
                        "CanMsg": message,
                        "PcTime": self.get_elapsed_time(),
                        "PeakCanTime": peakCanTimeStamp
                    })
                    getLogger('can').debug(f"{Message(message)}")
                elif status == PCAN_ERROR_QOVERRUN:
                    self.Logger.Error("RxOverRun")
                    print("RxOverRun")
                    self.RunReadThread = False
            except KeyboardInterrupt:
                self.RunReadThread = False

    def getReadMessage(self, element):
        return self.readArray[element]["CanMsg"]

    def getReadMessageId(self, element):
        return hex(self.getReadMessage(element).ID)

    def getReadMessageData(self, element):
        data = []
        for item in self.getReadMessage(element).DATA:
            data.append(item)
        return data

    def getReadMessageTimeStampMs(self, element):
        return self.readArray[element][
            "PeakCanTime"] - self.PeakCanTimeStampStart

    def getReadMessageTimeMs(self, preElement, postElement):
        return self.getReadMessageTimeStampMs(
            postElement) - self.getReadMessageTimeStampMs(preElement)

    def GetReadArrayIndex(self):
        return len(self.readArray)

    def BlueToothCmd(self, receiver, subCmd):
        cmd = self.CanCmd(MyToolItBlock["System"], MyToolItSystem["Bluetooth"],
                          1, 0)
        payload = [subCmd, 0, 0, 0, 0, 0, 0, 0]
        message = self.CanMessage20(cmd, self.sender, receiver, payload)
        ack = self.tWriteFrameWaitAckRetries(message, retries=2)["Payload"][2:]
        ack = AsciiStringWordLittleEndian(ack)
        return ack

    def vBlueToothConnectConnect(self, receiver, log=True):
        if False != log:
            self.Logger.Info("Bluetooth connect")
        cmd = self.CanCmd(MyToolItBlock["System"], MyToolItSystem["Bluetooth"],
                          1, 0)
        message = self.CanMessage20(
            cmd, self.sender, receiver,
            [SystemCommandBlueTooth["Connect"], 0, 0, 0, 0, 0, 0, 0])
        return self.tWriteFrameWaitAckRetries(message, retries=2)

    def iBlueToothConnectTotalScannedDeviceNr(self, receiver, log=True):
        if log:
            self.Logger.Info("Get number of available devices")
        cmd = self.CanCmd(MyToolItBlock["System"], MyToolItSystem["Bluetooth"],
                          1, 0)
        message = self.CanMessage20(cmd, self.sender, receiver, [
            SystemCommandBlueTooth["GetNumberAvailableDevices"], 0, 0, 0, 0, 0,
            0, 0
        ])
        msg = self.tWriteFrameWaitAckRetries(message, retries=2)
        return (int(sArray2String(msg["Payload"][2:])))

    def bBlueToothConnectDeviceConnect(self, receiver, iDeviceNr):
        cmd = self.CanCmd(MyToolItBlock["System"], MyToolItSystem["Bluetooth"],
                          1, 0)
        message = self.CanMessage20(cmd, self.sender, receiver, [
            SystemCommandBlueTooth["DeviceConnect"], iDeviceNr, 0, 0, 0, 0, 0,
            0
        ])
        return (0 != self.tWriteFrameWaitAckRetries(message,
                                                    retries=2)["Payload"][2])

    def bBlueToothCheckConnect(self, receiver):
        cmd = self.CanCmd(MyToolItBlock["System"], MyToolItSystem["Bluetooth"],
                          1, 0)
        message = self.CanMessage20(cmd, self.sender, receiver, [
            SystemCommandBlueTooth["DeviceCheckConnected"], 0, 0, 0, 0, 0, 0, 0
        ])
        connectToDevice = self.tWriteFrameWaitAckRetries(
            message, retries=2)["Payload"][2]
        self.bConnected = bool(0 != connectToDevice)
        return self.bConnected

    def bBlueToothDisconnect(self, stuNr, bLog=True):
        if False != bLog:
            self.Logger.Info("Bluetooth disconnect")
        cmd = self.CanCmd(MyToolItBlock["System"], MyToolItSystem["Bluetooth"],
                          1, 0)
        message = self.CanMessage20(
            cmd, self.sender, stuNr,
            [SystemCommandBlueTooth["Disconnect"], 0, 0, 0, 0, 0, 0, 0])
        self.tWriteFrameWaitAckRetries(message, retries=2)
        self.bConnected = (0 < self.bBlueToothCheckConnect(stuNr))
        return self.bConnected

    def vBlueToothNameWrite(self, receiver, DeviceNr, Name):
        """
        Write name and get name (bluetooth command)
        """
        cmd = self.CanCmd(MyToolItBlock["System"], MyToolItSystem["Bluetooth"],
                          1, 0)
        nameList = [0, 0, 0, 0, 0, 0]
        for i in range(0, 6):
            if (len(Name) <= i):
                break
            nameList[i] = ord(Name[i])
        Payload = [SystemCommandBlueTooth["SetName1"], DeviceNr]
        Payload.extend(nameList)
        message = self.CanMessage20(cmd, self.sender, receiver, Payload)
        self.tWriteFrameWaitAckRetries(message, retries=2)
        nameList = [0, 0, 0, 0, 0, 0]
        for i in range(6, len(Name)):
            nameList[i - 6] = ord(Name[i])
        Payload = [SystemCommandBlueTooth["SetName2"], DeviceNr]
        Payload.extend(nameList)
        message = self.CanMessage20(cmd, self.sender, receiver, Payload)
        self.tWriteFrameWaitAckRetries(message, retries=2)

    def BlueToothNameGet(self, receiver, DeviceNr):
        """
        Get name (bluetooth command)
        """
        cmd = self.CanCmd(MyToolItBlock["System"], MyToolItSystem["Bluetooth"],
                          1, 0)
        payload = [
            SystemCommandBlueTooth["GetName1"], DeviceNr, 0, 0, 0, 0, 0, 0
        ]
        message = self.CanMessage20(cmd, self.sender, receiver, payload)
        Name = self.tWriteFrameWaitAckRetries(message, retries=2)
        Name = Name["Payload"]
        Name = Name[2:]
        payload = [
            SystemCommandBlueTooth["GetName2"], DeviceNr, 0, 0, 0, 0, 0, 0
        ]
        message = self.CanMessage20(cmd, self.sender, receiver, payload)
        Name2 = self.tWriteFrameWaitAckRetries(message)
        Name2 = Name2["Payload"]
        Name = Name + Name2[2:]
        Name = sArray2String(Name)
        return Name

    def BlueToothAddressGet(self, receiver, DeviceNr):
        """
        Get address (bluetooth command)
        """
        cmd = self.CanCmd(MyToolItBlock["System"], MyToolItSystem["Bluetooth"],
                          1, 0)
        payload = [
            SystemCommandBlueTooth["MacAddress"], DeviceNr, 0, 0, 0, 0, 0, 0
        ]
        message = self.CanMessage20(cmd, self.sender, receiver, payload)
        Address = self.tWriteFrameWaitAckRetries(message, retries=2)
        Address = Address["Payload"]
        Address = Address[2:]
        return byte_list_to_int(Address)

    def BlueToothRssiGet(self, receiver, DeviceNr):
        """
        Get RSSI (Bluetooth command)
        """
        cmd = self.CanCmd(MyToolItBlock["System"], MyToolItSystem["Bluetooth"],
                          1, 0)
        message = self.CanMessage20(
            cmd, self.sender, receiver,
            [SystemCommandBlueTooth["Rssi"], DeviceNr, 0, 0, 0, 0, 0, 0])
        ack = self.tWriteFrameWaitAckRetries(message, retries=2)
        ack = ack["Payload"]
        ack = ack[2]
        ack = c_byte(ack).value  # Convert to signed value
        return ack

    def iBlueToothConnect2MacAddr(self, receiver, iMacAddr):
        """
        Connect to STH by connect to MAC Address command
        """
        cmd = self.CanCmd(MyToolItBlock["System"], MyToolItSystem["Bluetooth"],
                          1, 0)
        au8Payload = [SystemCommandBlueTooth["DeviceConnectMacAddr"], 0]
        au8MacAddr = int_to_byte_list(int(iMacAddr), 6)
        au8Payload.extend(au8MacAddr)
        message = self.CanMessage20(cmd, self.sender, receiver, au8Payload)
        ack = self.tWriteFrameWaitAckRetries(message, retries=2)
        ack = ack["Payload"]
        ack = ack[2:]
        iMacAddrReadBack = byte_list_to_int(
            ack)  # if not successful this will be 0
        if iMacAddrReadBack != iMacAddr:
            self.bConnected = False
        else:
            self.bConnected = True
        return iMacAddrReadBack

    def bBlueToothConnectPollingName(self, stuNr, sName, log=True):
        """
        Connect to device via name
        """
        self.sDevName = None
        endTime = time() + BluetoothTime["Connect"]
        self.Logger.Info("Try to connect to Device Name: " + sName)
        dev = None
        devList = None
        while time() < endTime and False == self.bConnected:
            devList = self.tDeviceList(stuNr)
            for dev in devList:
                if sName == dev["Name"]:
                    self.iAddress = dev["Address"]
                    self.sDevName = dev["Name"]
                    self.DeviceNr = dev["DeviceNumber"]
                    currentTime = time()
                    endTime = currentTime + BluetoothTime["Connect"]
                    self.bBlueToothConnectDeviceConnect(stuNr, self.DeviceNr)
                    while time() < endTime and False == self.bConnected:
                        self.bBlueToothCheckConnect(stuNr)
                    if self.bConnected and log:
                        self.Logger.Info("Connected to: " +
                                         int_to_mac_address(self.iAddress) +
                                         "(" + self.sDevName + ")")
                    break
        if None == self.sDevName:
            if False != log:
                self.Logger.Info("Available Devices: " + str(devList))
            self.__exitError(f"Unable to connect to device “{sName}”")
        return self.bConnected

    def tDeviceList(self, stuNr, bLog=True):
        devList = []
        self.vBlueToothConnectConnect(stuNr, log=False)
        devAll = self.iBlueToothConnectTotalScannedDeviceNr(stuNr, log=bLog)
        for dev in range(0, devAll):
            endTime = time() + BluetoothTime["Connect"]
            name = ''
            nameOld = None
            while nameOld != name and time() < endTime:
                nameOld = name
                name = self.BlueToothNameGet(stuNr, dev)[0:8]
            endTime = time() + BluetoothTime["Connect"]
            address = 0
            while 0 == address and time() < endTime:
                address = self.BlueToothAddressGet(stuNr, dev)
            rssi = 0
            while 0 == rssi and time() < endTime:
                rssi = self.BlueToothRssiGet(stuNr, dev)
            devList.append({
                "DeviceNumber": dev,
                "Name": name,
                "Address": address,
                "RSSI": rssi
            })
        return devList

    def bBlueToothConnectPollingAddress(self, stuNr, iAddress, bLog=True):
        """
        Connect to device via Bluetooth Address
        """
        endTime = time() + BluetoothTime["Connect"]
        self.Logger.Info("Try to connect to Test Device Address: " +
                         str(iAddress))
        self.sDevName = None
        while time() < endTime and False == self.bConnected:
            devList = self.tDeviceList(stuNr)
            for dev in devList:
                if iAddress == hex(dev["Address"]):
                    self.iAddress = iAddress
                    self.sDevName = dev["Name"]
                    self.DeviceNr = dev["DeviceNumber"]
                    currentTime = time()
                    endTime = currentTime + BluetoothTime["Connect"]
                    self.bBlueToothConnectDeviceConnect(stuNr, self.DeviceNr)
                    while time() < endTime and not self.bConnected:
                        self.bBlueToothCheckConnect(stuNr)
                    if False != self.bConnected and False != bLog:
                        self.Logger.Info("Connected to: " + self.iAddress)
        if self.sDevName is None:
            self.Logger.Info("Available Devices: " + str(devList))
            self.__exitError(
                f"Unable to connect to device with address “{iAddress}”")
        return self.bConnected

    def BlueToothEnergyModeNr(self, Sleep1TimeReset,
                              Sleep1AdvertisementTimeReset, modeNr):
        S1B0 = Sleep1TimeReset & 0xFF
        S1B1 = (Sleep1TimeReset >> 8) & 0xFF
        S1B2 = (Sleep1TimeReset >> 16) & 0xFF
        S1B3 = (Sleep1TimeReset >> 24) & 0xFF
        A1B0 = Sleep1AdvertisementTimeReset & 0xFF
        A1B1 = (Sleep1AdvertisementTimeReset >> 8) & 0xFF
        if 2 == modeNr:
            self.Logger.Info("Setting Bluetooth Energy Mode 2")
            modeNr = SystemCommandBlueTooth["EnergyModeLowestWrite"]
        else:
            self.Logger.Info("Setting Bluetooth Energy Mode 1")
            modeNr = SystemCommandBlueTooth["EnergyModeReducedWrite"]
        Payload = [modeNr, self.DeviceNr, S1B0, S1B1, S1B2, S1B3, A1B0, A1B1]
        sleep(0.1)
        [timeReset, timeAdvertisement] = self.BlueToothEnergyMode(Payload)
        self.Logger.Info("Energy Mode ResetTime/AdvertisementTime: " +
                         str(timeReset) + "/" + str(timeAdvertisement))
        return [timeReset, timeAdvertisement]

    def BlueToothEnergyMode(self, Payload):
        cmd = self.CanCmd(MyToolItBlock["System"], MyToolItSystem["Bluetooth"],
                          1, 0)
        message = self.CanMessage20(cmd, self.sender, self.receiver, Payload)
        EnergyModeReduced = self.tWriteFrameWaitAckRetries(
            message, retries=2)["Payload"][2:]
        timeReset = EnergyModeReduced[:4]
        timeAdvertisement = EnergyModeReduced[4:]
        timeReset = byte_list_to_int(timeReset)
        timeAdvertisement = byte_list_to_int(timeAdvertisement)
        return [timeReset, timeAdvertisement]

    def Standby(self, receiver):
        sendData = ActiveState()
        sendData.asbyte = 0
        sendData.b.bSetState = 1
        sendData.b.u2NodeState = NodeState["Application"]
        sendData.b.u3NetworkState = NetworkState["Standby"]
        self.Logger.Info("Send Standby Command")
        index = self.cmdSend(receiver, MyToolItBlock["System"],
                             MyToolItSystem["ActiveState"], [sendData.asbyte])
        self.Logger.Info("Received Payload " +
                         payload2Hex(self.getReadMessageData(index)))

    def sProductData(self, name, bLog=True):
        sReturn = ""
        if "GTIN" == name:
            index = self.cmdSend(Node("STH1").value,
                                 MyToolItBlock["ProductData"],
                                 MyToolItProductData["GTIN"], [],
                                 log=bLog)
            iGtin = byte_list_to_int(self.getReadMessageData(index))
            if False != bLog:
                self.Logger.Info("GTIN: " + str(iGtin))
            sReturn = str(iGtin)
        elif "HardwareRevision" == name:
            index = self.cmdSend(Node("STH1").value,
                                 MyToolItBlock["ProductData"],
                                 MyToolItProductData["HardwareRevision"], [],
                                 log=bLog)
            tHwRev = self.getReadMessageData(index)
            if False != bLog:
                self.Logger.Info("Hardware Revision: " + str(tHwRev))
            sReturn = str(tHwRev[5]) + "." + str(tHwRev[6]) + "." + str(
                tHwRev[7])
        elif "FirmwareVersion" == name:
            index = self.cmdSend(Node("STH1").value,
                                 MyToolItBlock["ProductData"],
                                 MyToolItProductData["FirmwareVersion"], [],
                                 log=bLog)
            tFirmwareVersion = self.getReadMessageData(index)
            if False != bLog:
                self.Logger.Info("Firmware Version: " + str(tFirmwareVersion))
            sReturn = str(tFirmwareVersion[5]) + "." + str(
                tFirmwareVersion[6]) + "." + str(tFirmwareVersion[7])
        elif "ReleaseName" == name:
            index = self.cmdSend(Node("STH1").value,
                                 MyToolItBlock["ProductData"],
                                 MyToolItProductData["ReleaseName"], [],
                                 log=bLog)
            aiName = self.getReadMessageData(index)
            sReturn = sArray2String(aiName)
            if False != bLog:
                self.Logger.Info("Release Name: " + str(sReturn))
        elif "SerialNumber" == name:
            aiSerialNumber = []
            for i in range(1, 5):
                index = self.cmdSend(Node("STH1").value,
                                     MyToolItBlock["ProductData"],
                                     MyToolItProductData["SerialNumber" +
                                                         str(i)], [],
                                     log=bLog)
                element = self.getReadMessageData(index)
                aiSerialNumber.extend(element)
            try:
                sReturn = array(
                    'b', bytearray(aiSerialNumber)).tostring().encode('utf-8')
            except:
                sReturn = ""
            if False != bLog:
                self.Logger.Info("Serial Number: " + str(sReturn))
        elif "Name" == name:
            aiName = []
            for i in range(1, 17):
                index = self.cmdSend(Node("STH1").value,
                                     MyToolItBlock["ProductData"],
                                     MyToolItProductData["Name" + str(i)], [],
                                     log=bLog)
                element = self.getReadMessageData(index)
                aiName.extend(element)
            try:
                sReturn = array('b',
                                bytearray(aiName)).tostring().encode('utf-8')
            except:
                sReturn = ""
            if False != bLog:
                self.Logger.Info("Name: " + str(sReturn))
        elif "OemFreeUse" == name:
            aiOemFreeUse = []
            for i in range(1, 9):
                index = self.cmdSend(
                    Node("STH1").value, MyToolItBlock["ProductData"],
                    MyToolItProductData["OemFreeUse" + str(i)], [])
                aiOemFreeUse.extend(self.getReadMessageData(index))
            sReturn = payload2Hex(aiOemFreeUse)
            if False != bLog:
                self.Logger.Info("OEM Free Use: " + str(sReturn))
        else:
            sReturn = "-1"
        return sReturn

    def BlueToothRssi(self, subscriber):
        cmd = self.CanCmd(MyToolItBlock["System"], MyToolItSystem["Bluetooth"],
                          1, 0)
        payload = [
            SystemCommandBlueTooth["Rssi"],
            SystemCommandBlueTooth["SelfAddressing"], 0, 0, 0, 0, 0, 0
        ]
        message = self.CanMessage20(cmd, self.sender, subscriber, payload)
        ack = self.tWriteFrameWaitAckRetries(message, retries=2)["Payload"][2]
        ack = c_byte(ack).value  # Convert to signed value
        return ack

    def BlueToothAddress(self, subscriber):
        cmd = self.CanCmd(MyToolItBlock["System"], MyToolItSystem["Bluetooth"],
                          1, 0)
        payload = [
            SystemCommandBlueTooth["MacAddress"],
            SystemCommandBlueTooth["SelfAddressing"], 0, 0, 0, 0, 0, 0
        ]
        message = self.CanMessage20(cmd, self.sender, subscriber, payload)
        ack = self.tWriteFrameWaitAckRetries(message, retries=2)["Payload"][2:]
        ack = byte_list_to_int(ack)
        return ack

    def RoutingInformationCmd(self, receiver, subCmd, port):
        cmd = self.CanCmd(MyToolItBlock["System"], MyToolItSystem["Routing"],
                          1, 0)
        payload = [subCmd, port, 0, 0, 0, 0, 0, 0]
        message = self.CanMessage20(cmd, self.sender, receiver, payload)
        ack = self.tWriteFrameWaitAckRetries(message,
                                             retries=10)["Payload"][2:]
        ack = AsciiStringWordLittleEndian(ack)
        return ack

    def SamplingPointNumber(self, b1, b2, b3):
        count = 0
        if 0 != b1:
            count += 1
        if 0 != b2:
            count += 1
        if 0 != b2:
            count += 1
        return count

    def Can20DataSet(self, b1, b2, b3):
        count = self.SamplingPointNumber(b1, b2, b3)
        if 0 == count:
            dataSets = DataSets[0]
        elif 1 == count:
            dataSets = DataSets[3]
        elif 3 >= count:
            dataSets = DataSets[1]
        else:
            self.__exitError("No valid CAN20 message (Data Set: " +
                             str("Sampling Points: ") + str(count) + ")")
        return dataSets

    def get_node_release_name(self, node='STH1'):
        """Retrieve the software release name of a certain node

        Parameters
        ----------

        node:
            A textual description that identifies the node

        Returns
        -------

        The name of the software release running on the specified node
        """

        index = self.cmdSend(
            Node(node).value, MyToolItBlock["ProductData"],
            MyToolItProductData["ReleaseName"], [])
        aiName = self.getReadMessageData(index)
        return sArray2String(aiName)

    def read_eeprom(self, address, offset, length):
        """Read EEPROM data at a specific address

        Parameters
        ----------

        address:
            The page number in the EEPROM

        offset:
            The offset to the base address in the specified page

        length:
            This value specifies how many bytes you want to read

        Returns
        -------

        A list that contains the byte values at the specified address starting
        with the byte at the smallest address
        """

        read_data = []
        reserved = [0] * 5
        data_start = 4  # Start index of data in response message

        while length > 0:
            # Read at most 4 bytes of data at once
            read_length = 4 if length > 4 else length
            payload = [address, offset, read_length, *reserved]
            index = self.cmdSend(self.receiver,
                                 MyToolItBlock['EEPROM'],
                                 MyToolItEeprom['Read'],
                                 payload,
                                 log=False)
            response = self.getReadMessageData(index)
            data_end = data_start + read_length
            read_data.extend(response[data_start:data_end])
            length -= read_length
            offset += read_length

        return read_data

    def read_eeprom_text(self, address, offset, length):
        """Read EEPROM data in ASCII format

        Please note, that this function will only return the characters up
        to the first null byte.

        Parameters
        ----------

        address:
            The page number in the EEPROM

        offset:
            The offset to the base address in the specified page

        length:
            This value specifies how many characters you want to read

        Returns
        -------

        A string that contains the text at the specified location
        """

        data = self.read_eeprom(address, offset, length)
        data_without_null = []
        for byte in data:
            if byte == 0:
                break
            data_without_null.append(byte)

        return "".join(map(chr, data_without_null))

    def read_eeprom_unsigned(self, address, offset, length):
        """Read EEPROM data in unsigned format

        Parameters
        ----------

        address:
            The page number in the EEPROM

        offset:
            The offset to the base address in the specified page

        length:
            This value specifies how long the unsigned number is in bytes

        Returns
        -------

        The unsigned number at the specified location of the EEPROM
        """

        return int.from_bytes(self.read_eeprom(address, offset, length),
                              'little')

    def read_eeprom_float(self, address, offset):
        """Read EEPROM data in float format

        Parameters
        ----------

        address:
            The page number in the EEPROM

        offset:
            The offset to the base address in the specified page

        Returns
        -------

        The float number at the specified location of the EEPROM
        """

        data = self.read_eeprom(address, offset, length=4)
        return unpack('<f', bytearray(data))[0]

    def write_eeprom(self, address, offset, data, length=None):
        """Write EEPROM data at the specified address

        Parameters
        ----------

        address:
            The page number in the EEPROM

        offset:
            The offset to the base address in the specified page

        data:
            A list of byte value that should be stored at the specified EEPROM
            location

        length:
            This optional parameter specifies how many of the bytes in `data`
            should be stored in the EEPROM. If you specify a length that is
            greater, than the size of the data list, then the remainder of
            the EEPROM data will be filled with null bytes.
        """

        # Change data, if
        # - only a subset, or
        # - additional data
        # should be written to the EEPROM.
        if length:
            # Cut off additional data bytes
            data = data[:length]
            # Fill up additional data bytes
            data.extend([0] * (length - len(data)))

        while data:
            write_data = data[:4]  # Maximum of 4 bytes per message
            write_length = len(write_data)
            # Use zeroes to fill up missing data bytes
            write_data.extend([0] * (4 - write_length))

            reserved = [0] * 1
            payload = [address, offset, write_length, *reserved, *write_data]
            self.cmdSend(self.receiver,
                         MyToolItBlock['EEPROM'],
                         MyToolItEeprom['Write'],
                         payload,
                         log=False)
            data = data[4:]
            offset += write_length

    def write_eeprom_text(self, address, offset, text, length=None):
        """Write a string at the specified EEPROM address

        Parameters
        ----------

        address:
            The page number in the EEPROM

        offset:
            The offset to the base address in the specified page

        text:
            A ASCII string that should be written to the specified location

        length:
            This optional parameter specifies how many of the character in
            `text` should be stored in the EEPROM. If you specify a length
            that is greater, than the size of the data list, then the
            remainder of the EEPROM data will be filled with null bytes.
        """

        data = list(map(ord, list(text)))
        self.write_eeprom(address, offset, data, length)

    def write_eeprom_unsigned(self, address, offset, value, length):
        """Write an unsigned integer at the specified EEPROM address

        Parameters
        ----------

        address:
            The page number in the EEPROM

        offset:
            The offset to the base address in the specified page

        value:
            The unsigned number that should be stored at the specified location

        length:
            This value specifies how long the unsigned number is in bytes
        """

        data = list(value.to_bytes(length, byteorder='little'))
        self.write_eeprom(address, offset, data)

    def write_eeprom_float(self, address, offset, value):
        """Write a float value at the specified EEPROM address

        Parameters
        ----------

        address:
            The page number in the EEPROM

        offset:
            The offset to the base address in the specified page

        value:
            The float value that should be stored at the specified location
        """

        data = list(pack('f', value))
        self.write_eeprom(address, offset, data)

    def read_eeprom_status(self):
        """Retrieve EEPROM status byte

        Returns
        -------

        An EEPROM status object for the current status byte value

        """

        return EEPROMStatus(
            self.read_eeprom(address=0, offset=0, length=1).pop())

    def write_eeprom_status(self, value):
        """Change the value of the EEPROM status byte

        Parameters
        ----------

        value:
            The new value for the status byte

        """

        self.write_eeprom_unsigned(address=0,
                                   offset=0,
                                   length=1,
                                   value=EEPROMStatus(value).value)

    def read_eeprom_name(self):
        """Retrieve the name of the node from the EEPROM

        Returns
        -------

        The name of the current receiver as string
        """

        return self.read_eeprom_text(address=0, offset=1, length=8)

    def write_eeprom_name(self, text):
        """Write the name of the node to the EEPROM

        Parameters
        ----------

        text:
            The new (Bluetooth advertisement) name of the current receiver

        """

        self.write_eeprom_text(address=0, offset=1, text=text, length=8)

    def read_eeprom_sleep_time_1(self):
        """Retrieve sleep time 1 from the EEPROM

        Returns
        -------

        The current value of sleep time 1 in milliseconds

        """

        return self.read_eeprom_unsigned(address=0, offset=9, length=4)

    def write_eeprom_sleep_time_1(self, milliseconds):
        """Write the value of sleep time 1 to the EEPROM

        Parameters
        ----------

        milliseconds:
            The value for sleep time 1 in milliseconds

        """

        self.write_eeprom_unsigned(address=0,
                                   offset=9,
                                   value=milliseconds,
                                   length=4)

    def read_eeprom_advertisement_time_1(self):
        """Retrieve advertisement time 1 from the EEPROM

        Returns
        -------

        The current value of advertisement time 1 in milliseconds

        """

        return self.read_eeprom_unsigned(address=0, offset=13, length=2)

    def write_eeprom_advertisement_time_1(self, milliseconds):
        """Write the value of advertisement time 1 to the EEPROM

        Parameters
        ----------

        milliseconds:
            The value for advertisement time 1 in milliseconds

        """

        self.write_eeprom_unsigned(address=0,
                                   offset=13,
                                   value=milliseconds,
                                   length=2)

    def read_eeprom_sleep_time_2(self):
        """Retrieve sleep time 2 from the EEPROM

        Returns
        -------

        The current value of sleep time 2 in milliseconds

        """

        return self.read_eeprom_unsigned(address=0, offset=15, length=4)

    def write_eeprom_sleep_time_2(self, milliseconds):
        """Write the value of sleep time 2 to the EEPROM

        Parameters
        ----------

        milliseconds:
            The value for sleep time 2 in milliseconds

        """

        self.write_eeprom_unsigned(address=0,
                                   offset=15,
                                   value=milliseconds,
                                   length=4)

    def read_eeprom_advertisement_time_2(self):
        """Retrieve advertisement time 2 from the EEPROM

        Returns
        -------

        The current value of advertisement time 2 in milliseconds

        """

        return self.read_eeprom_unsigned(address=0, offset=19, length=2)

    def write_eeprom_advertisement_time_2(self, milliseconds):
        """Write the value of advertisement time 2 to the EEPROM

        Parameters
        ----------

        milliseconds:
            The value for advertisement time 2 in milliseconds

        """

        self.write_eeprom_unsigned(address=0,
                                   offset=19,
                                   value=milliseconds,
                                   length=2)

    def read_eeprom_gtin(self):
        """Read the global trade identifier number (GTIN) from the EEPROM

        Returns
        -------

        The GTIN of the current receiver

        """

        return self.read_eeprom_unsigned(address=4, offset=0, length=8)

    def write_eeprom_gtin(self, value):
        """Write the global trade identifier number (GTIN) to the EEPROM

        Parameters
        ----------

        value:
            The new GTIN of the current receiver

        """

        return self.write_eeprom_unsigned(address=4,
                                          offset=0,
                                          length=8,
                                          value=value)

    def read_eeprom_hardware_revision(self):
        """Read the current hardware revision from the EEPROM

        Returns
        -------

        The hardware revision of the current receiver

        """

        major, minor, patch = self.read_eeprom(address=4, offset=13, length=3)

        return Version(major=major, minor=minor, patch=patch)

    def write_eeprom_hardware_revision(self, version):
        """Write hardware revision to the EEPROM

        Parameters
        ----------

        version:
            The new hardware revision of the current receiver

        """

        if isinstance(version, str):
            version = Version(version)

        self.write_eeprom(address=4,
                          offset=13,
                          length=3,
                          data=[version.major, version.minor, version.patch])

    def read_eeprom_firmware_version(self):
        """Retrieve the current firmware version from the EEPROM

        Returns
        -------

        The firmware version of the current receiver

        """

        major, minor, patch = self.read_eeprom(address=4, offset=21, length=3)
        return Version(major=major, minor=minor, patch=patch)

    def write_eeprom_firmware_version(self, version):
        """Write firmware version to the EEPROM

        Parameters
        ----------

        version:
            The new firmware version of the current receiver

        """

        if isinstance(version, str):
            version = Version(version)

        self.write_eeprom(address=4,
                          offset=21,
                          length=3,
                          data=[version.major, version.minor, version.patch])

    def read_eeprom_release_name(self):
        """Retrieve the current release name from the EEPROM

        Returns
        -------

        The firmware release name of the current receiver

        """

        return self.read_eeprom_text(address=4, offset=24, length=8)

    def write_eeprom_release_name(self, text):
        """Write the release name to the EEPROM

        Parameters
        ----------

        text:
            The new name of the release

        """

        return self.write_eeprom_text(address=4,
                                      offset=24,
                                      length=8,
                                      text=text)

    def read_eeprom_serial_number(self):
        """Retrieve the serial number from the EEPROM

        Returns
        -------

        The serial number of the current receiver

        """

        return self.read_eeprom_text(address=4, offset=32, length=32)

    def write_eeprom_serial_number(self, text):
        """Write the serial number to the EEPROM

        Parameters
        ----------

        text:
            The serial number of the current receiver

        """

        self.write_eeprom_text(address=4, offset=32, length=32, text=text)

    def read_eeprom_product_name(self):
        """Retrieve the product name from the EEPROM

        Returns
        -------

        The product name of the current receiver

        """

        return self.read_eeprom_text(address=4, offset=64, length=128)

    def write_eeprom_product_name(self, text):
        """Write the product name to the EEPROM

        Parameters
        ----------

        text:
            The product name of the current receiver

        """

        self.write_eeprom_text(address=4, offset=64, length=128, text=text)

    def read_eeprom_oem_data(self):
        """Retrieve the OEM data from the EEPROM

        Returns
        -------

        The OEM data of the current receiver

        """

        return self.read_eeprom(address=4, offset=192, length=64)

    def write_eeprom_oem_data(self, data):
        """Write OEM data to the EEPROM

        Parameters
        ----------

        data:
            The OEM data for the current receiver

        """

        self.write_eeprom(address=4, offset=192, length=64, data=data)

    def read_eeprom_power_on_cycles(self):
        """Retrieve the number of power on cycles from the EEPROM

        Returns
        -------

        The number of power on cycles of the current receiver

        """

        return self.read_eeprom_unsigned(address=5, offset=0, length=4)

    def write_eeprom_power_on_cycles(self, times):
        """Write the number of power on cycles to the EEPROM

        Parameters
        ----------

        times:
            The number of power on cycles of the current receiver

        """

        self.write_eeprom_unsigned(address=5, offset=0, length=4, value=times)

    def read_eeprom_power_off_cycles(self):
        """Retrieve the number of power off cycles from the EEPROM

        Returns
        -------

        The number of power off cycles of the current receiver

        """

        return self.read_eeprom_unsigned(address=5, offset=4, length=4)

    def write_eeprom_power_off_cycles(self, times):
        """Write the number of power off cycles to the EEPROM

        Parameters
        ----------

        times:
            The number of power off cycles of the current receiver

        """

        self.write_eeprom_unsigned(address=5, offset=4, length=4, value=times)

    def read_eeprom_operating_time(self):
        """Retrieve the operating time from the EEPROM

        Returns
        -------

        The operating time of the current receiver in seconds

        """

        return self.read_eeprom_unsigned(address=5, offset=8, length=4)

    def write_eeprom_operating_time(self, seconds):
        """Write operating time to the EEPROM

        Parameters
        ----------

        seconds:
            The operating time of the current receiver in seconds

        """

        self.write_eeprom_unsigned(address=5,
                                   offset=8,
                                   length=4,
                                   value=seconds)

    def read_eeprom_under_voltage_counter(self):
        """Retrieve the under voltage counter value from the EEPROM

        Returns
        -------

        The number of time the voltage was too low for the current receiver

        """

        return self.read_eeprom_unsigned(address=5, offset=12, length=4)

    def write_eeprom_under_voltage_counter(self, times):
        """Write the under voltage counter value to the EEPROM

        Parameters
        ----------

        times:
            The number of time the voltage was too low

        """

        self.write_eeprom_unsigned(address=5, offset=12, length=4, value=times)

    def read_eeprom_watchdog_reset_counter(self):
        """Retrieve the watchdog reset counter value from the EEPROM

        Returns
        -------

        The watchdog reset counter value of the current receiver

        """

        return self.read_eeprom_unsigned(address=5, offset=16, length=4)

    def write_eeprom_watchdog_reset_counter(self, times):
        """Write the watchdog reset counter value to the EEPROM

        Parameters
        ----------

        times:
            The value of the watchdog reset counter for the current receiver

        """

        self.write_eeprom_unsigned(address=5, offset=16, length=4, value=times)

    def read_eeprom_production_date(self):
        """Retrieve the production date from the EEPROM

        Returns
        -------

        The production date of the current receiver

        """

        date = self.read_eeprom_text(address=5, offset=20, length=8)
        year = date[0:4]
        month = date[4:6]
        day = date[6:8]
        return f"{year}-{month}-{day}"

    def write_eeprom_production_date(self, date="1970-12-31"):
        """Write the production date to the EEPROM

        Parameters
        ----------

        date:
            The production date of the current receiver

        """

        date = date.replace("-", "")
        self.write_eeprom_text(address=5, offset=20, length=8, text=date)

    def read_eeprom_batch_number(self):
        """Retrieve the batch number from the EEPROM

        Returns
        -------

        The batch number of the current receiver

        """

        return self.read_eeprom_unsigned(address=5, offset=28, length=4)

    def write_eeprom_batch_number(self, number):
        """Write the production date to the EEPROM

        Parameters
        ----------

        number:
            The batch number of the current receiver

        """

        self.write_eeprom_unsigned(address=5,
                                   offset=28,
                                   length=4,
                                   value=number)

    def read_eeprom_x_axis_acceleration_slope(self):
        """Retrieve the acceleration slope of the x-axis from the EEPROM

        Returns
        -------

        The acceleration slope of the x-axis of the current receiver

        """

        return self.read_eeprom_float(address=8, offset=0)

    def write_eeprom_x_axis_acceleration_slope(self, slope):
        """Write the acceleration slope of the x-axis to the EEPROM

        Parameters
        ----------

        slope:
            The increase of the acceleration value for one step of the ADC in
            multiples of g₀

        """

        self.write_eeprom_float(address=8, offset=0, value=slope)

    def read_eeprom_x_axis_acceleration_offset(self):
        """Retrieve the acceleration offset of the x-axis from the EEPROM

        Returns
        -------

        The acceleration offset of the x-axis of the current receiver

        """

        return self.read_eeprom_float(address=8, offset=4)

    def write_eeprom_x_axis_acceleration_offset(self, offset):
        """Write the acceleration offset of the x-axis to the EEPROM

        Parameters
        ----------

        offset:
            The (negative) offset of the acceleration value in multiples of g₀

        """

        self.write_eeprom_float(address=8, offset=4, value=offset)


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
