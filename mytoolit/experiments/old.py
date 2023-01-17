# -- Imports ------------------------------------------------------------------

from mytoolit.can import Node

from mytoolit.old.network import Network as OldNetwork
from mytoolit.old.MyToolItNetworkNumbers import MyToolItNetworkNr

# -- Class --------------------------------------------------------------------


class Network:
    def __init__(self, sth_name):
        self.sth_name = sth_name

        self.network = OldNetwork(
            sender=MyToolItNetworkNr["SPU1"], receiver=Node("STU 1").value
        )

        self.network.bConnected = False
        self.network.reset_node("STU 1")

    def __enter__(self):
        self.network.bBlueToothConnectPollingName(
            MyToolItNetworkNr["STU1"], self.sth_name, log=False
        )

        return self.network

    def __exit__(self, exception_type, exception_value, traceback):
        self.network.__exit__()


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    sth_name = "Test-SMH"
    with Network(sth_name) as network:
        print(f"Connected to “{sth_name}”\n")

        sensor_configuration = {"x": 9, "y": 10, "z": 11}
        print(
            "Change sensor configuration to: "
            + ", ".join(
                f"{axis}: {sensor}"
                for axis, sensor in sensor_configuration.items()
            )
        )
        network.write_sensor_config(**sensor_configuration)

        sensor_configuration = network.read_sensor_config()
        print(f"Updated sensor configuration: {sensor_configuration}")
