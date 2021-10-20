# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from pathlib import Path
from datetime import datetime
from types import TracebackType
from typing import Optional, Type, Union

from tables import (File, Filters, IsDescription, open_file, UInt8Col,
                    UInt16Col, UInt64Col)
from tables.exceptions import HDF5ExtError

# -- Classes ------------------------------------------------------------------


class Acceleration(IsDescription):
    """Description of HDF acceleration table"""
    counter = UInt8Col()
    timestamp = UInt64Col()
    acceleration = UInt16Col()


class StorageException(Exception):
    """Exception for HDF storage errors"""


class Storage:
    """Code to store measurement data in HDF5 format"""

    def __init__(self, filepath: Union[Path, str]):
        """Initialize the storage object using the given arguments

        Parameters
        ----------

        filepath:
            The filepath of the HDF5 file in which this object should store
            measurement data

        Example
        -------

        >>> filepath = Path("test.hdf5")
        >>> with Storage(filepath) as storage:
        ...     pass
        >>> filepath.unlink()

        """

        self.filepath = Path(filepath)

    def __enter__(self) -> Storage:
        """Open the HDF file for writing"""

        self.open()
        return self

    def __exit__(self, exception_type: Optional[Type[BaseException]],
                 exception_value: Optional[BaseException],
                 traceback: Optional[TracebackType]) -> None:
        """Clean up the resources used by the storage class

        Parameters
        ----------

        exception_type:
            The type of the exception in case of an exception

        exception_value:
            The value of the exception in case of an exception

        traceback:
            The traceback in case of an exception

        """

        self.close()

    def open(self) -> None:
        """Open and initialize the HDF file for writing"""

        try:
            self.hdf = open_file(self.filepath,
                                 'a',
                                 filters=Filters(4, 'zlib'))
        except HDF5ExtError as error:
            raise StorageException(
                f"Unable to open file “{self.filepath}”: {error}")

        self.data = self.hdf.create_table(self.hdf.root,
                                          name="acceleration",
                                          description=Acceleration,
                                          title="STH Acceleration Data")

    def close(self) -> None:
        """Close the HDF file"""

        if isinstance(self.hdf, File) and self.hdf.isopen:
            self.hdf.close()

    def set_starttime(self):
        """Set the measurement start time to the current ISO date

        Example
        -------

        >>> filepath = Path("test.hdf5")
        >>> with Storage(filepath) as storage:
        ...     storage.set_starttime()
        >>> filepath.unlink()

        """

        self.data.attrs['Measurement_Start'] = datetime.now().isoformat()


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
