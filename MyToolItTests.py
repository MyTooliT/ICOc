'''
Created on 26.02.2019

@author: operenyi
'''
import unittest
import sys
import os

sLogFile = 'TestStu.txt'
sLogLocation = '../Logs/'
testFileDir = '/'


class Test(unittest.TestCase):
    pass


if __name__ == "__main__":
    print(sys.version)    
    if not os.path.exists(os.path.dirname(sLogLocation + sLogFile)):
        os.makedirs(os.path.dirname(sLogLocation + sLogFile))
    f = open(sLogLocation + sLogFile, "w")
    loader = unittest.TestLoader()
    
    suite = loader.discover(testFileDir)
    runner = unittest.TextTestRunner(f)
    unittest.main(suite)
    f.close()
