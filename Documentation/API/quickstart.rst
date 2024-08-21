.. currentmodule:: mytoolit.can

API
===

To communicate with the ICOtronic system use the :class:`Network` class:

.. autoclass:: Network

.. note::
   Please ignore the ``sender`` parameter, you will never need to change it. In fact, we are `planning to get rid of the parameter in a future version of ICOc <https://github.com/MyTooliT/ICOc/issues/61>`_.

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

This object stores three lists containing :class:`TimestampedValue` objects, which you can access using the attributes:

- :attr:`StreamingData.first`,
- :attr:`StreamingData.second`, and
- :attr:`StreamingData.third`.

You can combine multiple :class:`TimestampedValue`’s using the method :meth:`StreamingData.extend`:

.. automethod:: StreamingData.extend

Another useful method is :meth:`StreamingData.apply`, which can be used to change the values stored in the streaming data (e.g. by converting the 16 bit ADC value into multiples of |math g|_):

.. |math g| replace:: :math:`g`
.. _math g: https://en.wikipedia.org/wiki/Standard_gravity

.. Source for link with formatted link text: https://jwodder.github.io/kbits/posts/rst-hyperlinks/

.. automethod:: StreamingData.apply

A :class:`TimestampedValue`:

.. autoclass:: TimestampedValue

contains:

- a value (:attr:`TimestampedValue.value`),
- a timestamp (:attr:`TimestampedValue.timestamp`), and
- a message counter (:attr:`TimestampedValue.counter`).

The attribute :attr:`TimestampedValue.value` will usually store a 16 bit ADC value (:type:`int`) unless you convert the data (for example, using :meth:`StreamingData.apply`).

Examples
========

For code examples, please check out the `examples directory <https://github.com/MyTooliT/ICOc/tree/master/mytoolit/examples>`_:

- `Read STH Name <https://github.com/MyTooliT/ICOc/tree/master/mytoolit/examples/sth_name.py>`_: Read the name of the „first“ available STH (device id `0`).
- `Read Data Points <https://github.com/MyTooliT/ICOc/tree/master/mytoolit/examples/read_data.py>`_: Read five acceleration messages (5 · 3 = 15 values) and print their string representation (value, timestamp and message counter)
