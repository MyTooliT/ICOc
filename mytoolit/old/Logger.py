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

        Examples
        --------

        Create logger

        >>> filename = "logging.txt"
        >>> logger = Logger(filename)

        Check if the logging file exists

        >>> from glob import glob
        >>> from os.path import isfile
        >>> files = glob(filename)
        >>> len(files) == 1 and isfile(files[0])
        True

        Remove empty log file

        >>> logger.vDel()

        """

        self.bFileOpen = False
        self.ErrorFlag = False
        self.startTime = int(round(time.time() * 1000))
        self.file = None
        self.filepath = None

        repository = Path(__file__).parent.parent.parent
        self.directory = repository

        self.vRename(fileName, FreshLog=FreshLog)

    def __exit__(self):
        """Close the logging file

        If there were any errors then this method adds the postfix `_error` to
        the end of the filename.

        """

        try:
            self.bFileOpen = False
            self.file.close()

            # If there was an error use the error filename instead of the
            # normal filename
            if self.ErrorFlag:
                filepath_error = self.filepath.parent.joinpath(
                    f"{self.filepath.stem}_error{self.filepath.suffix}")
                if filepath_error.is_file():
                    filepath_error.unlink()
                if self.filepath.is_file():
                    os.rename(self.filepath, filepath_error)
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
        """Write a log message to the current file

        Parameters
        ----------

        prefix:
            The prefix that should be written before the message

        message:
            The text that should be added to the file

        Example
        -------

        Write line

        >>> filename = "test.log"
        >>> logger = Logger("test.log")
        >>> logger.write("Info", "hello")

        Check written content

        >>> from re import fullmatch
        >>> with open(filename, 'r') as file:
        ...     line = file.readline()
        ...     fullmatch(r'\[Info\]\(\d+ms\): hello', line[:-1]) is not None
        True

        Remove written log file

        >>> logger.vDel()

        """

        if not self.bFileOpen:
            return

        self.file.write(f"[{prefix}]({self.getTimeStamp()}ms): {message}\n")
        self.file.flush()

    def Info(self, message):
        """Add a info message to the file

        Parameters
        ----------

        message:
            The info text that should be added at the end of the file

        """

        self.write("I", message)

    def Error(self, message):
        """Add an error message to the file

        Parameters
        ----------

        message:
            The error text that should be added at the end of the file

        """

        self.write("E", message)

    def Warning(self, message):
        """Add a warning message to the file

        Parameters
        ----------

        message:
            The warning text that should be added at the end of the file

        """

        self.write("W", message)

    def vRename(self, fileName, FreshLog=False):
        """Rename the current logging file

        Note: This method also removes the old log file

        Parameters
        ----------

        fileName:
            The new (base) name of the logging file

        Example
        -------

        >>> old_file = Path('old.txt')
        >>> new_file = Path('new.txt')

        Create logger

        >>> logger = Logger(old_file)
        >>> old_file.is_file()
        True

        Rename file

        >>> logger.vRename(new_file)
        >>> old_file.is_file()
        False
        >>> new_file.is_file()
        True

        Remove current log file

        >>> logger.vDel()
        >>> new_file.is_file()
        False

        """

        # Close old file handle
        if self.file is not None:
            self.vClose()

        # Rename file
        filepath = self.directory.joinpath(fileName)
        if self.filepath:
            os.rename(self.filepath, filepath)
        self.filepath = filepath

        # Open new file handle
        filepath = str(self.filepath)
        try:
            mode = 'w' if FreshLog else 'a'
            self.file = open(filepath, mode, encoding='utf-8')
        except:
            self.file = open(filepath, "x", encoding='utf-8')
        self.bFileOpen = True

    def vDel(self):
        """Remove the log (or error log) file"""

        self.vClose()
        filepath_error = self.filepath.parent.joinpath(
            f"{self.filepath.stem}_error{self.filepath.suffix}")

        if self.filepath.is_file():
            self.filepath.unlink()
        elif filepath_error().is_file():
            filepath_error().unlink()

    def vClose(self):
        """Close the log file"""

        try:
            self.__exit__()
        except:
            pass


if __name__ == '__main__':
    from doctest import testmod
    testmod()
