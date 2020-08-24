# ToDo

- The [CAN communication class](../CanFd.py) should support different CAN controllers. For that to work we should use the general purpose interface of the [Python CAN library](https://python-can.readthedocs.io/).
- Add test script for automated tests
- Add power usage test for different phases of STH:
  - Sleep Mode 1
  - Sleep Mode 2
  - Active
  - Streaming
- Format whole code base with code formatter (e.g. [YAPF](https://github.com/google/yapf)). We probably could use [Restyled](https://restyled.io) to do that, after we open the source code.
