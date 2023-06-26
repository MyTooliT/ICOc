import ctypes

c_uint8 = ctypes.c_uint8
c_uint32 = ctypes.c_uint32

TestConfig = {
    "Version": "v2.1.10",
    "AdcConfigAllPrescalerMax": 4,
    "ConTimeNormalMaxMs": 5000,
    "ConTimeSleep1MaxMs": 6000,
    "ConTimeSleep2MaxMs": 7000,
    "ConTimeMaximumMs": 15000,
    "DisconnectedCurrentMax": 0.8,  # in mA
    "EnergyMode1CurrentMax": 0.5,  # in mA
    "EnergyMode2CurrentMax": 0.48,  # in mA
    "EnergyModeMaxCurrentMax": 0.48,  # in mA
    "EnergyConnectedCurrentMax": 10,  # in mA
    "EnergyMeasuringCurrentMax": 17,  # in mA
    "EnergyMeasuringLedOffCurrentMax": 17,  # in mA
}

SleepTime = {
    "Min": 10000,
    "Reset1": 300000,
    "AdvertisementMin": 1000,
    "AdvertisementMax": 4000,
    "AdvertisementReset1": 2000,
    "Reset2": 3600000,
    "AdvertisementReset2": 4000,
}

SthModule = {
    "Streaming": 0,
}


class SthErrorWordFlags(ctypes.LittleEndianStructure):
    _fields_ = [
        ("bTxFail", c_uint32, 1),
        ("bAdcOverRun", c_uint32, 1),
        ("Reserved", c_uint32, 30),
    ]


class SthErrorWord(ctypes.Union):
    _fields_ = [("b", SthErrorWordFlags), ("asword", c_uint32)]


class SthStateWordFlags(ctypes.LittleEndianStructure):
    """Format for status word 0 of the STH/SHA

    bError: Error bit
        - 0: No Error
        - 1: Error

    u3NetworkState: Current network state of STH
        - 0: Failure
        - 1: Error
        - 2: Standby
        - 3: Graceful Degradation 2
        - 4: Graceful Degradation 1
        - 5: Operating
        - 6: Startup
        - 7: No Change

    Reserved: Reserved bits
    """

    _fields_ = [
        ("bError", c_uint32, 1),
        ("u3NetworkState", c_uint32, 3),
        ("Reserved", c_uint32, 28),
    ]


class SthStateWord(ctypes.Union):
    _fields_ = [("b", SthStateWordFlags), ("asword", c_uint32)]


def fVoltageBattery(x):
    if 0 < x:
        voltage = (x * 57 * 3.3) / (10 * 2**16)
    else:
        voltage = 0
    return voltage


def fAdcRawDat(x):
    return x
