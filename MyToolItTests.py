'''
Created on 26.02.2019

@author: operenyi
'''
import unittest
import sys
import os

log_file = 'TestStu.txt'
log_location='../Logs/'
testFileDir = '/'

class Test(unittest.TestCase):
    pass


if __name__ == "__main__":
    print(sys.version)    
    if not os.path.exists(os.path.dirname(log_location+log_file)):
        os.makedirs(os.path.dirname(log_location+log_file))
    f = open(log_location+log_file, "w")
    loader = unittest.TestLoader()
    
    suite = loader.discover(testFileDir)
    runner = unittest.TextTestRunner(f)
    unittest.main(suite)
    f.close()