import ctypes
c_uint8 = ctypes.c_uint8


class ActiveStateFlags(ctypes.BigEndianStructure):
    _fields_ = [
            ("bSetState", c_uint8, 1),
            ("bReserved", c_uint8, 1),
            ("u2NodeState", c_uint8, 2),
            ("bReserved1", c_uint8, 1),
            ("u3NetworkState", c_uint8, 3),
        ]


class ActiveState(ctypes.Union):
    _fields_ = [("b", ActiveStateFlags),
                ("asbyte", c_uint8)]
    

class AtvcFormatFlags(ctypes.BigEndianStructure):
    _fields_ = [
            ("bStreaming", c_uint8, 1),
            ("bDataSetBytes", c_uint8, 1),
            ("bNumber1", c_uint8, 1),
            ("bNumber2", c_uint8, 1),
            ("bNumber3", c_uint8, 1),
            ("u3DataSets", c_uint8, 3),
        ]


class AtvcFormat(ctypes.Union):
    _fields_ = [("b", AtvcFormatFlags),
                ("asbyte", c_uint8)]


class CalibrationMeassurementFormatFlags(ctypes.BigEndianStructure):
    _fields_ = [
            ("bSet", c_uint8, 1),
            ("u2Action", c_uint8, 2),
            ("bReset", c_uint8, 1),
            ("Reserved", c_uint8, 4),
            ]

 
class CalibrationMeassurement(ctypes.Union):
    _fields_ = [("b", CalibrationMeassurementFormatFlags),
                ("asbyte", c_uint8)]   

    
MyToolItBlock = {
    "System" : 0x00,
    "Streaming" : 0x04,
    "StatisticalData" : 0x08,
    "Configuration" : 0x28,
    "ProductData" : 0x3E,
    "Test" : 0x3F,
}

MyToolItSystem = {
    "Verboten" : 0x00,
    "Reset" : 0x01,
    "ActiveState" : 0x02,
    "Mode" : 0x03,
    "Alarm" : 0x04,
    "StatusWord0" : 0x05,
    "StatusWord1" : 0x06,
    "StatusWord2" : 0x07,
    "StatusWord3" : 0x08,
    "Test" : 0x09,
    "Log" : 0x0A,
    "Bluetooth" : 0x0B,
    "Routing" : 0x0C,
}

SystemCommandBlueTooth = {
    "Reserved" : 0,
    "Connect" : 1,
    "GetNumberAvailableDevices" : 2,
    "SetName1" : 3,
    "SetName2" : 4,
    "GetName1" : 5,
    "GetName2" : 6,
    "DeviceConnect" : 7,
    "DeviceCheckConnected" : 8,
    "Disconnect" : 9,
    "SendCounter" : 10,
    "ReceiveCounter" : 11,
    "Rssi" : 12,
    "EnergyModeReducedRead" : 13,
    "EnergyModeReducedWrite" : 14,
    "EnergyModeLowestRead" : 15,
    "EnergyModeLowestWrite" : 16,
    "MacAddress" : 17,
}

BluetoothTime = {
    "Connect" : 20,
    "Out" : (4 * 5),
    "Disconnect" : 1,
    "GetDeviceNumber" : 2,
    "DeviceConnect" : 5,
}

SystemCommandRouting = {
    "Reserved" : 0,
    "SendCounter" : 1,
    "SendFailCounter" : 2,
    "SendLowLevelByteCounter" : 3,
    "ReceiveCounter" : 4,
    "ReceiveFailCounter" : 5,
    "ReceiveLowLevelByteCounter" : 6,
}

MyToolItStreaming = {
    "Acceleration" : 0x00,
    "Temperature" : 0x01,
    "Voltage" : 0x20,
    "Current" : 0x40,
}

MyToolItStatData = {
    "PocPof" : 0x00,
    "OperatingTime" : 0x01,
    "Uvc" : 0x02,
    "Wdog" : 0x03,
    "MeasurementInterval" : 0x40,
    "QuantityInterval" : 0x41,
    "Energy" : 0x80,
}

MyToolItConfiguration = {
    "Acceleration" : 0x00,
    "Temperature" : 0x01,
    "Voltage" : 0x20,
    "Current" : 0x40,
    "CalibrationFactorK" : 0x60,
    "CalibrationFactorD" : 0x61,
    "CalibrateMeasurement" : 0x62,
    "Alarm" : 0x80,
    "Hmi" : 0xC0
}

MyToolItProductData = {
    "GTIN" : 0x00,
    "HardwareRevision" : 0x01,
    "FirmwareVersion" : 0x02,
    "ReleaseName" : 0x03,
    "SerialNumber1" : 0x04,
    "SerialNumber2" : 0x05,
    "SerialNumber3" : 0x06,
    "SerialNumber4" : 0x07,
    "Name1" : 0x08,
    "Name2" : 0x09,
    "Name3" : 0x0A,
    "Name4" : 0x0B,
    "Name5" : 0x0C,
    "Name6" : 0x0D,
    "Name7" : 0x0E,
    "Name8" : 0x0F,
    "Name9" : 0x10,
    "Name10" : 0x11,
    "Name11" : 0x12,
    "Name12" : 0x13,
    "Name13" : 0x14,
    "Name14" : 0x15,
    "Name15" : 0x16,
    "Name16" : 0x17,
    "OemFreeUse1" : 0x18,
    "OemFreeUse2" : 0x19,
    "OemFreeUse3" : 0x1A,
    "OemFreeUse4" : 0x1B,
    "OemFreeUse5" : 0x1C,
    "OemFreeUse6" : 0x1D,
    "OemFreeUse7" : 0x1E,
    "OemFreeUse8" : 0x1F,
}

MyToolItTest = {
"Signal" : 0x01,
}

CommandBlock = {
    MyToolItBlock["System"] : "Command Block System",
    MyToolItBlock["Streaming"] : "Command Block Streaming",
    MyToolItBlock["StatisticalData"] : "Command Block Statistical Data",
    MyToolItBlock["Configuration"] : "Command Block Configuration",
    MyToolItBlock["ProductData"] :"Command Block Product Data",
    MyToolItBlock["Test"] : "Command Block Test",
}

CommandBlockSystem = {
    MyToolItSystem["Verboten"]      : "System Command Verboten",
    MyToolItSystem["Reset"]         : "System Command Reset",
    MyToolItSystem["ActiveState"]   : "System Command Active State",
    MyToolItSystem["Mode"]          : "System Command Mode",
    MyToolItSystem["Alarm"]         : "System Command Alarm",
    MyToolItSystem["StatusWord0"]   : "System Command Status Word0",
    MyToolItSystem["StatusWord1"]   : "System Command Status Word1",
    MyToolItSystem["StatusWord2"]   : "System Command Status Word2",
    MyToolItSystem["StatusWord3"]   : "System Command Status Word3",
    MyToolItSystem["Test"]          : "System Command Test",
    MyToolItSystem["Log"]           : "System Command Log",
    MyToolItSystem["Bluetooth"]     : "System Command BlueTooth",
    MyToolItSystem["Routing"]       : "System Command Routing",
}

CommandBlockStreaming = {
    MyToolItStreaming["Acceleration"] : "Streaming Command Acceleration",
    MyToolItStreaming["Temperature"] : "Streaming Command Temperature",
    MyToolItStreaming["Voltage"] : "Streaming Command Voltage",
    MyToolItStreaming["Current"] : "Streaming Command Current",
}

CommandBlockStatisticalData = {
    MyToolItStatData["PocPof"] : "Statistical Data Command PowerOn/Off Counter",
    MyToolItStatData["OperatingTime"] : "Statistical Data Command Operating Time",
    MyToolItStatData["Uvc"] : "Statistical Data Command Undervoltage Counter",
    MyToolItStatData["Wdog"] : "Statistical Data Command Watchdog Counter",
    MyToolItStatData["MeasurementInterval"] : "Statistical Data Command Measurement Interval",
    MyToolItStatData["QuantityInterval"] : "Statistical Data Command Quantity Interval",
    MyToolItStatData["Energy"] : "Statistical Data Command Energy",
}

CommandBlockConfiguration = {
    MyToolItConfiguration["Acceleration"] : "Configuration Command Acceleration Configuration",
    MyToolItConfiguration["Temperature"] : "Configuration Command Temperature Configuration",
    MyToolItConfiguration["Voltage"] : "Configuration Command Voltage Configuration",
    MyToolItConfiguration["Current"] : "Configuration Command Current Configuration",
    MyToolItConfiguration["CalibrationFactorK"] : "Configuration Command Calibration Factor K",
    MyToolItConfiguration["CalibrationFactorD"] : "Configuration Command Calibration Factor D",
    MyToolItConfiguration["CalibrateMeasurement"] : "Configuration Command Calibration Measurement",
    MyToolItConfiguration["Alarm"] : "Configuration Command Alarm",
    MyToolItConfiguration["Hmi"] : "Configuration Command HMI",
}

CommandBlockProductData = {
    MyToolItProductData["GTIN"] : "Product Data Command GTIN",
    MyToolItProductData["HardwareRevision"] : "Product Data Command Hardware Revision",
    MyToolItProductData["FirmwareVersion"] : "Product Data Command Firmware Version",
    MyToolItProductData["ReleaseName"] : "Product Data Command Release Name",
    MyToolItProductData["SerialNumber1"] : "Product Data Command Serial Number 1",
    MyToolItProductData["SerialNumber2"] : "Product Data Command Serial Number 2",
    MyToolItProductData["SerialNumber3"] : "Product Data Command Serial Number 3",
    MyToolItProductData["SerialNumber4"] : "Product Data Command Serial Number 4",
    MyToolItProductData["Name1"] : "Product Data Command Name1",
    MyToolItProductData["Name2"] : "Product Data Command Name2",
    MyToolItProductData["Name3"]: "Product Data Command Name3",
    MyToolItProductData["Name4"]: "Product Data Command Name4",
    MyToolItProductData["Name5"]: "Product Data Command Name5",
    MyToolItProductData["Name6"]: "Product Data Command Name6",
    MyToolItProductData["Name7"]: "Product Data Command Name7",
    MyToolItProductData["Name8"]: "Product Data Command Name8",
    MyToolItProductData["Name9"]: "Product Data Command Name9",
    MyToolItProductData["Name10"] : "Product Data Command Name10",
    MyToolItProductData["Name11"] : "Product Data Command Name11",
    MyToolItProductData["Name12"] : "Product Data Command Name12",
    MyToolItProductData["Name13"] : "Product Data Command Name13",
    MyToolItProductData["Name14"] : "Product Data Command Name14",
    MyToolItProductData["Name15"] : "Product Data Command Name15",
    MyToolItProductData["Name16"] : "Product Data Command Name16",
    MyToolItProductData["OemFreeUse1"] : "Product Data Command Free Use 1",
    MyToolItProductData["OemFreeUse2"] : "Product Data Command Free Use 2",
    MyToolItProductData["OemFreeUse3"] : "Product Data Command Free Use 3",
    MyToolItProductData["OemFreeUse4"] : "Product Data Command Free Use 4",
    MyToolItProductData["OemFreeUse5"] : "Product Data Command Free Use 5",
    MyToolItProductData["OemFreeUse6"] : "Product Data Command Free Use 6",
    MyToolItProductData["OemFreeUse7"] : "Product Data Command Free Use 7",
    MyToolItProductData["OemFreeUse8"] : "Product Data Command Free Use 8",
}

CommandBlockTest = {
    MyToolItTest["Signal"] : "Test Command Signal",
}

CalibMeassurementActionNr = {
    "None" : 0,
    "Inject" : 1,
    "Eject" : 2,
    "Measure" : 3,
}

CalibMeassurementActionName = {
    0 : "Calibration Measurement Action - None/Reset",
    1 : "Calibration Measurement Action - Inject",
    2 : "Calibration Measurement Action - Eject",
    3 : "Calibration Measurement Action - Measure",
}

CalibMeassurementTypeNr = {
    "Acc" : 0,
    "Temp" : 1,
    "Voltage" : 32,
    "Vss" : 96,
    "Avdd" : 97,
    "RegulatedInternalPower" : 98,
    "OpvOutput" : 99,
}

CalibMeassurementTypeName = {
    CalibMeassurementTypeNr["Acc"] : "Calibration Measurement Type - Acceleration",
    CalibMeassurementTypeNr["Temp"] : "Calibration Measurement Type - Temperature",
    CalibMeassurementTypeNr["Voltage"] : "Calibration Measurement Type - Voltage",
    CalibMeassurementTypeNr["Vss"] : "Calibration Measurement Type - VSS(Ground)",
    CalibMeassurementTypeNr["Avdd"] :"Calibration Measurement Type - AVDD(Analog Supply)",
    CalibMeassurementTypeNr["RegulatedInternalPower"] : "Calibration Measurement Type - Regulated Internal Power",
    CalibMeassurementTypeNr["OpvOutput"]  : "Calibration Measurement Type - OPV Output",
}

AdcAcquisitionTime = {
    1 : 0,
    2 : 1,
    3 : 2,
    4 : 3,
    8 : 4,
    16 : 5,
    32 : 6,
    64 : 7,
    128 : 8,
    256 : 9,
}

AdcAcquisitionTimeReverse = {
    0 : 1,
    1 : 2,
    2 : 3,
    3 : 4,
    4 : 8,
    5 : 16,
    6 : 32,
    7 : 64,
    8 : 128,
    9 : 256,
}

AdcAcquisitionTimeName = {
    AdcAcquisitionTime[1] : "ADC Acquisition Time - 1 Cycle",
    AdcAcquisitionTime[2] : "ADC Acquisition Time - 2 Cycles",
    AdcAcquisitionTime[3] : "ADC Acquisition Time - 3 Cycles",
    AdcAcquisitionTime[4] : "ADC Acquisition Time - 4 Cycles",
    AdcAcquisitionTime[8] : "ADC Acquisition Time - 8 Cycles",
    AdcAcquisitionTime[16] : "ADC Acquisition Time - 16 Cycles",
    AdcAcquisitionTime[32] : "ADC Acquisition Time - 32 Cycles",
    AdcAcquisitionTime[64] : "ADC Acquisition Time - 64 Cycles",
    AdcAcquisitionTime[128] : "ADC Acquisition Time - 128 Cycles",
    AdcAcquisitionTime[256] : "ADC Acquisition Time - 256 Cycles"
}

AdcOverSamplingRate = {
    1 : 1,
    2 : 1,
    4 : 2,
    8 : 3,
    16 : 4,
    32 : 5,
    64 : 6,
    128 : 7,
    256 : 8,
    512 : 9,
    1024 : 10,
    2048 : 11,
    4096 : 12,
}

AdcOverSamplingRateReverse = {
    0 : 1,
    1 : 2,
    2 : 4,
    3 : 8,
    4 : 16,
    5 : 32,
    6 : 64,
    7 : 128,
    8 : 256,
    9 : 512,
    10 : 1024,
    11 : 2048,
    12 : 4096,
}

AdcOverSamplingRateName = {
    AdcOverSamplingRate[1] : "ADC Single Sampling",
    AdcOverSamplingRate[2] : "ADC Over Sampling Rate - 2",
    AdcOverSamplingRate[4] : "ADC Over Sampling Rate - 4",
    AdcOverSamplingRate[8] : "ADC Over Sampling Rate - 8",
    AdcOverSamplingRate[16] : "ADC Over Sampling Rate - 16",
    AdcOverSamplingRate[32] : "ADC Over Sampling Rate - 32",
    AdcOverSamplingRate[64] : "ADC Over Sampling Rate - 64",
    AdcOverSamplingRate[128] : "ADC Over Sampling Rate - 128",
    AdcOverSamplingRate[256] : "ADC Over Sampling Rate - 256",
    AdcOverSamplingRate[512] : "ADC Over Sampling Rate - 512",
    AdcOverSamplingRate[1024] : "ADC Over Sampling Rate - 1024",
    AdcOverSamplingRate[2048] : "ADC Over Sampling Rate - 2048",
    AdcOverSamplingRate[4096] : "ADC Over Sampling Rate - 4096"
}

AdcReference = {     
    "1V25" : 25,
    "Vfs1V65" : 33,
    "Vfs1V8" : 36,
    "Vfs2V1" : 42,
    "Vfs2V2" : 44,
    "2V5" : 50,
    "Vfs2V7" : 54,
    "VDD" : 66,
    "5V" : 100,
    "6V6" : 132,
}
 
VRefName = {
    25 : "ADC Reference 1V25",
    33   : "ADC Reference 1V65",
    36 : "ADC Reference 1V8",
    42 : "ADC Reference 2V1",
    44 : "ADC Reference 2V2",
    50 : "ADC Reference 2V5",
    54 : "ADC Reference 2V7",
    66 : "ADC Reference VDD(3V3)",
    100 : "ADC Reference 5V",
    132 : "ADC Reference 6V6",
}

AdcVRefValuemV = {
    AdcReference["1V25"] : 1250,
    AdcReference["Vfs1V65"] : 1650,
    AdcReference["Vfs1V8"] : 1800,
    AdcReference["Vfs2V1"] : 2100,
    AdcReference["Vfs2V2"] : 2200,
    AdcReference["2V5"] : 2500,
    AdcReference["Vfs2V7"] : 2700,
    AdcReference["VDD"] : 3300,
    AdcReference["5V"] : 5000,
    AdcReference["6V6"] : 6000
}

DataSets = {
    0 : 0,
    1 : 1,
    3 : 2,
    6 : 3,
    10 : 4,
    15 : 5,
    20 : 6,
    30 : 7,
}

TestCommandSignal = {
    "Line" : 1,
    "Ramp" : 2,
}

Prescaler = {
    "Min" : 2,
    "Max" : 127,
}

Node = {
    "NoChange" : 0,
    "Bootloader" : 1,
    "Application" : 2,
    "Reserved" : 3,
}

NetworkState = {
    "Failure" : 0,
    "Error"  : 1,
    "Standby" : 2,
    "GracefulDegration2" : 3,
    "GracefulDegration1" : 4,
    "Operating" : 5,
    "Startup" : 6,
    "NoChange"  : 7,
}

NetworkStateName = {
    0 : "Network State Failure",
    1 : "Network State Error",
    2 : "Network State Standby",
    3 : "Network State GracefulDegration2",
    4 : "Network State GracefulDegration1",
    5 : "Network State Operating",
    6 : "Network State Startup",
    7 : "Network State NoChange",
}

CalibrationFactor = {
    "Acceleration" : 0,
    "Temperature" : 1,
    "Voltage" : 32,
}


def to8bitSigned(num):
    mask7 = 128  # Check 8th bit ~ 2^8
    mask2s = 127  # Keep first 7 bits
    if (mask7 & num == 128):  # Check Sign (8th bit)
        num = -((~int(num) + 1) & mask2s)  # 2's complement
    return num


def messageWordGet(m):
    Word = ((0xFF & m[3]) << 24) | ((0xFF & m[2]) << 16) | ((0xFF & m[1]) << 8) | (0xFF & m[0])
    return Word


def messageValueGet(m):
    Acc = ((0xFF & m[1]) << 8) | (0xFF & m[0])
    return Acc

    
def calcSamplingRate(prescaler, acquisitionTime, OverSamplingRate):
    acquTime = AdcAcquisitionTimeReverse[acquisitionTime]
    samplingRate = AdcOverSamplingRateReverse[OverSamplingRate]
    return 38400000 / ((prescaler + 1) * (acquTime + 13) * samplingRate)


def payload2Hex(payload):
    payloadHex = '[{}]'.format(', '.join(hex(x) for x in payload))
    return payloadHex


def AsciiStringWordBigEndian(ByteArray):
    value = 0
    for byte in range(len(ByteArray)):
        value += (ByteArray[byte] << (8 * byte))
    return value


def AsciiStringWordLittleEndian(ByteArray):
    value = 0
    for byte in range(len(ByteArray)):
        value += (ByteArray[byte] << (8 * (len(ByteArray) - byte - 1)))
    return value
