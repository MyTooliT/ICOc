# -- Imports ------------------------------------------------------------------

from os.path import abspath, dirname
from sys import path as module_path

# Add path for custom libraries
repository_root = dirname(dirname(dirname(abspath(__file__))))
module_path.append(repository_root)

from mytoolit.old.MyToolItCommands import NetworkStateName

# -- Classes ------------------------------------------------------------------


class NodeStatus:
    """Wrapper class for the node status word

    Please do not use this class directly, but instead use one of the
    two specific status classes for the STH and STU.
    """

    def __init__(self, value):
        """Initialize the node status word using the given arguments

        Arguments
        ---------

        value:
            A 32 bit integer or list of bytes that specifies the value of the
            node status word
        """

        # Currently only the first byte (of the little endian version) of
        # status word 0 contains (non-reserved) data
        self.value = value if isinstance(value, int) else value[0]

    def __repr__(self):
        """Retrieve the textual representation of the node status word

        Returns
        -------

        A string that describes the attributes of the node status word

        Examples
        --------

        >>> NodeStatus(0b1010)
        State: Operating, No Error

        >>> NodeStatus([0b1010, 0, 0, 0])
        State: Operating, No Error

        >>> NodeStatus(0b1)
        State: Failure, Error
        """

        attributes = [
            f"State: {self.state_name()}",
            f"{'' if self.error() else 'No '}Error"
        ]

        return ", ".join(attributes)

    def error(self):
        """Retrieve the status of the error bit

        Returns
        -------

        True if the error bit was set or False otherwise

        Examples
        --------

        >>> NodeStatus(0b0).error()
        False

        >>> NodeStatus(0b1).error()
        True
        """

        return bool(self.value & 1)

    def state_name(self):
        """Get the name of the state represented by the node status word

        Returns
        -------

        A textual representation of the current node state

        Examples
        --------

        >>> NodeStatus(0b1010).state_name()
        'Operating'

        >>> NodeStatus(0b1110).state_name()
        'No Change'
        """

        state = (self.value >> 1) & 0b111
        return NetworkStateName[state]


class NodeStatusSTH(NodeStatus):
    def __init__(self, value):
        """Initialize the node status word using the given arguments

        Arguments
        ---------

        value:
            A 32 bit integer or list of bytes that specifies the value of the
            node status word
        """

        super().__init__(value)

    def __repr__(self):
        """Retrieve the textual representation of the node status word

        Returns
        -------

        A string that describes the attributes of the node status word

        Examples
        --------

        >>> NodeStatusSTH(0b0100)
        State: Standby, No Error
        """

        return super().__repr__()


class NodeStatusSTU(NodeStatus):
    def __init__(self, value):
        """Initialize the node status word using the given arguments

        Arguments
        ---------

        value:
            A 32 bit integer or list of bytes that specifies the value of the
            node status word
        """

        super().__init__(value)

    def __repr__(self):
        """Retrieve the textual representation of the node status word

        Returns
        -------

        A string that describes the attributes of the node status word

        Example
        -------

        >>> NodeStatusSTU(0b1101010) # doctest:+NORMALIZE_WHITESPACE
        State: Operating, No Error, Radio Port Disabled,
        CAN Port Enabled, Bluetooth Connected
        """

        radio_port_enabled = self.value >> 4 & 1
        can_port_enabled = self.value >> 5 & 1
        bluetooth_connected = self.value >> 6 & 1

        attributes = [
            super().__repr__(),
            "Radio Port {}".format(
                "Enabled" if radio_port_enabled else "Disabled"),
            "CAN Port {}".format(
                "Enabled" if can_port_enabled else "Disabled"),
            "Bluetooth {}".format(
                "Connected" if bluetooth_connected else "Disconnected"),
        ]

        return ", ".join(attributes)


class ErrorStatus:
    """Wrapper class for the error status word

    Please do not use this class directly, but instead use one of the
    two specific error status classes for the STH and STU.
    """

    def __init__(self, value):
        """Initialize the error status word using the given arguments

        Arguments
        ---------

        value:
            A 32 bit integer or list of bytes that specifies the value of the
            error status word
        """

        # Currently only the first byte (of the little endian version) of
        # status word contains (non-reserved) data
        self.value = value if isinstance(value, int) else value[0]

    def transmission_error(self):
        """Retrieve the status of the transmission error bit

        Returns
        -------

        True if the error bit was set or False otherwise

        Examples
        --------

        >>> ErrorStatus(0b0).transmission_error()
        False

        >>> ErrorStatus(0b1).transmission_error()
        True
        """

        return bool(self.value & 1)


class ErrorStatusSTH(ErrorStatus):
    """Wrapper class for error status word 1 of the STH"""

    def __init__(self, value):
        """Initialize the error status word using the given arguments

        Arguments
        ---------

        value:
            A 32 bit integer or list of bytes that specifies the value of the
            error status word
        """
        super().__init__(value)

    def __repr__(self):
        """Retrieve the textual representation of the error status word

        Returns
        -------

        A string that describes the attributes of the error status word

        Examples
        --------

        >>> ErrorStatusSTH(0b0)
        No Error

        >>> ErrorStatusSTH(0b11)
        Bluetooth Transmission Error, ADC Overrun Error

        >>> ErrorStatusSTH(0b10)
        ADC Overrun Error
        """

        errors = []

        if self.transmission_error():
            errors.append("Bluetooth Transmission Error")

        if self.adc_overrun():
            errors.append("ADC Overrun Error")

        if not errors:
            return "No Error"

        return ", ".join(errors)

    def adc_overrun(self):
        """Retrieve the status of the ADC overrun bit

        Returns
        -------

        True if the ADC overrun error bit is set or False otherwise

        Examples
        --------

        >>> ErrorStatusSTH(0b10).adc_overrun()
        True

        >>> ErrorStatusSTH(0b11).adc_overrun()
        True

        >>> ErrorStatusSTH(0b01).adc_overrun()
        False
        """

        return bool((self.value >> 1) & 1)


class ErrorStatusSTU(ErrorStatus):
    """Wrapper class for error status word 1 of the STH"""

    def __init__(self, value):
        """Initialize the error status word using the given arguments

        Arguments
        ---------

        value:
            A 32 bit integer or list of bytes that specifies the value of the
            error status word
        """
        super().__init__(value)

    def __repr__(self):
        """Retrieve the textual representation of the error status word

        Returns
        -------

        A string that describes the attributes of the error status word

        Examples
        --------

        >>> ErrorStatusSTU(0b0)
        No Error

        >>> ErrorStatusSTU(0b1)
        CAN Transmission Error
        """

        if self.transmission_error():
            return "CAN Transmission Error"

        return "No Error"


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
