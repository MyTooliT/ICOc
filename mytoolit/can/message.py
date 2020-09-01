# -- Imports ------------------------------------------------------------------

from can.interfaces.pcan.basic import TPCANMsg

# -- Class --------------------------------------------------------------------


class Message:
    """Wrapper class for CAN messages"""

    def __init__(self, pcan_message):
        """Create a new message based on the data of a PCAN message

        Parameters
        ----------

        pcan_message:
            A PCAN message structure as used by the PCAN Basic API

        Example
        -------

        >>> message = Message(TPCANMsg())

        """
        self.pcan_message = pcan_message


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
