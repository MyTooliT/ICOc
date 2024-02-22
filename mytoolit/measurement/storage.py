"""Support for storing measurement data (in HDF5)"""

# -- Imports ------------------------------------------------------------------

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from types import TracebackType
from typing import Dict, Iterable, Mapping, Optional, Type, Union

from tables import (
    File,
    Filters,
    Float32Col,
    IsDescription,
    MetaAtom,
    MetaIsDescription,
    Node,
    NoSuchNodeError,
    open_file,
    UInt8Col,
    UInt64Col,
)
from tables.exceptions import HDF5ExtError

from mytoolit.can.streaming import StreamingData

# -- Functions ----------------------------------------------------------------


def create_acceleration_description(
    attributes: Dict[str, MetaAtom],
) -> MetaIsDescription:
    """Create a new `IsDescription` class to store acceleration data

    Parameters
    ----------

    attributes:
        A dictionary containing additional columns to store specific
        acceleration data. The key specifies the name of the attribute, while
        the value specifies the type.

    Examples
    --------

    >>> description_x_acceleration = create_acceleration_description(
    ...     dict(x=Float32Col()))
    >>> list(description_x_acceleration.columns.keys())
    ['counter', 'timestamp', 'x']

    """

    description_class = type(
        "ExtendedAccelerationDescription",
        (AccelerationDescription,),
        attributes,
    )
    return description_class


# -- Classes ------------------------------------------------------------------


# pylint: disable=too-few-public-methods


class AccelerationDescription(IsDescription):
    """Description of HDF acceleration table"""

    counter = UInt8Col()
    timestamp = UInt64Col()  # Microseconds since measurement start


# pylint: enable=too-few-public-methods


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

        self.filepath = Path(filepath).expanduser().resolve()

        self.hdf: Optional[File] = None
        self.acceleration: Optional[Node] = None
        self.start_time: Optional[float] = None

    def __enter__(self) -> Storage:
        """Open the HDF file for writing"""

        self.open()
        return self

    def __exit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
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
            self.hdf = open_file(
                self.filepath,
                mode="a",
                filters=Filters(4, "zlib"),
                title="STH Measurement Data",
            )
        except (HDF5ExtError, OSError) as error:
            raise StorageException(
                f"Unable to open file “{self.filepath}”: {error}"
            ) from error

        try:
            # Try to get acceleration dataset, if it already exists
            self.acceleration = self.hdf.get_node("/acceleration")
            self.start_time = self.acceleration[-1][1] / 1000
        except NoSuchNodeError:
            pass

    def _assert_acceleration(self, message: str) -> None:
        """Check for existence of acceleration data

        Parameters
        ----------

        message:
            An Explanation about which operation is not possible, due
            to the missing dataset

        Raises
        ------

        UserWarning, if the acceleration dataset does not exist

        """

        if self.acceleration is None:
            raise UserWarning(
                f"Unable to {message} non existent "
                "acceleration table.\n"
                "Please call either `init_acceleration` or `add_acceleration` "
                "before you use this function"
            )

    def init_acceleration(
        self, axes: Iterable[str], start_time: float
    ) -> None:
        """Initialize the data storage for the collection of acceleration data

        Parameters
        ----------

        axes:
            All acceleration axes for which data should be collected

        start_time:
            The start time of the data acquisition in milliseconds

        Examples
        --------

        >>> filepath = Path("test.hdf5")
        >>> with Storage(filepath) as storage:
        ...      storage.init_acceleration(axes = ['x'], start_time = 1337.42)
        >>> filepath.unlink()

        >>> with Storage(filepath) as storage:
        ...      storage.init_acceleration(axes = ['x', 'z'],
        ...                                start_time = 42.1337)
        >>> filepath.unlink()

        """

        if self.hdf is None:
            self.open()

        assert isinstance(self.hdf, File)

        name = "acceleration"
        try:
            self.acceleration = self.hdf.get_node(f"/{name}")
        except NoSuchNodeError:
            self.acceleration = self.hdf.create_table(
                self.hdf.root,
                name=name,
                description=create_acceleration_description(
                    attributes={axis: Float32Col() for axis in axes}
                ),
                title="STH Acceleration Data",
            )

        self.start_time = start_time
        self.acceleration.attrs["Start_Time"] = datetime.now().isoformat()

    def add_acceleration(
        self, values: Mapping[str, float], counter: int, timestamp: float
    ) -> None:
        """Append acceleration data

        Parameters
        ----------

        values:
            The acceleration values that should be added

            - The key specifies the acceleration axis e.g. `x`, `y` or `z`
            - The value specifies the acceleration in the given direction

        counter:
            The message counter sent in the package that contained the
            acceleration value

        timestamp:
            The timestamp of the acceleration message in milliseconds

        Example
        -------

        >>> filepath = Path("test.hdf5")
        >>> with Storage(filepath) as storage:
        ...     storage.add_acceleration(values={'x': 12}, counter=1,
        ...                                    timestamp=4306978.449)
        >>> filepath.unlink()

        """

        if self.acceleration is None:
            self.init_acceleration(values.keys(), timestamp)

        assert isinstance(self.acceleration, Node)
        assert isinstance(self.start_time, (int, float))

        row = self.acceleration.row
        timestamp = (timestamp - self.start_time) * 1000
        row["timestamp"] = timestamp
        row["counter"] = counter
        for accelertation_type, value in values.items():
            row[accelertation_type] = value
        row.append()

        # Flush data to disk every few values to keep memory usage in check
        if self.acceleration.nrows % 1000 == 0:
            self.acceleration.flush()

    def add_streaming_data(
        self,
        streaming_data: StreamingData,
    ) -> None:
        """Add streaming data to the storage object

        Parameters
        ----------

        streaming_data:
            The streaming data that should be added to the storage

        Examples
        --------

        >>> from mytoolit.can.streaming import StreamingConfigBits

        Store streaming data for single channel

        >>> channel3 = StreamingConfigBits(
        ...     first=False, second=False, third=True)
        >>> data1 = StreamingData(
        ...     values=[1, 2, 3], counter=21, timestamp=1, channels=channel3)
        >>> data2 = StreamingData(
        ...     values=[4, 5, 6], counter=22, timestamp=2, channels=channel3)
        >>> filepath = Path("test.hdf5")
        >>> with Storage(filepath) as storage:
        ...     storage.add_streaming_data(data1)
        ...     storage.add_streaming_data(data2)
        >>> filepath.unlink()

        Store streaming data for three channels

        >>> all = StreamingConfigBits(first=True, second=True, third=True)
        >>> data1 = StreamingData(
        ...     values=[1, 2, 3], counter=21, timestamp=1, channels=all)
        >>> data2 = StreamingData(
        ...     values=[4, 5, 6], counter=22, timestamp=2, channels=all)
        >>> with Storage(filepath) as storage:
        ...     storage.add_streaming_data(data1)
        ...     storage.add_streaming_data(data2)
        >>> filepath.unlink()

        """

        channels = streaming_data.channels
        axes = [
            name
            for enabled, name in zip(
                (
                    channels.first,
                    channels.second,
                    channels.third,
                ),
                "xyz",
            )
            if enabled
        ]
        timestamp = streaming_data.timestamp * 1000

        assert len(axes) >= 1

        if len(axes) == 1:  # Single Channel: 3 Values
            axis = axes.pop()
            for value in streaming_data.values:
                self.add_acceleration(
                    values={axis: value},
                    timestamp=timestamp,
                    counter=streaming_data.counter,
                )

        else:  # One value for each channel
            self.add_acceleration(
                values=dict(zip(axes, streaming_data.values)),
                timestamp=timestamp,
                counter=streaming_data.counter,
            )

    def add_acceleration_meta(self, name: str, value: str) -> None:
        """Add acceleration metadata

        Precondition
        ------------

        Either the method

        - init_acceleration or
        - add_acceleration

        have to be called once before you use this method. This is required
        since otherwise the table that stores the acceleration (meta) data
        does not exist.

        Parameters
        ----------

        name:
            The name of the meta attribute

        value:
            The value of the meta attribute

        Example
        -------

        >>> filepath = Path("test.hdf5")
        >>> with Storage(filepath) as storage:
        ...     storage.add_acceleration(values={'x': 12}, counter=1,
        ...                                    timestamp=4306978.449)
        ...     storage.add_acceleration_meta('Sensor_Range', "± 100 g₀")
        >>> filepath.unlink()

        """

        self._assert_acceleration("add metadata to")
        assert self.acceleration

        self.acceleration.attrs[name] = value

    def dataloss(self) -> float:
        """Determine (minimum) data loss

        Returns
        -------

        Amount of lost messages divided by all messages (lost and retrieved)

        Example
        -------

        >>> from math import isclose
        >>> def calculate_dataloss():
        ...     filepath = Path("test.hdf5")
        ...     with Storage(filepath) as storage:
        ...         for counter in range(256):
        ...             storage.add_acceleration(values={'x': 1},
        ...                                      counter=counter,
        ...                                      timestamp=counter/10)
        ...         for counter in range(128, 256):
        ...             storage.add_acceleration(values={'x': 2},
        ...                                      counter=counter,
        ...                                      timestamp=(255 + counter)/10)
        ...
        ...         dataloss = storage.dataloss()
        ...     filepath.unlink()
        ...     return dataloss
        >>> isclose(0.25, calculate_dataloss(), rel_tol=0.005)
        True

        """

        self._assert_acceleration("determine data loss of")
        assert self.acceleration

        # Write back acceleration data so we can iterate over it
        self.acceleration.flush()

        lost_messages = 0
        retrieved_messages = 0
        last_counter = int(self.acceleration[0][0])
        for record in self.acceleration:
            counter = int(record[0])

            if counter == last_counter:
                continue  # Skip data with same message counter

            lost_messages += (counter - last_counter) % 256 - 1
            retrieved_messages += 1

            last_counter = counter

        messages = lost_messages + retrieved_messages

        return lost_messages / messages if messages > 0 else 0

    def close(self) -> None:
        """Close the HDF file"""

        if isinstance(self.hdf, File) and self.hdf.isopen:
            self.hdf.close()


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import testmod

    testmod()
