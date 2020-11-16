# -- Class --------------------------------------------------------------------


class Node:
    """This class represents a CAN node of ICOtronic system"""

    def __init__(self, *node):
        """Create a new node from the given argument

        A node represents a communication participant, such as a specific STH
        or a specific STU in the ICOtronic system.

        Parameters
        ----------

        node:
            The number that identifies this node

        Examples
        --------

        >>> Node().value
        0

        """

        self.value = node if node else 0


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
