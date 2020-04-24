"""
This Lists contains the list for all STH production tests run
"""

"""
STH Table Lists
"""

asTestTableSthList = [
"Flash",
"Ota",
"Ack",
"Temperature",
"AccumulatorVoltage",
"Version",
"Reset",
"Rssi",
"ApparentGravity",
"Snr",
"SelfTest",
"CalibrationVoltage",
"CalibrationAcceleration",
"Eeprom",
]

asProductionTableVariableDefSthList = {
"Flash" : "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), result boolean DEFAULT false",  # "Flash"
"Ota" : "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), result boolean DEFAULT false",  # "Ota"
"Ack" : "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), result boolean DEFAULT false",  # "Ack"
"Temperature" : "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), result float (5, 2)",  # "Temperature"
"AccumulatorVoltage" : "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), result float (5, 2)     ",  # "AccumulatorVoltage"
"Version" : "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), result boolean DEFAULT false, version VARCHAR(18)",  # "Version"
"Reset" : "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), result boolean DEFAULT false",  # "Reset"
"Rssi" : "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), sth INT, stu INT",  # "Rssi"
"ApparentGravity" : "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), x float (5, 2), y float (5, 2), z float (5, 2)",  # "ApparentGravity"
"Snr" : "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), x float (5, 2), y float (5, 2), z float (5, 2)",  # "Snr"
"SelfTest" : "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), x float (7, 4), y float (7, 4), z float (7, 4)",  # "SelfTest"
"CalibrationVoltage" : "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), k float (30, 20), d float (30, 20)",  # "CalibrationVoltage"
"CalibrationAcceleration" : "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), k float (30, 20), d float (30, 20)",  # "CalibrationAcceleration"
"Eeprom" : "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), result boolean DEFAULT false",  # "Eeprom" ]
}

asProductionTableVariableInitSthList = {
"Flash" : ["BlueToothAddress, dateTime, result", "%s, %s, %s", ["", "", "0"]],
"Ota" : ["BlueToothAddress, dateTime, result", "%s, %s, %s", ["", "", "0"]],
"Ack" : ["BlueToothAddress, dateTime, result", "%s, %s, %s", ["", "", "0"]],
"Temperature" : ["BlueToothAddress, dateTime, result", "%s, %s, %s", ["", "", "999.99"]],
"AccumulatorVoltage" : ["BlueToothAddress, dateTime, result", "%s, %s, %s", ["", "", "999.99"]],
"Version" : ["BlueToothAddress, dateTime, result, version", "%s, %s, %s, %s", ["", "", "0", "v0.0.0"]],
"Reset" : ["BlueToothAddress, dateTime, result", "%s, %s, %s", ["", "", "0"]],
"Rssi" : ["BlueToothAddress, dateTime, sth, stu", "%s, %s, %s, %s", ["", "", "-1000", "-1000"]],
"ApparentGravity" : ["BlueToothAddress, dateTime, x , y, z", "%s, %s, %s, %s, %s", ["","", "999.99", "999.99", "999.99"]],
"Snr" : ["BlueToothAddress, dateTime, x , y, z", "%s, %s, %s, %s, %s", ["", "", "999.99", "999.99", "999.99"]],
"SelfTest" : ["BlueToothAddress, dateTime, x , y, z", "%s, %s, %s, %s, %s", ["", "", "999.99", "999.99", "999.99"]],
"CalibrationVoltage" : ["BlueToothAddress, dateTime, k, d", "%s, %s, %s, %s", ["", "", "1.0", "0.0"]],
"CalibrationAcceleration" : ["BlueToothAddress, dateTime, k, d", "%s, %s, %s, %s", ["", "", "1.0", "0.0"]],
"Eeprom" : ["BlueToothAddress, dateTime, result", "%s, %s, %s", ["", "", "0"]],
}


"""
STU Lists
"""
asTestTableStuList = [
"Flash",
"Ota",
"Ack",
"Version",
"Reset",
"Rssi",
"Eeprom",
]

asProductionTableVariableDefStuList = {
"Flash" : "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), result boolean DEFAULT false",  # "Flash"
"Ota" : "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), result boolean DEFAULT false",  # "Ota"
"Ack" : "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), result boolean DEFAULT false",  # "Ack"
"Version" : "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), result boolean DEFAULT false, version VARCHAR(18)",  # "Version"
"Reset" : "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), result boolean DEFAULT false",  # "Reset"
"Rssi" : "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), sth INT, stu INT",  # "Rssi"
"Eeprom" : "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), result boolean DEFAULT false",  # "Eeprom" ]
}

asProductionTableVariableInitStuList = {
"Flash" : ["BlueToothAddress, dateTime, result", "%s, %s, %s", ["", "", "0"]],
"Ota" : ["BlueToothAddress, dateTime, result", "%s, %s, %s", ["", "", "0"]],
"Ack" : ["BlueToothAddress, dateTime, result", "%s, %s, %s", ["", "", "0"]],
"Version" : ["BlueToothAddress, dateTime, result, version", "%s, %s, %s, %s", ["", "", "0", "v0.0.0"]],
"Reset" : ["BlueToothAddress, dateTime, result", "%s, %s, %s", ["", "", "0"]],
"Rssi" : ["BlueToothAddress, dateTime, sth, stu", "%s, %s, %s, %s", ["", "", "-1000", "-1000"]],
"Eeprom" : ["BlueToothAddress, dateTime, result", "%s, %s, %s", ["", "", "0"]],
}

"""
General EEPROM Page Data
"""
asProductData = [
"Gtin",
"HardwareRevision",
"FirmwareVersion",
"ReleaseName",
"SerialNumber",
"Name",
"OemFreeUse",
]

asStatistics = [
"PowerOnCycles",
"PowerOffCycles",
"OperatingTime",
"UnderVoltageCounter",
"WatchdogResetCounter",
"ProductionDate",
"BatchNumber",
]
