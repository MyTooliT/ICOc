# ToDo

- Reset STH after renaming it in [STH test](../mytoolit/test/sth.py). This would make sure that the STH actually realizes that it has a new name
- The [CAN communication class](../CanFd.py) should support different CAN controllers. For that to work we should use the general purpose interface of the [Python CAN library](https://python-can.readthedocs.io/).
- Add a list of manual and automated tests that should be executed before each release.
