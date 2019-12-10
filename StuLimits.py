

class StuLimits():

    def __init__(self, bPcbOnly, iRssiMin):
        self.vRssiMin(iRssiMin)
        self.vPcbOnly(bPcbOnly)
      

    def vRssiMin(self, iRssiMin):
        self.iRssiMin = iRssiMin
        
    def vPcbOnly(self, bPcbOnly):
        self.bPcbOnly = bPcbOnly
        