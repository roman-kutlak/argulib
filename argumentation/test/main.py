import sys
import unittest

# we are assuming that the file runs from $(ASPIC-_ROOT)/tests
sys.path.insert(0, '../src')

if __name__ == '__main__':
    loader = unittest.TestLoader()
    tests = loader.discover('.', pattern="*_test.py")
    testRunner = unittest.runner.TextTestRunner(verbosity=2)
    testRunner.run(tests)
