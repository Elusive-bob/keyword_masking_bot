import inspect
import os
import sys
import unittest


class FinalTestResult(unittest.TextTestResult):
    def _location(self, test: unittest.case.TestCase) -> str:
        source_file = inspect.getsourcefile(test.__class__) or "<unknown>"
        relative_file = os.path.relpath(source_file, os.getcwd())
        return f"{relative_file}::{test.__class__.__name__}.{test._testMethodName}"

    def getDescription(self, test: unittest.case.TestCase) -> str:
        details = getattr(test, "_log_details", None)
        if details:
            return f"{self._location(test)} | {details}"
        return f"{self._location(test)} | {test.shortDescription() or test.id()}"

    def addSuccess(self, test: unittest.case.TestCase) -> None:
        super().addSuccess(test)
        self.stream.writeln(f"{self.getDescription(test)} ... OK\n")

    def addFailure(self, test: unittest.case.TestCase, err) -> None:
        super().addFailure(test, err)
        self.stream.writeln(f"{self.getDescription(test)} ... FAILED\n")

    def addError(self, test: unittest.case.TestCase, err) -> None:
        super().addError(test, err)
        self.stream.writeln(f"{self.getDescription(test)} ... ERROR\n")


class FinalTestRunner(unittest.TextTestRunner):
    resultclass = FinalTestResult


def main() -> int:
    # Discover all tests in the dedicated test folder.
    suite = unittest.defaultTestLoader.discover("tests")
    print("Starting test run")
    print("Discovery path: tests")
    runner = FinalTestRunner(stream=sys.stdout, verbosity=0)
    result = runner.run(suite)

    total = result.testsRun
    failed = len(result.failures) + len(result.errors)
    passed = total - failed
    print("\nTest run complete")
    print(f"Summary: total={total}, passed={passed}, failed={failed}")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
