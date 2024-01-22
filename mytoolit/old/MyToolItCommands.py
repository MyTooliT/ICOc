from ctypes import BigEndianStructure, c_uint8, Union

from bidict import bidict

AdcMax = 0xFFFF


class ActiveStateFlags(BigEndianStructure):
    """Byte format for get/set state data

    bSetState: Set or get state data
        - 0: Get
        - 1: Set

    bReserved: Reserved bit

    u2NodeState: Current state of the node
        - 0: No Change/Init
        - 1: BootLoader
        - 2: Application
        - 3: Reserved

    bReserved2: Reserved bit

    u3NetworkState: Current state of network
        - 0: Failure (No acknowledgement will be sent;
                      Only power on resets this state)
        - 1: Error (No active communication)
        - 2: Turn Off/Standby
        - 3: Graceful degradation level 2
        - 4: Graceful degradation level 1
        - 5: Operating
        - 6: Startup
        - 7: No change

    See also: https://mytoolit.github.io/Documentation/#command:get-set-state
    """

    _fields_ = [
        ("bSetState", c_uint8, 1),
        ("bReserved", c_uint8, 1),
        ("u2NodeState", c_uint8, 2),
        ("bReserved1", c_uint8, 1),
        ("u3NetworkState", c_uint8, 3),
    ]


class ActiveState(Union):
    _fields_ = [("b", ActiveStateFlags), ("asbyte", c_uint8)]


class AtvcFormatFlags(BigEndianStructure):
    """Byte format for streaming data

    bStreaming: Streaming or single request (latest data)
        - 0: Single request
        - 1: Streaming

    bDataSetBytes: Number of bytes per data set
        - 0: 2 Bytes
        - 1: 3 Bytes

    bNumber1: Collect first part of streaming data (e.g. x-axis, temperature 1)
        - 0: Disable data collection
        - 1: Activate data collection

    bNumber2: Collect second part of streaming data (e.g. y-axis,
              temperature 2)
        - 0: Disable data collection
        - 1: Activate data collection

    bNumber3: Collect third part of streaming data (e.g. z-axis,
              temperature 3)
        - 0: Disable data collection
        - 1: Activate data collection

    u3DataSets: Number of collected data sets
        - 0: Stop (stream)
        - 1: 1 Data sets (x, y, z, x-y-z, x-y, x-z or y-z)
        - 2: 3 Data sets
        - 3: 6 Data sets
        - 4: 10 Data sets
        - 5: 15 Data sets
        - 6: 20 Data sets
        - 7: 30 Data sets (x, y, or z)
    """

    _fields_ = [
        ("bStreaming", c_uint8, 1),
        ("bDataSetBytes", c_uint8, 1),
        ("bNumber1", c_uint8, 1),
        ("bNumber2", c_uint8, 1),
        ("bNumber3", c_uint8, 1),
        ("u3DataSets", c_uint8, 3),
    ]


class AtvcFormat(Union):
    _fields_ = [("b", AtvcFormatFlags), ("asbyte", c_uint8)]


class CalibrationMeassurementFormatFlags(BigEndianStructure):
    _fields_ = [
        ("bSet", c_uint8, 1),
        ("u2Action", c_uint8, 2),
        ("bReset", c_uint8, 1),
        ("Reserved", c_uint8, 4),
    ]


class CalibrationMeassurement(Union):
    _fields_ = [("b", CalibrationMeassurementFormatFlags), ("asbyte", c_uint8)]


MyToolItBlock = bidict({
    "System": 0x00,
    "Streaming": 0x04,
    "StatisticalData": 0x08,
    "Configuration": 0x28,
    "EEPROM": 0x3D,
    "Product Data": 0x3E,
    "Test": 0x3F,
})

MyToolItSystem = bidict({
    "Verboten": 0x00,
    "Reset": 0x01,
    "Get/Set State": 0x02,
    "Mode": 0x03,
    "Alarm": 0x04,
    "Node Status": 0x05,
    "Error Status": 0x06,
    "StatusWord2": 0x07,
    "StatusWord3": 0x08,
    "Test": 0x09,
    "Log": 0x0A,
    "Bluetooth": 0x0B,
    "Routing": 0x0C,
})

SystemCommandBlueTooth = {
    "Reserved": 0,
    "Connect": 1,
    "GetNumberAvailableDevices": 2,
    "SetName1": 3,
    "SetName2": 4,
    "GetName1": 5,
    "GetName2": 6,
    "DeviceConnect": 7,
    "DeviceCheckConnected": 8,
    "Disconnect": 9,
    "SendCounter": 10,
    "ReceiveCounter": 11,
    "Rssi": 12,
    "EnergyModeReducedRead": 13,
    "EnergyModeReducedWrite": 14,
    "EnergyModeLowestRead": 15,
    "EnergyModeLowestWrite": 16,
    "MacAddress": 17,
    "DeviceConnectMacAddr": 18,
    "SelfAddressing": 255,
}

BluetoothTime = {
    "Connect": 20,
    "Out": 4 * 5,
    "Disconnect": 2,
    "GetDeviceNumber": 2,
    "DeviceConnect": 6,
    "TestConnect": 4,
}

SystemCommandRouting = {
    "Reserved": 0,
    "SendCounter": 1,
    "SendFailCounter": 2,
    "SendLowLevelByteCounter": 3,
    "ReceiveCounter": 4,
    "ReceiveFailCounter": 5,
    "ReceiveLowLevelByteCounter": 6,
}

MyToolItStreaming = bidict({
    "Data": 0x00,
    "Temperature": 0x01,
    "Voltage": 0x20,
    "Current": 0x40,
})

MyToolItStatData = bidict({
    "PocPof": 0x00,
    "OperatingTime": 0x01,
    "Uvc": 0x02,
    "Wdog": 0x03,
    "ProductionDate": 0x04,
    "MeasurementInterval": 0x40,
    "QuantityInterval": 0x41,
    "Energy": 0x80,
})

MyToolItConfiguration = bidict({
    "Get/Set ADC Configuration": 0x00,
    "Channel Configuration": 0x01,
    "Voltage": 0x20,
    "Current": 0x40,
    "CalibrationFactorK": 0x60,
    "CalibrationFactorD": 0x61,
    "Calibration Measurement": 0x62,
    "Alarm": 0x80,
    "Hmi": 0xC0,
})

MyToolItEeprom = bidict(
    {"Read": 0x00, "Write": 0x01, "Read Write Request Counter": 0x20}
)

MyToolItProductData = bidict({
    "GTIN": 0x00,
    "Hardware Version": 0x01,
    "Firmware Version": 0x02,
    "Release Name": 0x03,
    "Serial Number 1": 0x04,
    "Serial Number 2": 0x05,
    "Serial Number 3": 0x06,
    "Serial Number 4": 0x07,
    "Product Name 1": 0x08,
    "Product Name 2": 0x09,
    "Product Name 3": 0x0A,
    "Product Name 4": 0x0B,
    "Product Name 5": 0x0C,
    "Product Name 6": 0x0D,
    "Product Name 7": 0x0E,
    "Product Name 8": 0x0F,
    "Product Name 9": 0x10,
    "Product Name 10": 0x11,
    "Product Name 11": 0x12,
    "Product Name 12": 0x13,
    "Product Name 13": 0x14,
    "Product Name 14": 0x15,
    "Product Name 15": 0x16,
    "Product Name 16": 0x17,
    "OEM Free Use 1": 0x18,
    "OEM Free Use 2": 0x19,
    "OEM Free Use 3": 0x1A,
    "OEM Free Use 4": 0x1B,
    "OEM Free Use 5": 0x1C,
    "OEM Free Use 6": 0x1D,
    "OEM Free Use 7": 0x1E,
    "OEM Free Use 8": 0x1F,
})

MyToolItTest = bidict({
    "Signal": 0x01,
    "Pfeifferl": 0x69,
})

blocknumber_to_commands = {
    MyToolItBlock["System"]: MyToolItSystem,
    MyToolItBlock["Streaming"]: MyToolItStreaming,
    MyToolItBlock["StatisticalData"]: MyToolItStatData,
    MyToolItBlock["Configuration"]: MyToolItConfiguration,
    MyToolItBlock["EEPROM"]: MyToolItEeprom,
    MyToolItBlock["Product Data"]: MyToolItProductData,
    MyToolItBlock["Test"]: MyToolItTest,
}

CommandBlock = {
    MyToolItBlock["System"]: "Command Block System",
    MyToolItBlock["Streaming"]: "Command Block Streaming",
    MyToolItBlock["StatisticalData"]: "Command Block Statistical Data",
    MyToolItBlock["Configuration"]: "Command Block Configuration",
    MyToolItBlock["EEPROM"]: "Command Block EEPROM",
    MyToolItBlock["Product Data"]: "Command Block Product Data",
    MyToolItBlock["Test"]: "Command Block Test",
}

CommandBlockSystem = {
    MyToolItSystem["Verboten"]: "System Command Verboten",
    MyToolItSystem["Reset"]: "System Command Reset",
    MyToolItSystem["Get/Set State"]: "System Command Get/Set State",
    MyToolItSystem["Mode"]: "System Command Mode",
    MyToolItSystem["Alarm"]: "System Command Alarm",
    MyToolItSystem["Node Status"]: "System Command Status Word0",
    MyToolItSystem["Error Status"]: "System Command Status Word1",
    MyToolItSystem["StatusWord2"]: "System Command Status Word2",
    MyToolItSystem["StatusWord3"]: "System Command Status Word3",
    MyToolItSystem["Test"]: "System Command Test",
    MyToolItSystem["Log"]: "System Command Log",
    MyToolItSystem["Bluetooth"]: "System Command BlueTooth",
    MyToolItSystem["Routing"]: "System Command Routing",
}

CommandBlockStreaming = {
    MyToolItStreaming["Data"]: "Streaming Command Data",
    MyToolItStreaming["Temperature"]: "Streaming Command Temperature",
    MyToolItStreaming["Voltage"]: "Streaming Command Voltage",
    MyToolItStreaming["Current"]: "Streaming Command Current",
}

CommandBlockStatisticalData = {
    MyToolItStatData["PocPof"]: "Statistical Data Command PowerOn/Off Counter",
    MyToolItStatData[
        "OperatingTime"
    ]: "Statistical Data Command Operating Time",
    MyToolItStatData["Uvc"]: "Statistical Data Command Undervoltage Counter",
    MyToolItStatData["Wdog"]: "Statistical Data Command Watchdog Counter",
    MyToolItStatData[
        "ProductionDate"
    ]: "Statistical Data Command Production Date",
    MyToolItStatData[
        "MeasurementInterval"
    ]: "Statistical Data Command Measurement Interval",
    MyToolItStatData[
        "QuantityInterval"
    ]: "Statistical Data Command Quantity Interval",
    MyToolItStatData["Energy"]: "Statistical Data Command Energy",
}

CommandBlockConfiguration = {
    MyToolItConfiguration[
        "Get/Set ADC Configuration"
    ]: "Configuration Command Acceleration Configuration",
    MyToolItConfiguration[
        "Channel Configuration"
    ]: "Configuration Command Channel Configuration",
    MyToolItConfiguration[
        "Voltage"
    ]: "Configuration Command Voltage Configuration",
    MyToolItConfiguration[
        "Current"
    ]: "Configuration Command Current Configuration",
    MyToolItConfiguration[
        "CalibrationFactorK"
    ]: "Configuration Command Calibration Factor K",
    MyToolItConfiguration[
        "CalibrationFactorD"
    ]: "Configuration Command Calibration Factor D",
    MyToolItConfiguration[
        "Calibration Measurement"
    ]: "Configuration Command Calibration Measurement",
    MyToolItConfiguration["Alarm"]: "Configuration Command Alarm",
    MyToolItConfiguration["Hmi"]: "Configuration Command HMI",
}

CommandBlockEeprom = {
    MyToolItEeprom["Read"]: "EEPROM Command Read",
    MyToolItEeprom["Write"]: "EEPROM Command Write",
    MyToolItEeprom[
        "Read Write Request Counter"
    ]: "EEPROM Command Write Request Counter",
}

CommandBlockProductData = {
    MyToolItProductData["GTIN"]: "Product Data Command GTIN",
    MyToolItProductData[
        "Hardware Version"
    ]: "Product Data Command Hardware Version",
    MyToolItProductData[
        "Firmware Version"
    ]: "Product Data Command Firmware Version",
    MyToolItProductData["Release Name"]: "Product Data Command Release Name",
    MyToolItProductData[
        "Serial Number 1"
    ]: "Product Data Command Serial Number 1",
    MyToolItProductData[
        "Serial Number 2"
    ]: "Product Data Command Serial Number 2",
    MyToolItProductData[
        "Serial Number 3"
    ]: "Product Data Command Serial Number 3",
    MyToolItProductData[
        "Serial Number 4"
    ]: "Product Data Command Serial Number 4",
    MyToolItProductData["Product Name 1"]: "Product Data Command Name1",
    MyToolItProductData["Product Name 2"]: "Product Data Command Name2",
    MyToolItProductData["Product Name 3"]: "Product Data Command Name3",
    MyToolItProductData["Product Name 4"]: "Product Data Command Name4",
    MyToolItProductData["Product Name 5"]: "Product Data Command Name5",
    MyToolItProductData["Product Name 6"]: "Product Data Command Name6",
    MyToolItProductData["Product Name 7"]: "Product Data Command Name7",
    MyToolItProductData["Product Name 8"]: "Product Data Command Name8",
    MyToolItProductData["Product Name 9"]: "Product Data Command Name9",
    MyToolItProductData["Product Name 10"]: "Product Data Command Name10",
    MyToolItProductData["Product Name 11"]: "Product Data Command Name11",
    MyToolItProductData["Product Name 12"]: "Product Data Command Name12",
    MyToolItProductData["Product Name 13"]: "Product Data Command Name13",
    MyToolItProductData["Product Name 14"]: "Product Data Command Name14",
    MyToolItProductData["Product Name 15"]: "Product Data Command Name15",
    MyToolItProductData["Product Name 16"]: "Product Data Command Name16",
    MyToolItProductData["OEM Free Use 1"]: "Product Data Command Free Use 1",
    MyToolItProductData["OEM Free Use 2"]: "Product Data Command Free Use 2",
    MyToolItProductData["OEM Free Use 3"]: "Product Data Command Free Use 3",
    MyToolItProductData["OEM Free Use 4"]: "Product Data Command Free Use 4",
    MyToolItProductData["OEM Free Use 5"]: "Product Data Command Free Use 5",
    MyToolItProductData["OEM Free Use 6"]: "Product Data Command Free Use 6",
    MyToolItProductData["OEM Free Use 7"]: "Product Data Command Free Use 7",
    MyToolItProductData["OEM Free Use 8"]: "Product Data Command Free Use 8",
}

CommandBlockTest = {
    MyToolItTest["Signal"]: "Test Command Signal",
    MyToolItTest["Pfeifferl"]: "Test Command Pfeifferl",
}

EepromPage = {
    "SystemConfiguration0": 0,
    "Product Data": 4,
    "Statistics": 5,
    "Calibration0": 8,
}

CalibMeassurementActionNr = {
    "None": 0,
    "Activate": 1,
    "Deactivate": 2,
    "Measure": 3,
}

CalibMeassurementActionName = {
    0: "Calibration Measurement Action - None/Reset",
    1: "Calibration Measurement Action - Activate",
    2: "Calibration Measurement Action - Deactivate",
    3: "Calibration Measurement Action - Measure",
}

CalibMeassurementTypeNr = {
    "Acc": 0,
    "Temp": 1,
    "Voltage": 32,
    "Vss": 96,
    "Avdd": 97,
    "OpvOutput": 99,
}

CalibMeassurementTypeName = {
    CalibMeassurementTypeNr[
        "Acc"
    ]: "Calibration Measurement Type - Acceleration",
    CalibMeassurementTypeNr[
        "Temp"
    ]: "Calibration Measurement Type - Temperature",
    CalibMeassurementTypeNr[
        "Voltage"
    ]: "Calibration Measurement Type - Voltage",
    CalibMeassurementTypeNr[
        "Vss"
    ]: "Calibration Measurement Type - VSS(Ground)",
    CalibMeassurementTypeNr[
        "Avdd"
    ]: "Calibration Measurement Type - AVDD(Analog Supply)",
    CalibMeassurementTypeNr[
        "OpvOutput"
    ]: "Calibration Measurement Type - OPV Output",
}

AdcAcquisitionTime = bidict({
    1: 0,
    2: 1,
    3: 2,
    4: 3,
    8: 4,
    16: 5,
    32: 6,
    64: 7,
    128: 8,
    256: 9,
})

AdcAcquisitionTimeName = {
    AdcAcquisitionTime[1]: "ADC Acquisition Time - 1 Cycle",
    AdcAcquisitionTime[2]: "ADC Acquisition Time - 2 Cycles",
    AdcAcquisitionTime[3]: "ADC Acquisition Time - 3 Cycles",
    AdcAcquisitionTime[4]: "ADC Acquisition Time - 4 Cycles",
    AdcAcquisitionTime[8]: "ADC Acquisition Time - 8 Cycles",
    AdcAcquisitionTime[16]: "ADC Acquisition Time - 16 Cycles",
    AdcAcquisitionTime[32]: "ADC Acquisition Time - 32 Cycles",
    AdcAcquisitionTime[64]: "ADC Acquisition Time - 64 Cycles",
    AdcAcquisitionTime[128]: "ADC Acquisition Time - 128 Cycles",
    AdcAcquisitionTime[256]: "ADC Acquisition Time - 256 Cycles",
}

AdcOverSamplingRate = bidict({
    1: 0,
    2: 1,
    4: 2,
    8: 3,
    16: 4,
    32: 5,
    64: 6,
    128: 7,
    256: 8,
    512: 9,
    1024: 10,
    2048: 11,
    4096: 12,
})

AdcOverSamplingRateName = {
    AdcOverSamplingRate[1]: "ADC Single Sampling",
    AdcOverSamplingRate[2]: "ADC Over Sampling Rate - 2",
    AdcOverSamplingRate[4]: "ADC Over Sampling Rate - 4",
    AdcOverSamplingRate[8]: "ADC Over Sampling Rate - 8",
    AdcOverSamplingRate[16]: "ADC Over Sampling Rate - 16",
    AdcOverSamplingRate[32]: "ADC Over Sampling Rate - 32",
    AdcOverSamplingRate[64]: "ADC Over Sampling Rate - 64",
    AdcOverSamplingRate[128]: "ADC Over Sampling Rate - 128",
    AdcOverSamplingRate[256]: "ADC Over Sampling Rate - 256",
    AdcOverSamplingRate[512]: "ADC Over Sampling Rate - 512",
    AdcOverSamplingRate[1024]: "ADC Over Sampling Rate - 1024",
    AdcOverSamplingRate[2048]: "ADC Over Sampling Rate - 2048",
    AdcOverSamplingRate[4096]: "ADC Over Sampling Rate - 4096",
}

AdcReference = {
    "1V25": 25,
    "Vfs1V65": 33,
    "Vfs1V8": 36,
    "Vfs2V1": 42,
    "Vfs2V2": 44,
    "2V5": 50,
    "Vfs2V7": 54,
    "VDD": 66,
    "5V": 100,
    "6V6": 132,
}

VRefName = {
    25: "ADC Reference 1V25",
    33: "ADC Reference 1V65",
    36: "ADC Reference 1V8",
    42: "ADC Reference 2V1",
    44: "ADC Reference 2V2",
    50: "ADC Reference 2V5",
    54: "ADC Reference 2V7",
    66: "ADC Reference VDD(3V3)",
    100: "ADC Reference 5V",
    132: "ADC Reference 6V6",
}

AdcVRefValuemV = {
    AdcReference["1V25"]: 1250,
    AdcReference["Vfs1V65"]: 1650,
    AdcReference["Vfs1V8"]: 1800,
    AdcReference["Vfs2V1"]: 2100,
    AdcReference["Vfs2V2"]: 2200,
    AdcReference["2V5"]: 2500,
    AdcReference["Vfs2V7"]: 2700,
    AdcReference["VDD"]: 3300,
    AdcReference["5V"]: 5000,
    AdcReference["6V6"]: 6000,
}

DataSets = bidict({
    0: 0,
    1: 1,
    3: 2,
    6: 3,
    10: 4,
    15: 5,
    20: 6,
    30: 7,
})

TestCommandSignal = {
    "Line": 1,
    "Ramp": 2,
}

Prescaler = {
    "Min": 2,
    "Max": 127,
}

NodeState = bidict({
    "No Change": 0,
    "Bootloader": 1,
    "Application": 2,
    "Reserved": 3,
})

NetworkState = bidict({
    "Failure": 0,
    "Error": 1,
    "Standby": 2,
    "Graceful Degradation 2": 3,
    "Graceful Degradation 1": 4,
    "Operating": 5,
    "Startup": 6,
    "No Change": 7,
})

CalibrationFactor = {
    "Acceleration": 0,
    "Temperature": 1,
    "Voltage": 32,
}

BlueToothDeviceNr = {
    "Self": 255,
}


def byte_list_to_int(m):
    return int.from_bytes(m, "little")


def int_to_byte_list(iValue, iLength, byte_order="little"):
    return list(iValue.to_bytes(iLength, byte_order))


def calcSamplingRate(prescaler, acquisitionTime, OverSamplingRate):
    acquTime = AdcAcquisitionTime.inverse[acquisitionTime]
    samplingRate = AdcOverSamplingRate.inverse[OverSamplingRate]
    return int(
        38400000 / ((prescaler + 1) * (acquTime + 13) * samplingRate) + 0.5
    )


def payload2Hex(payload):
    payloadHex = "[{}]".format(", ".join(hex(x) for x in payload))
    return payloadHex


def AsciiStringWordBigEndian(ByteArray):
    value = 0
    for byte in range(len(ByteArray)):
        value += ByteArray[byte] << (8 * byte)
    return value


def AsciiStringWordLittleEndian(ByteArray):
    value = 0
    for byte in range(len(ByteArray)):
        value += ByteArray[byte] << (8 * (len(ByteArray) - byte - 1))
    return value


def sArray2String(Name):
    for i in range(0, len(Name)):
        Name[i] = chr(Name[i])
        i += 1
    Name = "".join(Name)
    for character in range(0, ord(" ")):
        Name = Name[0:8].replace(chr(character), "")
    for character in range(128, 0xFF):
        Name = Name[0:8].replace(chr(character), "")
    return Name


def int_to_mac_address(iAddr):
    return ":".join(
        f"{byte:02x}" for byte in int_to_byte_list(iAddr, 6, "big")
    )
