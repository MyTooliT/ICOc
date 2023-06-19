# -- Imports ------------------------------------------------------------------

from pint import Quantity, Unit, UnitRegistry

# -- Attributes ---------------------------------------------------------------

units = UnitRegistry()
del UnitRegistry

# -- Functions ----------------------------------------------------------------


def celsius(temperature: float) -> Quantity:
    """Return given value as temperature quantity

    Parameters
    ----------

    temperature:
        Magnitude of the temperature in degree Celsius

    Returns
    -------

    A temperature quantity with the given magnitude

    """

    assert isinstance(units.celsisus, Unit)

    return Quantity(temperature, units.celsius)


def g0(acceleration: float) -> Quantity:
    """Return given value as acceleration quantity

    Parameters
    ----------

    acceleration:
        Magnitude of acceleration in multiples of g₀

    Returns
    -------

    An acceleration quantity with the given magnitude

    """

    assert isinstance(units.g0, Unit)

    return Quantity(acceleration, units.g0)


def volt(voltage: float) -> Quantity:
    """Return given value as voltage quantity

    Parameters
    ----------

    voltage:
        Magnitude of voltage

    Returns
    -------

    A voltage quantity with the given magnitude

    """

    assert isinstance(units.volt, Unit)

    return Quantity(voltage, units.volt)
