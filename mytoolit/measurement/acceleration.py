# -- Imports ------------------------------------------------------------------

from os.path import abspath, dirname
from math import log
from sys import path as module_path

# Add path for custom libraries
repository_root = dirname(dirname(abspath(__file__)))
module_path.append(repository_root)

from mytoolit.config import settings

# -- Functions ----------------------------------------------------------------


def convert_acceleration_adc_to_g(acceleration_raw):
    """Convert an acceleration value sent by the STH into a factor

    The factor measures the amount of the gravitational force
    (g₀ = 9.807 m/s²) applied to the STH.

    Parameters
    ----------

    acceleration_raw:
        The 16 bit integer acceleration value as sent by the STH

    Returns
    -------

    The acceleration in multiples of the standard gravity g₀
    """

    max_value_adc = 0xffff
    acceleration_to_gravity = (
        settings.STH.Acceleration_Sensor.Acceleration.Maximum)

    # The code (probably) subtracts 1/2 from the computed value, since the STH
    # linearly maps the maximum negative acceleration to 0 and the maximum
    # positive acceleration to the maximum ADC value.
    acceleration_in_g = (acceleration_raw / max_value_adc -
                         1 / 2) * acceleration_to_gravity
    return acceleration_in_g


def signal_noise_ratio(expected_value, values):
    """Calculate the signal to noise ratio in dB

    Parameters
    ----------

    expected_value:
        A single value that represents the expected value of the signal
    values:
        An iterable object that stores a series of measured values
        (signal value + noise)

    Returns
    -------

    The signal to noise ratio of the measured values in dB
    """

    noise = [abs(expected_value - value) for value in values]
    average_noise = sum(noise) / len(noise)
    return 20 * log(expected_value / average_noise, 10)
