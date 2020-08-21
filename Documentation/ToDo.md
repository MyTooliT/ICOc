# ToDo

- Reset STH after renaming it in [STH test](../mytoolit/test/sth.py). This would make sure that the STH actually realizes that it has a new name
- Create a script that converts [Base64 encoded MAC addresses to a readable MAC](https://github.com/MyTooliT/ICOc/issues/1) address. The other direction: MAC to Base64 address should be supported too. For that we should probably create another script.
- The [CAN communication class](../CanFd.py) should support different CAN controllers. For that to work we should use the general purpose interface of the [Python CAN library](https://python-can.readthedocs.io/).
