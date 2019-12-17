#Please open a cmd prompt with administrator rights and run it via python installModules.py
import importlib
from importlib import util
import subprocess
import sys
import os

asModuleList = ["openpyxl", "matplotlib", "windows-curses"]

def bModuleExists(sModuleName):
    spam_spec = util.find_spec(sModuleName)
    found = spam_spec is not None
    return found

def install_and_import(name):
    subprocess.call([sys.executable, "-m", "pip", "install", name])

if __name__ == "__main__":
    os.system("python -m ensurepip")
    os.system("python -m pip install --upgrade pip")
    os.system("copy libusb-1.0.dll "+sys.path[1]+"\\libusb-1.0.dll")
    sPythonPath = subprocess.check_output(["where", "python"])
    sPythonPath = str(sPythonPath)
    print(sPythonPath)
    sPythonPath = sPythonPath.rsplit("\\", 1)
    print(sPythonPath)
    for sModule in asModuleList:
        if False != bModuleExists(sModule):
            print(sModule+" exists")
        else:
            install_and_import(sModule)
