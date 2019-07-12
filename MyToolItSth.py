import ctypes
c_uint8 = ctypes.c_uint8
c_uint32 = ctypes.c_uint32


SthModuleStreaming = 0
AdcConfigAllPrescalerMax=4
Sleep1TimeReset = 300000
Sleep1AdvertisementTimeReset = 800
Sleep2TimeReset = 3600000
Sleep2AdvertisementTimeReset = 4000

class SthErrorWordFlags(ctypes.BigEndianStructure):
    _fields_ = [
            ("Reserved", c_uint32, 31),
            ("bAdcOverRun", c_uint32, 1),
        ]


class SthErrorWord(ctypes.Union):
    _fields_ = [("b", SthErrorWordFlags),
                ("asword", c_uint32)]