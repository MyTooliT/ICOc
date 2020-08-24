import ctypes
c_uint8 = ctypes.c_uint8
c_uint32 = ctypes.c_uint32

TestConfig = {
    "DevName": "Valerie",
    "Version": "v2.1.10",
    "ProductionDate": "20191106",
    "HolderName": "Tanja",
    "StuName": "Valerie",
}


class StuErrorWordFlags(ctypes.LittleEndianStructure):
    _fields_ = [
        ("bTxFail", c_uint32, 1),
        ("Reserved", c_uint32, 31),
    ]


class StuErrorWord(ctypes.Union):
    _fields_ = [("b", StuErrorWordFlags), ("asword", c_uint32)]
