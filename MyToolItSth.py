import ctypes
c_uint8 = ctypes.c_uint8
c_uint32 = ctypes.c_uint32

# Version
VersionMajor = 2
VersionMinor = 1
VersionBuild = 0
TestDeviceName = "Tanja"

SthModuleStreaming = 0
AdcConfigAllPrescalerMax = 4
SleepTimeMin = 10000
Sleep1TimeReset = 300000
SleepAdvertisementTimeMin = 50
SleepAdvertisementTimeMax = 4000
Sleep1AdvertisementTimeReset = 400
Sleep2TimeReset = 3600000
Sleep2AdvertisementTimeReset = 1600
ConnectionTimeNormalMaxMs = 4000
ConnectionTimeSleep1MaxMs = 5000
ConnectionTimeSleep2MaxMs = 6000
ConnectionTimeMaximumMs = 15000


class SthErrorWordFlags(ctypes.BigEndianStructure):
    _fields_ = [
            ("Reserved", c_uint32, 31),
            ("bAdcOverRun", c_uint32, 1),
        ]


class SthErrorWord(ctypes.Union):
    _fields_ = [("b", SthErrorWordFlags),
                ("asword", c_uint32)]
