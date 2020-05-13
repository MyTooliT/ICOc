from enum import Enum
from MyToolItDbTables import MyToolItDbTables 
from MyToolItDbLimitsList import asProductionLimitsSthList, asProductionLimitsStuList
from MyToolItDbTablesList import asTestTableSthList, \
asProductionTableVariableDefSthList, asProductionTableVariableInitSthList, \
asProductData, asStatistics, asTestTableStuList, asProductionTableVariableDefStuList,\
asProductionTableVariableInitStuList

import datetime

"""
EEPROM Page definitions for tables
"""

class Eeprom():
    uProductData = 1
    uStatistics = 2

"""
EEPROM Page definitions for tables
"""

    
"""
Test Definition
"""

class TestDefSth():
    uProductionPcb = 0
    uProductionAssembled = 1
    uProductionPotted = 2
    uService = 9
    
"""
Test Definition
"""


class TestDefStu():
    uProduction = 0
    uService = 9
    
"""
Constant Definitions STH
"""
class ConstantsSth():
    uProductionTestTotalTestRuns = 3
    
"""
Constant Definitions STU
"""
class ConstantsStu():
    uProductionTestLimitTable = 0

"""
This class hanldes the prodution test tables

"""


class MyToolItDb(MyToolItDbTables):
    
    sDateTime = datetime.datetime.now().isoformat()  # This is the Time Stamp for ALL entries of a test case
    sSetDateTime = "dateTime = " + "'" + sDateTime + "'"
    
    """
    @param sHost Which host e.g. localhost or any IP address
    @param sUser User Name for login
    @param sPassword Password for user
    @param sDataBase Which data base should be used
    """

    def __init__(self, sHost, sUser, sPassWord, sDataBase):
        MyToolItDbTables.__init__(self, sHost, sUser, sPassWord, sDataBase)
 
    """
    Use this to create all production test tables.
    """

    def vShowDataBases(self):
        self.tMyCursor.execute("SHOW DATABASES")
        for x in self.tMyCursor:
            print(x)

    """
    Use this to create all result tables for the STH.
    @param iTestStage Test Stage the is part of the table names (that are created here)
    @param sProductionTest Name of the production test
    """

    def vProductionTestSthTablesResults(self, iTestStage, sProductionTest):
        sTable = "SthProductionTests" + str(iTestStage) + sProductionTest
        if False == self.bTableExists(sTable):
            self.vTableCreate(sTable, asProductionTableVariableDefSthList[sProductionTest])
             
    """
    Use this to create all result tables for the STH.
    @param iTestStage Test Stage the is part of the table names (that are created here)
    @param sProductionTest Name of the production test
    """

    def vServiceTestSthTablesResults(self, sProductionTest):
        sTable = "SthServiceTests" + sProductionTest
        if False == self.bTableExists(sTable):
            self.vTableCreate(sTable, asProductionTableVariableDefSthList[sProductionTest])            

    """
    Use this to create all limit tables for the STH and set all parameters as well
    @param iTestStage Test Stage the is part of the table names (that are created here)
    @param sProductionTest Name of the production test
    """

    def vSthTablesLimits(self, iTestStage, sProductionTest):
        sDefLimits = "ProductKey VARCHAR(255), Limit0 VARCHAR(255), Limit1 VARCHAR(255), Limit2 VARCHAR(255), Limit3 VARCHAR(255), Limit4 VARCHAR(255), Limit5 VARCHAR(255), Limit6 VARCHAR(255), Limit7 VARCHAR(255), Limit8 VARCHAR(255)"
        if TestDefSth.uService == iTestStage:
            iTestStage = TestDefSth.uProductionPotted
        sTable = "SthTestLimits" + str(iTestStage) + sProductionTest 
        if False == self.bTableExists(sTable):
            self.vTableCreate(sTable, sDefLimits)
        for sKey in asProductionLimitsSthList:
            atLimit = asProductionLimitsSthList[sKey][iTestStage][sProductionTest]
            sEntry = "ProductKey = '" + sKey + "'"
            if False != self.bTableEntryExists(sTable, sEntry):
                for i in range(0, len(atLimit)):
                    sSet = "Limit" + str(i) + " = '" + atLimit[i] + "'"
                    self.vTableUpdate(sTable, sEntry, sSet)
            else:
                atLimit = [sKey] + atLimit
                self.vTableInsert(sTable, "ProductKey, Limit0, Limit1, Limit2, Limit3, Limit4, Limit5, Limit6, Limit7, Limit8", "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s", tuple(atLimit))
 
    """
    Use this to create Product Data Tables i.e. store content of EEPROM
    @param iTestStage Test Stage the is part of the table names (that are created here)
    @param sProductionTest Name of the production test
    """

    def vProductionTestSthTablesProductData(self, iTestStage, sProductData):
        sTable = "SthProductionTestsProductData" + str(iTestStage) + sProductData
        if False == self.bTableExists(sTable):
            self.vTableCreate(sTable, "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), Data VARCHAR(1023)")
            
    """
    Use this to create Service Data Tables i.e. store content of EEPROM
    @param iTestStage Test Stage the is part of the table names (that are created here)
    @param sProductionTest Name of the production test
    """

    def vServiceTestSthTablesProductData(self, sProductData):
        sTable = "SthServiceTestsProductData" + sProductData
        if False == self.bTableExists(sTable):
            self.vTableCreate(sTable, "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), Data VARCHAR(1023)")
            
    """
    Use this to create Product Data Tables i.e. store content of EEPROM
    @param iTestStage Test Stage the is part of the table names (that are created here)
    @param sProductionTest Name of the production test
    """

    def vProductionTestSthTablesStatistics(self, iTestStage, sProductData):
        sTable = "SthProductionTestsStatistics" + str(iTestStage) + sProductData
        if False == self.bTableExists(sTable):
            self.vTableCreate(sTable, "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), Data VARCHAR(255)")

    """
    Use this to create Product Data Tables i.e. store content of EEPROM
    @param iTestStage Test Stage the is part of the table names (that are created here)
    @param sProductionTest Name of the production test
    """

    def vServiceTestSthTablesStatistics(self, sProductData):
        sTable = "SthServiceTestsStatistics" + sProductData
        if False == self.bTableExists(sTable):
            self.vTableCreate(sTable, "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), Data VARCHAR(255)")
            
    """
    Use this to create Product Data Tables i.e. store content of EEPROM
    @param iTestStage Test Stage the is part of the table names (that are created here)
    @param sProductionTest Name of the production test
    """

    def vProductionTestSthTablesResult(self, iTestStage):
        sTable = "SthProductionTestStageResult" + str(iTestStage)
        if False == self.bTableExists(sTable):
            self.vTableCreate(sTable, "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), result boolean DEFAULT false")
             
    """
    This creates the production test tables
    (PCB only, assembled STH, potted STH and service STH test)
    """

    def vSthTablesProduction(self):
        for iTestStage in range(0, ConstantsSth.uProductionTestTotalTestRuns):
            for iTable in range(0, len(asTestTableSthList)):
                sProductionTest = asTestTableSthList[iTable]
                self.vProductionTestSthTablesResults(iTestStage, sProductionTest)
            for iTable in range(0, len(asProductData)):    
                sProductData = asProductData[iTable]
                self.vProductionTestSthTablesProductData(iTestStage, sProductData)
            for iTable in range(0, len(asStatistics)):
                sStatistics = asStatistics[iTable]
                self.vProductionTestSthTablesStatistics(iTestStage, sStatistics)
            self.vProductionTestSthTablesResult(iTestStage)
            sTable = "SthProductionTestStageResult" + str(iTestStage)
            if False == self.bTableExists(sTable):
                self.vTableCreate(sTable, "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), result boolean DEFAULT false")
        sTable = "SthProductionTestResultOverall"
        if False == self.bTableExists(sTable):
            self.vTableCreate(sTable, "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), result boolean DEFAULT false")        
        
    """
    This creates the service test tables
    (PCB only, assembled STH, potted STH and service STH test)
    """

    def vSthTablesService(self):
        for iTable in range(0, len(asTestTableSthList)):
            sServiceTest = asTestTableSthList[iTable]
            self.vServiceTestSthTablesResults(sServiceTest)
        for iTable in range(0, len(asProductData)):    
            sServiceTest = asProductData[iTable]
            self.vServiceTestSthTablesProductData(sServiceTest)
        for iTable in range(0, len(asStatistics)):
            sStatistics = asStatistics[iTable]
            self.vServiceTestSthTablesStatistics(sStatistics)
        sTable = "SthServiceTestResultOverall"
        if False == self.bTableExists(sTable):
            self.vTableCreate(sTable, "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), result boolean DEFAULT false") 
                
    """
    This creats the limit tables for the STH. Please note that the last
    production stage limit are equally to the service limits.
    """

    def vSthTablesOverallLimits(self):
        for iTestStage in range(0, ConstantsSth.uProductionTestTotalTestRuns):
            for iTable in range(0, len(asTestTableSthList)):
                sProductionTest = asTestTableSthList[iTable]
                self.vSthTablesLimits(iTestStage, sProductionTest)
                                      
    """
    Use this to create all STH tables if not created
    (PCB only, assembled STH, potted STH and service STH test)
    """

    def vSthTables(self):
        self.vSthTablesProduction()
        self.vSthTablesService()
        self.vSthTablesOverallLimits()

    """
    Create entries for all production test case tables
    @param sBlueToothAddress STH Address
    @param iTestStage Test Stage
    """

    def vProductionTestSthEntryTestCases(self, sBlueToothAddress, iTestStage):
        sEntry = "BlueToothAddress = '" + sBlueToothAddress + "'"
        for iTable in range(0, len(asTestTableSthList)):
            sTest = asTestTableSthList[iTable]
            sTable = "SthProductionTests" + str(iTestStage) + sTest
            bEntry = self.bTableEntryExists(sTable, sEntry)
            if False == bEntry:  
                atEntry = asProductionTableVariableInitSthList[sTest]    
                sVariables = atEntry[0]   
                sArg = atEntry[1] 
                atInit = atEntry[2]  
                atInit[0] = sBlueToothAddress   
                self.vTableInsert(sTable, sVariables, sArg, tuple(atInit))
                
    """
    Create service test case entry
    @param sBlueToothAddress STH Address
    @param iTestStage Test Stage
    """

    def vServiceTestSthEntryTestCases(self, sTest, sBlueToothAddress):
        sTable = "SthServiceTests" + sTest
        bEntry = self.bTableEntryExists(sTable, self.sSetDateTime)
        if False == bEntry:  
            atEntry = asProductionTableVariableInitSthList[sTest]    
            sVariables = atEntry[0]   
            sArg = atEntry[1] 
            atInit = atEntry[2]  
            atInit[0] = sBlueToothAddress   
            atInit[1] = self.sDateTime 
            self.vTableInsert(sTable, sVariables, sArg, tuple(atInit))

    """
    Create entries for all product data tables
    @param sBlueToothAddress STH Address
    @param iTestStage Test Stage
    """

    def vProductionTestSthEepromProductData(self, sBlueToothAddress, iTestStage):
        sEntry = "BlueToothAddress = '" + sBlueToothAddress + "'"
        for iTable in range(0, len(asProductData)):
            sProductDataEntry = asProductData[iTable]
            sTable = "SthProductionTestsProductData" + str(iTestStage) + sProductDataEntry
            bEntry = self.bTableEntryExists(sTable, sEntry)
            if False == bEntry:  
                sVariables = "BlueToothAddress, dateTime, data"
                sArg = "%s, %s, %s"
                atInit = ["", self.sDateTime, "0"]
                atInit[0] = sBlueToothAddress
                self.vTableInsert(sTable, sVariables, sArg, tuple(atInit))
 
    """
    Create entries for all STH EEPROM statistics tables
    @param sBlueToothAddress STH Address
    @param iTestStage Test Stage
    """

    def vProductionTestSthEntryStatistics(self, sBlueToothAddress, iTestStage):
        sEntry = "BlueToothAddress = '" + sBlueToothAddress + "'"
        for iTable in range(0, len(asStatistics)):
            sTest = asStatistics[iTable]
            sTable = "SthProductionTestsStatistics" + str(iTestStage) + sTest
            bEntry = self.bTableEntryExists(sTable, sEntry)
            if False == bEntry:  
                sVariables = "BlueToothAddress, dateTime, data"
                sArg = "%s, %s, %s"
                atInit = ["", self.sDateTime, "0"]
                atInit[0] = sBlueToothAddress
                self.vTableInsert(sTable, sVariables, sArg, tuple(atInit))                     
        
    """
    Use this to create a new DB entry for a production test (run).
    Please, note that the same STH may be tested multiple times in a same way e.g.
    Forgot to power on the test STU. Moreover, there are multiple runs for
    each STH (PCB only, assembled STH and potted STH)
    @param sBlueToothAddress STH Address
    """

    def vProductionTestSthEntry(self, sBlueToothAddress, iTestStage):
        if TestDefSth.uProductionPotted >= iTestStage:
            self.vProductionTestSthEntryTestCases(sBlueToothAddress, iTestStage)
            self.vProductionTestSthEepromProductData(sBlueToothAddress, iTestStage)
            self.vProductionTestSthEntryStatistics(sBlueToothAddress, iTestStage)
     
    """
    Putting service Test Results into Table
    @param sTest Which Test to insert
    @param sBluetoothAddress Bluetooth MAC address of device
    @param sSet Set
    """

    def vProductionTestSthResultService(self, sTest, sBluetoothAddress, sSet):
        sTable = "SthServiceTests" + sTest
        self.vServiceTestSthEntryTestCases(sTest, sBluetoothAddress)
        self.vTableUpdate(sTable, self.sSetDateTime, sSet)
                            
    """
    Use this to file a single STH test results.
    @param iTestStage Which test run (PCB, assembled or potted)
    @param sTest Which test
    @param sBluetoothAddress Bluetooth address of tested STH
    @param sColumn Variable to set
    @param sValue Value to be set
    """

    def vProductionTestSthResult(self, iTestStage, sTest, sBluetoothAddress, sColumn, Value):
        sSetValue = None
        if type(Value) is bool:
            if False != Value:
                sSetValue = "1"
            else:
                sSetValue = "0"
        elif type(Value) is str:
            sSetValue = "'" + Value + "'"
        else:  # Please note that there are other data types. However, if not used...
            sSetValue = "'" + str(Value) + "'"
        sSet = sColumn + " = " + sSetValue
        sKey = "BlueToothAddress = '" + sBluetoothAddress + "'"
        if TestDefSth.uProductionPotted >= iTestStage:
            sTable = "SthProductionTests" + str(iTestStage) + sTest
            self.vTableUpdate(sTable, sKey, sSet)
            self.vTableUpdate(sTable, sKey, self.sSetDateTime)
        elif TestDefSth.uService == iTestStage:            
            self.vProductionTestSthResultService(sTest, sBluetoothAddress, sSet)
        else:
            raise
    
    """
    Use this to file a single STH production test stage EEPROM page entry.
    @param iTestStage Which test run (PCB, assembled or potted)
    @param sBluetoothAddress Bluetooth address of tested STH
    @param tEepromPage Which Eeprom Page to write
    @param sEntry Which page entry to be set
    @param sSet Entry value to be set
    """

    def vTestSthEepromProduction(self, sBluetoothAddress, tEepromPage, sEntry, sSet):    
        if tEepromPage is Eeprom.uProductData:
            sTable = "SthProductionTestsProductData" 
        elif tEepromPage is Eeprom.uStatistics:   
            sTable = "SthProductionTestsStatistics" 
        else:
            raise Exception
        sTable = sTable + str(iTestStage) + sEntry
        sKey = "BlueToothAddress = '" + sBluetoothAddress + "'"
        self.vTableUpdate(sTable, sKey, sSet)    
    

    """
    Use this to file a single STH production test stage EEPROM page entry.
    @param iTestStage Which test run (PCB, assembled or potted)
    @param sBluetoothAddress Bluetooth address of tested STH
    @param tEepromPage Which Eeprom Page to write
    @param sEntry Which page entry to be set
    @param sSet Entry value to be set
    """

    def vTestSthEepromService(self, sBluetoothAddress, tEepromPage, sEntry, sSet):    
        if tEepromPage is Eeprom.uProductData:
            sTable = "SthServiceTestsProductData" 
        elif tEepromPage is Eeprom.uStatistics:   
            sTable = "SthServiceTestsStatistics" 
        else:
            raise Exception
        sTable = sTable + sEntry
        bEntry = self.bTableEntryExists(sTable, self.sSetDateTime)
        if False == bEntry:
            sVariables = "BlueToothAddress, dateTime, Data"
            sArg = "%s, %s, %s"
            sInit = ["", "", "0"]
            sInit[0] = sBluetoothAddress
            sInit[1] = self.sDateTime
            self.vTableInsert(sTable, sVariables, sArg, tuple(sInit))
        self.vTableUpdate(sTable, self.sSetDateTime, sSet)            
    
            
    """
    Use this to file a single STH test page entry.
    @param iTestStage Which test run (PCB, assembled or potted)
    @param sTest Which test
    @param sBluetoothAddress Bluetooth address of tested STH
    @param tEepromPage Which Eeprom Page to write
    @param sEntry Which page entry to be set
    @param sValue Value to be set
    """

    def vTestSthEeprom(self, iTestStage, sBluetoothAddress, tEepromPage, sEntry, Value):
        sSetValue = None
        if type(Value) is bool:
            if False != Value:
                sSetValue = "1"
            else:
                sSetValue = "0"
        elif type(Value) is str:
            sSetValue = "'" + Value + "'"
        else:  # Please note that there are other data types. However, if not used...
            sSetValue = "'" + str(Value) + "'"
        sSet = "data = " + sSetValue
        if iTestStage <= TestDefSth.uProductionPotted:
            self.vTestSthEepromProduction(iTestStage, sBluetoothAddress, tEepromPage, sEntry, sSet)
        else:
            self.vTestSthEepromService(sBluetoothAddress, tEepromPage, sEntry, sSet)
       
    """
    Use this to get a specific single data base entry for a STH production test limit.
    @param iTestStage Which test run (PCB, assembled or potted)
    @param sTest Which test
    @param sBluetoothAddress Bluetooth address of tested STH
    @param sColumn Variable to set
    @param sValue Value to be set
    """

    def tProductionTestSthLimit(self, iTestStage, sTest, sProductKey, sColumn):
        if TestDefSth.uService == iTestStage:
            iTestStage = TestDefSth.uProductionPotted
        sTable = "SthTestLimits" + str(iTestStage) + sTest
        sKey = "ProductKey = '" + sProductKey + "'"
        tLimit = self.tTableSelect(sTable, sKey, sColumn)
        tLimit = tLimit[0][0]
        return tLimit

    """
    Use this to set the overall test result of a single test stage
    @param iTestStage Which test run (PCB, assembled or potted)
    @param sBluetoothAddress Bluetooth address of tested STH
    @param bOk Ok(True) or Nok(False)
    @return Nothing
    """

    def vProductionTestSthResultRunStage(self, iTestStage, sBlueToothAddress, bOk):
        if TestDefSth.uProductionPotted >= iTestStage:
            sTable = "SthProductionTestStageResult" + str(iTestStage)      
            sVariables = "BlueToothAddress, dateTime, result"
            sArg = "%s, %s, %s"
            if False != bOk:
                sSetValue = [sBlueToothAddress, self.sDateTime, "1"]
                sSet = "result = 1"
            else:
                sSetValue = [sBlueToothAddress, self.sDateTime, "0"]
                sSet = "result = 0"
            sEntry = "BlueToothAddress = '" + sBlueToothAddress + "'"
            if False != self.bTableEntryExists(sTable, sEntry):
                self.vTableUpdate(sTable, sEntry, sSet)
            else:    
                self.vTableInsert(sTable, sVariables, sArg, tuple(sSetValue))

    """
    Use this to determine the test result over all production test stages. This also
    sets the table entry for to overall test result iff all test stage results
    has been set.
    @param sBluetoothAddress Bluetooth address of tested STH
    @param bOk Ok(True) or Nok(False)
    @return Nothing
    """

    def bTestSthResultOverallProduction(self, sBlueToothAddress):        
        bOk = False
        sEntry = "BlueToothAddress = '" + sBlueToothAddress + "'"
        for iTestStage in range(0, ConstantsSth.uProductionTestTotalTestRuns):
            sTable = "SthProductionTestStageResult" + str(iTestStage) 
            if(False != self.bTableEntryExists(sTable, sEntry)):
                tLimit = self.tTableSelect(sTable, sEntry, "result")
                bOk = bool(tLimit[0][0])     
                if False != bOk:
                    sSetValue = [sBlueToothAddress, self.sDateTime, "1"]
                    sSet = "result = '1'"
                else:
                    sSetValue = [sBlueToothAddress, self.sDateTime, "0"]
                    sSet = "result = '0'"             
                if False != self.bTableEntryExists(sTable, sEntry):
                    self.vTableUpdate(sTable, sEntry, sSet)
                else:    
                    sVariables = "BlueToothAddress, dateTime, result"
                    sArg = "%s, %s, %s"
                    self.vTableInsert(sTable, sVariables, sArg, tuple(sSetValue))
        return bOk

    """
    Use this to determine the test result over all service tests. This also
    sets the table entry for to overall test result iff all service tests results
    has been set.
    @param sBluetoothAddress Bluetooth address of tested STH
    @param bOk Ok(True) or Nok(False)
    @return Nothing
    """

    def bTestSthResultOverallService(self, sBlueToothAddress, bOk):                     
        sTable = "SthServiceTestResultOverall"   
        sVariables = "BlueToothAddress, dateTime, result"
        sArg = "%s, %s, %s"
        if False != bOk:
            sSetValue = [sBlueToothAddress, self.sDateTime, "1"]
            sSet = "result = 1"
        else:
            sSetValue = [sBlueToothAddress, self.sDateTime, "0"]
            sSet = "result = 0"
        sEntry = "BlueToothAddress = '" + sBlueToothAddress + "'"
        if False != self.bTableEntryExists(sTable, sEntry):
            self.vTableUpdate(sTable, sEntry, sSet)
        else:    
            self.vTableInsert(sTable, sVariables, sArg, tuple(sSetValue))               
               
    """
    Use this to determine the test result over the actual test stage and over
    all test stages. This also sets the table entry for to overall test result 
    iff all test stage results has been set.
    @param iTestStage Which test run (PCB, assembled or potted)
    @param sBluetoothAddress Bluetooth address of tested STH
    @param bOk Ok(True) or Nok(False)
    @return Nothing
    """

    def bTestSthResultOverall(self, iTestStage, sBlueToothAddress, bOk):        
        bReturn = False
        if TestDefSth.uProductionPotted >= iTestStage:
            self.vProductionTestSthResultRunStage(iTestStage, sBlueToothAddress, bOk)
            bReturn = self.bTestSthResultOverallProduction(sBlueToothAddress)
        else:
            bReturn = self.bTestSthResultOverallService(sBlueToothAddress, bOk)
        return bReturn

    """
    Use this to create all result tables for the STU.
    @param sProductionTest Name of the production test
    """

    def vProductionTestStuTablesResults(self, sProductionTest):
        sTable = "StuProductionTests" + sProductionTest
        if False == self.bTableExists(sTable):
            self.vTableCreate(sTable, asProductionTableVariableDefStuList[sProductionTest])
             
    """
    Use this to create all result tables for the STU.
    @param sProductionTest Name of the production test
    """

    def vServiceTestStuTablesResults(self, sProductionTest):
        sTable = "StuServiceTests" + sProductionTest
        if False == self.bTableExists(sTable):
            self.vTableCreate(sTable, asProductionTableVariableDefStuList[sProductionTest])            

    """
    Use this to create all limit tables for the STU and set all parameters as well
    @param sProductionTest Name of the production test
    """
    def vStuTablesLimits(self, sProductionTest):
        sDefLimits = "ProductKey VARCHAR(255), Limit0 VARCHAR(255), Limit1 VARCHAR(255), Limit2 VARCHAR(255), Limit3 VARCHAR(255), Limit4 VARCHAR(255), Limit5 VARCHAR(255), Limit6 VARCHAR(255), Limit7 VARCHAR(255), Limit8 VARCHAR(255)"
        sTable = "StuTestLimits" + sProductionTest 
        if False == self.bTableExists(sTable):
            self.vTableCreate(sTable, sDefLimits)
        for sKey in asProductionLimitsStuList:
            atLimit = asProductionLimitsStuList[sKey][ConstantsStu.uProductionTestLimitTable][sProductionTest]
            sEntry = "ProductKey = '" + sKey + "'"
            if False != self.bTableEntryExists(sTable, sEntry):
                for i in range(0, len(atLimit)):
                    sSet = "Limit" + str(i) + " = '" + atLimit[i] + "'"
                    self.vTableUpdate(sTable, sEntry, sSet)
            else:
                atLimit = [sKey] + atLimit
                self.vTableInsert(sTable, "ProductKey, Limit0, Limit1, Limit2, Limit3, Limit4, Limit5, Limit6, Limit7, Limit8", "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s", tuple(atLimit))

    """
    Use this to create Product Data Tables i.e. store content of EEPROM
    @param iTestStage Test Stage the is part of the table names (that are created here)
    @param sProductionTest Name of the production test
    """

    def vProductionTestStuTablesProductData(self, sProductData):
        sTable = "StuProductionTestsProductData" + sProductData
        if False == self.bTableExists(sTable):
            self.vTableCreate(sTable, "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), Data VARCHAR(1023)")
            
    """
    Use this to create Service Data Tables i.e. store content of EEPROM
    @param iTestStage Test Stage the is part of the table names (that are created here)
    @param sProductionTest Name of the production test
    """

    def vServiceTestStuTablesProductData(self, sProductData):
        sTable = "StuServiceTestsProductData" + sProductData
        if False == self.bTableExists(sTable):
            self.vTableCreate(sTable, "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), Data VARCHAR(1023)")
            
    """
    Use this to create Product Data Tables i.e. store content of EEPROM
    @param iTestStage Test Stage the is part of the table names (that are created here)
    @param sProductionTest Name of the production test
    """

    def vProductionTestStuTablesStatistics(self, sProductData):
        sTable = "StuProductionTestsStatistics" + sProductData
        if False == self.bTableExists(sTable):
            self.vTableCreate(sTable, "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), Data VARCHAR(255)")

    """
    Use this to create Product Data Tables i.e. store content of EEPROM
    @param iTestStage Test Stage the is part of the table names (that are created here)
    @param sProductionTest Name of the production test
    """

    def vServiceTestStuTablesStatistics(self, sProductData):
        sTable = "StuServiceTestsStatistics" + sProductData
        if False == self.bTableExists(sTable):
            self.vTableCreate(sTable, "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), Data VARCHAR(255)")
            
    """
    This creates the production test tables
    """

    def vStuTablesProduction(self):
        for i in range(0, len(asTestTableStuList)):
            sProductionTest = asTestTableStuList[i]
            self.vProductionTestStuTablesResults(sProductionTest)
            sProductData = asProductData[i] 
            self.vProductionTestStuTablesProductData(sProductData)   
            sStatistics = asStatistics[i]
            self.vProductionTestStuTablesStatistics(sStatistics)
        sTable = "StuProductionTestResultOverall"
        if False == self.bTableExists(sTable):
            self.vTableCreate(sTable, "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), result boolean DEFAULT false")        
        
    """
    This creates the service test tables
    """

    def vStuTablesService(self):
        for i in range(0, len(asTestTableStuList)):
            sServiceTest = asTestTableStuList[i]
            self.vServiceTestStuTablesResults(sServiceTest)
            sServiceTest = asProductData[i] 
            self.vServiceTestStuTablesProductData(sServiceTest) 
            sStatistics = asStatistics[i]
            self.vServiceTestStuTablesStatistics(sStatistics)
        sTable = "StuServiceTestResultOverall"
        if False == self.bTableExists(sTable):
            self.vTableCreate(sTable, "BlueToothAddress VARCHAR(18), dateTime VARCHAR(255), result boolean DEFAULT false") 
                
    """
    This creates the limit tables for the STU. Please note that the
    production limit are equally to the service limits.
    """

    def vStuTablesOverallLimits(self):
        for i in range(0, len(asTestTableStuList)):
            sProductionTest = asTestTableStuList[i]
            self.vStuTablesLimits(sProductionTest)


                                      
    """
    Use this to create all STU tables if not created
    (STU production and service STU test)
    """

    def vStuTables(self):
        self.vStuTablesProduction()
        self.vStuTablesService()
        self.vStuTablesOverallLimits()

    """
    Create entries for all production test case tables
    @param sBlueToothAddress STU Address
    @param iTestStage Test Stage
    """

    def vProductionTestStuEntryTestCases(self, sBlueToothAddress):
        sEntry = "BlueToothAddress = '" + sBlueToothAddress + "'"
        for iTable in range(0, len(asTestTableStuList)):
            sTest = asTestTableStuList[iTable]
            sTable = "StuProductionTests" + sTest
            bEntry = self.bTableEntryExists(sTable, sEntry)
            if False == bEntry:  
                atEntry = asProductionTableVariableInitStuList[sTest]    
                sVariables = atEntry[0]   
                sArg = atEntry[1] 
                atInit = atEntry[2]  
                atInit[0] = sBlueToothAddress   
                self.vTableInsert(sTable, sVariables, sArg, tuple(atInit))

                
    """
    Create service test case entry
    @param sBlueToothAddress STU Address
    @param iTestStage Test Stage
    """

    def vServiceTestStuEntryTestCases(self, sTest, sBlueToothAddress):
        sTable = "StuServiceTests" + sTest
        bEntry = self.bTableEntryExists(sTable, self.sSetDateTime)
        if False == bEntry:  
            atEntry = asProductionTableVariableInitStuList[sTest]    
            sVariables = atEntry[0]   
            sArg = atEntry[1] 
            atInit = atEntry[2]  
            atInit[0] = sBlueToothAddress   
            atInit[1] = self.sDateTime 
            self.vTableInsert(sTable, sVariables, sArg, tuple(atInit))

    """
    Create entries for all product data tables
    @param sBlueToothAddress STU Address
    @param iTestStage Test Stage
    """

    def vProductionTestStuEepromProductData(self, sBlueToothAddress):
        sEntry = "BlueToothAddress = '" + sBlueToothAddress + "'"
        for iTable in range(0, len(asProductData)):
            sProductDataEntry = asProductData[iTable]
            sTable = "StuProductionTestsProductData" + sProductDataEntry
            bEntry = self.bTableEntryExists(sTable, sEntry)
            if False == bEntry:  
                sVariables = "BlueToothAddress, dateTime, data"
                sArg = "%s, %s, %s"
                atInit = ["", self.sDateTime, "0"]
                atInit[0] = sBlueToothAddress
                self.vTableInsert(sTable, sVariables, sArg, tuple(atInit))
 
    """
    Create entries for all STU EEPROM statistics tables
    @param sBlueToothAddress STU Address
    """

    def vProductionTestStuEntryStatistics(self, sBlueToothAddress):
        sEntry = "BlueToothAddress = '" + sBlueToothAddress + "'"
        for iTable in range(0, len(asStatistics)):
            sTest = asStatistics[iTable]
            sTable = "StuProductionTestsStatistics" + sTest
            bEntry = self.bTableEntryExists(sTable, sEntry)
            if False == bEntry:  
                sVariables = "BlueToothAddress, dateTime, data"
                sArg = "%s, %s, %s"
                atInit = ["", self.sDateTime, "0"]
                atInit[0] = sBlueToothAddress
                self.vTableInsert(sTable, sVariables, sArg, tuple(atInit))                     
        
    """
    Use this to create a new DB entry for a production test (run).
    Please, note that the same STU may be tested multiple times in a same way e.g.
    Forgot to power on the test STU. Moreover, there are multiple runs for
    each STU 
    @param sBlueToothAddress STU Address
    @param iTestStage Service or Production
    """

    def vProductionTestStuEntry(self, sBlueToothAddress, iTestStage):
        if TestDefStu.uProduction >= iTestStage:
            self.vProductionTestStuEntryTestCases(sBlueToothAddress)
            self.vProductionTestStuEepromProductData(sBlueToothAddress)
            self.vProductionTestStuEntryStatistics(sBlueToothAddress)
     
    """
    Putting service Test Results into Table
    @param sTest Which Test to insert
    @param sBluetoothAddress Bluetooth MAC address of device
    @param sSet Set
    """

    def vProductionTestStuResultService(self, sTest, sBluetoothAddress, sSet):
        sTable = "StuServiceTests" + sTest
        self.vServiceTestStuEntryTestCases(sTest, sBluetoothAddress)
        self.vTableUpdate(sTable, self.sSetDateTime, sSet)
                            
    """
    Use this to file a single STU test results.
    @param iTestStage Serivce or Production Test
    @param sTest Which test
    @param sBluetoothAddress Bluetooth address of tested STU
    @param sColumn Variable to set
    @param sValue Value to be set
    """

    def vProductionTestStuResult(self, iTestStage, sTest, sBluetoothAddress, sColumn, Value):
        sSetValue = None
        if type(Value) is bool:
            if False != Value:
                sSetValue = "1"
            else:
                sSetValue = "0"
        elif type(Value) is str:
            sSetValue = "'" + Value + "'"
        else:  # Please note that there are other data types. However, if not used...
            sSetValue = "'" + str(Value) + "'"
        sSet = sColumn + " = " + sSetValue
        sKey = "BlueToothAddress = '" + sBluetoothAddress + "'"
        if TestDefStu.uProduction >= iTestStage:
            sTable = "StuProductionTests" + sTest
            self.vTableUpdate(sTable, sKey, sSet)
            self.vTableUpdate(sTable, sKey, self.sSetDateTime)
        elif TestDefStu.uService == iTestStage:            
            self.vProductionTestStuResultService(sTest, sBluetoothAddress, sSet)
        else:
            raise
    
    """
    Use this to file a single STU production test stage EEPROM page entry.
    @param sBluetoothAddress Bluetooth address of tested STU
    @param tEepromPage Which Eeprom Page to write
    @param sEntry Which page entry to be set
    @param sSet Entry value to be set
    """

    def vTestStuEepromProduction(self, sBluetoothAddress, tEepromPage, sEntry, sSet):    
        if tEepromPage is Eeprom.uProductData:
            sTable = "StuProductionTestsProductData" 
        elif tEepromPage is Eeprom.uStatistics:   
            sTable = "StuProductionTestsStatistics" 
        else:
            raise Exception
        sTable = sTable + sEntry
        sKey = "BlueToothAddress = '" + sBluetoothAddress + "'"
        self.vTableUpdate(sTable, sKey, sSet)    

    """
    Use this to file a single STU production test stage EEPROM page entry.
    @param sBluetoothAddress Bluetooth address of tested STU
    @param tEepromPage Which Eeprom Page to write
    @param sEntry Which page entry to be set
    @param sSet Entry value to be set
    """

    def vTestStuEepromService(self, sBluetoothAddress, tEepromPage, sEntry, sSet):    
        if tEepromPage is Eeprom.uProductData:
            sTable = "StuServiceTestsProductData" 
        elif tEepromPage is Eeprom.uStatistics:   
            sTable = "StuServiceTestsStatistics" 
        else:
            raise Exception
        sTable = sTable + sEntry
        bEntry = self.bTableEntryExists(sTable, self.sSetDateTime)
        if False == bEntry:
            sVariables = "BlueToothAddress, dateTime, Data"
            sArg = "%s, %s, %s"
            sInit = ["", "", "0"]
            sInit[0] = sBluetoothAddress
            sInit[1] = self.sDateTime
            self.vTableInsert(sTable, sVariables, sArg, tuple(sInit))
        self.vTableUpdate(sTable, self.sSetDateTime, sSet)            
            
    """
    Use this to file a single STU test page entry.
    @param iTestStage Service or production test
    @param sTest Which test
    @param sBluetoothAddress Bluetooth address of tested STU
    @param tEepromPage Which Eeprom Page to write
    @param sEntry Which page entry to be set
    @param sValue Value to be set
    """

    def vTestStuEeprom(self, iTestStage, sBluetoothAddress, tEepromPage, sEntry, Value):
        sSetValue = None
        if type(Value) is bool:
            if False != Value:
                sSetValue = "1"
            else:
                sSetValue = "0"
        elif type(Value) is str:
            sSetValue = "'" + Value + "'"
        else:  # Please note that there are other data types. However, if not used...
            sSetValue = "'" + str(Value) + "'"
        sSet = "data = " + sSetValue
        if iTestStage <= TestDefStu.uProduction:
            self.vTestStuEepromProduction(sBluetoothAddress, tEepromPage, sEntry, sSet)
        else:
            self.vTestStuEepromService(sBluetoothAddress, tEepromPage, sEntry, sSet)
       
    """
    Use this to get a specific single data base entry for a STU production test limit.
    @param sTest Which test
    @param sBluetoothAddress Bluetooth address of tested STU
    @param sColumn Variable to set
    @param sValue Value to be set
    """

    def tProductionTestStuLimit(self, sTest, sProductKey, sColumn):
        sTable = "StuTestLimits" + sTest
        sKey = "ProductKey = '" + sProductKey + "'"
        tLimit = self.tTableSelect(sTable, sKey, sColumn)
        tLimit = tLimit[0][0]
        return tLimit

    """
    Use this to determine the test result over all production test stages. This also
    sets the table entry for to overall test result iff all test stage results
    has been set.
    @param sBluetoothAddress Bluetooth address of tested STU
    @param bOk Ok(True) or Nok(False)
    @return Nothing
    """

    def bTestStuResultOverallProduction(self, sBlueToothAddress, bOk):        
        sEntry = "BlueToothAddress = '" + sBlueToothAddress + "'"
        sTable = "StuProductionTestResultOverall"     
        if False != bOk:
            sSetValue = [sBlueToothAddress, self.sDateTime, "1"]
            sSet = "result = '1'"
        else:
            sSetValue = [sBlueToothAddress, self.sDateTime, "0"]
            sSet = "result = '0'"             
        if False != self.bTableEntryExists(sTable, sEntry):
            self.vTableUpdate(sTable, sEntry, sSet)
        else:    
            sVariables = "BlueToothAddress, dateTime, result"
            sArg = "%s, %s, %s"
            self.vTableInsert(sTable, sVariables, sArg, tuple(sSetValue))
        return bOk

    """
    Use this to determine the test result over all service tests. This also
    sets the table entry for to overall test result iff all service tests results
    has been set.
    @param sBluetoothAddress Bluetooth address of tested STU
    @param bOk Ok(True) or Nok(False)
    @return Nothing
    """

    def bTestStuResultOverallService(self, sBlueToothAddress, bOk):                     
        sTable = "StuServiceTestResultOverall"   
        sVariables = "BlueToothAddress, dateTime, result"
        sArg = "%s, %s, %s"
        if False != bOk:
            sSetValue = [sBlueToothAddress, self.sDateTime, "1"]
            sSet = "result = 1"
        else:
            sSetValue = [sBlueToothAddress, self.sDateTime, "0"]
            sSet = "result = 0"
        sEntry = "BlueToothAddress = '" + sBlueToothAddress + "'"
        if False != self.bTableEntryExists(sTable, sEntry):
            self.vTableUpdate(sTable, sEntry, sSet)
        else:    
            self.vTableInsert(sTable, sVariables, sArg, tuple(sSetValue))               
               
    """
    Use this to determine the test result over all test stages. This also sets 
    the table entry for to overall test result 
    iff all test stage results has been set.
    @param iTestStage Which test run (PCB, assembled or potted)
    @param sBluetoothAddress Bluetooth address of tested STU
    @param bOk Ok(True) or Nok(False)
    @return Nothing
    """

    def bTestStuResultOverall(self, iTestStage, sBlueToothAddress, bOk):        
        bReturn = False
        if TestDefStu.uProduction >= iTestStage:
            bReturn = self.bTestStuResultOverallProduction(sBlueToothAddress, bOk)
        else:
            bReturn = self.bTestStuResultOverallService(sBlueToothAddress, bOk)
        return bReturn
        
            
if __name__ == "__main__":
    #mdb = MyToolItDb("localhost", "root", "MRh12JG&is", "icoTronic")
    mdb = MyToolItDb("localhost", "root", "icotronic", "icoTronic") # (sHost, sUser, sPassWord, sDataBase):
    mdb.vTablesCreate()
    mdb.vShowDataBases()
