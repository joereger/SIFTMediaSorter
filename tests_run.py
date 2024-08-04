import unittest
import os
import importlib

def load_tests(loader, standard_tests, pattern):
    suite = unittest.TestSuite()
    for file in os.listdir(os.path.dirname(__file__)):
        if file.startswith("test_") and file.endswith(".py"):
            module_name = file[:-3]  # Remove .py extension
            module = importlib.import_module(module_name)
            suite.addTests(loader.loadTestsFromModule(module))
    return suite

if __name__ == "__main__":
    unittest.main()