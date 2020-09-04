import xml.etree.ElementTree as ET


class ConfigKeys():
    """
    Set file location of xml path and load xml tree
    @param sFileName File Name of xml file
    """

    def __init__(self, sFileName):
        self.sXmlFileName = sFileName
        self.tree = ET.parse(self.sXmlFileName)
        self.root = self.tree.getroot()

    """

    """

    def close(self):
        self.tree.close()

    """
    Load STH configuration out of xml file
    @return Nothing
    """

    def atXmlConfigurationSth(self):
        atDbData = {}
        for tSetup in self.root.find('Setup'):
            if "ProductionSth" == tSetup.get('name'):
                self.sUsedHwSth = str(tSetup.find('usedHw').text)
                self.sUsedHwSubSth = str(tSetup.find('usedHwSub').text)
                self.sLogLocationSth = str(
                    tSetup.find('VerificationInternal').find(
                        'LogLocation').text)
                for tHwRev in tSetup.find('HwRev'):
                    if self.sUsedHwSth == tHwRev.get('name'):
                        for tHwRevSub in tHwRev.find('HwRevSub'):
                            if self.sUsedHwSubSth == tHwRevSub.get('name'):
                                atDbData["sVersionSth"] = str(
                                    tHwRevSub.find('Version').text)
                                atDbData["sLogNameSth"] = str(
                                    tHwRevSub.find('LogName').text)
                                atDbData["sLogLocationSth"] = str(
                                    tHwRevSub.find('LogLocation').text)
                                atDbData["sOtaComPortSth"] = str(
                                    tHwRevSub.find('OtaComPort').text)
                                atDbData["sBuildLocationSth"] = str(
                                    tHwRevSub.find('BuildLocation').text)
                                atDbData["sSilabsCommanderLocatonSth"] = str(
                                    tHwRevSub.find(
                                        'SilabsCommanderLocaton').text)
                                atDbData["sAdapterSerialNoSth"] = str(
                                    tHwRevSub.find('AdapterSerialNo').text)
                                atDbData["sBoardTypeSth"] = str(
                                    tHwRevSub.find('BoardType').text)
                                atDbData["iSensorAxisSth"] = int(
                                    tHwRevSub.find('SensorAxis').text)
                                atDbData["iAdc2AccSth"] = int(
                                    tHwRevSub.find('Adc2Acc').text)
                                atDbData["sKeySth"] = str(
                                    tHwRevSub.find('Key').text)
        return atDbData

    """
    Load STU configuration out of xml file
    """

    def atXmlConfigurationStu(self):
        atDbData = {}
        for tSetup in self.root.find('Setup'):
            if "ProductionStu" == tSetup.get('name'):
                self.sUsedHwStu = str(tSetup.find('usedHw').text)
                self.sUsedHwSubStu = str(tSetup.find('usedHwSub').text)
                self.sLogLocationStu = str(
                    tSetup.find('VerificationInternal').find(
                        'LogLocation').text)
                for tHwRev in tSetup.find('HwRev'):
                    if self.sUsedHwStu == tHwRev.get('name'):
                        for tHwRevSub in tHwRev.find('HwRevSub'):
                            if self.sUsedHwSubStu == tHwRevSub.get('name'):
                                atDbData["sVersionStu"] = str(
                                    tHwRevSub.find('Version').text)
                                atDbData["sLogNameStu"] = str(
                                    tHwRevSub.find('LogName').text)
                                atDbData["sLogLocationStu"] = str(
                                    tHwRevSub.find('LogLocation').text)
                                atDbData["bPcbOnlyStu"] = bool(
                                    tHwRevSub.find('PcbOnly').text)
                                atDbData["sBuildLocationStu"] = str(
                                    tHwRevSub.find('BuildLocation').text)
                                atDbData["sSilabsCommanderLocatonStu"] = str(
                                    tHwRevSub.find(
                                        'SilabsCommanderLocation').text)
                                atDbData["sAdapterSerialNoStu"] = str(
                                    tHwRevSub.find('AdapterSerialNo').text)
                                atDbData["sBoardTypeStu"] = str(
                                    tHwRevSub.find('BoardType').text)
                                atDbData["sKeyStu"] = str(
                                    tHwRevSub.find('Key').text)
        return atDbData
