import ctypes
c_uint8 = ctypes.c_uint8
c_uint32 = ctypes.c_uint32

Version = {
    "VersionMajor" : 2,
    "VersionMinor" : 1,
    "VersionBuild" : 1,
    "Name" : "Valerie",
}



class StuErrorWordFlags(ctypes.LittleEndianStructure):
    _fields_ = [
            ("bTxFail", c_uint32, 1),
            ("Reserved", c_uint32, 31),
        ]


class StuErrorWord(ctypes.Union):
    _fields_ = [("b", StuErrorWordFlags),
                ("asword", c_uint32)]
