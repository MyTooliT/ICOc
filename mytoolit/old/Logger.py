import os
import time

from pathlib import Path


class Logger():
    """A logging class used to store useful information in text files.

    Note: Please do not use this class in your code unless you have to.
          Instead use the [logging facility of Python](
          https://docs.python.org/3/library/logging.html).
    """

    def __init__(self, fileName, FreshLog=False):
        """Create a new logger with the given arguments

        Parameters
        ----------

        fileName:
            The name of the file where the logged information should be stored

        FreshLog:
            Specifies, if the information should be written to a new file
            (`True`) or appended at the end of an already existing file
            (`False`).

        Example
        -------

        >>> logger = Logger("logging.txt")
        >>> logger.vDel() # Remove empty log file

        """

        self.bFileOpen = False
        self.ErrorFlag = False
        self.startTime = int(round(time.time() * 1000))
        self.file = None
        self.fileName = None
        self.vRename(fileName, FreshLog=FreshLog)

    def __exit__(self):
        try:
            self.bFileOpen = False
            self.file.close()

            # If there was an error use the error filename instead of the
            # normal filename
            if self.ErrorFlag:
                if os.path.isfile(self.fileNameError):
                    os.remove(self.fileNameError)
                if os.path.isfile(self.fileName):
                    os.rename(self.fileName, self.fileNameError)
        except:
            pass

    def getTimeStamp(self):
        """Return the time since the logger was initialized

        Returns
        -------

        The time since logger creation in milliseconds

        Example
        -------

        >>> logger = Logger("something.log")
        >>> # We assume the initialization takes 20 ms or less
        >>> 0 <= logger.getTimeStamp() <= 20
        True
        >>> logger.vDel() # Remove empty log file

        """

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

    def vRename(self, fileName, FreshLog=False):
        # Store log files in root of repository
        repository = Path(__file__).parent.parent.parent
        filepath = repository.joinpath(fileName)
        filepath_error = filepath.with_stem(f"{filepath.stem}_error")

        fileName = str(filepath)
        fileNameError = str(filepath_error)

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


if __name__ == '__main__':
    from doctest import testmod
    testmod()
