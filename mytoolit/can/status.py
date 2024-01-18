"""Support code for different states of nodes/network"""

# -- Imports ------------------------------------------------------------------

from typing import List, Optional, Union

from bidict import bidict

# -- Classes ------------------------------------------------------------------


class State:
    """Wrapper class for the byte returned by the Get/Set State command

    See also: https://mytoolit.github.io/Documentation/#command:get-set-state

    """

    node_states = bidict({
        "No Change": 0,
        "Bootloader": 1,
        "Application": 2,
        "Reserved": 3,
    })

    network_states = bidict({
        "Failure": 0,
        "Error": 1,
        "Standby": 2,
        "Graceful Degradation 2": 3,
        "Graceful Degradation 1": 4,
        "Operating": 5,
        "Startup": 6,
        "No Change": 7,
    })

    def __init__(
        self,
        *value: int,
        mode: Optional[str] = None,
        location: Union[None, int, str] = None,
        state: Union[None, int, str] = None,
    ) -> None:
        """Initialize the node status word using the given arguments

        Parameters
        -----------

        value:
            The value of the state byte

        mode:
            Specifies if the state should be set or retrieved (get)

        location:
            A string or number that specifies the code location

        state:
            A string or number that specifies the network state

        Examples
        --------

        >>> State(mode='Get', location='Bootloader', state='Operating')
        Get State, Location: Bootloader, State: Operating

        >>> State(mode='Set', state='Operating').value == 0b1_0000_101
        True

        """

        def set_part(start, width, number):
            """Store bit pattern number at bit start of the identifier"""

            state_ones = 0xFF
            mask = (1 << width) - 1

            # Set all bits for targeted part to 0
            self.value &= (mask << start) ^ state_ones
            # Make sure we use the correct number of bits for number
            number = number & mask
            # Set bits to given value
            self.value |= number << start

        self.value = value[0] if value else 0
        cls = type(self)

        # ========
        # = Mode =
        # ========

        if mode is not None:
            if mode not in {"Get", "Set"}:
                raise ValueError(f"Unknown mode “{mode}”")

            set_part(start=7, width=1, number=int(mode == "Set"))

        # ============
        # = Location =
        # ============

        if isinstance(location, str):
            try:
                location = cls.node_states[location]
            except KeyError as error:
                raise ValueError(f"Unknown location “{location}”") from error

        if location is not None:
            set_part(start=4, width=2, number=location)

        # =========
        # = State =
        # =========

        if isinstance(state, str):
            try:
                state = cls.network_states[state]
            except KeyError as error:
                raise ValueError(f"Unknown state “{state}”") from error

        if state is not None:
            set_part(start=0, width=3, number=state)

    def __eq__(self, other: object) -> bool:
        """Compare this state to another object

        Parameters
        ----------

        other:
            The other object this state should be compared to

        Returns
        -------

        - True, if the given object is a state and it has the same
          value as this state

        - False, otherwise

        Examples
        --------

        >>> state1 = State(mode='Get',
        ...                location='Bootloader',
        ...                state='Operating')
        >>> state2 = State(mode='Set',
        ...                location='Bootloader',
        ...                state='Operating')

        >>> state1 == state2
        False

        >>> state1 == State(state2.value, mode='Get')
        True

        """

        if isinstance(other, State):
            return self.value == other.value

        return False

    def is_set(self) -> bool:
        """Check if the status should be set

        If this method returns `False`, then the state should be retrieved
        (get) instead.

        Examples
        --------

        >>> State(0b1_0000000).is_set()
        True
        >>> State(0b0_0000000).is_set()
        False
        >>> State(mode='Get').is_set()
        False
        >>> State(mode='Set').is_set()
        True

        """

        return bool((self.value >> 7) & 1)

    def location_name(self) -> str:
        """Retrieve the name of the current (code) location

        Returns
        -------

        The name of the node state represented by this state object

        Examples
        --------

        >>> State(0b00_1010).location_name()
        'No Change'
        >>> State(0b01_1010).location_name()
        'Bootloader'
        >>> State(location='Application').location_name()
        'Application'

        """

        location = (self.value >> 4) & 0b11
        cls = type(self)
        # pylint: disable=unsubscriptable-object
        return cls.node_states.inverse[location]

    def state_name(self) -> str:
        """Retrieve the name of the network state

        Returns
        -------

        The name of the network state represented by this state object

        Examples
        --------

        >>> State(0b000).state_name()
        'Failure'
        >>> State(0b101).state_name()
        'Operating'
        >>> State(state='Startup').state_name()
        'Startup'

        """

        network_state = self.value & 0b111
        cls = type(self)
        # pylint: disable=unsubscriptable-object
        return cls.network_states.inverse[network_state]

    def __repr__(self) -> str:
        """Retrieve the textual representation of the state

        Returns
        -------

        A string that describes the attributes of the state

        Examples
        --------

        >>> State(0b1_0_01_0_110)
        Set State, Location: Bootloader, State: Startup
        >>> State(0b0_1_11_1_001)
        Get State, Location: Reserved, State: Error

        """

        attributes = [
            f"{'Set' if self.is_set() else 'Get'} State",
            f"Location: {self.location_name()}",
            f"State: {self.state_name()}",
        ]

        return ", ".join(attributes)


class NodeStatus:
    """Wrapper class for the node status word

    Please do not use this class directly, but instead use one of the
    two specific status classes for the STH and STU.

    """

    def __init__(self, value: Union[List[int], int]) -> None:
        """Initialize the node status word using the given arguments

        Parameters
        ----------

        value:
            A 32 bit integer or list of bytes that specifies the value of the
            node status word

        """

        # Currently only the first byte (of the little endian version) of
        # status word 0 contains (non-reserved) data
        self.value = value if isinstance(value, int) else value[0]

    def __repr__(self) -> str:
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
            f"{'' if self.error() else 'No '}Error",
        ]

        return ", ".join(attributes)

    def error(self) -> bool:
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

    def state_name(self) -> str:
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
        # pylint: disable=unsubscriptable-object
        return State.network_states.inverse[state]


class NodeStatusSTH(NodeStatus):
    """Wrapper for the node status word of the STH"""


class NodeStatusSTU(NodeStatus):
    """Wrapper for the node status word of the STU"""

    def __repr__(self) -> str:
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
            f"Radio Port {'Enabled' if radio_port_enabled else 'Disabled'}",
            f"CAN Port {'Enabled' if can_port_enabled else 'Disabled'}",
            (
                "Bluetooth "
                f"{'Connected' if bluetooth_connected else 'Disconnected'}"
            ),
        ]

        return ", ".join(attributes)


# pylint: disable=too-few-public-methods


class ErrorStatus:
    """Wrapper class for the error status word

    Please do not use this class directly, but instead use one of the
    two specific error status classes for the STH and STU.
    """

    def __init__(self, value: Union[List[int], int]) -> None:
        """Initialize the error status word using the given arguments

        Parameters
        ----------

        value:
            A 32 bit integer or list of bytes that specifies the value of the
            error status word

        """

        # Currently only the first byte (of the little endian version) of
        # status word contains (non-reserved) data
        self.value = value if isinstance(value, int) else value[0]

    def transmission_error(self) -> bool:
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


# pylint: enable=too-few-public-methods


class ErrorStatusSTH(ErrorStatus):
    """Wrapper class for error status word 1 of the STH"""

    def __repr__(self) -> str:
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

    def adc_overrun(self) -> bool:
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

    def __repr__(self) -> str:
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

if __name__ == "__main__":
    from doctest import testmod

    testmod()
