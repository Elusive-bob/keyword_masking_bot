import unittest


class LoggedTestCase(unittest.TestCase):
    """Base test case with structured log fields for the custom runner."""

    def set_test_log(
        self,
        module_object: str,
        test_arguments: str,
        asserted_output: str,
        output: str,
    ) -> None:
        """Store structured log details consumed by the custom test runner."""

        self._log_module_object = module_object
        self._log_arguments = test_arguments
        self._log_asserted_output = asserted_output
        self._log_output = output