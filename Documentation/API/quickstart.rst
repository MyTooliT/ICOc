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

To connect to an STH to read streaming data you can use the coroutine ``Network.open_data_stream``:

.. automethod:: Network.open_data_stream

You can use an ``async with`` statement to iterate over the received streaming data. For example, the code below:

.. doctest::

   >>> async def read_streaming_data():
   ...     async with Network() as network:
   ...         await network.connect_sensor_device("Test-STH")
   ...
   ...         async with network.open_data_stream(first=True) as stream:
   ...             async for data in stream:
   ...                 print(data)
   ...                 break

   >>> run(read_streaming_data()) # doctest:+ELLIPSIS
   1: [...]
   2: []
   3: []

- connects to a device called Test-STH,
- opens a data stream for the first measurement channel,
- receives a single streaming message and
  prints its representation.

Examples
========

For code examples, please check out the `examples directory <https://github.com/MyTooliT/ICOc/tree/master/mytoolit/examples>`_:

- `Read STH Name <https://github.com/MyTooliT/ICOc/tree/master/mytoolit/examples/sth_name.py>`_: Read the name of the „first“ available STH (device id `0`).
- `Read Data Points <https://github.com/MyTooliT/ICOc/tree/master/mytoolit/examples/read_data.py>`_: Read five acceleration messages (5 · 3 = 15 values) and print their string representation (value, timestamp and message counter)
