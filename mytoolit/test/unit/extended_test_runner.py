# -- Imports ------------------------------------------------------------------

from unittest import TextTestRunner

from .extended_test_result import ExtendedTestResult

# -- Class --------------------------------------------------------------------


class ExtendedTestRunner(TextTestRunner):
    """Extend default test runner to change result class"""

    def __init__(self, *arguments, **keyword_arguments):
        """Initialize the test runner"""

        keyword_arguments["resultclass"] = ExtendedTestResult
        super().__init__(*arguments, **keyword_arguments)
