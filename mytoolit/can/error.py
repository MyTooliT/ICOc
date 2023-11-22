"""CAN error handling support"""

# -- Classes ------------------------------------------------------------------


class UnsupportedFeatureException(Exception):
    """Indicate that a certain feature is not supported by a device"""
