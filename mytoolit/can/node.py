# -- Imports ------------------------------------------------------------------

from os.path import abspath, dirname
from sys import path as module_path

# Add path for custom libraries
repository_root = dirname(dirname(dirname(abspath(__file__))))
module_path.append(repository_root)

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

        self.value = node[0] if node else 0

    def __repr__(self):
        """Return the string representation of the current node

        Returns
        -------

        A string that describes the node

        Examples
        --------

        >>> Node(0)
        Broadcast With Acknowledgment

        >>> Node(31)
        Broadcast Without Acknowledgment

        >>> Node(10)
        STH 10

        >>> Node(15)
        SPU 1

        >>> Node(18)
        STU 2

        """

        if self.value == 0 or self.value == 31:
            return "Broadcast With{} Acknowledgment".format("" if self.value ==
                                                            0 else "out")
        if 1 <= self.value <= 14:
            return f"STH {self.value}"

        if 15 <= self.value <= 16:
            return f"SPU {self.value-14}"

        return f"STU {self.value-16}"


# -- Main ---------------------------------------------------------------------

if __name__ == '__main__':
    from doctest import testmod
    testmod()
