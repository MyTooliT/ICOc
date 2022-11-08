# -- Imports ------------------------------------------------------------------

from statistics import mean
from typing import Iterable

# -- Functions ----------------------------------------------------------------


def guess_sensor_type(values: Iterable[int]) -> str:
    """Guess the sensor type from raw 16 bit ADC values

    Parameters
    ----------

    values:
        Multiple raw 16 bit ADC measurement values

    Returns
    -------

    A textual representation of the assumed sensor type

    Examples
    --------

    >>> guess_sensor_type([38024, 38000, 37950])
    'Piezo Sensor'

    >>> guess_sensor_type([32500, 32571, 32499])
    'Acceleration Sensor'

    >>> guess_sensor_type([10650, 10500, 10780])
    'Temperature Sensor'

    >>> guess_sensor_type([123, 10, 50])
    'Broken/Unknown Sensor'

    """

    mean_raw = mean(values)
    half = 2**15

    tolerance_acceleration = 1000
    min_acceleration = half - tolerance_acceleration
    max_acceleration = half + tolerance_acceleration

    if 10000 <= mean_raw <= 11000:
        return "Temperature Sensor"
    if min_acceleration <= mean_raw <= max_acceleration:
        return "Acceleration Sensor"
    if 37500 <= mean_raw <= 38500:
        return "Piezo Sensor"

    return "Broken/Unknown Sensor"


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
