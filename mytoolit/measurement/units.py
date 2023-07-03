"""Support for different measurement units"""

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

    # As workaround for the `UndefinedUnitError` the code below throws, if
    # we assert the type of `units.celsius` directly, we just use a
    # variable to access and check the type.
    _celsius = units.celsius
    assert isinstance(_celsius, Unit)

    return Quantity(temperature, _celsius)


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

    _g0 = units.g0
    assert isinstance(_g0, Unit)

    return Quantity(acceleration, _g0)


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

    _volt = units.volt
    assert isinstance(_volt, Unit)

    return Quantity(voltage, _volt)
