
from PCANBasic import *
import threading
from time import sleep, time
import os

PeakCanIoPort = 0x2A0
PeakCanInterrupt = 11
PeakCanBitrateFd = "f_clock_mhz=20, nom_brp=5, nom_tseg1=2, nom_tseg2=1, nom_sjw=1, data_brp=2, data_tseg1=3, data_tseg2=1, data_sjw=1"

from MyToolItCommands import *
from MyToolItNetworkNumbers import NetworkNumber


def fSleepTime(timeReset):
    return ((0xFF & timeReset[3]) << 24) | ((0xFF & timeReset[2]) << 16) | ((0xFF & timeReset[1]) << 8) | (0xFF & timeReset[0])


def fSleepAdvertisement(timeAdvertisement):
    return ((0xFF & timeAdvertisement[1]) << 8) | (0xFF & timeAdvertisement[0])


def fBlueToothMacAddress(macAddress):
    return ((0xFF & macAddress[5]) << 40) | ((0xFF & macAddress[4]) << 32) | ((0xFF & macAddress[3]) << 24) | ((0xFF & macAddress[2]) << 16) | ((0xFF & macAddress[1]) << 8) | (0xFF & macAddress[0])


def to8bitSigned(num): 
    mask7 = 128  # Check 8th bit ~ 2^8
    mask2s = 127  # Keep first 7 bits
    if (mask7 & num == 128):  # Check Sign (8th bit)
        num = -((~int(num) + 1) & mask2s)  # 2's complement
    return num


def rreplace(s, old, new):
    return (s[::-1].replace(old[::-1], new[::-1], 1))[::-1]


class Logger():

    def __init__(self, fileName, fileNameError):
        if not os.path.exists(os.path.dirname(fileName)):
            os.makedirs(os.path.dirname(fileName))
        self.file = open(fileName, "w")
        self.startTime = int(round(time() * 1000))
        self.fileName = fileName
        self.fileNameError = fileNameError

    def __exit__(self):
        self.file.close()
        if False != self.ErrorFlag:
            if os.path.isfile(self.fileNameError) and os.path.isfile(self.fileName):
                os.remove(self.fileNameError)
            if os.path.isfile(self.fileName):
                os.rename(self.fileName, self.fileNameError)

    def getTimeStamp(self):     
        return int(round(time() * 1000)) - int(self.startTime)
                            
    def Info(self, message):
        self.file.write("[I](")
        self.file.write(str(self.getTimeStamp()))
        self.file.write("ms): ")
        self.file.write(message)
        self.file.write("\n")
        
    def Error(self, message):
        self.file.write("[E](")
        self.file.write(str(self.getTimeStamp()))
        self.file.write("ms): ")
        self.file.write(message)
        self.file.write("\n")
        
    def Warning(self, message):
        self.file.write("[W](")
        self.file.write(str(self.getTimeStamp()))
        self.file.write("ms): ")
        self.file.write(message)
        self.file.write("\n")
        
        
class PeakCanFd(object):

    def __init__(self, baudrate, testMethodName, testMethodNameError, sender, receiver):
        self.sender = sender
        self.receiver = receiver
        self.Logger = Logger(testMethodName, testMethodNameError)
        self.Logger.ErrorFlag = False
        self.startTime = int(round(time() * 1000))
        self.m_objPCANBasic = PCANBasic()
        self.baudrate = baudrate
        self.hwtype = PCAN_TYPE_ISA
        self.ioport = PeakCanIoPort
        self.interrupt = PeakCanInterrupt
        self.m_PcanHandle = PCAN_USBBUS1
        self.Error = False
        self.RunReadThread = False
        self.CanTimeStampStart(0)
        if 0 == baudrate:
            self.m_IsFD = True
        else:
            self.m_IsFD = False
        if self.m_IsFD:
            result = self.m_objPCANBasic.InitializeFD(self.m_PcanHandle, PeakCanBitrateFd)
        else:
            result = self.m_objPCANBasic.Initialize(self.m_PcanHandle, baudrate, self.hwtype, self.ioport, self.interrupt)
        if result != PCAN_ERROR_OK:
            print("Error while init Peak Can Basi Module: " , result)
        else:
            # Prepares the PCAN-Basic's PCAN-Trace file
            #
            result = self.m_objPCANBasic.SetValue(self.m_PcanHandle, PCAN_BUSOFF_AUTORESET, PCAN_PARAMETER_ON)
            if result != PCAN_ERROR_OK:
                print("Error while setting PCAN_BUSOFF_AUTORESET")
            self.ConfigureTraceFile()
            self.Reset()
            self.ReadArrayReset()
                        
    def __exit__(self): 
        if False == self.Error:
            if False != self.RunReadThread:
                self.readThreadStop()
            else:
                self.Logger.Error("Peak CAN Message Over Run")
                self.Error = True
        self.Reset()   
        self.m_objPCANBasic.Uninitialize(self.m_PcanHandle)
        sleep(1)
        [iDs, cmds] = self.ReadMessageStatistics()
        for cmd, value in cmds.items():
            self.Logger.Info(self.strCmdNrToCmdName(cmd) + " received " + str(value) + " times")
        self.Logger.__exit__()
            
    def __exitError(self):
        self.Logger.ErrorFlag = True
        self.__exit__()
        self.Error = True
        raise

    def readThreadStop(self):
        if False != self.RunReadThread:
            self.RunReadThread = False            
            self.readThread.join()
                    
    def ReadArrayReset(self):
        self.readThreadStop()            
        self.readArray = [{"CanMsg" : self.CanMessage20(0, 0, 0, [0, 0, 0, 0, 0, 0, 0, 0]), "PcTime" : self.getTimeMs(), "PeakCanTime" : 0}]
        self.readArray.append({"CanMsg" : self.CanMessage20(0, 0, 0, [0, 0, 0, 0, 0, 0, 0, 0]), "PcTime" : self.getTimeMs(), "PeakCanTime" : 0})
        sleep(0.2)
        self.timeStampStart = self.getTimeMs()
        self.RunReadThread = True
        self.readThread = threading.Thread(target=self.ReadMessage, name="CanReadThread")
        self.readThread.start()
        self.Reset()
        sleep(0.2)
        
    def ConfigureTraceFile(self):
        # Configure the maximum size of a trace file to 5 megabytes
        #
        iBuffer = 5
        stsResult = self.m_objPCANBasic.SetValue(self.m_PcanHandle, PCAN_TRACE_SIZE, iBuffer)
        if stsResult != PCAN_ERROR_OK:
            print("Error while init Peak Can Basi Module while configurating Trace File: " , stsResult)

        # Configure the way how trace files are created: 
        # * Standard name is used
        # * Existing file is ovewritten, 
        # * Only one file is created.
        # * Recording stopts when the file size reaches 5 megabytes.
        #
        iBuffer = TRACE_FILE_SINGLE | TRACE_FILE_OVERWRITE
        stsResult = self.m_objPCANBasic.SetValue(self.m_PcanHandle, PCAN_TRACE_CONFIGURE, iBuffer)        
        if stsResult != PCAN_ERROR_OK:
            print("Error while init Peak Can Basic Module while setting value in Trace File: " , stsResult)
            
    def Reset(self):
        self.m_objPCANBasic.Reset(self.m_PcanHandle)

    def CanTimeStampStart(self, CanTimeStampStart):
        self.PeakCanTimeStampStart = CanTimeStampStart
        
    def strCmdNrToBlockName(self, cmd):
        return CommandBlock[self.CanCmdGetBlock(cmd)]
        
    def strCmdNrToCmdName(self, cmd):
        cmdBlock = self.CanCmdGetBlock(cmd)
        cmdNr = self.CanCmdGetBlockCmd(cmd)
        cmdNrName = "Unknown"
        if MY_TOOL_IT_BLOCK_SYSTEM == cmdBlock:
            cmdNrName = CommandBlockSystem[cmdNr]
        elif MY_TOOL_IT_BLOCK_STREAMING == cmdBlock:
            cmdNrName = CommandBlockStreaming[cmdNr]
        elif MY_TOOL_IT_BLOCK_STATISTICAL_DATA == cmdBlock:
            cmdNrName = CommandBlockStatisticalData[cmdNr]
        elif MY_TOOL_IT_BLOCK_CONFIGURATION == cmdBlock:
            cmdNrName = CommandBlockConfiguration[cmdNr]
        elif MY_TOOL_IT_BLOCK_PRODUCT_DATA == cmdBlock:
            cmdNrName = CommandBlockProductData[cmdNr]
        elif MY_TOOL_IT_BLOCK_TEST == cmdBlock:
            cmdNrName = CommandBlockTest[cmdNr]
        return cmdNrName
    
    def PeakCanPayload2Array(self, message):
        payload = []
        if None != message:
            for item in message.DATA:
                payload.append(item)
        return payload
    
    def ComparePayloadEqual(self, payload1, payload2):
        bEqual = False
        if None != payload1 and None != payload2:
            if len(payload1) == len(payload2):
                bEqual = True
                for i in range(0, len(payload1)):
                    if payload1[i] != payload2[i]:
                        bEqual = False
                        break
        return bEqual
                
    def WriteFrame(self, CanMsg):  
        returnMessage = CanMsg
        if "Error" != returnMessage:
            returnMessage = self.m_objPCANBasic.Write(self.m_PcanHandle, CanMsg)
            if(PCAN_ERROR_OK != returnMessage):
                print("WriteFrame Error: " + hex(returnMessage))
                self.Logger.Info("WriteFrame Error: " + hex(returnMessage))
                returnMessage = "Error"    
                self.__exitError()
        return returnMessage
    
    def WriteFrameWaitAck(self, CanMsg, waitMs=1000, currentIndex=None, printLog=False, assumedPayload=None, bError=False):  
        indexStart = self.GetReadArrayIndex()
        sleep(0.001)  # to assure granularity
        if None == currentIndex:
            currentIndex = self.GetReadArrayIndex() - 1
        if currentIndex < len(self.readArray):
            message = self.readArray[currentIndex]
        else: 
            message = {"CanMsg" : self.CanMessage20(0, 0, 0, [0, 0, 0, 0, 0, 0, 0, 0]), "PcTime" : self.getTimeMs(), "PeakCanTime" : 0}
        if(False != printLog):
            print("Message ID Send: " + hex(CanMsg.ID))
            print("Message DATA Send: " + self.payload2Hex(CanMsg.DATA))
        self.timeStampStart = self.getTimeMs()
        returnMessage = self.WriteFrame(CanMsg)        
        if "Error" != returnMessage:
            waitTimeMax = self.getTimeMs() + waitMs
            if False != bError:
                CanMsgAckError = self.CanMessage20Ack(CanMsg)
                CanMsgAck = self.CanMessage20AckError(CanMsg)                 
            else:
                CanMsgAck = self.CanMessage20Ack(CanMsg)
                CanMsgAckError = self.CanMessage20AckError(CanMsg) 
            indexStartError = currentIndex
            while (CanMsgAck.ID != message["CanMsg"].ID) or (message["PcTime"] <= self.timeStampStart) or indexStart == self.GetReadArrayIndex() or (not self.ComparePayloadEqual(self.PeakCanPayload2Array(message["CanMsg"]), assumedPayload) and None != assumedPayload):
                if((CanMsgAckError.ID == message["CanMsg"].ID) and (indexStartError < currentIndex)):
                    indexStartError = currentIndex
                    [command, sender, receiver] = self.CanMessage20GetFields(message["CanMsg"].ID)
                    cmdBlockName = self.strCmdNrToBlockName(command)
                    cmdName = self.strCmdNrToCmdName(command)
                    senderName = NetworkNumber[sender]
                    receiverName = NetworkNumber[receiver]
                    if False != bError:
                        self.Logger.Error("Error Ack Received: " + cmdBlockName + " - " + cmdName + "(" + senderName + "->" + receiverName + ")" + "; Payload - " + self.payload2Hex(CanMsg.DATA))
                        if False != printLog:
                            print("Error Ack Received: " + cmdBlockName + " - " + cmdName + "(" + senderName + "->" + receiverName + ")" + "; Payload - " + self.payload2Hex(CanMsg.DATA))
                    else:
                        self.Logger.Error("Ack Received(Error assumed): " + cmdBlockName + " - " + cmdName + "(" + senderName + "->" + receiverName + ")" + "; Payload - " + self.payload2Hex(CanMsg.DATA))
                        if False != printLog:
                            print("Ack Received(Error assumed): " + cmdBlockName + " - " + cmdName + "(" + senderName + "->" + receiverName + ")" + "; Payload - " + self.payload2Hex(CanMsg.DATA))
                    break
                elif(waitTimeMax < self.getTimeMs()):
                    returnMessage = "Error"
                    [command, sender, receiver] = self.CanMessage20GetFields(CanMsg.ID)
                    cmdBlockName = self.strCmdNrToBlockName(command)
                    cmdName = self.strCmdNrToCmdName(command)
                    senderName = NetworkNumber[sender]
                    receiverName = NetworkNumber[receiver]
                    self.Logger.Warning("No (Error) Ack Received: " + cmdBlockName + " - " + cmdName + "(" + senderName + "->" + receiverName + ")" + "; Payload - " + self.payload2Hex(CanMsg.DATA))
                    if False != printLog:
                        print("No (Error) Ack Received: " + cmdBlockName + " - " + cmdName + "(" + senderName + "->" + receiverName + ")" + "; Payload - " + str(CanMsg.DATA))
                    break
                
                if currentIndex < (self.GetReadArrayIndex() - 1):
                    currentIndex += 1
                    message = self.readArray[currentIndex]
                else:
                    sleep(waitMs / 10000)
                
        if "Error" != returnMessage:
            payload = self.PeakCanPayload2Array(message["CanMsg"])
            returnMessage = {"ID" : hex(message["CanMsg"].ID), "Payload" : payload, "PcTime" : message["PcTime"], "CanTime" : message["PeakCanTime"]}
            self.timeStampStart = self.getTimeMs()
        return [returnMessage, currentIndex]
    
    def WriteFrameWaitAckRetries(self, CanMsg, retries=2, waitMs=1000, printLog=False, bErrorAck=False, assumedPayload=None, bErrorExit=True):  
        currentIndex = self.GetReadArrayIndex() - 1
        retries += 1
        for i in range(0, retries):
            [returnMessage, currentIndex] = self.WriteFrameWaitAck(CanMsg, waitMs=waitMs, currentIndex=currentIndex, printLog=printLog, assumedPayload=assumedPayload, bError=bErrorAck)
            if "Error" != returnMessage:
                break
            elif (retries - 1) == i:                
                [command, sender, receiver] = self.CanMessage20GetFields(CanMsg.ID)
                cmdBlockName = self.strCmdNrToBlockName(command)
                cmdName = self.strCmdNrToCmdName(command)
                senderName = NetworkNumber[sender]
                receiverName = NetworkNumber[receiver]
                self.Logger.Error("Message Request Failed: " + cmdBlockName + " - " + cmdName + "(" + senderName + "->" + receiverName + ")" + "; Payload - " + self.payload2Hex(CanMsg.DATA))
                if False != printLog:
                    print("Message Request Failed: " + cmdBlockName + " - " + cmdName + "(" + senderName + "->" + receiverName + ")" + "; Payload - " + self.payload2Hex(CanMsg.DATA))
                if False != bErrorExit:
                    self.__exitError()
        return returnMessage

    def cmdSend(self, receiver, blockCmd, subCmd, payload, log=True, retries=3, bErrorAck=False, printLog=False):
        cmd = self.CanCmd(blockCmd, subCmd, 1, 0)
        message = self.CanMessage20(cmd, self.sender, receiver, payload)
        index = self.GetReadArrayIndex()
        msgAck = self.WriteFrameWaitAckRetries(message, retries=retries, waitMs=1000, bErrorAck=bErrorAck, printLog=printLog)
        if False != log:
            canCmd = self.CanCmd(blockCmd, subCmd, 1, 0)
            self.Logger.Info(NetworkNumber[self.sender] + "->" + NetworkNumber[receiver] + "(CanTimeStamp: " + str(msgAck["CanTime"] - self.PeakCanTimeStampStart) + "ms): " + self.strCmdNrToCmdName(canCmd) + " - " + self.payload2Hex(payload))
            self.Logger.Info("Assumed receive message number: " + str(index))
        sleep(0.2)  # synch to read thread
        return index 

    def cmdReset(self, receiver, retries=5, log=True):
        if False != log:
            self.Logger.Info("Reset " + NetworkNumber[receiver])
        cmd = self.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_RESET, 1, 0)
        retMsg = self.WriteFrameWaitAckRetries(self.CanMessage20(cmd, self.sender, receiver, []), retries=retries)
        sleep(2)
        return retMsg
        
    def singleValueCollect(self, receiver, subCmd, b1, b2, b3, log=True, printLog=False):
        accFormat = AtvcFormat()
        accFormat.asbyte = 0
        accFormat.b.bNumber1 = b1
        accFormat.b.bNumber2 = b2
        accFormat.b.bNumber3 = b3
        accFormat.b.u3DataSets = DataSets1
        return self.cmdSend(receiver, MY_TOOL_IT_BLOCK_STREAMING, subCmd, [accFormat.asbyte], log=log, printLog=printLog)

    def ValueDataSet1(self, data, b1, b2, b3, array1, array2, array3):
        count = 0
        if False != b1:
            Acc = messageValueGet(data[2:4])
            array1.append(Acc)
            count += 1
        if False != b2:
            if 0 == count:
                Acc = messageValueGet(data[2:4])
            else:
                Acc = messageValueGet(data[4:6])
            array2.append(Acc)
            count += 1
        if False != b3:
            if 0 == count:
                Acc = messageValueGet(data[2:4])
            elif 1 == count:
                Acc = messageValueGet(data[4:6])
            else:
                Acc = messageValueGet(data[6:8])
            array3.append(Acc)
        return [array1, array2, array3]

    def ValueDataSet3(self, data, b1, b2, b3, array1, array2, array3):
        Acc1 = messageValueGet(data[2:4])
        Acc2 = messageValueGet(data[4:6])
        Acc3 = messageValueGet(data[6:8])
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
        messageIdFilter = self.CanCmd(MY_TOOL_IT_BLOCK_STREAMING, subCmd, 0, 0)
        messageIdFilter = self.CanMessage20Id(messageIdFilter, receiver, self.sender)
        messageIdFilter = hex(messageIdFilter)
        data = self.getReadMessageData(index)
        messageId = self.getReadMessageId(index)
        array1 = []
        array2 = []
        array3 = []
        if messageId == messageIdFilter:
            self.ValueDataSet1(data, b1, b2, b3, array1, array2, array3)
        else:
            raise
        if 0 < len(array1):
            array1 = [array1[0]]
        if 0 < len(array2):
            array2 = [array2[0]]
        if 0 < len(array3):
            array3 = [array3[0]]
        return [array1, array2, array3]
       
    def streamingValueCollect(self, receiver, subCmd, dataSets, b1, b2, b3, testTimeMs, log=True, StartupTimeMs=0):
        if False != log:
            self.Logger.Info("Test Time: " + str(testTimeMs) + "ms")
        indexStart = self.streamingStart(receiver, subCmd, dataSets, b1, b2, b3, log=log)
        if False != log:
            self.Logger.Info("indexStart: " + str(indexStart))
        sleep(testTimeMs / 1000)
        self.streamingStop(receiver, subCmd)
        sleep(1)  # synch to read thread
        indexEnd = self.GetReadArrayIndex() - 180  # do not catch stop command
        countDel = 0
        while testTimeMs < self.getReadMessageTimeMs(indexStart, indexEnd) - 0.5:
            countDel += 1
            indexEnd -= 1
        if False != log:
            self.Logger.Info("Deleted Messages do achieve " + str(testTimeMs) + "ms: " + str(countDel + 180))
            self.Logger.Info("indexEnd: " + str(indexEnd))
        if 0.2 * (indexEnd - indexStart) < countDel:
            self.Logger.Warning("Deleted Messages do achieve " + str(testTimeMs) + "ms: " + str(countDel + 180))
        
        return[indexStart, indexEnd]

    def streamingValueArray(self, receiver, streamingCmd, dataSets, b1, b2, b3, indexStart, indexEnd):
        messageIdFilter = self.CanCmd(MY_TOOL_IT_BLOCK_STREAMING, streamingCmd, 0, 0)
        messageIdFilter = self.CanMessage20Id(messageIdFilter, receiver, self.sender)
        messageIdFilter = hex(messageIdFilter)
        runIndex = indexStart
        array1 = []
        array2 = []
        array3 = []
        while runIndex <= indexEnd:
            data = self.getReadMessageData(runIndex)
            messageId = self.getReadMessageId(runIndex)
            if messageId == messageIdFilter:
                if DataSets1 == dataSets:
                    [array1, array2, array3] = self.ValueDataSet1(data, b1, b2, b3, array1, array2, array3)
                elif DataSets3 == dataSets:
                    [array1, array2, array3] = self.ValueDataSet3(data, b1, b2, b3, array1, array2, array3)
                else:
                    raise
            runIndex += 1
        return [array1, array2, array3]

    def ValueDataSet1MsgCounter(self, data, b1, b2, b3, array1, array2, array3):
        if False != b1:
            array1.append(data[1])
        if False != b2:
            array2.append(data[1])
        if False != b3:
            array3.append(data[1])
        return [array1, array2, array3]

    def ValueDataSet3MsgCounter(self, data, b1, b2, b3, array1, array2, array3):
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
    
    
    def streamingValueArrayMessageCounters(self, receiver, streamingCmd, dataSets, b1, b2, b3, indexStart, indexEnd):
        messageIdFilter = self.CanCmd(MY_TOOL_IT_BLOCK_STREAMING, streamingCmd, 0, 0)
        messageIdFilter = self.CanMessage20Id(messageIdFilter, receiver, self.sender)
        messageIdFilter = hex(messageIdFilter)
        runIndex = indexStart
        array1 = []
        array2 = []
        array3 = []
        while runIndex <= indexEnd:
            data = self.getReadMessageData(runIndex)
            messageId = self.getReadMessageId(runIndex)
            if messageId == messageIdFilter:
                if DataSets1 == dataSets:
                    [array1, array2, array3] = self.ValueDataSet1MsgCounter(data, b1, b2, b3, array1, array2, array3)
                elif DataSets3 == dataSets:
                    [array1, array2, array3] = self.ValueDataSet3MsgCounter(data, b1, b2, b3, array1, array2, array3)
                else:
                    raise
            runIndex += 1
        return [array1, array2, array3]
    
    def samplingPoints(self, array1, array2, array3):
        samplingPoints = len(array1)
        samplingPoints += len(array2)
        samplingPoints += len(array3)
        return samplingPoints
    
    def ValueLog(self, array1, array2, array3, fCbfRecalc, preFix, postFix):
        samplingPointMax = len(array1)
        if(len(array2) > samplingPointMax):
            samplingPointMax = len(array2)
        if(len(array3) > samplingPointMax):
            samplingPointMax = len(array3)

        samplingPoints = self.samplingPoints(array1, array2, array3)
        self.Logger.Info("Received Sampling Points: " + str(samplingPoints))

        for i in range(0, samplingPointMax):
            if 0 < len(array1):
                self.Logger.Info(preFix + "X: " + str(fCbfRecalc(array1[i])) + postFix)
            if 0 < len(array2):
                self.Logger.Info(preFix + "Y: " + str(fCbfRecalc(array2[i])) + postFix)
            if 0 < len(array3):
                self.Logger.Info(preFix + "Z: " + str(fCbfRecalc(array3[i])) + postFix)
        return samplingPoints
      
    def streamingStart(self, receiver, subCmd, dataSets, b1, b2, b3, log=True):
        accFormat = AtvcFormat()
        accFormat.asbyte = 0
        accFormat.b.bStreaming = 1
        accFormat.b.bNumber1 = b1
        accFormat.b.bNumber2 = b2
        accFormat.b.bNumber3 = b3
        accFormat.b.u3DataSets = dataSets
        cmd = self.CanCmd(MY_TOOL_IT_BLOCK_STREAMING, subCmd, 1, 0)
        message = self.CanMessage20(cmd, self.sender, receiver, [accFormat.asbyte])
        if False != log:
            canCmd = self.CanCmd(MY_TOOL_IT_BLOCK_STREAMING, subCmd, 1, 0)
            self.Logger.Info("Start sending  " + self.strCmdNrToCmdName(canCmd) + "; Subpayload: " + hex(accFormat.asbyte))
            
        indexStart = self.GetReadArrayIndex() + 1
        self.WriteFrameWaitAckRetries(message) 
        return indexStart
        
    def streamingStop(self, receiver, subCmd, bErrorExit=True):
        AtvcSet = AtvcFormat()
        AtvcSet.asbyte = 0
        AtvcSet.b.bStreaming = 1
        AtvcSet.b.u3DataSets = DataSetsNone
        cmd = self.CanCmd(MY_TOOL_IT_BLOCK_STREAMING, subCmd, 1, 0)
        message = self.CanMessage20(cmd, self.sender, receiver, [AtvcSet.asbyte])
        self.Logger.Info("_____________________________________________________________")
        self.Logger.Info("Stop Streaming - " + self.strCmdNrToCmdName(cmd))
        ack = self.WriteFrameWaitAckRetries(message, retries=200, waitMs=250, printLog=False, assumedPayload=[AtvcSet.asbyte, 0, 0, 0, 0, 0, 0, 0], bErrorExit=bErrorExit)
        self.Logger.Info("_____________________________________________________________")
        return ack
        
    def ConfigAdc(self, receiver, preq, aquistionTime, oversampling, adcRef, log=True):
        if False != log:
            self.Logger.Info("Config ADC - Prescaler: " + str(preq) + "/" + str(AdcAcquisitionTimeName[aquistionTime]) + "/" + str(AdcOverSamplingRateName[oversampling]) + "/" + str(VRefName[adcRef]))
            self.Logger.Info("Calculated Sampling Rate: " + str(calcSamplingRate(preq, aquistionTime, oversampling)))
        byte1 = 1 << 7  # Set Sampling Rate
        cmd = self.CanCmd(MY_TOOL_IT_BLOCK_CONFIGURATION, MY_TOOL_IT_CONFIGURATION_ACCELERATION_CONFIGURATION, 1, 0)
        message = self.CanMessage20(cmd, self.sender, receiver, [byte1, preq, aquistionTime, oversampling, adcRef, 0, 0, 0])
        return self.WriteFrameWaitAckRetries(message, retries=5)["Payload"]
    
    def calibMeasurement(self, receiver, u2Action, signal, dimension, vRef, log=True, retries=3, bSet=True, bErrorAck=False, bReset=False, printLog=False):
        messageIdFilter = self.CanCmd(MY_TOOL_IT_BLOCK_CONFIGURATION, MY_TOOL_IT_CONFIGURATION_CALIBRATE_MEASSUREMENT, 0, bErrorAck != False)
        messageIdFilter = self.CanMessage20Id(messageIdFilter, receiver, self.sender)
        messageIdFilter = hex(messageIdFilter)
        byte1 = CalibrationMeassurement()
        byte1.asbyte = 0
        byte1.b.bReset = bReset
        byte1.b.u2Action = u2Action
        byte1.b.bSet = bSet
        calibPayload = [byte1.asbyte, signal, dimension, vRef, 0, 0, 0, 0]
        indexAssumed = self.cmdSend(receiver, MY_TOOL_IT_BLOCK_CONFIGURATION, MY_TOOL_IT_CONFIGURATION_CALIBRATE_MEASSUREMENT, calibPayload, log=log, retries=retries, bErrorAck=bErrorAck, printLog=printLog)
        indexRun = indexAssumed
        indexEnd = self.GetReadArrayIndex()
        returnAck = []
        while indexRun <= indexEnd:
            if messageIdFilter == self.getReadMessageId(indexRun):
                returnAck = self.getReadMessageData(indexRun)
                break
            indexRun += indexRun
        if indexRun != indexAssumed:
            self.Logger.Warning("Calibration Measurement Index Miss (Assumed/Truly): " + str(indexAssumed) + "/" + str(indexRun))
        if indexRun == indexEnd:
            self.Logger.Error("Calibration Measurement Fail Request")
        return returnAck
    
    def statisticalData(self, receiver, subCmd, log=True, retries=3, ErrorAck=False, printLog=False):
        messageIdFilter = self.CanCmd(MY_TOOL_IT_BLOCK_STATISTICAL_DATA, subCmd, 0, ErrorAck != False)
        messageIdFilter = self.CanMessage20Id(messageIdFilter, receiver, self.sender)
        messageIdFilter = hex(messageIdFilter)
        indexAssumed = self.cmdSend(receiver, MY_TOOL_IT_BLOCK_STATISTICAL_DATA, subCmd, [], log=log, retries=retries, ErrorAck=ErrorAck, printLog=printLog)
        indexRun = indexAssumed
        indexEnd = self.GetReadArrayIndex()
        returnAck = []
        while indexRun <= indexEnd:
            if messageIdFilter == self.getReadMessageId(indexRun):
                returnAck = self.getReadMessageData(indexRun)
                break
            indexRun += indexRun
        if indexRun != indexAssumed:
            self.Logger.Warning("Statistical Data Index Miss (Assumed/Truly): " + str(indexAssumed) + "/" + str(indexRun))
        if indexRun == indexEnd:
            self.Logger.Error("Statistical Data Fail Request")
        return returnAck

    def statusWord0(self, receiver):
        cmd = self.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_STATUS_WORD0, 1, 0)
        msg = self.CanMessage20(cmd, self.sender, receiver, [])
        psw0 = self.WriteFrameWaitAckRetries(msg, retries=5)["Payload"]
        psw0 = self.AsciiStringWordBigEndian(psw0[0:4])
        return psw0

    def statusWord1(self, receiver):
        cmd = self.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_STATUS_WORD1, 1, 0)
        msg = self.CanMessage20(cmd, self.sender, receiver, [])
        psw1 = self.WriteFrameWaitAckRetries(msg, retries=5)["Payload"]
        psw1 = self.AsciiStringWordBigEndian(psw1[0:4])
        return psw1
           
    def payload2Hex(self, payload):
        payloadHex = '[{}]'.format(', '.join(hex(x) for x in payload))
        return payloadHex
    
    def AsciiStringWordBigEndian(self, ByteArray):
        value = 0
        for byte in range(len(ByteArray)):
            value += (ByteArray[byte] << (8 * byte))
        return value
    
    def AsciiStringWordLittleEndian(self, ByteArray):
        value = 0
        for byte in range(len(ByteArray)):
            value += (ByteArray[byte] << (8 * (len(ByteArray) - byte - 1)))
        return value
        
    def getTimeMs(self):
        return int(round(time() * 1000)) - int(self.startTime)
    
    def CanMessage20(self, command, sender, receiver, data):   
        # We create a TPCANMsg message structure
        #
        msgLen = len(data)
        
        if(8 >= msgLen):
            CANMsg = TPCANMsg()
            command = command & 0xFFFF
            sender = sender & 0x1F
            receiver = receiver & 0x1F
            CANMsg.ID = (command << 12)
            CANMsg.ID |= (sender << 6)
            CANMsg.ID |= receiver
            CANMsg.LEN = len(data)
            CANMsg.MSGTYPE = PCAN_MESSAGE_EXTENDED 
    
            for i in range(CANMsg.LEN):
                CANMsg.DATA[i] = int(data[i])
    
            # The message is sent to the configured hardware
            #
            return CANMsg     
        else:
            return "Error "  
        
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
        ackCmd = self.CanCmd(self.CanCmdGetBlock(fields[0]), self.CanCmdGetBlockCmd(fields[0]), 0, 0)
        data = []
        for i in range(CANMsg.LEN):
            data.append(int(CANMsg.DATA[i]))
        return self.CanMessage20(ackCmd, fields[2], fields[1], data)   

    def CanMessage20AckError(self, CANMsg): 
        fields = self.CanMessage20GetFields(CANMsg.ID)
        ackCmd = self.CanCmd(self.CanCmdGetBlock(fields[0]), self.CanCmdGetBlockCmd(fields[0]), 0, 1)
        data = []
        for i in range(CANMsg.LEN):
            data.append(int(CANMsg.DATA[i]))
        return self.CanMessage20(ackCmd, fields[2], fields[1], data) 
             
    def CanCmd(self, block, cmd, request, error):
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
        for i in range(2, self.GetReadArrayIndex()):
            msg = self.readArray[i]["CanMsg"]              
            if msg.ID in iDs:
                iDs[msg.ID] += 1
            else:
                iDs[msg.ID] = 1
                
        for iD in iDs:
            [command, sender, receiver] = self.CanMessage20GetFields(iD)  
            cmds[command] = iDs[iD]
                
        return [iDs, cmds]
            
    def ReadMessage(self):
        # We execute the "Read" function of the PCANBasic
        #
        while False != self.RunReadThread:
            result = self.m_objPCANBasic.Read(self.m_PcanHandle)
            if result[0] == PCAN_ERROR_OK:
                peakCanTimeStamp = result[2].millis_overflow * (2 ** 32) + result[2].millis
                self.readArray.append({"CanMsg" : result[1], "PcTime" : self.getTimeMs(), "PeakCanTime" : peakCanTimeStamp})                
            elif result[0] == PCAN_ERROR_QOVERRUN:
                self.Logger.Error("RxOverRun")
                print("RxOverRun")
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
        return self.readArray[element]["PeakCanTime"] - self.PeakCanTimeStampStart
    
    def getReadMessageTimeMs(self, preElement, postElement):
        return self.getReadMessageTimeStampMs(postElement) - self.getReadMessageTimeStampMs(preElement)
    
    def GetReadArrayIndex(self):
        return len(self.readArray)
    
    def BlueToothCmd(self, receiver, subCmd):
        cmd = self.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
        payload = [subCmd, 0, 0, 0, 0, 0, 0, 0]
        message = self.CanMessage20(cmd, self.sender, receiver, payload)
        ack = self.WriteFrameWaitAckRetries(message, retries=2)["Payload"][2:]
        ack = self.AsciiStringWordLittleEndian(ack)
        return ack
            
    def BlueToothConnectConnect(self, receiver):
        cmd = self.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
        message = self.CanMessage20(cmd, self.sender, receiver, [SystemCommandBlueToothConnect, 0, 0, 0, 0, 0, 0, 0])
        self.WriteFrameWaitAckRetries(message, retries=2)            
        
    def BlueToothConnectTotalScannedDeviceNr(self, receiver):
        cmd = self.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
        message = self.CanMessage20(cmd, self.sender, receiver, [SystemCommandBlueToothGetNumberAvailableDevices, 0, 0, 0, 0, 0, 0, 0])
        msg = self.WriteFrameWaitAckRetries(message, retries=2)
        deviceNumbers = int(msg["Payload"][2]) - ord('0')
        return deviceNumbers
    
    def BlueToothConnectDeviceConnect(self, receiver, deviceNr):
        cmd = self.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
        message = self.CanMessage20(cmd, self.sender, receiver, [SystemCommandBlueToothDeviceConnect, deviceNr, 0, 0, 0, 0, 0, 0])
        self.WriteFrameWaitAckRetries(message, retries=2)

    def BlueToothCheckConnect(self, receiver):
        cmd = self.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
        message = self.CanMessage20(cmd, self.sender, receiver, [SystemCommandBlueToothDeviceCheckConnected, 0, 0, 0, 0, 0, 0, 0])
        connectToDevice = self.WriteFrameWaitAckRetries(message, retries=2)["Payload"][2]
        return connectToDevice
    
    def BlueToothConnect(self, stuNr, deviceNr):        
        self.BlueToothConnectConnect(stuNr)
        deviceNumbers = self.BlueToothConnectTotalScannedDeviceNr(stuNr)
        ret = 0
        if deviceNr < deviceNumbers:
            currentTime = time()            
            endTime = currentTime + SystemCommandBlueToothConnectTimeOut 
            self.BlueToothConnectDeviceConnect(stuNr, deviceNr)    
            while time() < endTime and 0 == ret:      
                ret = self.BlueToothCheckConnect(stuNr)            
        return ret

    def BlueToothDisconnect(self, stuNr):
        cmd = self.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
        message = self.CanMessage20(cmd, self.sender, stuNr, [SystemCommandBlueToothDisconnect, 0, 0, 0, 0, 0, 0, 0])
        self.WriteFrameWaitAckRetries(message, retries=2)
        return 0 == self.BlueToothCheckConnect(stuNr)

    """
    Write name and get name (bluetooth command)
    """

    def BlueToothNameWrite(self, DeviceNr, Name):
        cmd = self.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
        Payload = [SystemCommandBlueToothSetName1, DeviceNr, 0, 0, 0, 0, 0, 0]
        for i in range(0, 6):
            if(len(Name) <= i):
                break
            Payload[i + 2] = ord(Name[i])
        message = self.CanMessage20(cmd, self.sender, self.receiver, Payload)
        self.WriteFrameWaitAckRetries(message, retries=2)
        Payload = [SystemCommandBlueToothSetName2, DeviceNr, 0, 0, 0, 0, 0, 0]
        for i in range(0, 6):
            if(len(Name) <= i + 6):
                break
            Payload[i + 2] = ord(Name[i + 6])
        message = self.CanMessage20(cmd, self.sender, self.receiver, Payload)
        self.WriteFrameWaitAckRetries(message, retries=2)

    """
    Get name (bluetooth command)
    """

    def BlueToothNameGet(self, DeviceNr):
        cmd = self.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
        message = self.CanMessage20(cmd, self.sender, self.receiver, [SystemCommandBlueToothGetName1, DeviceNr, 0, 0, 0, 0, 0, 0])
        Name = self.WriteFrameWaitAckRetries(message, retries=2)["Payload"][2:]
        message = self.CanMessage20(cmd, self.sender, self.receiver, [SystemCommandBlueToothGetName2, DeviceNr, 0, 0, 0, 0, 0, 0])
        Name = Name + self.WriteFrameWaitAckRetries(message)["Payload"][2:]
        i = 0
        while i < len(Name):
            Name[i] = chr(Name[i])
            i += 1
        Name = ''.join(Name)
        for character in range(0, ord(' ')):
            Name = Name[0:8].replace(chr(character), '')
        for character in range(128, 0xFF):
            Name = Name[0:8].replace(chr(character), '')
        return Name
    
    """
    Connect to device via name
    """    

    def BlueToothConnectPollingName(self, stuNr, Name):
        self.Name = None       
        deviceNumber = 0 
        recNameList = []
        endTime = time() + SystemCommandBlueToothConnectTime
        while None == self.Name and 8 > deviceNumber and time() < endTime:
            if 0 < self.BlueToothConnect(stuNr, deviceNumber):
                endTime = time() + SystemCommandBlueToothConnectTime
                RecName = ''
                while '' == RecName and time() < endTime:
                    RecName = self.BlueToothNameGet(deviceNumber)[0:8]
                recNameList.append(RecName)
                if Name == RecName:
                    self.Name = Name
                    self.DeviceNr = deviceNumber
                else:
                    deviceNumber += 1
                    self.BlueToothDisconnect(stuNr)
        if None == self.Name:
            self.Logger.Info("Available Names: " + str(recNameList))
            print("Available Names: " + str(recNameList))
            self.__exitError()

    def BlueToothEnergyModeNr(self, Sleep1TimeReset, Sleep1AdvertisementTimeReset, modeNr):
        S1B0 = Sleep1TimeReset & 0xFF
        S1B1 = (Sleep1TimeReset >> 8) & 0xFF
        S1B2 = (Sleep1TimeReset >> 16) & 0xFF
        S1B3 = (Sleep1TimeReset >> 24) & 0xFF
        A1B0 = Sleep1AdvertisementTimeReset & 0xFF
        A1B1 = (Sleep1AdvertisementTimeReset >> 8) & 0xFF
        if 2 == modeNr:
            self.Logger.Info("Setting Bluetooth Energy Mode 2")
            modeNr = SystemCommandBlueToothEnergyModeLowestWrite
        else:
            self.Logger.Info("Setting Bluetooth Energy Mode 1")
            modeNr = SystemCommandBlueToothEnergyModeReducedWrite
        Payload = [modeNr, self.DeviceNr, S1B0, S1B1, S1B2, S1B3, A1B0, A1B1]
        [timeReset, timeAdvertisement] = self.BlueToothEnergyMode(Payload) 
        self.Logger.Info("Energy Mode ResetTime/AdvertisementTime: " + str(timeReset) + "/" + str(timeAdvertisement))
        return [timeReset, timeAdvertisement]   
    
    def BlueToothEnergyMode(self, Payload):
        cmd = self.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
        message = self.CanMessage20(cmd, self.sender, self.receiver, Payload)
        EnergyModeReduced = self.WriteFrameWaitAckRetries(message, retries=2)["Payload"][2:]
        timeReset = EnergyModeReduced[:4]
        timeAdvertisement = EnergyModeReduced[4:]
        timeReset = fSleepTime(timeReset)
        timeAdvertisement = fSleepAdvertisement(timeAdvertisement)
        return [timeReset, timeAdvertisement]

    def Standby(self, receiver):
        sendData = ActiveState()
        sendData.asbyte = 0
        sendData.b.bSetState = 1
        sendData.b.u2NodeState = 2
        sendData.b.u3NetworkState = 2
        self.Logger.Info("Send Standby Command")
        index = self.cmdSend(receiver, MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ACTIVE_STATE, [sendData.asbyte])        
        self.Logger.Info("Received Payload " + self.payload2Hex(self.getReadMessageData(index)))

    def BlueToothRssi(self, subscriber):
        cmd = self.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
        payload = [SystemCommandBlueToothRssi, 0, 0, 0, 0, 0, 0, 0]
        message = self.CanMessage20(cmd, self.sender, subscriber, payload)
        ack = self.WriteFrameWaitAckRetries(message, retries=2)["Payload"][2]
        ack = to8bitSigned(ack)
        return ack

    def BlueToothAddress(self, subscriber):
        cmd = self.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_BLUETOOTH, 1, 0)
        payload = [SystemCommandBlueToothMacAddress, 0, 0, 0, 0, 0, 0, 0]
        message = self.CanMessage20(cmd, self.sender, subscriber, payload)
        ack = self.WriteFrameWaitAckRetries(message, retries=2)["Payload"][2:]
        ack = fBlueToothMacAddress(ack)
        return ack    

    def RoutingInformationCmd(self, receiver, subCmd, port):
        cmd = self.CanCmd(MY_TOOL_IT_BLOCK_SYSTEM, MY_TOOL_IT_SYSTEM_ROUTING, 1, 0)
        payload = [subCmd, port, 0, 0, 0, 0, 0, 0]
        message = self.CanMessage20(cmd, self.sender, receiver, payload)
        ack = self.WriteFrameWaitAckRetries(message, retries=5)["Payload"][2:]
        ack = self.AsciiStringWordLittleEndian(ack)
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
            dataSets = DataSetsNone
        elif 1 == count:
            dataSets = DataSets3
        elif 3 >= count:
            dataSets = DataSets1
        else:
            self.__exitError()  
        return dataSets  
