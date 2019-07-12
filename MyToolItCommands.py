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
    

MY_TOOL_IT_BLOCK_SYSTEM = 0x00   
MY_TOOL_IT_BLOCK_STREAMING = 0x04
MY_TOOL_IT_BLOCK_STATISTICAL_DATA = 0x08
MY_TOOL_IT_BLOCK_CONFIGURATION = 0x28
MY_TOOL_IT_BLOCK_PRODUCT_DATA = 0x3E 
MY_TOOL_IT_BLOCK_TEST = 0x3F

MY_TOOL_IT_SYSTEM_VERBOTEN = 0x00
MY_TOOL_IT_SYSTEM_RESET = 0x01
MY_TOOL_IT_SYSTEM_ACTIVE_STATE = 0x02
MY_TOOL_IT_SYSTEM_MODE = 0x03
MY_TOOL_IT_SYSTEM_ALARM = 0x04
MY_TOOL_IT_SYSTEM_STATUS_WORD0 = 0x05
MY_TOOL_IT_SYSTEM_STATUS_WORD1 = 0x06
MY_TOOL_IT_SYSTEM_STATUS_WORD2 = 0x07
MY_TOOL_IT_SYSTEM_STATUS_WORD3 = 0x08
MY_TOOL_IT_SYSTEM_TEST = 0x09
MY_TOOL_IT_SYSTEM_LOG = 0x0A
MY_TOOL_IT_SYSTEM_BLUETOOTH = 0x0B
MY_TOOL_IT_SYSTEM_ROUTING = 0x0C
MY_TOOL_IT_STREAMING_ACCELERATION = 0x00
MY_TOOL_IT_STREAMING_TEMPERATURE = 0x01
MY_TOOL_IT_STREAMING_VOLTAGE = 0x20
MY_TOOL_IT_STREAMING_CURRENT = 0x40
MY_TOOL_IT_STATISTICAL_DATA_POC_POF = 0x00
MY_TOOL_IT_STATISTICAL_DATA_OPERATING_TIME = 0x01
MY_TOOL_IT_STATISTICAL_DATA_UVC = 0x02
MY_TOOL_IT_STATISTICAL_DATA_MEASUREMENT_INTERVAL = 0x40
MY_TOOL_IT_STATISTICAL_DATA_QUANTITY_INTERVAL = 0x41
MY_TOOL_IT_STATISTICAL_DATA_ENERGY = 0x80
MY_TOOL_IT_CONFIGURATION_ACCELERATION_CONFIGURATION = 0x00
MY_TOOL_IT_CONFIGURATION_TEMPERATURE_CONFIGURATION = 0x01
MY_TOOL_IT_CONFIGURATION_VOLTAGE_CONFIGURATION = 0x20
MY_TOOL_IT_CONFIGURATION_CURRENT_CONFIGURATION = 0x40
MY_TOOL_IT_CONFIGURATION_CALIBRATION_FACTOR_K = 0x60
MY_TOOL_IT_CONFIGURATION_CALIBRATION_FACTOR_D = 0x61
MY_TOOL_IT_CONFIGURATION_CALIBRATE_MEASSUREMENT = 0x62
MY_TOOL_IT_CONFIGURATION_ALARM = 0x80
MY_TOOL_IT_CONFIGURATION_CONFIGURATION_HMI = 0xC0
MY_TOOL_IT_PRODUCT_DATA_GTIN = 0x00
MY_TOOL_IT_PRODUCT_DATA_HARDWARE_REVISION = 0x01
MY_TOOL_IT_PRODUCT_DATA_FIRMWARE_VERSION = 0x02
MY_TOOL_IT_PRODUCT_DATA_RELEASE_NAME = 0x03
MY_TOOL_IT_PRODUCT_DATA_SERIAL_NUMBER1 = 0x04
MY_TOOL_IT_PRODUCT_DATA_SERIAL_NUMBER2 = 0x05
MY_TOOL_IT_PRODUCT_DATA_SERIAL_NUMBER3 = 0x06
MY_TOOL_IT_PRODUCT_DATA_SERIAL_NUMBER4 = 0x07
MY_TOOL_IT_PRODUCT_DATA_NAME1 = 0x08
MY_TOOL_IT_PRODUCT_DATA_NAME2 = 0x09
MY_TOOL_IT_PRODUCT_DATA_NAME3 = 0x0A
MY_TOOL_IT_PRODUCT_DATA_NAME4 = 0x0B
MY_TOOL_IT_PRODUCT_DATA_NAME5 = 0x0C
MY_TOOL_IT_PRODUCT_DATA_NAME6 = 0x0D
MY_TOOL_IT_PRODUCT_DATA_NAME7 = 0x0E
MY_TOOL_IT_PRODUCT_DATA_NAME8 = 0x0F
MY_TOOL_IT_PRODUCT_DATA_NAME9 = 0x10
MY_TOOL_IT_PRODUCT_DATA_NAME10 = 0x11
MY_TOOL_IT_PRODUCT_DATA_NAME11 = 0x12
MY_TOOL_IT_PRODUCT_DATA_NAME12 = 0x13
MY_TOOL_IT_PRODUCT_DATA_NAME13 = 0x14
MY_TOOL_IT_PRODUCT_DATA_NAME14 = 0x15
MY_TOOL_IT_PRODUCT_DATA_NAME15 = 0x16
MY_TOOL_IT_PRODUCT_DATA_NAME16 = 0x17
MY_TOOL_IT_PRODUCT_DATA_OEM_FREE_USE1 = 0x18
MY_TOOL_IT_PRODUCT_DATA_OEM_FREE_USE2 = 0x19
MY_TOOL_IT_PRODUCT_DATA_OEM_FREE_USE3 = 0x1A
MY_TOOL_IT_PRODUCT_DATA_OEM_FREE_USE4 = 0x1B
MY_TOOL_IT_PRODUCT_DATA_OEM_FREE_USE5 = 0x1C
MY_TOOL_IT_PRODUCT_DATA_OEM_FREE_USE6 = 0x1D
MY_TOOL_IT_PRODUCT_DATA_OEM_FREE_USE7 = 0x1E
MY_TOOL_IT_PRODUCT_DATA_OEM_FREE_USE8 = 0x1F
MY_TOOL_IT_TEST_SIGNAL = 0x01

CommandBlock = {
    MY_TOOL_IT_BLOCK_SYSTEM : "Command Block System",
    MY_TOOL_IT_BLOCK_STREAMING : "Command Block Streaming",
    MY_TOOL_IT_BLOCK_STATISTICAL_DATA : "Command Block Statistical Data",
    MY_TOOL_IT_BLOCK_CONFIGURATION : "Command Block Configuration",
    MY_TOOL_IT_BLOCK_PRODUCT_DATA :"Command Block Product Data",
    MY_TOOL_IT_BLOCK_TEST : "Command Block Test",
    }

CommandBlockSystem = {
    MY_TOOL_IT_SYSTEM_VERBOTEN : "System Command Verboten",
    MY_TOOL_IT_SYSTEM_RESET : "System Command Reset",
    MY_TOOL_IT_SYSTEM_ACTIVE_STATE : "System Command Active State",
    MY_TOOL_IT_SYSTEM_MODE : "System Command Mode",
    MY_TOOL_IT_SYSTEM_ALARM : "System Command Alarm",
    MY_TOOL_IT_SYSTEM_STATUS_WORD0 : "System Command Status Word0",
    MY_TOOL_IT_SYSTEM_STATUS_WORD1 : "System Command Status Word1",
    MY_TOOL_IT_SYSTEM_STATUS_WORD2 : "System Command Status Word2",
    MY_TOOL_IT_SYSTEM_STATUS_WORD3 : "System Command Status Word3",
    MY_TOOL_IT_SYSTEM_TEST : "System Command Test",
    MY_TOOL_IT_SYSTEM_LOG : "System Command Log",
    MY_TOOL_IT_SYSTEM_BLUETOOTH : "System Command BlueTooth",
    MY_TOOL_IT_SYSTEM_ROUTING : "System Command Routing",
    }

CommandBlockStreaming = {
    MY_TOOL_IT_STREAMING_ACCELERATION : "Streaming Command Acceleration",
    MY_TOOL_IT_STREAMING_TEMPERATURE : "Streaming Command Temperature",
    MY_TOOL_IT_STREAMING_VOLTAGE : "Streaming Command Voltage",
    MY_TOOL_IT_STREAMING_CURRENT : "Streaming Command Current",
    }

CommandBlockStatisticalData= {
    MY_TOOL_IT_STATISTICAL_DATA_POC_POF : "Statistical Data Command PowerOn/Off Counter",
    MY_TOOL_IT_STATISTICAL_DATA_OPERATING_TIME : "Statistical Data Command Operating Time",
    MY_TOOL_IT_STATISTICAL_DATA_UVC : "Statistical Data Command Undervoltage Counter",
    MY_TOOL_IT_STATISTICAL_DATA_MEASUREMENT_INTERVAL : "Statistical Data Command Measurement Interval",
    MY_TOOL_IT_STATISTICAL_DATA_QUANTITY_INTERVAL : "Statistical Data Command Quantity Interval",
    MY_TOOL_IT_STATISTICAL_DATA_ENERGY : "Statistical Data Command Energy",
    }

CommandBlockConfiguration= {
    MY_TOOL_IT_CONFIGURATION_ACCELERATION_CONFIGURATION : "Configuration Command Acceleration Configuration",
    MY_TOOL_IT_CONFIGURATION_TEMPERATURE_CONFIGURATION : "Configuration Command Temperature Configuration",
    MY_TOOL_IT_CONFIGURATION_VOLTAGE_CONFIGURATION : "Configuration Command Voltage Configuration",
    MY_TOOL_IT_CONFIGURATION_CURRENT_CONFIGURATION : "Configuration Command Current Configuration",
    MY_TOOL_IT_CONFIGURATION_CALIBRATION_FACTOR_K : "Configuration Command Calibration Factor K",
    MY_TOOL_IT_CONFIGURATION_CALIBRATION_FACTOR_D : "Configuration Command Calibration Factor D",
    MY_TOOL_IT_CONFIGURATION_CALIBRATE_MEASSUREMENT : "Configuration Command Calibration Measurement",
    MY_TOOL_IT_CONFIGURATION_ALARM : "Configuration Command Alarm",
    MY_TOOL_IT_CONFIGURATION_CONFIGURATION_HMI : "Configuration Command HMI",
    }


CommandBlockProductData= {
    MY_TOOL_IT_PRODUCT_DATA_GTIN : "Product Data Command GTIN",
    MY_TOOL_IT_PRODUCT_DATA_HARDWARE_REVISION : "Product Data Command Hardware Revision",
    MY_TOOL_IT_PRODUCT_DATA_FIRMWARE_VERSION : "Product Data Command Firmware Version",
    MY_TOOL_IT_PRODUCT_DATA_RELEASE_NAME : "Product Data Command Release Name",
    MY_TOOL_IT_PRODUCT_DATA_SERIAL_NUMBER1 : "Product Data Command Serial Number 1",
    MY_TOOL_IT_PRODUCT_DATA_SERIAL_NUMBER2 : "Product Data Command Serial Number 2",
    MY_TOOL_IT_PRODUCT_DATA_SERIAL_NUMBER3 : "Product Data Command Serial Number 3",
    MY_TOOL_IT_PRODUCT_DATA_SERIAL_NUMBER4 : "Product Data Command Serial Number 4",
    MY_TOOL_IT_PRODUCT_DATA_NAME1 : "Product Data Command Name1",
    MY_TOOL_IT_PRODUCT_DATA_NAME2 : "Product Data Command Name2",
    MY_TOOL_IT_PRODUCT_DATA_NAME3 : "Product Data Command Name3",
    MY_TOOL_IT_PRODUCT_DATA_NAME4 : "Product Data Command Name4",
    MY_TOOL_IT_PRODUCT_DATA_NAME5 : "Product Data Command Name5",
    MY_TOOL_IT_PRODUCT_DATA_NAME6 : "Product Data Command Name6",
    MY_TOOL_IT_PRODUCT_DATA_NAME7 : "Product Data Command Name7",
    MY_TOOL_IT_PRODUCT_DATA_NAME8 : "Product Data Command Name8",
    MY_TOOL_IT_PRODUCT_DATA_NAME9 : "Product Data Command Name9",
    MY_TOOL_IT_PRODUCT_DATA_NAME10 : "Product Data Command Name10",
    MY_TOOL_IT_PRODUCT_DATA_NAME11 : "Product Data Command Name11",
    MY_TOOL_IT_PRODUCT_DATA_NAME12 : "Product Data Command Name12",
    MY_TOOL_IT_PRODUCT_DATA_NAME13 : "Product Data Command Name13",
    MY_TOOL_IT_PRODUCT_DATA_NAME14 : "Product Data Command Name14",
    MY_TOOL_IT_PRODUCT_DATA_NAME15 : "Product Data Command Name15",
    MY_TOOL_IT_PRODUCT_DATA_NAME16 : "Product Data Command Name16",
    MY_TOOL_IT_PRODUCT_DATA_OEM_FREE_USE1 : "Product Data Command Free Use 1",
    MY_TOOL_IT_PRODUCT_DATA_OEM_FREE_USE2 : "Product Data Command Free Use 2",
    MY_TOOL_IT_PRODUCT_DATA_OEM_FREE_USE3 : "Product Data Command Free Use 3",
    MY_TOOL_IT_PRODUCT_DATA_OEM_FREE_USE4 : "Product Data Command Free Use 4",
    MY_TOOL_IT_PRODUCT_DATA_OEM_FREE_USE5 : "Product Data Command Free Use 5",
    MY_TOOL_IT_PRODUCT_DATA_OEM_FREE_USE6 : "Product Data Command Free Use 6",
    MY_TOOL_IT_PRODUCT_DATA_OEM_FREE_USE7 : "Product Data Command Free Use 7",
    MY_TOOL_IT_PRODUCT_DATA_OEM_FREE_USE8 : "Product Data Command Free Use 8",
    }

CommandBlockTest = {
    MY_TOOL_IT_TEST_SIGNAL : "Test Command Signal",
    }

CalibMeassurementActionNone = 0
CalibMeassurementActionInject = 1
CalibMeassurementActionEject = 2
CalibMeassurementActionMeasure = 3

CalibMeassurementTypeAcc = 0
CalibMeassurementTypeTemp = 1
CalibMeassurementTypeVoltage = 32
CalibMeassurementTypeVss = 96
CalibMeassurementTypeAvdd = 97
CalibMeassurementTypeRegulatedInternalPower = 98
CalibMeassurementTypeOpvOutput = 99

AdcAcquisitionTime1 = 0
AdcAcquisitionTime2 = 1
AdcAcquisitionTime3 = 2
AdcAcquisitionTime4 = 3
AdcAcquisitionTime8 = 4
AdcAcquisitionTime16 = 5
AdcAcquisitionTime32 = 6
AdcAcquisitionTime64 = 7
AdcAcquisitionTime128 = 8
AdcAcquisitionTime256 = 9
AdcAcquisitionTimeList = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
AdcOverSamplingRateNone = 0
AdcOverSamplingRate2 = 1
AdcOverSamplingRate4 = 2
AdcOverSamplingRate8 = 3
AdcOverSamplingRate16 = 4
AdcOverSamplingRate32 = 5
AdcOverSamplingRate64 = 6 
AdcOverSamplingRate128 = 7
AdcOverSamplingRate256 = 8
AdcOverSamplingRate512 = 9
AdcOverSamplingRate1024 = 10
AdcOverSamplingRate2048 = 11
AdcOverSamplingRate4096 = 12
AdcOverSamplingRateList = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
AdcReferenceNone = 0      
AdcReference1V25 = 25     
AdcReferenceVfs1V65 = 33  
AdcReferenceVfs1V8 = 36   
AdcReferenceVfs2V1 = 42   
AdcReferenceVfs2V2 = 44   
AdcReference2V5 = 50      
AdcReferenceVfs2V7 = 54    
AdcReferenceVDD = 66      
AdcReference5V = 100      
AdcReference6V6 = 132     
AdcReferenceList = [AdcReference1V25, AdcReferenceVfs1V65, AdcReferenceVfs1V8, AdcReferenceVfs2V1, AdcReferenceVfs2V2, AdcReference2V5, AdcReferenceVfs2V7, AdcReferenceVDD, AdcReference5V, AdcReference6V6]

DataSetsNone = 0
DataSets1 = 1
DataSets3 = 2
DataSets6 = 3
DataSets10 = 4
DataSets15 = 5
DataSets20 = 6
DataSets30 = 7

TestCommandSignalLine = 1
TestCommandSignalRamp = 2
    
SystemCommandBlueToothConnectTime = 20
SystemCommandBlueToothConnectTimeOut = 16
SystemCommandBlueToothDisconnectTime = 1
SystemCommandBlueToothReserved = 0
SystemCommandBlueToothConnect = 1
SystemCommandBlueToothGetNumberAvailableDevices = 2
SystemCommandBlueToothSetName1 = 3
SystemCommandBlueToothSetName2 = 4
SystemCommandBlueToothGetName1 = 5
SystemCommandBlueToothGetName2 = 6
SystemCommandBlueToothDeviceConnect = 7
SystemCommandBlueToothDeviceCheckConnected = 8
SystemCommandBlueToothDisconnect = 9
SystemCommandBlueToothSendCounter = 10
SystemCommandBlueToothReceiveCounter = 11
SystemCommandBlueToothRssi = 12
SystemCommandBlueToothEnergyModeReducedRead = 13
SystemCommandBlueToothEnergyModeReducedWrite = 14
SystemCommandBlueToothEnergyModeLowestRead = 15
SystemCommandBlueToothEnergyModeLowestWrite = 16
SystemCommandBlueToothMacAddress = 17

SystemCommandRoutingReserved = 0
SystemCommandRoutingSendCounter = 1
SystemCommandRoutingSendFailCounter = 2
SystemCommandRoutingSendLowLevelByteCounter = 3
SystemCommandRoutingReceiveCounter = 4
SystemCommandRoutingReceiveFailCounter = 5
SystemCommandRoutingReceiveLowLevelByteCounter = 6

CalibMeassurementAction = {
    CalibMeassurementTypeAcc : "Calibration Measurement Type - Acceleration",
    CalibMeassurementTypeTemp : "Calibration Measurement Type - Temperature",
    CalibMeassurementTypeVoltage : "Calibration Measurement Type - Voltage",
    CalibMeassurementTypeVss : "Calibration Measurement Type - VSS(Ground)",
    CalibMeassurementTypeAvdd :"Calibration Measurement Type - AVDD(Analog Supply)",
    CalibMeassurementTypeRegulatedInternalPower : "Calibration Measurement Type - Regulated Internal Power",
    CalibMeassurementTypeOpvOutput  : "Calibration Measurement Type - OPV Output",
    }

CalibMeassurementAction = {
    CalibMeassurementActionNone : "Calibration Measurement Action - None/Reset",
    CalibMeassurementActionInject : "Calibration Measurement Action - Inject",
    CalibMeassurementActionEject : "Calibration Measurement Action - Eject",
    CalibMeassurementActionMeasure : "Calibration Measurement Action - Measure",
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
    if AdcAcquisitionTime1 == acquisitionTime:
        acquTime = 1
    elif AdcAcquisitionTime2 == acquisitionTime:
        acquTime = 2
    elif AdcAcquisitionTime3 == acquisitionTime:
        acquTime = 3
    elif AdcAcquisitionTime4 == acquisitionTime:
        acquTime = 4
    elif AdcAcquisitionTime8 == acquisitionTime:
        acquTime = 8
    elif AdcAcquisitionTime16 == acquisitionTime:
        acquTime = 16
    elif AdcAcquisitionTime32 == acquisitionTime:
        acquTime = 32
    elif AdcAcquisitionTime64 == acquisitionTime:
        acquTime = 64
    elif AdcAcquisitionTime128 == acquisitionTime:
        acquTime = 128
    elif AdcAcquisitionTime256 == acquisitionTime:
        acquTime = 256
    else:
        raise
    if AdcOverSamplingRateNone == OverSamplingRate:
        samplingRate = 1
    elif AdcOverSamplingRate2 == OverSamplingRate:
        samplingRate = 2
    elif AdcOverSamplingRate4 == OverSamplingRate:
        samplingRate = 4
    elif AdcOverSamplingRate8 == OverSamplingRate:
        samplingRate = 8
    elif AdcOverSamplingRate16 == OverSamplingRate:
        samplingRate = 16
    elif AdcOverSamplingRate32 == OverSamplingRate:
        samplingRate = 32
    elif AdcOverSamplingRate64 == OverSamplingRate:
        samplingRate = 64
    elif AdcOverSamplingRate128 == OverSamplingRate:
        samplingRate = 128
    elif AdcOverSamplingRate256 == OverSamplingRate:
        samplingRate = 256
    elif AdcOverSamplingRate512 == OverSamplingRate:
        samplingRate = 512
    elif AdcOverSamplingRate1024 == OverSamplingRate:
        samplingRate = 1024
    elif AdcOverSamplingRate2048 == OverSamplingRate:
        samplingRate = 2048
    elif AdcOverSamplingRate4096 == OverSamplingRate:
        samplingRate = 4096
    else:
        raise
    return 38400000 / ((prescaler + 1) * (acquTime + 13) * samplingRate)


AdcAcquisitionTime = {
    AdcAcquisitionTime1 : "ADC Acquisition Time - 1Cycle",
    AdcAcquisitionTime2 : "ADC Acquisition Time - 2Cycle",
    AdcAcquisitionTime3 : "ADC Acquisition Time - 3Cycle",
    AdcAcquisitionTime4 : "ADC Acquisition Time - 4Cycle",
    AdcAcquisitionTime8 : "ADC Acquisition Time - 8Cycle",
    AdcAcquisitionTime16 : "ADC Acquisition Time - 16Cycle",
    AdcAcquisitionTime32 : "ADC Acquisition Time - 32Cycle",
    AdcAcquisitionTime64 : "ADC Acquisition Time - 64Cycle",
    AdcAcquisitionTime128 : "ADC Acquisition Time - 128Cycle",
    AdcAcquisitionTime256 : "ADC Acquisition Time - 256Cycle"
    }

AdcOverSamplingRateName = {
    AdcOverSamplingRateNone : "ADC Single Sampling",
    AdcOverSamplingRate2 : "ADC Over Sampling Rate - 2",
    AdcOverSamplingRate4 : "ADC Over Sampling Rate - 4",
    AdcOverSamplingRate8 : "ADC Over Sampling Rate - 8",
    AdcOverSamplingRate16 : "ADC Over Sampling Rate - 16",
    AdcOverSamplingRate32 : "ADC Over Sampling Rate - 32",
    AdcOverSamplingRate64 : "ADC Over Sampling Rate - 64",
    AdcOverSamplingRate128 : "ADC Over Sampling Rate - 128",
    AdcOverSamplingRate256 : "ADC Over Sampling Rate - 256",
    AdcOverSamplingRate512 : "ADC Over Sampling Rate - 512",
    AdcOverSamplingRate1024 : "ADC Over Sampling Rate - 1024",
    AdcOverSamplingRate2048 : "ADC Over Sampling Rate - 2048",
    AdcOverSamplingRate4096 : "ADC Over Sampling Rate - 4096"
    }

VRefName = {
    AdcReferenceNone : "ADC Reference None",
    AdcReference1V25 : "ADC Reference 1V25",
    AdcReferenceVfs1V65 : "ADC Reference 1V65",
    AdcReferenceVfs1V8 : "ADC Reference 1V8",
    AdcReferenceVfs2V1 : "ADC Reference 2V1",
    AdcReferenceVfs2V2 : "ADC Reference 2V2",
    AdcReference2V5 : "ADC Reference 2V5",
    AdcReferenceVfs2V7 : "ADC Reference 2V7",
    AdcReferenceVDD : "ADC Reference VDD(3V3)",
    AdcReference5V : "ADC Reference 5V",
    AdcReference6V6 : "ADC Reference 6V6"
    }

AdcVRefValuemV = {
    AdcReferenceNone : 0,
    AdcReference1V25 : 1250,
    AdcReferenceVfs1V65 : 1650,
    AdcReferenceVfs1V8 : 1800,
    AdcReferenceVfs2V1 : 2100,
    AdcReferenceVfs2V2 : 2200,
    AdcReference2V5 : 2500,
    AdcReferenceVfs2V7 : 2700,
    AdcReferenceVDD : 3300,
    AdcReference5V : 5000,
    AdcReference6V6 : 6000
    }

