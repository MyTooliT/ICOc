 _______________________________________________________________________________________________________________________________________________
|																		|
|					MyToolItWatch - MyToolItWatchTerminal - MyToolItTestFrameWork						|	
|_______________________________________________________________________________________________________________________________________________|


This Framework supports the following integral parts:
	* MyToolIt Protocol: Protocol to communcate via Bluetooth and CAN. Prepared for CAN-FD too. 
			     Extendable for other Logical Link Layer protocols
	* MyToolIt PeakCanFd driver: Driver to interact via Peak CAN with CAN20. Prepared for CAN-FD.
	* MyToolIt Production Tests: Production tests for quality management.
	* MyToolIt Verfication: Verifications for Firmware and Hardware. 
	* MyToolItWatch: Supports high level MyToolIt functionallity. May be integrated in alien frame works and/or software
	* MyToolItTerminal: Terminal program that supports MyToolItWatch functionality

This frame work runs under Microsoft Windows 10 and supports its features via console (Mircosoft Command Promt) and Liclipse. Liclipse (Version 5.1.3.201811082122)
is an integrated development environment (IDE) and may be used to access the MyToolIt Test functionalities. Furthermore, Python 3.5 and 
additional Python Modules are requiered to support the frame work functionallities.

 _______________________________________
|			       		|
| 	IcoTronic System	   	|
|_______________________________________|
TODO

 _______________________________________
|			       		|
| 	Technical Requirements    	|
|_______________________________________|
Simplicity Commander...
Todo

 _______________________________________
|			       		|
| 	Image Locations		    	|
|_______________________________________|

 _______________________________________
|			       		|
|	Production Tests       		|
|_______________________________________|

Any production Test may be called multiple times for the same STH/STU (PCB). Furthermore, the test results are stored by the Bluetooth Address and a consecutively run number (file name). Thus a
PCBs, aassemled STH/STU and a potted STH may be tested in a row.

The Production Tests are supported via:
	* ProductionTests/Sth.py: Tests Sensory Tool Holder (STH) and STH print circuit boards (PCBs).
	* ProductionTests/Stu.py: Tests Stationary Transceiver Unit(STU) and STU PCBs.
Moreover, the parameters may/must be changed inside the script if it runs via Liclipse and this is fullfilled via changing:
	* sVersion = "v2.1.9" -> Related STH/STU Firmware Version.
	* sLogName = 'ProductionTestStX' -> Related logFile.txt (X=U for STU or H for STH)
	* sLogLocation = '../../Logs/ProductionTestStX/' -> Where the archieve logs and test protocol (X=U for STU or H for STH)
	* sOtaComPort = 'COM6' ->  COM-Port of the Over-The-Air (OTA) programming board (Assembled with BGM111 module). Please, refer to chapter Over-The-Air (OTA) update.
	* sBuildLocation = "../../SimplicityStudio/v4_workspace/STH/builds/" -> Location of the firmware builds, manufacturing images and the OTA Files. Please refer to the chapter 
	  Image Locations.
	* sSilabsCommanderLocation = "../../SimplicityStudio/SimplicityCommander/" -> Location of the Simplicity Command. Please refer to Technical Requirements.
	* sAdapterSerialNo = "440115849" The number of the programming board. Please refer to the chapter technical requirements.
	* sBoardType = "BGM113A256V2" -> Model Name of the assembled µC. Please refer to the chapter Icotronic system. 
	* iSensorAxis = 1 -> STH only... 3 axis sensor or single axis sensor.
	* bPcbOnly = True Testing PCB or assembled STH/STU or potted STH
	* bBatteryExternalDcDc = True -> USB is connected to the 3V3 rail or connects to the DC/DC converted and the DC/DC converter supplies the 3V3 rail.

To run this via command prompt dir to the location of the procution test scripts. The production test scripts are located in the ProductionTests subfolder in 
MyToolItWatch install directory. Furthermore, the scrips may be called via:
	1. Opening a command prompt
	2. Navigate to mytoolitwatch/ProductionTests (cd ..\mytoolitwatch\ProductionTests
	3. Type "python Sth.py loglocation temporaryLogName VERSION e.g. python Sth.py ../../Logs/ProductionTestSth/ LogsSth.txt v2.1.10
	   or type python Stu.py LogLocation temporaryLogName VERSION e.g. python Stu.py ../../Logs/ProductionTestStu/ LogsStu.txt v2.1.9
	4. The console prints any negative result or nothing it the test was OK. Moreover, the logs as well as a test protocol are achieved in the 
	   log location.
Additionally, the production test may be called via Licpse. Liclipse supports complete test runs, single test runs or partially test runs. Test Runs may be called 
via opening the corresponding production Test script (Open directory in Liclipse and double click on the file):
	* mytoolitwatch\ProductionTests\Stu.py (STU production test), pressing CTRL + F9 (STRG + F9), selecting TestStu or any single test case or selecting partial test case and pressing ENTER.
	* mytoolitwatch\ProductionTests\Sth.py (STH production test), pressing CTRL + F9 (STRG + F9), selecting TestSth or any single test case or selecting partial test case and pressing ENTER.
Furthermore, Liclipse prints any negative result or nothing it the test was OK. Moreover, the logs as well as a test protocol are achieved in the 
	  log location. 

 _______________________________________
|			       		|
|	Over-The-Air (OTA) - Update     |
|_______________________________________|


	

