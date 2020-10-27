# -- Imports ------------------------------------------------------------------

from os.path import abspath, dirname
from sys import path as module_path
from unittest import main

# Add path for custom libraries
repository_root = dirname(dirname(dirname(dirname(abspath(__file__)))))
module_path.append(repository_root)

from mytoolit.test.production import TestNode
from mytoolit.unittest import ExtendedTestRunner

# -- Class --------------------------------------------------------------------


class TestSTU(TestNode):
    """This class contains tests for the Stationary Transceiver Unit (STU)"""


# -- Main ---------------------------------------------------------------------

if __name__ == "__main__":
    main(testRunner=ExtendedTestRunner)
