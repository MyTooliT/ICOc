from MyToolItCommands import AdcAcquisitionTime, AdcOverSamplingRate, AdcReference, calcSamplingRate, AdcMax



class SthLimits():

    def __init__(self, iAccSensorAxis, bConnectedBattery, uAccelerationToAccGravitity, iRssiMin, iTemperatureInternalMin, iTemperatureInternalMax):
        self.vBatteryParameters(bConnectedBattery)
        self.vAccParameters(iAccSensorAxis, uAccelerationToAccGravitity)
        self.vSamplingRate()
        self.vRssiSthMin(iRssiMin) 
        self.vStreaming()
        self.vVoltageRaw()
        self.vTemperature(iTemperatureInternalMin, iTemperatureInternalMax)
        
        
    def vBatteryParameters(self, bConnectedBattery):
        if False != bConnectedBattery:
            self.uBatteryMiddle = 3.9
            self.uBatteryQ1 = 8000         
            self.uBatteryQ25 = 9000       
            self.uBatteryMedL = 10000        
            self.uBatteryMedH = 12000    
            self.uBatteryQ75 = 13000     
            self.uBatteryQ99 = 14000     
            self.uBatteryVar = 40000     
            self.uBatterySkewness = 20   
            self.uBatterySNR = 60 
            self.uBatteryMiddleRaw = 11000 
            self.uBatteryToleranceRaw = 300
        else:
            self.uBatteryMiddle = 0.15
            self.uBatteryQ1 = 600         
            self.uBatteryQ25 = 630       
            self.uBatteryMedL = 633        
            self.uBatteryMedH = 670    
            self.uBatteryQ75 = 680     
            self.uBatteryQ99 = 710     
            self.uBatteryVar = 40000     
            self.uBatterySkewness = 20   
            self.uBatteryMiddleRaw = 60 
            self.VoltRawMiddleBat = 700 
            self.uBatteryToleranceRaw = 200
        self.uBatteryTolerance = 0.3      
        self.iBatteryK = (57 * 3.3) / (10 * 2 ** 16)
        
    def vAccParameters(self, iAccSensorAxis, uAccelerationToAccGravitity):
        self.uAccelerationToAccGravitity = uAccelerationToAccGravitity
        self.iAdcAccXMiddle = 0
        self.iAdcAccYMiddle = 0
        self.iAdcAccZMiddle = 0
        self.iAdcAccXTolerance = 3
        self.iAdcAccXRawMiddle = 2 ** 15
        self.iAdcAccXRawTolerance = 2048
        self.uAccXQ1 = 2 ** 15 * 0.95
        self.uAccXQ25 = 2 ** 15 * 0.955
        self.uAccXMedL = 2 ** 15 * 0.97
        self.uAccXMedH = 2 ** 15 * 1.03
        self.uAccXQ75 = 2 ** 15 * 1.045
        self.uAccXQ99 = 2 ** 15 * 1.05
        self.uAccXVar = 2000
        self.uAccXSkewness = 0.9
        self.uAccXSNR = 60
        if 1 == iAccSensorAxis:
            self.iAdcAccYTolerance = 200
            self.iAdcAccZTolerance = 200
            self.iAdcAccYRawMiddle = 0
            self.iAdcAccZRawMiddle = 0
            self.iAdcAccYRawTolerance = 54000
            self.iAdcAccZRawTolerance = 54000
            self.uAccYQ1 = 0
            self.uAccYQ25 = 1
            self.uAccYMedL = 2
            self.uAccYMedH = 2 ** 16 - 3
            self.uAccYQ75 = 2 ** 16 - 2
            self.uAccYQ99 = 2 ** 16 - 1
            self.uAccYVar = 40000
            self.uAccYSkewness = 20
            self.uAccYSNR = 60
            self.uAccZQ1 = 0
            self.uAccZQ25 = 1
            self.uAccZMedL = 2
            self.uAccZMedH = 2 ** 16 - 3
            self.uAccZQ75 = 2 ** 16 - 2
            self.uAccZQ99 = 2 ** 16 - 1
            self.uAccZVar = 40000
            self.uAccZSkewness = 20
            self.uAccZSNR = 60
        else:
            self.iAdcAccYTolerance = 3
            self.iAdcAccZTolerance = 3
            self.iAdcAccYRawMiddle = 2 ** 15
            self.iAdcAccZRawMiddle = 2 ** 15
            self.iAdcAccYRawTolerance = 2048
            self.iAdcAccZRawTolerance = 2048    
            self.uAccYQ1 = 2 ** 15 * 0.95
            self.uAccYQ25 = 2 ** 15 * 0.955
            self.uAccYMedL = 2 ** 15 * 0.97
            self.uAccYMedH = 2 ** 15 * 1.03
            self.uAccYQ75 = 2 ** 15 * 1.045
            self.uAccYQ99 = 2 ** 15 * 1.05
            self.uAccYVar = 2000
            self.uAccYSkewness = 0.9
            self.uAccYSNR = 60
            self.uAccZQ1 = 2 ** 15 * 0.95
            self.uAccZQ25 = 2 ** 15 * 0.955
            self.uAccZMedL = 2 ** 15 * 0.97
            self.uAccZMedH = 2 ** 15 * 1.03
            self.uAccZQ75 = 2 ** 15 * 1.045
            self.uAccZQ99 = 2 ** 15 * 1.05
            self.uAccZVar = 2000
            self.uAccZSkewness = 0.9
            self.uAccZSNR = 60        
        self.iSelfTestOutputChangemVMin = 70
        self.iSelfTestOutputChangemVTyp = 170
        self.iAccX_K = self.uAccelerationToAccGravitity / (2 ** 16 - 1)
        self.iAccX_D = -(self.uAccelerationToAccGravitity/2)
        
    def auAccXStatistics(self):
        return [self.uAccXQ1, self.uAccXQ25, self.uAccXMedL, self.uAccXMedH, self.uAccXQ75, self.uAccXQ99]

    def auAccYStatistics(self):
        return [self.uAccYQ1, self.uAccYQ25, self.uAccYMedL, self.uAccYMedH, self.uAccYQ75, self.uAccYQ99]

    def auAccZStatistics(self):
        return [self.uAccZQ1, self.uAccZQ25, self.uAccZMedL, self.uAccZMedH, self.uAccZQ75, self.uAccZQ99] 

    def fAcceleration(self, x):
        return ((x / AdcMax - 1 / 2) * self.uAccelerationToAccGravitity)      
        
    def vSamplingRate(self):
        self.uSamplingRatePrescalerReset = 2
        self.uSamplingRateAcqTimeReset = AdcAcquisitionTime[8]               
        self.uSamplingRateOverSamplesReset = AdcOverSamplingRate[64]   
        self.uSamplingRateMin = 150  # To check maximum frequencies to be max
        self.uSamplingRateMax = 14000  # To check maximum frequencies to be max
        self.uSamplingRateSinglePrescalerMax = 2
        self.uSamplingRateSingleAcqTimeMax = AdcAcquisitionTime[8]
        self.uSamplingRateSingleOverSamplesMax = AdcOverSamplingRate[64]
        self.uSamplingRateDoublePrescalerMax = 2
        self.uSamplingRateDoubleAcqTimeMax = AdcAcquisitionTime[16]
        self.uSamplingRateDoubleOverSamplesMax = AdcOverSamplingRate[64]
        self.uSamplingRateTripplePrescalerMax = 2
        self.uSamplingRateTrippleAcqTimeMax = AdcAcquisitionTime[8]
        self.uSamplingRateTrippleOverSamplesMax = AdcOverSamplingRate[64] 
        self.uSamplingToleranceLow = 0.90
        self.uSamplingToleranceHigh = 1.1
          
        
    def uSamplingRateSingle(self):
        return calcSamplingRate(self.uSamplingRateSinglePrescalerMax, self.uSamplingRateSingleAcqTimeMax, self.uSamplingRateSingleOverSamplesMax) 
    
    def uSamplingRateDouble(self):
        return calcSamplingRate(self.uSamplingRateDoublePrescalerMax, self.uSamplingRateDoubleAcqTimeMax, self.uSamplingRateDoubleOverSamplesMax)
    
    def uSamplingRateTripple(self):
        return calcSamplingRate(self.uSamplingRateTripplePrescalerMax, self.uSamplingRateTrippleAcqTimeMax, self.uSamplingRateTrippleOverSamplesMax)
    
    
    def vRssiSthMin(self, iRssiMin):
        self.iRssiMin = iRssiMin
        
    def vStreaming(self):
        self.uStartupTimeMs = 250
        self.uStandardTestTimeMs = (10000)
        
    def vVoltageRaw(self):
        self.uVoltRawOpa2Middle = 0
        self.uVoltRawOpa2Tolerance = 3
        self.uVoltRawOpa3Middle = 0
        self.uVoltRawOpa3Tolerance = 3
        self.uVoltRawVssTolerance = 3
        self.uVoltMiddleBatProduction = 3.2
        self.uVoltMiddleBatProductionMax = 4.4

    def vTemperature(self, iTemperatureInternalMin, iTemperatureInternalMax):
        self.uTemperatureInternal3V3Middle = 13000
        self.uTemperatureInternal3V3Tolerance = 2000
        self.iTemperatureInternalMin = iTemperatureInternalMin
        self.iTemperatureInternalMax = iTemperatureInternalMax

    def vVirtualFullScale(self):
        self.Vfs = 32
