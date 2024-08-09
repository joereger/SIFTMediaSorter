import pytest
import os
import json
import shutil
import random
import logging
import sys

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# Change the current working directory to the project root
os.chdir(project_root)

from sift_io_utils import SiftIOUtils
from sift_metadata_utils import SiftMetadataUtils
from constants import PUBLIC_ROOT, PRIVATE_ROOT, SAFE_DELETE_ROOT, METADATA_FOLDER

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

@pytest.fixture(scope="module")
def io_utils():
    return SiftIOUtils(PUBLIC_ROOT, PRIVATE_ROOT, SAFE_DELETE_ROOT)

@pytest.fixture
def test_environment(request):
    is_public_to_private = request.param
    source_root = PRIVATE_ROOT if is_public_to_private else PUBLIC_ROOT
    target_root = PUBLIC_ROOT if is_public_to_private else PRIVATE_ROOT
    
    test_folder = os.path.join(source_root, "1979", "tests", "test_01")
    os.makedirs(test_folder, exist_ok=True)
    random_images = find_random_images(PUBLIC_ROOT)
    for i, image_path in enumerate(random_images):
        _, ext = os.path.splitext(image_path)
        new_filename = f"test_image_{i+1}{ext}"
        shutil.copy2(image_path, os.path.join(test_folder, new_filename))
    print(f"Created test folder with {len(random_images)} images: {test_folder}")
    print(f"Test folder contents: {os.listdir(test_folder)}")

    yield test_folder, target_root, random_images, is_public_to_private

    if os.path.exists(test_folder):
        shutil.rmtree(test_folder)
    target_test_folder = os.path.join(target_root, "1979", "tests", "test_01")
    if os.path.exists(target_test_folder):
        shutil.rmtree(target_test_folder)

def find_random_images(root_dir, num_images=3):
    image_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                image_files.append(os.path.join(root, file))
        if len(image_files) >= num_images:
            break
    return random.sample(image_files, min(num_images, len(image_files)))

@pytest.mark.parametrize("test_environment", [True, False], indirect=True)
def test_batch_sort_directory(io_utils, test_environment, caplog):
    caplog.set_level(logging.DEBUG)
    
    test_folder, target_root, random_images, is_public_to_private = test_environment
    print("Starting test_batch_sort_directory")
    print(f"Current working directory: {os.getcwd()}")
    print(f"PUBLIC_ROOT: {PUBLIC_ROOT}")
    print(f"PRIVATE_ROOT: {PRIVATE_ROOT}")
    print(f"Test folder: {test_folder}")
    print(f"Target root: {target_root}")
    print(f"Is public to private: {is_public_to_private}")
    
    # Print contents of source folder before sorting
    print(f"Source folder contents before sort: {os.listdir(test_folder)}")
    
    # Sort the directory
    print(f"Sorting directory: {test_folder}")
    io_utils.sort(test_folder, is_public=not is_public_to_private)
    
    # 1. Verify files moved to target root
    target_test_folder = os.path.join(target_root, "1979", "tests", "test_01")
    print(f"Verifying files moved to target root: {target_test_folder}")
    print(f"Target folder exists: {os.path.exists(target_test_folder)}")
    
    if os.path.exists(target_test_folder):
        print(f"Target folder contents: {os.listdir(target_test_folder)}")
    else:
        print("Target folder does not exist")
    
    assert os.path.exists(target_test_folder), f"Files were not moved to target root: {target_test_folder}"
    
    for i in range(len(random_images)):
        expected_file = f"test_image_{i+1}"
        assert any(f.startswith(expected_file) for f in os.listdir(target_test_folder)), \
            f"{expected_file} was not moved to target root"
    
    # 2. Verify files deleted from source root
    print(f"Verifying files deleted from source root: {test_folder}")
    print(f"Source folder exists: {os.path.exists(test_folder)}")
    
    if os.path.exists(test_folder):
        print(f"Source folder contents after sort: {os.listdir(test_folder)}")
    else:
        print("Source folder no longer exists")
    
    assert not os.path.exists(test_folder), f"Files were not deleted from source root: {test_folder}"
    
    # 3. Verify metadata in target json file
    expected_status = "public" if not is_public_to_private else "private"
    metadata_file = os.path.join(METADATA_FOLDER, expected_status, f"{expected_status}_1979.json")
    print(f"Verifying metadata file: {metadata_file}")
    assert os.path.exists(metadata_file), f"Metadata file not found: {metadata_file}"
    
    with open(metadata_file, "r") as f:
        metadata = json.load(f)
    
    for i in range(len(random_images)):
        test_image_path = f"1979/tests/test_01/test_image_{i+1}"
        assert any(key.startswith(test_image_path) for key in metadata.keys()), \
            f"Metadata for {test_image_path} not found"
        file_metadata = next(metadata[key] for key in metadata.keys() if key.startswith(test_image_path))
        assert file_metadata["status"] == expected_status, f"File status is not set to {expected_status} for {test_image_path}"
        assert file_metadata["reviewed"], f"File is not marked as reviewed for {test_image_path}"
    
    # 4. Verify metadata not in source json file
    source_status = "private" if not is_public_to_private else "public"
    source_metadata_file = os.path.join(METADATA_FOLDER, source_status, f"{source_status}_1979.json")
    if os.path.exists(source_metadata_file):
        with open(source_metadata_file, "r") as f:
            source_metadata = json.load(f)
        for i in range(len(random_images)):
            test_image_path = f"1979/tests/test_01/test_image_{i+1}"
            assert not any(key.startswith(test_image_path) for key in source_metadata.keys()), \
                f"Metadata found in source json file for {test_image_path}"
    
    print("All tests completed")
    
    # Print captured log
    print("\nCaptured log:")
    print(caplog.text)