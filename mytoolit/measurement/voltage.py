"""Support for reading voltage data"""

# -- Imports ------------------------------------------------------------------

from icotronic.measurement.constants import ADC_MAX_VALUE

# -- Functions ----------------------------------------------------------------


def convert_raw_to_supply_voltage(
    voltage_raw: int, reference_voltage: float = 3.3
) -> float:
    """Convert a raw 2 byte supply voltage value to a voltage value

    Parameters
    ----------

    voltage_raw:
        A 2 byte supply voltage value (returned by the `Streaming` command)

    reference_voltage:
        The ADC reference voltage

    Returns
    -------

    The supply voltage in volts

    Example:

    >>> voltage = convert_raw_to_supply_voltage(11000)
    >>> 3.15 < voltage < 3.16
    True

    >>> voltage = convert_raw_to_supply_voltage(2**15, reference_voltage=1.8)
    >>> 5.12 < voltage < 5.14
    True

    """

    if voltage_raw <= 0:
        return 0

    # The value below is the result of the voltage divider circuit, which
    # uses a 4.7 kΩ and 1 kΩ resistor: (470 kΩ + 100 kΩ) / 100 kΩ = 5.7
    # If you want to know why we used these resistor values, then please
    # take a look
    # [here](https://en.wikipedia.org/wiki/E_series_of_preferred_numbers).
    voltage_divider_factor = 5.7
    return (
        voltage_raw
        * voltage_divider_factor
        * reference_voltage
        / ADC_MAX_VALUE
    )


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    from doctest import testmod

    testmod()
