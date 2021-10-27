# -- Imports ------------------------------------------------------------------

from math import log, sqrt
from statistics import pvariance
from typing import Iterable

# -- Functions ----------------------------------------------------------------


def convert_acceleration_adc_to_g(acceleration_raw: int,
                                  max_value: int) -> float:
    """Convert an acceleration value sent by the STH into a factor

    The factor measures the amount of the gravitational force
    (g₀ = 9.807 m/s²) applied to the STH.

    Parameters
    ----------

    acceleration_raw:
        The 16 bit integer acceleration value as sent by the STH

    max_value:
        The maximum acceleration value as factor of g₀

    Returns
    -------

    The acceleration in multiples of the standard gravity g₀
    """

    max_value_adc = 0xffff
    acceleration_to_gravity = max_value

    # The code subtracts 1/2 from the computed value, since the STH linearly
    # maps the maximum negative acceleration to 0 and the maximum positive
    # acceleration to the maximum ADC value. Currently the stationary
    # acceleration value seems to be slightly negative (-4·g₀ <
    # acceleration_in_g 0 < 0 ), while in theory it should have a value of g₀.
    acceleration_in_g = (acceleration_raw / max_value_adc -
                         1 / 2) * acceleration_to_gravity
    return acceleration_in_g


def ratio_noise_max(values: Iterable[int]) -> float:
    """Calculate the ratio noise to max ADC amplitude in dB

    Parameters
    ----------

    values:
        An iterable object that stores a series of measured (acceleration)
        values

    Returns
    -------

    The ratio of the average noise to the highest possible measured value
    """

    adc_max = 0xffff
    max_value = adc_max / 2
    standard_deviation = sqrt(pvariance(values))
    return 20 * log(standard_deviation / max_value, 10)
