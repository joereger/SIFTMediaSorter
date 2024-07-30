import os
from sift_io_utils import SiftIOUtils

# Setup test directories
public_root = 'test_public'
private_root = 'test_private'
safe_delete_root = 'test_safe_delete'

# Ensure safe_delete_root exists
os.makedirs(safe_delete_root, exist_ok=True)

# Initialize SiftIOUtils
sift = SiftIOUtils(public_root, private_root, safe_delete_root)

def test_list_directory():
    print("\n--- Testing list_directory ---")
    public_files = sift.list_directory(public_root)
    private_files = sift.list_directory(private_root)
    print(f"Public files: {public_files}")
    print(f"Private files: {private_files}")

def test_sort_file():
    print("\n--- Testing sort_file ---")
    # Sort a file from public to private
    public_files = [f for f in sift.list_directory(public_root) if os.path.isfile(os.path.join(public_root, f))]
    if public_files:
        test_file = os.path.join(public_root, public_files[0])
        print(f"Sorting {test_file} to private")
        sift.sort_file(test_file, False)
    else:
        print("No files in public directory to test sorting")

    # Sort a file from private to public
    private_files = [f for f in sift.list_directory(private_root) if os.path.isfile(os.path.join(private_root, f))]
    if private_files:
        test_file = os.path.join(private_root, private_files[0])
        print(f"Sorting {test_file} to public")
        sift.sort_file(test_file, True)
    else:
        print("No files in private directory to test sorting")

def test_get_file_status():
    print("\n--- Testing get_file_status ---")
    for root in [public_root, private_root]:
        for item in sift.list_directory(root):
            item_path = os.path.join(root, item)
            if os.path.isfile(item_path):
                status = sift.get_file_status(item_path)
                print(f"{item_path}: {status}")

def test_get_directory_status():
    print("\n--- Testing get_directory_status ---")
    public_status = sift.get_directory_status(public_root)
    private_status = sift.get_directory_status(private_root)
    print(f"Public status: {public_status}")
    print(f"Private status: {private_status}")

def test_batch_sort_directory():
    print("\n--- Testing batch_sort_directory ---")
    # Find a subdirectory in public to test
    public_subdirs = [d for d in sift.list_directory(public_root) if os.path.isdir(os.path.join(public_root, d))]
    if public_subdirs:
        test_subdir = os.path.join(public_root, public_subdirs[0])
        print(f"Batch sorting {test_subdir} to private")
        sift.batch_sort_directory(test_subdir, False)
    else:
        print("No subdirectories in public directory to test batch sorting")

def test_search_files():
    print("\n--- Testing search_files ---")
    query = input("Enter a search query: ")
    public_results = sift.search_files(query, public_root)
    private_results = sift.search_files(query, private_root)
    print(f"Search results in public: {public_results}")
    print(f"Search results in private: {private_results}")

def test_get_sorting_statistics():
    print("\n--- Testing get_sorting_statistics ---")
    stats = sift.get_sorting_statistics()
    print(f"Sorting statistics: {stats}")

def test_get_recent_changes():
    print("\n--- Testing get_recent_changes ---")
    days = 7  # Get changes in the last 7 days
    recent_changes = sift.get_recent_changes(days)
    print(f"Changes in the last {days} days: {recent_changes}")

def test_validate_file_paths():
    print("\n--- Testing validate_file_paths ---")
    invalid_paths = sift.validate_file_paths()
    if invalid_paths:
        print(f"Invalid paths found: {invalid_paths}")
    else:
        print("All file paths are valid")

def run_tests():
    test_list_directory()
    test_sort_file()
    test_get_file_status()
    test_get_directory_status()
    test_batch_sort_directory()
    test_search_files()
    test_get_sorting_statistics()
    test_get_recent_changes()
    test_validate_file_paths()

if __name__ == "__main__":
    run_tests()