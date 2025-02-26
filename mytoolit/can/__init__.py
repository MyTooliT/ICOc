"""Support for the MyTooliT CAN protocol

See: https://mytoolit.github.io/Documentation/#mytoolit-communication-protocol

for more information
"""

# -- Exports ------------------------------------------------------------------

from .network import Network, ErrorResponseError, NetworkError, NoResponseError
