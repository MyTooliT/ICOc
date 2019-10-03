from MyToolItCommands import AdcAcquisitionTime, AdcOverSamplingRate, AdcReference
Axis = 1
PcbOnly = True

def vSthLimitsConfig(iAxis, bPcbOnly):
    global Axis
    global PcbOnly
    Axis=iAxis
    PcbOnly = bPcbOnly


RssiStuMin=-60#dBm
RssiSthMin=-60#dBm

# Recalculation Factors
AccelerationToAccGravitity = 200
SamplingRateVfsToleranceRation = 64

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
VoltRawDecoupleMiddle = 23678
VoltRawDecoupleTolerance = 100
VoltRawOpa2Middle = 0
VoltRawOpa2Tolerance = 3
VoltRawOpa3Middle = 0
VoltRawOpa3Tolerance = 3
VoltRawVssTolerance = 3
VoltMiddleBat = 3.2
VoltToleranceBat = 0.2   
VoltRawMiddleBat = 11000 
VoltRawToleranceBat = 300
SigIndBatteryQ1 = 8000         
SigIndBatteryQ25 = 9000       
SigIndBatteryMedL = 10000        
SigIndBatteryMedH = 12000    
SigIndBatteryQ75 = 13000     
SigIndBatteryQ99 = 14000     
SigIndBatteryVar = 40000     
SigIndBatterySkewness = 20   
SigIndBatterySNR = 60        

    
# Acceleration
AdcMiddleX = 0
AdcMiddleY = 0
AdcMiddleZ = 0
AdcToleranceX = 2
AdcRawMiddleX = 2 ** 15
AdcRawToleranceX = 512
SelfTestOutputChangemVMin = 70
SelfTestOutputChangemVTyp = 110

SigIndAccXQ1 = 2 ** 15 * 0.99
SigIndAccXQ25 = 2 ** 15 * 0.994
SigIndAccXMedL = 2 ** 15 * 0.996
SigIndAccXMedH = 2 ** 15 * 1.004
SigIndAccXQ75 = 2 ** 15 * 1.008
SigIndAccXQ99 = 2 ** 15 * 1.01
SigIndAccXVar = 2000
if 1 == Axis:
    AdcToleranceY = 200
    AdcToleranceZ = 200
    AdcRawMiddleY = 0
    AdcRawMiddleZ = 0
    AdcRawToleranceY = 54000
    AdcRawToleranceZ = 54000
    SigIndAccXSkewness = 0.9
    SigIndAccXSNR = 60
    SigIndAccYQ1 = 0
    SigIndAccYQ25 = 1
    SigIndAccYMedL = 2
    SigIndAccYMedH = 2**16-3
    SigIndAccYQ75 = 2**16-2
    SigIndAccYQ99 = 2**16-1
    SigIndAccYVar = 40000
    SigIndAccYSkewness = 20
    SigIndAccYSNR = 60
    SigIndAccZQ1 = 0
    SigIndAccZQ25 = 1
    SigIndAccZMedL = 2
    SigIndAccZMedH = 2**16-3
    SigIndAccZQ75 = 2**16-2
    SigIndAccZQ99 = 2**16-1
    SigIndAccZVar = 40000
    SigIndAccZSkewness = 20
    SigIndAccZSNR = 60
else:
    AdcToleranceY = 5
    AdcToleranceZ = 5
    AdcRawMiddleY = 0
    AdcRawMiddleZ = 0
    AdcRawToleranceY = 512
    AdcRawToleranceZ = 512    
    SigIndAccY1 = 2 ** 15 * 0.99
    SigIndAccY25 = 2 ** 15 * 0.995
    SigIndAccYedL = 2 ** 15 * 0.999
    SigIndAccYedH = 2 ** 15 * 1.001
    SigIndAccY75 = 2 ** 15 * 1.005
    SigIndAccY99 = 2 ** 15 * 1.01
    SigIndAccYar = 100
    SigIndAccYkewness = 0.6
    SigIndAccYNR = 70
    SigIndAccZQ1 = 2 ** 15 * 0.99
    SigIndAccZQ25 = 2 ** 15 * 0.995
    SigIndAccZMedL = 2 ** 15 * 0.999
    SigIndAccZMedH = 2 ** 15 * 1.001
    SigIndAccZQ75 = 2 ** 15 * 1.005
    SigIndAccZQ99 = 2 ** 15 * 1.01
    SigIndAccZVar = 100
    SigIndAccZSkewness = 0.6
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
