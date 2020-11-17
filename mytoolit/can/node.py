# -- Imports ------------------------------------------------------------------

from re import fullmatch

# -- Class --------------------------------------------------------------------


class Node:
    """This class represents a CAN node of ICOtronic system"""

    def __init__(self, node=0):
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

        >>> Node('STH 1')
        STH 1

        >>> Node('STU1')
        STU 1

        >>> Node('STU 15')
        Traceback (most recent call last):
           ...
        ValueError: Unknown node identifier “STU 15”

        >>> Node('SPU 1').value
        15

        """

        if isinstance(node, str):

            # Check for broadcast pseudo nodes
            broadcast_match = fullmatch(
                "Broadcast With(?P<no_acknowledgment>out)? Acknowledgment",
                node)
            if broadcast_match:
                node.value = 0 if broadcast_match['no_acknowledgment'] else 31
                return

            # Check normal nodes
            node_match = fullmatch(
                "(?P<name>S(?:PU|TH|TU))\ ?(?P<number>\d{1,2})", node)

            node_name = node_match['name']
            node_number = int(node_match['number'])

            if node_name == 'STH' and 1 <= node_number <= 14:
                self.value = node_number
                return

            if node_name == 'SPU' and 1 <= node_number <= 2:
                self.value = node_number + 14
                return

            if node_name == 'STU' and 1 <= node_number <= 14:
                self.value = node_number + 16
                return

            raise ValueError(f"Unknown node identifier “{node}”")

        self.value = node

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
