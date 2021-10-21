# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from pathlib import Path
from datetime import datetime
from time import monotonic_ns
from types import TracebackType
from typing import Optional, Type, Union

from tables import (File, Filters, IsDescription, NoSuchNodeError, open_file,
                    UInt8Col, UInt16Col, UInt64Col)
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
        self.start_time = monotonic_ns()

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
                                 mode='a',
                                 filters=Filters(4, 'zlib'),
                                 title='STH Measurement Data')
        except HDF5ExtError as error:
            raise StorageException(
                f"Unable to open file “{self.filepath}”: {error}")

        name = "acceleration"
        try:
            self.data = self.hdf.get_node(f'/{name}')
        except NoSuchNodeError:
            self.data = self.hdf.create_table(self.hdf.root,
                                              name=name,
                                              description=Acceleration,
                                              title="STH Acceleration Data")

    def add_acceleration_value(self, counter: int, value: int) -> None:
        """Append acceleration data

        Parameters
        ----------

        counter:
            The message counter sent in the package that contained the
            acceleration value

        value:
            The acceleration value that should be added

        Example
        -------

        >>> filepath = Path("test.hdf5")
        >>> with Storage(filepath) as storage:
        ...     storage.add_acceleration_value(counter=1, value=100)
        >>> filepath.unlink()

        """

        row = self.data.row
        # TODO: Use time stamp of CAN message instead
        timestamp = (monotonic_ns() - self.start_time) / 1000
        row['timestamp'] = timestamp
        row['counter'] = counter
        row['acceleration'] = value
        row.append()

        # Flush data to disk every few values to keep memory usage in check
        if self.data.nrows % 1000 == 0:
            self.data.flush()

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

        self.start_time = monotonic_ns()
        self.data.attrs['Measurement_Start'] = datetime.now().isoformat()


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
