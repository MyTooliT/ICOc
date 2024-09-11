.. currentmodule:: mytoolit.can

***
API
***

Connecting to STU
=================

To communicate with the ICOtronic system use the :class:`Network` class:

.. autoclass:: Network

We recommend you use the context manager to open and close the connection (to the STU):

.. doctest::

   >>> from asyncio import run
   >>> from mytoolit.can import Network

   >>> async def create_and_shutdown_network():
   ...     async with Network() as network:
   ...         pass # ← Your code goes here

   >>> run(create_and_shutdown_network())

Connecting to Sensor Device
===========================

To connect to an STH use the coroutine :meth:`Network.connect_sensor_device`

.. automethod:: Network.connect_sensor_device

Reading Names
=============

After your are connected to the sensor device you can read its (advertisement) name using the coroutine :meth:`Network.get_name`.

.. automethod:: Network.get_name

If you want to read the name of the sensor device then the parameter node should have the value ``"STH 1"``, if you want to read the name of the STU use the default value ``"STU 1"``.

.. doctest::

   >>> from asyncio import run
   >>> from mytoolit.can import Network

   >>> async def read_sensor_name(name):
   ...     async with Network() as network:
   ...         await network.connect_sensor_device(name)
   ...         sensor_name = await network.get_name("STH 1")
   ...         return sensor_name

   >>> sensor_name = "Test-STH"
   >>> run(read_sensor_name(sensor_name))
   'Test-STH'

Reading Streaming Data
======================

After you connected to the sensor device you use the coroutine :meth:`Network.open_data_stream` to open the data stream:

.. automethod:: Network.open_data_stream

After you opened the stream use an ``async with`` statement to iterate over the received streaming data. For example, the code below:

.. doctest::

   >>> async def read_streaming_data():
   ...     async with Network() as network:
   ...         await network.connect_sensor_device("Test-STH")
   ...
   ...         async with network.open_data_stream(first=True) as stream:
   ...             async for data, lost_messages in stream:
   ...                 print(data)
   ...                 break

   # Example Output: [32579, 32637, 32575]@1724251001.976368
   >>> run(read_streaming_data()) # doctest:+ELLIPSIS
   [...]@... #...

- connects to a device called ``Test-STH``,
- opens a data stream for the first measurement channel,
- receives a single streaming message and
  prints its representation.

.. currentmodule:: mytoolit.can.streaming

The data returned by the ``async for`` (``stream``) is an object of the class :class:`StreamingData`:

.. autoclass:: StreamingData

This object has the following attributes:

- :attr:`StreamingData.values`: a list containing either two or three values,
- :attr:`StreamingData.timestamp`: the timestamp when the data was collected (actually `when it was received by the CAN controller <https://docs.peak-system.com/API/PCAN-Basic.Net/html/4f55937b-3d8f-de9e-62a9-be1b8a150f05.htm>`_)
- :attr:`StreamingData.counter`: a cyclic message counter (0 – 255) that can be used to detect data loss

.. note::
   The amount of data stored in :attr:`StreamingData.values` depends on the enabled streaming channels. For the `recommended amount of one or three enabled channels`_ the list contains three values. For

   - one enabled channel all three values belong to the same channel, while
   - for the three enabled channels

     - the first value belongs to the first channel,
     - the second to the second channel,
     - and the third to the third channel.

.. |recommended amount of one or three enabled channels| replace:: **recommended amount** of one or three enabled channels
.. _recommended amount of one or three enabled channels: https://mytoolit.github.io/ICOc/#channel-selection

Storing Streaming Data
======================

.. currentmodule:: mytoolit.measurement.storage

If you want to store streaming data for later use you can use the :class:`Storage` class to open a context manager that lets you store data as `HDF5 <https://en.wikipedia.org/wiki/Hierarchical_Data_Format>`_ file via the method :func:`add_streaming_data` of the class :class:`StorageData`:

.. automethod:: StorageData.add_streaming_data

For a more complete example, please take a look at the :ref:`HDF5 example code<Examples>`.

Determining Data Loss
=====================

.. currentmodule:: mytoolit.can.streaming

Sometimes the

- **connection** to your sensor device might be **bad** or
- code might run **too slow to retrieve/process streaming data**.

In both cases there will be some form of data loss. The ICOc library currently takes multiple measures to detect data loss.

Bad Connection
--------------

The iterator for streaming data :class:`AsyncStreamBuffer` will raise a :class:`StreamingTimeoutError`, if there is **no streaming data for a certain amount of time** (default: 5 seconds):

.. autoexception:: StreamingTimeoutError

:class:`AsyncStreamBuffer` also provides access to statistics that can be used to determine the amount of lost data. For example, if you iterate through the streaming messages with ``async for``, then in addition to the streaming data the iterator will also return the **amount of lost messages since the last successfully received message** (``lost_messages`` in the example below):

.. code-block::
   :emphasize-lines: 2

   async with network.open_data_stream(first=True) as stream:
       async for data, lost_messages in stream:
           if lost_messages > 0:
               print(f"Lost {lost_messages} messages!")

To access the overall data quality, since the start of streaming you can use the method :meth:`AsyncStreamBuffer.dataloss`:

.. automethod:: AsyncStreamBuffer.dataloss

The example code below shows how to use this method:

.. doctest::

   >>> from asyncio import run
   >>> from time import monotonic
   >>> from mytoolit.can import Network

   >>> async def determine_data_loss(identifier):
   ...       async with Network() as network:
   ...           await network.connect_sensor_device(identifier)
   ...
   ...           end = monotonic() + 1 # Read data for roughly one second
   ...           async with network.open_data_stream(first=True) as stream:
   ...               async for data, lost_messages in stream:
   ...                   if monotonic() > end:
   ...                       break
   ...
   ...               return stream.dataloss()

   >>> data_loss = run(determine_data_loss(identifier="Test-STH"))
   >>> data_loss < 0.1 # We assume that the data loss was less than 10 %
   True

If you want to calculate the amount of data loss for a specific time-span you can use the method :meth:`AsyncStreamBuffer.reset` to reset the message statistics at the start of the time-span. In the following example we stream data for (roughly) 2.1 seconds and return a list with the amount of data loss over periods of 0.5 seconds:

.. doctest::

   >>> from asyncio import run
   >>> from time import monotonic
   >>> from mytoolit.can import Network

   >>> async def determine_data_loss(identifier):
   ...       async with Network() as network:
   ...           await network.connect_sensor_device(identifier)
   ...
   ...           start = monotonic()
   ...           end = monotonic() + 2.1
   ...           last_reset = start
   ...           data_lost = []
   ...           async with network.open_data_stream(first=True) as stream:
   ...               async for data, lost_messages in stream:
   ...                   current = monotonic()
   ...                   if current >= last_reset + 0.5:
   ...                      data_lost.append(stream.dataloss())
   ...                      stream.reset_stats()
   ...                      last_reset = current
   ...                   if current > end:
   ...                       break
   ...
   ...               return data_lost

   >>> data_lost = run(determine_data_loss(identifier="Test-STH"))
   >>> len(data_lost)
   4
   >>> all(map(lambda loss: loss < 0.1, data_lost))
   True

.. note:: We used a overall runtime of 2.1 seconds, since in a timing interval of 2 seconds there is always the possibility that the code above either returns three or four data loss values depending on the specific timing.

Slow Processing of Data
-----------------------

The buffer of the CAN controller is only able to store a certain amount of streaming messages before it has to drop them to make room for new ones. For this reason the ICOc library will raise a :class:`StreamingBufferError`, if the buffer for streaming messages exceeds a certain threshold (default: 10 000 messages):

.. autoexception:: StreamingBufferError

.. _Examples:

********
Examples
********

For code examples, please check out the `examples directory <https://github.com/MyTooliT/ICOc/tree/master/mytoolit/examples>`_:

- `Read STH Name <https://github.com/MyTooliT/ICOc/tree/master/mytoolit/examples/sth_name.py>`_: Read the name of the „first“ available STH (device id `0`).
- `Read Data Points <https://github.com/MyTooliT/ICOc/tree/master/mytoolit/examples/read_data.py>`_: Read five acceleration messages (5 · 3 = 15 values) and print their string representation (value, timestamp and message counter)
- `Store Data as HDF5 file <https://github.com/MyTooliT/ICOc/tree/master/mytoolit/examples/store_data.py>`_: Read five seconds of acceleration data and store it as HDF5 file
