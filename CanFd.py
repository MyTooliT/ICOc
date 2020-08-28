from can.interfaces.pcan.basic import *
import threading
import array
import math
from sys import stderr

from mytoolit.can.identifier import Identifier

from MyToolItCommands import *
from MyToolItNetworkNumbers import MyToolItNetworkNr, MyToolItNetworkName
from Logger import Logger


class CanFd(object):
    """A class used to communicate over CAN

    Objects of this class will create a thread that reads data from the CAN
    bus. The thread will store the read data into a list, appending the latest
    data at the end.

    Unlike it name suggests, this class does currently not offer support for
    CAN FD.
    """

    def __init__(self,
                 testMethodName,
                 testMethodNameError,
                 sender,
                 receiver,
                 prescaler=2,
                 acquisition=8,
                 oversampling=64,
                 FreshLog=False):
        self.bConnected = False
        self.sender = sender
        self.receiver = receiver
        self.Logger = Logger(testMethodName,
                             testMethodNameError,
                             FreshLog=FreshLog)
        self.Logger.Info(str(sDateClock()))
        self.startTime = int(round(time.time() * 1000))
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
        self.tCanReadWriteMutex = threading.Lock()
        self.reset()
        self.ReadThreadReset()

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
            time.sleep(1)
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
            self.readArray = [{
                "CanMsg": self.CanMessage20(data=[0] * 8),
                "PcTime": 1 << 64,
                "PeakCanTime": 0
            }]
            time.sleep(0.2)
            self.RunReadThread = True
            self.readThread = threading.Thread(target=self.ReadMessage,
                                               name="CanReadThread")
            self.readThread.start()
            self.reset()
            time.sleep(0.2)
        except:
            pass

    def reset(self):
        with self.tCanReadWriteMutex:
            self.pcan.Reset(self.m_PcanHandle)

    def CanTimeStampStart(self, CanTimeStampStart):
        self.PeakCanTimeStampStart = CanTimeStampStart

    def WriteFrame(self, CanMsg):
        returnMessage = CanMsg
        if returnMessage != "Error":
            with self.tCanReadWriteMutex:
                returnMessage = self.pcan.Write(self.m_PcanHandle, CanMsg)
            if returnMessage != PCAN_ERROR_OK:
                print("WriteFrame bError: " + hex(returnMessage))
                self.Logger.Info("WriteFrame bError: " + hex(returnMessage))
                returnMessage = "Error"
                self.__exitError("Driver Problems or Physical Layer Problems")
        return returnMessage

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
        if 200 > waitMs:
            self.__exitError("Meantime between send retry to low(" +
                             str(waitMs) + "ms)")
        if None == sendTime:
            sendTime = self.getTimeMs()
        if None == currentIndex:
            currentIndex = self.GetReadArrayIndex()
        if currentIndex >= self.GetReadArrayIndex():
            currentIndex = self.GetReadArrayIndex() - 1
        message = self.readArray[currentIndex]

        if printLog:
            print("Message ID Send: " + hex(CanMsg.ID))
            print("Message DATA Send: " + payload2Hex(CanMsg.DATA))
        returnMessage = self.WriteFrame(CanMsg)
        if "Error" != returnMessage:
            waitTimeMax = self.getTimeMs() + waitMs
            if False != bError:
                CanMsgAckError = self.CanMessage20Ack(CanMsg)
                CanMsgAck = self.CanMessage20AckError(CanMsg)
            else:
                CanMsgAck = self.CanMessage20Ack(CanMsg)
                CanMsgAckError = self.CanMessage20AckError(CanMsg)
            returnMessage = "Run"
            while "Run" == returnMessage:
                if (waitTimeMax < self.getTimeMs()):
                    returnMessage = self.WriteFrameWaitAckTimeOut(
                        CanMsg, printLog)
                elif sendTime > message["PcTime"]:
                    message = self.readArray[0]
                elif CanMsgAck.ID == message["CanMsg"].ID and (
                        assumedPayload is None
                        or list(message["CanMsg"].DATA) == assumedPayload):
                    returnMessage = self.WriteFrameWaitAckOk(message)
                elif CanMsgAckError.ID == message["CanMsg"].ID:
                    returnMessage = self.WriteFrameWaitAckError(
                        message, bError, printLog)
                elif currentIndex < (self.GetReadArrayIndex() - 1):
                    currentIndex += 1
                    message = self.readArray[currentIndex]
                else:
                    time.sleep(notAckIdleWaitTimeMs)
        return [returnMessage, currentIndex]

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
            retries += 1
            currentIndex = self.GetReadArrayIndex() - 1
            sendTime = self.getTimeMs()
            for i in range(0, retries):
                [returnMessage, currentIndex] = self.tWriteFrameWaitAck(
                    CanMsg,
                    waitMs=waitMs,
                    currentIndex=currentIndex,
                    printLog=printLog,
                    assumedPayload=assumedPayload,
                    bError=bErrorAck,
                    sendTime=sendTime,
                    notAckIdleWaitTimeMs=notAckIdleWaitTimeMs)
                if "Error" != returnMessage:
                    break
                elif (retries - 1) == i:
                    identifier = Identifier(CanMsg.ID)
                    cmdBlockName = identifier.block_name()
                    cmdName = identifier.block_command_name()
                    senderName = identifier.sender_name()
                    receiverName = identifier.receiver_name()
                    self.Logger.Error("Message Request Failed: " +
                                      cmdBlockName + " - " + cmdName + "(" +
                                      senderName + "->" + receiverName + ")" +
                                      "; Payload - " +
                                      payload2Hex(CanMsg.DATA))
                    if False != printLog:
                        print("Message Request Failed: " + cmdBlockName +
                              " - " + cmdName + "(" + senderName + "->" +
                              receiverName + ")" + "; Payload - " +
                              payload2Hex(CanMsg.DATA))
                    if False != bErrorExit:
                        self.__exitError("To many retries(" + str(retries) +
                                         ")")
            time.sleep(0.01)
            return returnMessage
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
        cmd = self.CanCmd(blockCmd, subCmd, 1, 0)
        message = self.CanMessage20(cmd, self.sender, receiver, payload)
        index = self.GetReadArrayIndex()
        msgAck = self.tWriteFrameWaitAckRetries(
            message,
            retries=retries,
            waitMs=1000,
            bErrorAck=bErrorAck,
            printLog=printLog,
            bErrorExit=bErrorExit,
            notAckIdleWaitTimeMs=notAckIdleWaitTimeMs)
        if msgAck != "Error" and False == bErrorExit:
            self.__exitError("Command was not send able")
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
        # time.sleep(0.2)  # synch to read thread TODO: Really kick it out?
        return index

    """
    Send cmd and return Ack
    """

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
        cmd = self.CanCmd(blockCmd, subCmd, 1, 0)
        message = self.CanMessage20(cmd, self.sender, receiver, payload)
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
        # time.sleep(0.2)  # synch to read thread TODO: Really kick it out?
        return msgAck

    def cmdReset(self, receiver, retries=5, log=True):
        if False != log:
            self.Logger.Info("Reset " + MyToolItNetworkName[receiver])
        cmd = self.CanCmd(MyToolItBlock["System"], MyToolItSystem["Reset"], 1,
                          0)
        retMsg = self.tWriteFrameWaitAckRetries(self.CanMessage20(
            cmd, self.sender, receiver, []),
                                                retries=retries)
        time.sleep(2)
        return retMsg

    """
    Get EEPROM Write Request Counter, please note that the count start is power on
    """

    def u32EepromWriteRequestCounter(self, receiver):
        index = self.cmdSend(receiver, MyToolItBlock["Eeprom"],
                             MyToolItEeprom["WriteRequest"], [0] * 8)
        dataReadBack = self.getReadMessageData(index)[4:]
        u32WriteRequestCounter = iMessage2Value(dataReadBack)
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
            Acc = iMessage2Value(data[2:4])
            array1.append(Acc)
            count += 1
        if False != b2:
            if 0 == count:
                Acc = iMessage2Value(data[2:4])
            else:
                Acc = iMessage2Value(data[4:6])
            array2.append(Acc)
            count += 1
        if False != b3:
            if 0 == count:
                Acc = iMessage2Value(data[2:4])
            elif 1 == count:
                Acc = iMessage2Value(data[4:6])
            else:
                Acc = iMessage2Value(data[6:8])
            array3.append(Acc)
        return [array1, array2, array3]

    def ValueDataSet3(self, data, b1, b2, b3, array1, array2, array3):
        Acc1 = iMessage2Value(data[2:4])
        Acc2 = iMessage2Value(data[4:6])
        Acc3 = iMessage2Value(data[6:8])
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
        messageIdFilter = cmdFilter
        messageIdFilter = self.CanMessage20Id(messageIdFilter, receiver,
                                              self.sender)
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
        if False != log:
            self.Logger.Info("Test Time: " + str(testTimeMs) + "ms")
        indexStart = self.streamingStart(receiver,
                                         subCmd,
                                         dataSets,
                                         b1,
                                         b2,
                                         b3,
                                         log=log)
        if False != log:
            self.Logger.Info("indexStart: " + str(indexStart))
        testTimeMs += StartupTimeMs
        time.sleep(testTimeMs / 1000)
        self.streamingStop(receiver, subCmd)
        time.sleep(2)  # synch to read thread
        indexEnd = self.GetReadArrayIndex() - 180  # do not catch stop command
        countDel = 0
        while testTimeMs < self.getReadMessageTimeMs(indexStart,
                                                     indexEnd) - 0.5:
            countDel += 1
            indexEnd -= 1
        if False != log:
            self.Logger.Info("Deleted Messages do achieve " + str(testTimeMs) +
                             "ms: " + str(countDel + 180))
            self.Logger.Info("indexEnd: " + str(indexEnd))
        if 0.2 * (indexEnd - indexStart) < countDel:
            self.Logger.Warning("Deleted Messages do achieve " +
                                str(testTimeMs) + "ms: " + str(countDel + 180))

        return [indexStart, indexEnd]

    def streamingValueArray(self, receiver, streamingCmd, dataSets, b1, b2, b3,
                            indexStart, indexEnd):
        messageIdFilter = self.CanCmd(MyToolItBlock["Streaming"], streamingCmd,
                                      0, 0)
        messageIdFilter = self.CanMessage20Id(messageIdFilter, receiver,
                                              self.sender)
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
        messageIdFilter = self.CanMessage20Id(messageIdFilter, receiver,
                                              self.sender)
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
                SNR = 20 * math.log((stat["StandardDeviation"] / AdcMax), 10)
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

    def streamingStart(self, receiver, subCmd, dataSets, b1, b2, b3, log=True):
        if MyToolItStreaming["Acceleration"] == subCmd:
            self.AccConfig.asbyte = 0
            self.AccConfig.b.bStreaming = 1
            self.AccConfig.b.bNumber1 = b1
            self.AccConfig.b.bNumber2 = b2
            self.AccConfig.b.bNumber3 = b3
            self.AccConfig.b.u3DataSets = dataSets
            streamingFormat = self.AccConfig
        elif MyToolItStreaming["Voltage"] == subCmd:
            self.VoltageConfig.asbyte = 0
            self.VoltageConfig.b.bStreaming = 1
            self.VoltageConfig.b.bNumber1 = b1
            self.VoltageConfig.b.bNumber2 = b2
            self.VoltageConfig.b.bNumber3 = b3
            self.VoltageConfig.b.u3DataSets = dataSets
            streamingFormat = self.VoltageConfig
        else:
            self.__exitError("Streaming unknown at streaming start: + (" +
                             str(subCmd) + ")")
        if False != log:
            self.Logger.Info("Can Bandwitdh(Lowest, may be more): " +
                             str(self.canBandwith()) + "bit/s")
            self.Logger.Info("Bluetooth Bandwitdh(Lowest, may be more): " +
                             str(self.bluetoothBandwidth()) + "bit/s")

        cmd = self.CanCmd(MyToolItBlock["Streaming"], subCmd, 1, 0)
        message = self.CanMessage20(cmd, self.sender, receiver,
                                    [streamingFormat.asbyte])
        if False != log:
            canCmd = self.CanCmd(MyToolItBlock["Streaming"], subCmd, 1, 0)
            self.Logger.Info("Start sending  " +
                             Identifier(command=canCmd).block_command_name() +
                             "; Subpayload: " + hex(streamingFormat.asbyte))

        indexStart = self.GetReadArrayIndex()
        self.tWriteFrameWaitAckRetries(message)
        return indexStart

    def streamingStop(self,
                      receiver,
                      subCmd,
                      bErrorExit=True,
                      notAckIdleWaitTimeMs=0.00005):
        if MyToolItStreaming["Acceleration"] == subCmd:
            self.AccConfig.asbyte = 0
            self.AccConfig.b.bStreaming = 1
            self.AccConfig.b.u3DataSets = DataSets[0]
            streamingFormat = self.AccConfig
        elif MyToolItStreaming["Voltage"] == subCmd:
            self.VoltageConfig.asbyte = 0
            self.VoltageConfig.b.bStreaming = 1
            self.VoltageConfig.b.u3DataSets = DataSets[0]
            streamingFormat = self.VoltageConfig
        else:
            self.__exitError("Streaming unknown at streaming stop: + (" +
                             str(subCmd) + ")")
        cmd = self.CanCmd(MyToolItBlock["Streaming"], subCmd, 1, 0)
        message = self.CanMessage20(cmd, self.sender, receiver,
                                    [streamingFormat.asbyte])
        self.Logger.Info(
            "_____________________________________________________________")
        self.Logger.Info("Stop Streaming - " +
                         Identifier(command=cmd).block_command_name())
        ack = self.tWriteFrameWaitAckRetries(
            message,
            retries=20,
            printLog=False,
            assumedPayload=[streamingFormat.asbyte, 0, 0, 0, 0, 0, 0, 0],
            bErrorExit=bErrorExit,
            notAckIdleWaitTimeMs=notAckIdleWaitTimeMs)
        self.Logger.Info(
            "_____________________________________________________________")
        return ack

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
        messageIdFilter = self.CanCmd(
            MyToolItBlock["Configuration"],
            MyToolItConfiguration["CalibrateMeasurement"], 0,
            bErrorAck != False)
        messageIdFilter = self.CanMessage20Id(messageIdFilter, receiver,
                                              self.sender)
        messageIdFilter = hex(messageIdFilter)
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
        messageIdFilter = self.CanCmd(MyToolItBlock["StatisticalData"], subCmd,
                                      0, bErrorAck != False)
        messageIdFilter = self.CanMessage20Id(messageIdFilter, receiver,
                                              self.sender)
        messageIdFilter = hex(messageIdFilter)
        msgAck = self.cmdSendData(receiver,
                                  MyToolItBlock["StatisticalData"],
                                  subCmd, [],
                                  log=log,
                                  retries=retries,
                                  bErrorAck=bErrorAck,
                                  printLog=printLog)
        return msgAck["Payload"]

    def statusWord0(self, receiver, payload=[0] * 8):
        cmd = self.CanCmd(MyToolItBlock["System"],
                          MyToolItSystem["StatusWord0"], 1, 0)
        msg = self.CanMessage20(cmd, self.sender, receiver, payload)
        psw0 = self.tWriteFrameWaitAckRetries(msg, retries=5)["Payload"]
        psw0 = AsciiStringWordBigEndian(psw0[0:4])
        return psw0

    def statusWord1(self, receiver, payload=[0] * 8):
        cmd = self.CanCmd(MyToolItBlock["System"],
                          MyToolItSystem["StatusWord1"], 1, 0)
        msg = self.CanMessage20(cmd, self.sender, receiver, payload)
        psw1 = self.tWriteFrameWaitAckRetries(msg, retries=5)["Payload"]
        psw1 = AsciiStringWordBigEndian(psw1[0:4])
        return psw1

    def getTimeMs(self):
        return int(round(time.time() * 1000)) - int(self.startTime)

    def CanMessage20(self, command=0, sender=0, receiver=0, data=[]):
        if len(data) > 8:
            return "Error "

        # We create a TPCANMsg message structure
        CANMsg = TPCANMsg()
        CANMsg.ID = Identifier(command=command,
                               sender=sender,
                               receiver=receiver).value
        CANMsg.LEN = len(data)
        CANMsg.MSGTYPE = PCAN_MESSAGE_EXTENDED

        for i in range(CANMsg.LEN):
            CANMsg.DATA[i] = int(data[i])

        # The message is sent to the configured hardware
        return CANMsg

    def CanCmdGetBlock(self, command):
        return 0x3F & (command >> 10)

    def CanCmdGetBlockCmd(self, command):
        return 0xFF & (command >> 2)

    def CanMessage20GetFields(self, CANMsgId):
        command = 0xFFFF & (CANMsgId >> 12)
        sender = 0x3F & (CANMsgId >> 6)
        receiver = 0x3F & (CANMsgId >> 0)
        return [command, sender, receiver]

    def CanMessage20Ack(self, CANMsg):
        fields = self.CanMessage20GetFields(CANMsg.ID)
        ackCmd = self.CanCmd(self.CanCmdGetBlock(fields[0]),
                             self.CanCmdGetBlockCmd(fields[0]), 0, 0)
        data = []
        for i in range(CANMsg.LEN):
            data.append(int(CANMsg.DATA[i]))
        return self.CanMessage20(ackCmd, fields[2], fields[1], data)

    def CanMessage20AckError(self, CANMsg):
        fields = self.CanMessage20GetFields(CANMsg.ID)
        ackCmd = self.CanCmd(self.CanCmdGetBlock(fields[0]),
                             self.CanCmdGetBlockCmd(fields[0]), 0, 1)
        data = []
        for i in range(CANMsg.LEN):
            data.append(int(CANMsg.DATA[i]))
        return self.CanMessage20(ackCmd, fields[2], fields[1], data)

    def CanCmd(self, block, cmd, request, error=0):
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
            Specifies if you want to set the error bit (`0`) or not (`1`).
            Please note that the values have these values according to the
            documentation. According to the usage in the tool, it would make
            more sense that these value are swapped, since most calls of this
            function use `0` as argument for the error value.

        Returns
        -------

        A 16 bit integer number representing the requested command
        """

        # TODO: This method does not use `self` at all. Maybe it makes sense to
        # remove this code from the class and use a standalone function
        # instead.
        block = block & 0x3F
        cmd = cmd & 0xFF
        request = request & 1
        error = error & 1
        CanCmd = block << 10
        CanCmd |= (cmd << 2)
        CanCmd |= (request << 1)
        CanCmd |= error
        return CanCmd

    def CanMessage20Id(self, command, sender, receiver):
        ID = (command << 12)
        ID |= (sender << 6)
        ID |= receiver
        return ID

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
        for i in range(0, self.GetReadArrayIndex()):
            msg = self.readArray[i]["CanMsg"]
            if msg.ID in iDs:
                iDs[msg.ID] += 1
            else:
                iDs[msg.ID] = 1

        for iD in iDs:
            [command, _sender, _receiver] = self.CanMessage20GetFields(iD)
            cmds[command] = iDs[iD]

        return [iDs, cmds]

    def ReadMessage(self):
        while self.RunReadThread:
            try:
                self.tCanReadWriteMutex.acquire()
                result = self.pcan.Read(self.m_PcanHandle)
                self.tCanReadWriteMutex.release()
                if result[0] == PCAN_ERROR_OK:
                    peakCanTimeStamp = result[2].millis_overflow * (
                        2**32) + result[2].millis + result[2].micros / 1000
                    self.readArray.append({
                        "CanMsg": result[1],
                        "PcTime": self.getTimeMs(),
                        "PeakCanTime": peakCanTimeStamp
                    })
                elif result[0] == PCAN_ERROR_QOVERRUN:
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
        self.tWriteFrameWaitAckRetries(message, retries=2)

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

    """
    Write name and get name (bluetooth command)
    """

    def vBlueToothNameWrite(self, receiver, DeviceNr, Name):
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

    """
    Get name (bluetooth command)
    """

    def BlueToothNameGet(self, receiver, DeviceNr):
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

    """
    Get address (bluetooth command)
    """

    def BlueToothAddressGet(self, receiver, DeviceNr):
        cmd = self.CanCmd(MyToolItBlock["System"], MyToolItSystem["Bluetooth"],
                          1, 0)
        payload = [
            SystemCommandBlueTooth["MacAddress"], DeviceNr, 0, 0, 0, 0, 0, 0
        ]
        message = self.CanMessage20(cmd, self.sender, receiver, payload)
        Address = self.tWriteFrameWaitAckRetries(message, retries=2)
        Address = Address["Payload"]
        Address = Address[2:]
        return iMessage2Value(Address)

    """
    Get RSSI (Bluetooth command)
    """

    def BlueToothRssiGet(self, receiver, DeviceNr):
        cmd = self.CanCmd(MyToolItBlock["System"], MyToolItSystem["Bluetooth"],
                          1, 0)
        message = self.CanMessage20(
            cmd, self.sender, receiver,
            [SystemCommandBlueTooth["Rssi"], DeviceNr, 0, 0, 0, 0, 0, 0])
        ack = self.tWriteFrameWaitAckRetries(message, retries=2)
        ack = ack["Payload"]
        ack = ack[2]
        ack = to8bitSigned(ack)
        return ack

    """
    Connect to STH by connect to MAC Address command
    """

    def iBlueToothConnect2MacAddr(self, receiver, iMacAddr):
        cmd = self.CanCmd(MyToolItBlock["System"], MyToolItSystem["Bluetooth"],
                          1, 0)
        au8Payload = [SystemCommandBlueTooth["DeviceConnectMacAddr"], 0]
        au8MacAddr = au8Value2Array(int(iMacAddr), 6)
        au8Payload.extend(au8MacAddr)
        message = self.CanMessage20(cmd, self.sender, receiver, au8Payload)
        ack = self.tWriteFrameWaitAckRetries(message, retries=2)
        ack = ack["Payload"]
        ack = ack[2:]
        iMacAddrReadBack = iMessage2Value(
            ack)  # if not successful this will be 0
        if iMacAddrReadBack != iMacAddr:
            self.bConnected = False
        else:
            self.bConnected = True
        return iMacAddrReadBack

    """
    Connect to device via name
    """

    def bBlueToothConnectPollingName(self, stuNr, sName, log=True):
        self.sDevName = None
        endTime = time.time() + BluetoothTime["Connect"]
        self.Logger.Info("Try to connect to Device Name: " + sName)
        dev = None
        devList = None
        while time.time() < endTime and False == self.bConnected:
            devList = self.tDeviceList(stuNr)
            for dev in devList:
                if sName == dev["Name"]:
                    self.iAddress = dev["Address"]
                    self.sDevName = dev["Name"]
                    self.DeviceNr = dev["DeviceNumber"]
                    currentTime = time.time()
                    endTime = currentTime + BluetoothTime["Connect"]
                    self.bBlueToothConnectDeviceConnect(stuNr, self.DeviceNr)
                    while time.time() < endTime and False == self.bConnected:
                        self.bBlueToothCheckConnect(stuNr)
                    if self.bConnected and log:
                        self.Logger.Info("Connected to: " +
                                         sBlueToothMacAddr(self.iAddress) +
                                         "(" + self.sDevName + ")")
                    break
        if None == self.sDevName:
            if False != log:
                self.Logger.Info("Available Devices: " + str(devList))
            self.__exitError("Unable to connect to device")
        return self.bConnected

    def tDeviceList(self, stuNr, bLog=True):
        devList = []
        self.vBlueToothConnectConnect(stuNr, log=False)
        devAll = self.iBlueToothConnectTotalScannedDeviceNr(stuNr, log=bLog)
        for dev in range(0, devAll):
            endTime = time.time() + BluetoothTime["Connect"]
            name = ''
            nameOld = None
            while nameOld != name and time.time() < endTime:
                nameOld = name
                name = self.BlueToothNameGet(stuNr, dev)[0:8]
            endTime = time.time() + BluetoothTime["Connect"]
            address = 0
            while 0 == address and time.time() < endTime:
                address = self.BlueToothAddressGet(stuNr, dev)
            rssi = 0
            while 0 == rssi and time.time() < endTime:
                rssi = self.BlueToothRssiGet(stuNr, dev)
            devList.append({
                "DeviceNumber": dev,
                "Name": name,
                "Address": address,
                "RSSI": rssi
            })
        return devList

    """
    Connect to device via Bluetooth Address
    """

    def bBlueToothConnectPollingAddress(self, stuNr, iAddress, bLog=True):
        endTime = time.time() + BluetoothTime["Connect"]
        self.Logger.Info("Try to connect to Test Device Address: " +
                         str(iAddress))
        while time.time() < endTime and False == self.bConnected:
            devList = self.tDeviceList(stuNr)
            for dev in devList:
                if iAddress == hex(dev["Address"]):
                    self.iAddress = iAddress
                    self.sDevName = dev["Name"]
                    self.DeviceNr = dev["DeviceNumber"]
                    currentTime = time.time()
                    endTime = currentTime + BluetoothTime["Connect"]
                    self.bBlueToothConnectDeviceConnect(stuNr, self.DeviceNr)
                    while time.time() < endTime and False == self.bConnected:
                        self.bBlueToothCheckConnect(stuNr)
                    if False != self.bConnected and False != bLog:
                        self.Logger.Info("Connected to: " + self.iAddress)
        if None == self.sDevName:
            self.Logger.Info("Available Devices: " + str(dev))
            self.__exitError("No Device Name was available")
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
        time.sleep(0.1)
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
        timeReset = iMessage2Value(timeReset)
        timeAdvertisement = iMessage2Value(timeAdvertisement)
        return [timeReset, timeAdvertisement]

    def Standby(self, receiver):
        sendData = ActiveState()
        sendData.asbyte = 0
        sendData.b.bSetState = 1
        sendData.b.u2NodeState = Node["Application"]
        sendData.b.u3NetworkState = NetworkState["Standby"]
        self.Logger.Info("Send Standby Command")
        index = self.cmdSend(receiver, MyToolItBlock["System"],
                             MyToolItSystem["ActiveState"], [sendData.asbyte])
        self.Logger.Info("Received Payload " +
                         payload2Hex(self.getReadMessageData(index)))

    def sProductData(self, name, bLog=True):
        sReturn = ""
        if "GTIN" == name:
            index = self.cmdSend(MyToolItNetworkNr["STH1"],
                                 MyToolItBlock["ProductData"],
                                 MyToolItProductData["GTIN"], [],
                                 log=bLog)
            iGtin = iMessage2Value(self.getReadMessageData(index))
            if False != bLog:
                self.Logger.Info("GTIN: " + str(iGtin))
            sReturn = str(iGtin)
        elif "HardwareRevision" == name:
            index = self.cmdSend(MyToolItNetworkNr["STH1"],
                                 MyToolItBlock["ProductData"],
                                 MyToolItProductData["HardwareRevision"], [],
                                 log=bLog)
            tHwRev = self.getReadMessageData(index)
            if False != bLog:
                self.Logger.Info("Hardware Revision: " + str(tHwRev))
            sReturn = str(tHwRev[5]) + "." + str(tHwRev[6]) + "." + str(
                tHwRev[7])
        elif "FirmwareVersion" == name:
            index = self.cmdSend(MyToolItNetworkNr["STH1"],
                                 MyToolItBlock["ProductData"],
                                 MyToolItProductData["FirmwareVersion"], [],
                                 log=bLog)
            tFirmwareVersion = self.getReadMessageData(index)
            if False != bLog:
                self.Logger.Info("Firmware Version: " + str(tFirmwareVersion))
            sReturn = str(tFirmwareVersion[5]) + "." + str(
                tFirmwareVersion[6]) + "." + str(tFirmwareVersion[7])
        elif "ReleaseName" == name:
            index = self.cmdSend(MyToolItNetworkNr["STH1"],
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
                index = self.cmdSend(MyToolItNetworkNr["STH1"],
                                     MyToolItBlock["ProductData"],
                                     MyToolItProductData["SerialNumber" +
                                                         str(i)], [],
                                     log=bLog)
                element = self.getReadMessageData(index)
                aiSerialNumber.extend(element)
            try:
                sReturn = array.array(
                    'b', bytearray(aiSerialNumber)).tostring().encode('utf-8')
            except:
                sReturn = ""
            if False != bLog:
                self.Logger.Info("Serial Number: " + str(sReturn))
        elif "Name" == name:
            aiName = []
            for i in range(1, 17):
                index = self.cmdSend(MyToolItNetworkNr["STH1"],
                                     MyToolItBlock["ProductData"],
                                     MyToolItProductData["Name" + str(i)], [],
                                     log=bLog)
                element = self.getReadMessageData(index)
                aiName.extend(element)
            try:
                sReturn = array.array(
                    'b', bytearray(aiName)).tostring().encode('utf-8')
            except:
                sReturn = ""
            if False != bLog:
                self.Logger.Info("Name: " + str(sReturn))
        elif "OemFreeUse" == name:
            aiOemFreeUse = []
            for i in range(1, 9):
                index = self.cmdSend(
                    MyToolItNetworkNr["STH1"], MyToolItBlock["ProductData"],
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
        ack = to8bitSigned(ack)
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
        ack = iMessage2Value(ack)
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
