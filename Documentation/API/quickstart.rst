API
===

To communicate with the ICOtronic system use the :class:`mytoolit.can.Network`:

.. autoclass:: mytoolit.can.Network

.. note::
   Please ignore the ``sender`` parameter, you will never need to change it. In fact, we are `planning to get rid of the parameter in a future version of ICOc <https://github.com/MyTooliT/ICOc/issues/61>`_.

We recommend you use the context manager to open and close the connection (to the STU):

>>> from asyncio import run
>>> from mytoolit.can import Network
>>> async def create_and_shutdown_network():
...     async with Network() as network:
...         pass # ← Your code goes here
>>> run(create_and_shutdown_network())
