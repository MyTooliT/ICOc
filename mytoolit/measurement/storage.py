# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from types import TracebackType
from typing import Optional, Type, Union

from tables import (File, Filters, Float32Col, IsDescription, Node,
                    NoSuchNodeError, open_file, UInt8Col, UInt64Col)
from tables.exceptions import HDF5ExtError

# -- Classes ------------------------------------------------------------------


class Acceleration(IsDescription):
    """Description of HDF acceleration table"""
    counter = UInt8Col()
    timestamp = UInt64Col()  # Microseconds since measurement start
    x = Float32Col()  # Acceleration value in multiples of g₀


class StorageException(Exception):
    """Exception for HDF storage errors"""


class Storage:
    """Code to store measurement data in HDF5 format"""

    def __init__(self, filepath: Union[Path, str]) -> None:
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

        repository = Path(__file__).parent.parent.parent
        filepath = Path(filepath).expanduser()
        self.filepath = (filepath if filepath.is_absolute() else
                         repository.joinpath(filepath)).resolve()

        self.hdf: Optional[File] = None
        self.data: Optional[Node] = None
        self.start_time: Optional[float] = None

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

    def init_acceleration(self, start_time: float) -> None:
        """Initialize the data storage for the collection of acceleration data

        Parameters
        ----------

        start_time:
            The start time of the data acquisition in milliseconds

        Example
        -------

        >>> filepath = Path("test.hdf5")
        >>> with Storage(filepath) as storage:
        ...      storage.init_acceleration(1337.42)
        >>> filepath.unlink()

        """

        if self.hdf is None:
            self.open()

        assert (isinstance(self.hdf, File))

        name = "acceleration"
        try:
            self.data = self.hdf.get_node(f'/{name}')
        except NoSuchNodeError:
            self.data = self.hdf.create_table(self.hdf.root,
                                              name=name,
                                              description=Acceleration,
                                              title="STH Acceleration Data")

        self.start_time = start_time
        self.data.attrs['Start_Time'] = datetime.now().isoformat()

    def add_acceleration_value(self, value: float, counter: int,
                               timestamp: float) -> None:
        """Append acceleration data

        Parameters
        ----------

        value:
            The acceleration value that should be added

        counter:
            The message counter sent in the package that contained the
            acceleration value

        timestamp:
            The timestamp of the acceleration message in milliseconds

        Example
        -------

        >>> filepath = Path("test.hdf5")
        >>> with Storage(filepath) as storage:
        ...     storage.add_acceleration_value(value=32000, counter=1,
        ...                                    timestamp=4306978.449)
        >>> filepath.unlink()

        """

        if self.data is None:
            self.init_acceleration(timestamp)

        assert (isinstance(self.data, Node))
        assert (isinstance(self.start_time, float))

        row = self.data.row
        timestamp = (timestamp - self.start_time) * 1000
        row['timestamp'] = timestamp
        row['counter'] = counter
        row['x'] = value
        row.append()

        # Flush data to disk every few values to keep memory usage in check
        if self.data.nrows % 1000 == 0:
            self.data.flush()

    def close(self) -> None:
        """Close the HDF file"""

        if isinstance(self.hdf, File) and self.hdf.isopen:
            self.hdf.close()


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
