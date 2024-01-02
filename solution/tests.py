import unittest

if __name__ == '__main__':
    loader = unittest.TestLoader()
    tests = loader.discover('solution/tests', pattern='test_*.py')
    test_runner = unittest.TextTestRunner()
    result = test_runner.run(tests)