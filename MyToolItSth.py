import ctypes
c_uint8 = ctypes.c_uint8
c_uint32 = ctypes.c_uint32
from SthLimits import *
from MyToolItCommands import AdcMax

Version = {
    "VersionMajor" : 2,
    "VersionMinor" : 1,
    "VersionBuild" : 1,
    "Name" : "Tanja",
}

TestConfig = {
    "DevName" : "Tanja",
    "AdcConfigAllPrescalerMax" : 4,
    "ConTimeNormalMaxMs" : 5000,
    "ConTimeSleep1MaxMs" : 6000,
    "ConTimeSleep2MaxMs" : 7000,
    "ConTimeMaximumMs" : 15000,
    }

SleepTime = {
    "Min" : 10000,
    "Reset1" : 300000,
    "AdvertisementMin" : 1000,
    "AdvertisementMax" : 4000,
    "AdvertisementReset1" : 2000,
    "Reset2" : 3600000,
    "AdvertisementReset2" : 3000,
    }

SthModule = {
    "Streaming" : 0,
}


class SthErrorWordFlags(ctypes.LittleEndianStructure):
    _fields_ = [
            ("bTxFail", c_uint32, 1),
            ("bAdcOverRun", c_uint32, 1),
            ("Reserved", c_uint32, 30),
        ]


class SthErrorWord(ctypes.Union):
    _fields_ = [("b", SthErrorWordFlags),
                ("asword", c_uint32)]

    
class SthStateWordFlags(ctypes.LittleEndianStructure):
    _fields_ = [
            ("bError", c_uint32, 1),
            ("u3NetworkState", c_uint32, 3),
            ("Reserved", c_uint32, 28),
        ]


class SthStateWord(ctypes.Union):
    _fields_ = [("b", SthStateWordFlags),
                ("asword", c_uint32)]


def fVoltageBattery(x):
    if(0 < x):
        voltage = (x*57*3.3)/(10*2**16)
    else:
        voltage = 0
    return voltage

def fAdcRawDat(x):
    return x


def fAcceleration(x):
    return ((x / AdcMax - 1 / 2) * AccelerationToAccGravitity)

