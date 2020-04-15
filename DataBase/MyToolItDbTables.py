import mysql.connector
from MyToolItDbTablesList import asTestTableSthList, asProductionTableVariableDefSthList



"""
This class handles all tables from all MyToolItDatabases.
Use this to create tables or include tables from other files.
This class also connects to the MySqlDataBase
    @param sHost Which host e.g. localhost or any IP address
    @param sUser User Name for login
    @param sPassword Password for user
    @param sDataBase Which data base should be used
"""

class MyToolItDbTables():
    def __init__(self, sHost, sUser, sPassWord, sDataBase):
        self.tMyDb = mysql.connector.connect(host=sHost, user=sUser, 
        passwd=sPassWord, database=sDataBase)
        self.tMyCursor = self.tMyDb.cursor()
        self.tMyCursor.execute("CREATE DATABASE IF NOT EXISTS IcoTronic")
        self.tMyDb.commit()

        
    """
    Use this to create any table
    @param sTable Which table
    @param sVariable Variables for creation
    """
    def vTableCreate(self, sTable, sVariables):
        sCmd = "CREATE TABLE IF NOT EXISTS " + sTable + "(id INT AUTO_INCREMENT PRIMARY KEY, " + sVariables + ")"
        try:
            self.tMyCursor.execute(sCmd)  
        except:
            self.tMyCursor.fetchall()   
            self.tMyCursor.execute(sCmd)       
        self.tMyDb.commit()

    """
    Select some column 
    @param sTable Which table
    @param sSelect Variables to select 
    @param sKey Which key to select
    @return Column Value
    """    
    def tTableSelect(self, sTable, sKey, sRowSelect):     
        sCmd = "SELECT " + sRowSelect  + " FROM " + sTable + " WHERE " + sKey  
        self.tMyCursor.execute(sCmd)   
        tColumn = self.tMyCursor.fetchall()             
        return tColumn   
 


    """
    Check if Table exits
    @param sTable Which table
    @return Column Value
    """    
    def bTableExists(self, sTable):     
        sCmd = "SELECT * FROM " + sTable
        try:
            self.tMyCursor.execute(sCmd) 
            tMyResult = self.tMyCursor.fetchone()    # However, just to be sure to empty any cue 
            bExits = True
        except:
            bExits = False        
        return bExits
    
    """
    Check if entry exists for a single Table
    @param sTable Which Table
    @param sEntry Which entry to be checked
    """
    def bTableEntryExists(self, sTable, sEntry):       
        sCmd = "SELECT * FROM " + sTable + " WHERE " + sEntry
        try:
            self.tMyCursor.execute(sCmd)
            tMyResult = self.tMyCursor.fetchall()
        except:
            self.tMyCursor.fetchall()
            self.tMyCursor.execute(sCmd)
            tMyResult = self.tMyCursor.fetchall()
        bResult = [] != tMyResult
        return bResult
    
    """
    Use this to update already existing records
    @param sTable Table Name
    @param sSet What should be set
    @param sKey By which key entry should be set
    """              
    def vTableUpdate(self, sTable, sKey, sSet):
        sCmd = "UPDATE " + sTable + " SET " + sSet + " WHERE "  + sKey
        self.tMyCursor.execute(sCmd) 
        self.tMyDb.commit()       
        
    """
    Insert an entry into a table
    @param sTable Table Name
    @param sVariablesName Variables to insert
    @param sVariablesType which type of value
    @param tVariableValue Values 
    """    
    def vTableInsert(self, sTable, sVariablesName, sVariablesType, tVariableValue):
        sCmd = "INSERT INTO " + sTable + " (" + sVariablesName + ") VALUES (" + sVariablesType + ")"
        self.tMyCursor.execute(sCmd, tVariableValue)
        self.tMyDb.commit()        
        
    """
    Create Production Test Result Tables for the STH
    """
    def vTablesCreateProductionTestsSth(self):    
        for iNr in range(0, 3):  
            for iTableNr in range(0, len(asTestTableSthList)):
                self.vTableCreate("SthProductionTests" + str(iNr) + asTestTableSthList[iTableNr], asProductionTableVariableDefSthList[iTableNr])
                                                     
        
    """
    Use this to create all tables.
    """       
    def vTablesCreate(self):
        self.vTablesCreateProductionTests()
        self.vTablesCreateProductionTestsLimits()
        
        
