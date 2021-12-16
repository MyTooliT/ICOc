# -- Imports ------------------------------------------------------------------

from mytoolit.measurement.constants import ADC_MAX_VALUE

# -- Functions ----------------------------------------------------------------


def convert_voltage_adc_to_volts(voltage_raw: int) -> float:
    """Convert a raw 2 byte supply voltage value to a voltage value

    Parameters
    ----------

    voltage_raw:
        A 2 byte supply voltage value (returned by the `Streaming` command )

    Returns
    -------

    The supply voltage in volts

    Example:

    >>> 3.15 < convert_voltage_adc_to_volts(11000) < 3.16
    True

    """

    if voltage_raw <= 0:
        return 0

    reference_voltage = 3.3
    return voltage_raw * 5.7 * reference_voltage / ADC_MAX_VALUE


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
