from MyToolItSth import *
from MyToolItCommands import *
Axis = 1
PcbOnly = True

# Recalculation Factors
AdcMax = 0xFFFF
AccelerationToAccGravitity = 200
SamplingRateVfsToleranceRation = 64

SamplingRateMin = 150  # To check maximum frequencies to be max
SamplingRateMax = 14000  # To check maximum frequencies to be max
SamplingRateSingleMax = 9600
SamplingRateSingleMaxAcqTime = AdcAcquisitionTime[8]
SamplingRateSingleMaxOverSamples = AdcOverSamplingRate[64]
SamplingRateDoubleMax = 7200
SamplingRateDoubleMaxPrescaler=3
SamplingRateDoubleMaxAcqTime = AdcAcquisitionTime[8]
SamplingRateDoubleMaxOverSamples = AdcOverSamplingRate[64]
SamplingRateTrippleMax = 9600
SamplingRateTrippleMaxAcqTime = SamplingRateSingleMaxAcqTime
SamplingRateTrippleMaxOverSamples = SamplingRateSingleMaxOverSamples
# Time Definition
StreamingStartupTimeMs = 250
StreamingStandardTestTimeMs = (10000)
SAMPLING_POINTS_SECOND_RESET = 9523

# Reset Values
AdcPrescalerReset = 2
AdcAcquisitionTimeReset = AdcAcquisitionTime[8]               
AdcAcquisitionOverSamplingRateReset = AdcOverSamplingRate[64]             

# Limits
# Voltage
VoltRawDecoupleMiddle = 23678
VoltRawDecoupleTolerance = 100
VoltRawOpa2Middle = 0
VoltRawOpa2Tolerance = 2
VoltRawOpa3Middle = 0
VoltRawOpa3Tolerance = 2
VoltRawVssTolerance = 1
if False != PcbOnly:
    VoltMiddleBat = 0
    VoltToleranceBat = 0.5
    VoltRawMiddleBat = 780
    VoltRawToleranceBat = 300
    SigIndBatteryQ1 = 0
    SigIndBatteryQ25 = 1
    SigIndBatteryMedL = 2
    SigIndBatteryMedH = 10
    SigIndBatteryQ75 = 20
    SigIndBatteryQ99 = 30
    SigIndBatteryVar = 100
    SigIndBatterySkewness = 0.6
    SigIndBatterySNR = 70
else:
    VoltMiddleBat = 0
    VoltToleranceBat = 0.5   
    VoltRawMiddleBat = 780 
    VoltRawToleranceBat = 300
    SigIndBatteryQ1 = 0
    SigIndBatteryQ25 = 1
    SigIndBatteryMedL = 2
    SigIndBatteryMedH = 10
    SigIndBatteryQ75 = 20
    SigIndBatteryQ99 = 30
    SigIndBatteryVar = 100
    SigIndBatterySkewness = 0.6
    SigIndBatterySNR = 70
    
# Acceleration
AdcMiddleX = 0
AdcMiddleY = 0
AdcMiddleZ = 0
AdcToleranceX = 5
AdcRawMiddleX = 2 ** 15
AdcRawToleranceX = 128
SelfTestOutputChangemVMin = 70
SelfTestOutputChangemVTyp = 110

SigIndAccXQ1 = 2 ** 15 * 0.99
SigIndAccXQ25 = 2 ** 15 * 0.995
SigIndAccXMedL = 2 ** 15 * 0.997
SigIndAccXMedH = 2 ** 15 * 1.003
SigIndAccXQ75 = 2 ** 15 * 1.005
SigIndAccXQ99 = 2 ** 15 * 1.01
SigIndAccXVar = 100
if 1 == Axis:
    AdcToleranceY = 200
    AdcToleranceZ = 200
    AdcRawMiddleY = 0
    AdcRawMiddleZ = 0
    VoltRawToleranceBat = 60
    AdcRawToleranceY = 54000
    AdcRawToleranceZ = 54000
    SigIndAccXSkewness = 0.9
    SigIndAccXSNR = 75
    SigIndAccYQ1 = 0
    SigIndAccYQ25 = 1
    SigIndAccYMedL = 2
    SigIndAccYMedH = 2000
    SigIndAccYQ75 = 2000
    SigIndAccYQ99 = 2000
    SigIndAccYVar = 40000
    SigIndAccYSkewness = 20
    SigIndAccYSNR = 40
    SigIndAccZQ1 = 0
    SigIndAccZQ25 = 1
    SigIndAccZMedL = 2
    SigIndAccZMedH = 2000
    SigIndAccZQ75 = 2000
    SigIndAccZQ99 = 2000
    SigIndAccZVar = 40000
    SigIndAccZSkewness = 20
    SigIndAccZSNR = 40
else:
    AdcToleranceY = 5
    AdcToleranceZ = 5
    AdcRawMiddleY = 0
    AdcRawMiddleZ = 0
    VoltRawToleranceBat = 60
    AdcRawToleranceY = 54000
    AdcRawToleranceZ = 54000    
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
    SigIndAccZSNR = 70

# Time
SamplingToleranceLow = 0.90
SamplingToleranceHigh = 1.1

# Temperature
TempInternal3V3Middle = 13000
TempInternal3V3Tolerance = 2000
TempInternalMin = 10.0
TempInternalMax = 60.0

# Reset States
CalibrationMeassurementPayloadReset = [0, 0, 0, AdcReference["VDD"], 0, 0, 0, 0]
