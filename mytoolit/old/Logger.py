import os
import time

from pathlib import Path


class Logger():
    """
    Logger class used to create logs (in a .txt format)
    """

    def __init__(self, fileName, fileNameError, FreshLog=False):
        self.bFileOpen = False
        self.ErrorFlag = False
        self.startTime = int(round(time.time() * 1000))
        self.file = None
        self.fileName = None

        self.vRename(fileName, fileNameError, FreshLog=FreshLog)

    def __exit__(self):
        try:
            self.bFileOpen = False
            self.file.close()
            if False != self.ErrorFlag:
                if os.path.isfile(self.fileNameError) and os.path.isfile(
                        self.fileName):
                    os.remove(self.fileNameError)
                if os.path.isfile(self.fileName):
                    os.rename(self.fileName, self.fileNameError)
        except:
            pass

    def getTimeStamp(self):
        return int(round(time.time() * 1000)) - int(self.startTime)

    def write(self, prefix, message):
        if not self.bFileOpen:
            return

        self.file.write(f"[{prefix}]({self.getTimeStamp()}ms): {message}\n")
        self.file.flush()

    def Info(self, message):
        self.write("I", message)

    def Error(self, message):
        self.write("E", message)

    def Warning(self, message):
        self.write("W", message)

    def vRename(self, fileName, fileNameError, FreshLog=False):
        # Store log files in root of repository
        repository = Path(__file__).parent.parent.parent
        fileName = str(repository.joinpath(fileName))
        fileNameError = str(repository.joinpath(fileNameError))

        if None != self.file:
            self.vClose()
        if not os.path.exists(os.path.dirname(fileName)) and os.path.isdir(
                os.path.dirname(fileName)):
            os.makedirs(os.path.dirname(fileName))
        if None != self.fileName:
            os.rename(self.fileName, fileName)
        self.fileName = fileName
        self.fileNameError = fileNameError
        if '/' in fileName:
            tPath = fileName.rsplit('/', 1)[0]
            if False == os.path.isdir(tPath):
                os.mkdir(tPath)
        self.bFileOpen = True
        if False != FreshLog:
            try:
                self.file = open(fileName, "w", encoding='utf-8')
            except:
                self.file = open(fileName, "x", encoding='utf-8')
        else:
            try:
                self.file = open(fileName, "a", encoding='utf-8')
            except:
                self.file = open(fileName, "x", encoding='utf-8')

    def vDel(self):
        self.vClose()
        if os.path.isfile(self.fileName):
            os.remove(self.fileName)
        elif os.path.isfile(self.fileNameError):
            os.remove(self.fileNameError)

    def vClose(self):
        try:
            self.__exit__()
        except:
            pass
