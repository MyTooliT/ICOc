# -- Imports ------------------------------------------------------------------

from pint import Quantity, UnitRegistry

# -- Attributes ---------------------------------------------------------------

units = UnitRegistry()
del UnitRegistry

# -- Functions ----------------------------------------------------------------


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

    return Quantity(voltage, units.volt)
