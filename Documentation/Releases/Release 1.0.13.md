# Version 1.0.13

## Production Test

- The “connection test” now uses the [new network class](../../mytoolit/can/network.py) instead of the [old network class](../../mytoolit/old/network.py)

## Internal

### Message

- The string representation of a message (`repr`) now includes additional information for the [Get/Set State](https://mytoolit.github.io/Documentation/#command:get-set-state) block command

### Network

- Add the coroutine `get_state` to [retrieve information about the current state of a node](https://mytoolit.github.io/Documentation/#command:get-set-state)
