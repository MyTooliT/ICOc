.. currentmodule:: mytoolit.can

***
API
***

General
=======

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

To connect to an STH to read streaming data you can use the coroutine :meth:`Network.open_data_stream`:

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

The code will raise a :class:`StreamingTimeoutError`, if there is **no streaming data for a certain amount of time** (default: 5 seconds):

.. autoexception:: StreamingTimeoutError

The iterator for streaming data also provides

- the amount of lost messages between to consecutively received messages and
- also keeps track of the messages lost overall.

The code below shows you how you can use this value together with the overall amount of messages to determine the percentage of data loss.

.. doctest::

   >>> from asyncio import run
   >>> from time import monotonic
   >>> from mytoolit.can import Network

   >>> async def determine_data_loss(identifier):
   ...       async with Network() as network:
   ...           await network.connect_sensor_device(identifier)
   ...
   ...           end = monotonic() + 1 # Read data for roughly one second
   ...           messages = 0
   ...           async with network.open_data_stream(first=True) as stream:
   ...               async for data, lost_messages in stream:
   ...                   messages += lost_messages + 1
   ...                   if monotonic() > end:
   ...                       break
   ...
   ...               data_loss = stream.lost_messages
   ...               return data_loss

   >>> data_loss = run(determine_data_loss(identifier="Test-STH"))
   >>> data_loss < 0.1
   True

Slow Processing of Data
-----------------------

The buffer of the CAN controller is only able to store a certain amount of streaming messages before it has to drop them to make room for new ones. For this reason the ICOc library will raise a :class:`StreamingBufferError`, if the buffer for streaming messages exceeds a certain threshold (default: 10 000 messages).

.. autoexception:: StreamingBufferError

.. _Examples:

********
Examples
********

For code examples, please check out the `examples directory <https://github.com/MyTooliT/ICOc/tree/master/mytoolit/examples>`_:

- `Read STH Name <https://github.com/MyTooliT/ICOc/tree/master/mytoolit/examples/sth_name.py>`_: Read the name of the „first“ available STH (device id `0`).
- `Read Data Points <https://github.com/MyTooliT/ICOc/tree/master/mytoolit/examples/read_data.py>`_: Read five acceleration messages (5 · 3 = 15 values) and print their string representation (value, timestamp and message counter)
- `Store Data as HDF5 file <https://github.com/MyTooliT/ICOc/tree/master/mytoolit/examples/store_data.py>`_: Read five seconds of acceleration data and store it as HDF5 file
