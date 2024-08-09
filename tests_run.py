import pytest
import sys

if __name__ == "__main__":
    print("Running tests with pytest...")
    
    # Run pytest and capture the return code
    return_code = pytest.main(["-v", "--tb=short"])
    
    # Print a summary based on the return code
    if return_code == 0:
        print("\nAll tests passed successfully!")
    elif return_code == 1:
        print("\nSome tests failed. Please check the output above for details.")
    elif return_code == 2:
        print("\nTest execution was interrupted by the user.")
    elif return_code == 3:
        print("\nAn internal error occurred while running the tests.")
    elif return_code == 4:
        print("\nPytest usage error.")
    elif return_code == 5:
        print("\nNo tests were collected.")
    
    # Exit with the return code from pytest
    sys.exit(return_code)