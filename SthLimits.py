from MyToolItCommands import AdcAcquisitionTime, AdcOverSamplingRate, AdcReference
iSensorAxis = 3
bPcbOnly = True
bConnectedBattery = False

def vSthLimitsConfig(iSensorAxisVar, bPcbOnlyPar, bConnectedBatteryVar):
    global iSensorAxis
    global bPcbOnly
    global bConnectedBattery
    iSensorAxis = iSensorAxisVar
    bPcbOnly = bPcbOnlyPar
    bConnectedBattery = bConnectedBatteryVar

# Calculated kx+d correction factors
kAccX = 200 / (2 ** 16 - 1)
dAccX = -100
kBattery = (57 * 3.3) / (10 * 2 ** 16)

RssiSthMin = -60  # dBm

# Recalculation Factors
AccelerationToAccGravitity = 200
SamplingRateVfsToleranceRation = 32

SamplingRateMin = 150  # To check maximum frequencies to be max
SamplingRateMax = 14000  # To check maximum frequencies to be max
SamplingRateSingleMax = 9524
SamplingRateSingleMaxPrescaler = 2
SamplingRateSingleMaxAcqTime = AdcAcquisitionTime[8]
SamplingRateSingleMaxOverSamples = AdcOverSamplingRate[64]
SamplingRateDoubleMax = 6897
SamplingRateDoubleMaxPrescaler = 2
SamplingRateDoubleMaxAcqTime = AdcAcquisitionTime[16]
SamplingRateDoubleMaxOverSamples = AdcOverSamplingRate[64]
SamplingRateTrippleMax = 9524
SamplingRateTrippleMaxPrescaler = SamplingRateSingleMaxPrescaler
SamplingRateTrippleMaxAcqTime = SamplingRateSingleMaxAcqTime
SamplingRateTrippleMaxOverSamples = SamplingRateSingleMaxOverSamples
# Time Definition
StreamingStartupTimeMs = 250
StreamingStandardTestTimeMs = (10000)

# Reset Values
AdcPrescalerReset = 2
AdcAcquisitionTimeReset = AdcAcquisitionTime[8]               
AdcAcquisitionOverSamplingRateReset = AdcOverSamplingRate[64]             

# Limits
# Voltage
VoltRawOpa2Middle = 0
VoltRawOpa2Tolerance = 3
VoltRawOpa3Middle = 0
VoltRawOpa3Tolerance = 3
VoltRawVssTolerance = 3
if True == bConnectedBattery:
    VoltMiddleBat = 3.2
    SigIndBatteryQ1 = 8000         
    SigIndBatteryQ25 = 9000       
    SigIndBatteryMedL = 10000        
    SigIndBatteryMedH = 12000    
    SigIndBatteryQ75 = 13000     
    SigIndBatteryQ99 = 14000     
    SigIndBatteryVar = 40000     
    SigIndBatterySkewness = 20   
    SigIndBatterySNR = 60 
    VoltRawMiddleBat = 11000 
    VoltRawToleranceBat = 300
else:
    VoltMiddleBat = 0.15
    SigIndBatteryQ1 = 600         
    SigIndBatteryQ25 = 630       
    SigIndBatteryMedL = 640        
    SigIndBatteryMedH = 670    
    SigIndBatteryQ75 = 680     
    SigIndBatteryQ99 = 710     
    SigIndBatteryVar = 40000     
    SigIndBatterySkewness = 20   
    SigIndBatterySNR = 60 
    VoltRawMiddleBat = 700 
    VoltRawToleranceBat = 200
VoltToleranceBat = 0.1  

    
# Acceleration
AdcMiddleX = 0
AdcMiddleY = 0
AdcMiddleZ = 0
AdcToleranceX = 3
AdcRawMiddleX = 2 ** 15
AdcRawToleranceX = 2048
SelfTestOutputChangemVMin = 70
SelfTestOutputChangemVTyp = 110

SigIndAccXQ1 = 2 ** 15 * 0.95
SigIndAccXQ25 = 2 ** 15 * 0.955
SigIndAccXMedL = 2 ** 15 * 0.97
SigIndAccXMedH = 2 ** 15 * 1.03
SigIndAccXQ75 = 2 ** 15 * 1.045
SigIndAccXQ99 = 2 ** 15 * 1.05
SigIndAccXVar = 2000
SigIndAccXSkewness = 0.9
SigIndAccXSNR = 60
if 1 == iSensorAxis:
    AdcToleranceY = 200
    AdcToleranceZ = 200
    AdcRawMiddleY = 0
    AdcRawMiddleZ = 0
    AdcRawToleranceY = 54000
    AdcRawToleranceZ = 54000
    SigIndAccYQ1 = 0
    SigIndAccYQ25 = 1
    SigIndAccYMedL = 2
    SigIndAccYMedH = 2 ** 16 - 3
    SigIndAccYQ75 = 2 ** 16 - 2
    SigIndAccYQ99 = 2 ** 16 - 1
    SigIndAccYVar = 40000
    SigIndAccYSkewness = 20
    SigIndAccYSNR = 60
    SigIndAccZQ1 = 0
    SigIndAccZQ25 = 1
    SigIndAccZMedL = 2
    SigIndAccZMedH = 2 ** 16 - 3
    SigIndAccZQ75 = 2 ** 16 - 2
    SigIndAccZQ99 = 2 ** 16 - 1
    SigIndAccZVar = 40000
    SigIndAccZSkewness = 20
    SigIndAccZSNR = 60
else:
    AdcToleranceY = 3
    AdcToleranceZ = 3
    AdcRawMiddleY = 2 ** 15
    AdcRawMiddleZ = 2 ** 15
    AdcRawToleranceY = 2048
    AdcRawToleranceZ = 2048    
    SigIndAccYQ1 = 2 ** 15 * 0.95
    SigIndAccYQ25 = 2 ** 15 * 0.955
    SigIndAccYMedL = 2 ** 15 * 0.97
    SigIndAccYMedH = 2 ** 15 * 1.03
    SigIndAccYQ75 = 2 ** 15 * 1.045
    SigIndAccYQ99 = 2 ** 15 * 1.05
    SigIndAccYVar = 2000
    SigIndAccYSkewness = 0.9
    SigIndAccYSNR = 60
    SigIndAccZQ1 = 2 ** 15 * 0.95
    SigIndAccZQ25 = 2 ** 15 * 0.955
    SigIndAccZMedL = 2 ** 15 * 0.97
    SigIndAccZMedH = 2 ** 15 * 1.03
    SigIndAccZQ75 = 2 ** 15 * 1.045
    SigIndAccZQ99 = 2 ** 15 * 1.05
    SigIndAccZVar = 2000
    SigIndAccZSkewness = 0.9
    SigIndAccZSNR = 60

# Time
SamplingToleranceLow = 0.90
SamplingToleranceHigh = 1.1

# Temperature
TempInternal3V3Middle = 13000
TempInternal3V3Tolerance = 2000
TempInternalMin = 10.0
TempInternalMax = 60.0
TempInternalProductionTestMin = 20.0
TempInternalProductionMax = 35.0
# Reset States
CalibrationMeassurementPayloadReset = [0, 0, 0, AdcReference["VDD"], 0, 0, 0, 0]
