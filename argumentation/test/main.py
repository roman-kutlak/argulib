import sys
import unittest

if __name__ == '__main__':
    loader = unittest.TestLoader()
    tests = loader.discover('./argumentation/test/', pattern="test_*.py")
    testRunner = unittest.runner.TextTestRunner(verbosity=2)
    testRunner.run(tests)
