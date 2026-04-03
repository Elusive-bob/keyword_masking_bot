import inspect
import os
import sys
import unittest


class FinalTestResult(unittest.TextTestResult):
    def _location(self, test: unittest.case.TestCase) -> str:
        source_file = inspect.getsourcefile(test.__class__) or "<unknown>"
        relative_file = os.path.relpath(source_file, os.getcwd())
        return f"{relative_file}::{test.__class__.__name__}.{test._testMethodName}"

    def _format_result(self, test: unittest.case.TestCase, status: str) -> str:
        module_object = getattr(test, "_log_module_object", self._location(test))
        test_arguments = getattr(test, "_log_arguments", "n/a")
        asserted_output = getattr(test, "_log_asserted_output", "n/a")
        output = getattr(test, "_log_output", test.shortDescription() or test.id())
        return (
            f"TESTED OBJECT: {module_object}\n"
            f"TEST ARGUMENTS: {test_arguments}\n"
            f"EXPECTED RESULT: {asserted_output}\n"
            f"ACTUAL RESULT: {output}\n"
            f"STATUS: {status}\n"
        )

    def addSuccess(self, test: unittest.case.TestCase) -> None:
        super().addSuccess(test)
        self.stream.writeln(self._format_result(test, "OK"))

    def addFailure(self, test: unittest.case.TestCase, err) -> None:
        super().addFailure(test, err)
        self.stream.writeln(self._format_result(test, "FAILED"))

    def addError(self, test: unittest.case.TestCase, err) -> None:
        super().addError(test, err)
        self.stream.writeln(self._format_result(test, "FAILED"))


class FinalTestRunner(unittest.TextTestRunner):
    resultclass = FinalTestResult


def main() -> int:
    suite = unittest.defaultTestLoader.discover("tests", pattern="test_*.py")
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
