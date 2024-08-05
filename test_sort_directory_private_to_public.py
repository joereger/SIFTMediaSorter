import unittest
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TestIOMetadata(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.io_utils = SiftIOUtils(PUBLIC_ROOT, PRIVATE_ROOT, SAFE_DELETE_ROOT)

    def setUp(self):
        self.test_folder = os.path.join(PRIVATE_ROOT, "1979", "tests", "test_01")
        os.makedirs(self.test_folder, exist_ok=True)
        self.random_images = self.find_random_images(PUBLIC_ROOT)
        for i, image_path in enumerate(self.random_images):
            _, ext = os.path.splitext(image_path)
            new_filename = f"test_image_{i+1}{ext}"
            shutil.copy2(image_path, os.path.join(self.test_folder, new_filename))
        logging.info(f"Created test folder with {len(self.random_images)} images: {self.test_folder}")

    def tearDown(self):
        if os.path.exists(self.test_folder):
            shutil.rmtree(self.test_folder)
        private_test_folder = os.path.join(PUBLIC_ROOT, "1979", "tests", "test_01")
        if os.path.exists(private_test_folder):
            shutil.rmtree(private_test_folder)

    @staticmethod
    def find_random_images(root_dir, num_images=3):
        image_files = []
        for root, _, files in os.walk(root_dir):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    image_files.append(os.path.join(root, file))
            if len(image_files) >= num_images:
                break
        return random.sample(image_files, min(num_images, len(image_files)))

    def test_batch_sort_directory(self):
        logging.info("Starting test_batch_sort_directory")
        logging.info(f"Current working directory: {os.getcwd()}")
        
        # Sort the directory as Private
        logging.info(f"Sorting directory: {self.test_folder}")
        self.io_utils.sort(self.test_folder, is_public=True)
        
        # 1. Verify files moved to private root
        public_test_folder = os.path.join(PUBLIC_ROOT, "1979", "tests", "test_01")
        logging.info(f"Verifying files moved to private root: {public_test_folder}")
        self.assertTrue(os.path.exists(public_test_folder), f"Files were not moved to public root: {public_test_folder}")
        for i in range(len(self.random_images)):
            self.assertTrue(any(f.startswith(f"test_image_{i+1}") for f in os.listdir(public_test_folder)), 
                            f"test_image_{i+1} was not moved to public root")
        
        # 2. Verify files deleted from public root
        logging.info(f"Verifying files deleted from private root: {self.test_folder}")
        self.assertFalse(os.path.exists(self.test_folder), f"Files were not deleted from private root: {self.test_folder}")
        
        # 3. Verify metadata in public_1979.json
        metadata_file = os.path.join(METADATA_FOLDER, "public", "public_1979.json")
        logging.info(f"Verifying metadata file: {metadata_file}")
        self.assertTrue(os.path.exists(metadata_file), f"Metadata file not found: {metadata_file}")
        
        with open(metadata_file, "r") as f:
            metadata = json.load(f)
        
        for i in range(len(self.random_images)):
            test_image_path = f"1979/tests/test_01/test_image_{i+1}"
            self.assertTrue(any(key.startswith(test_image_path) for key in metadata.keys()), 
                            f"Metadata for {test_image_path} not found")
            file_metadata = next(metadata[key] for key in metadata.keys() if key.startswith(test_image_path))
            self.assertEqual(file_metadata["status"], "public", f"File status is not set to public for {test_image_path}")
            self.assertTrue(file_metadata["reviewed"], f"File is not marked as reviewed for {test_image_path}")
        
        # 4. Verify metadata not in private_1979.json
        private_metadata_file = os.path.join(METADATA_FOLDER, "private", "private_1979.json")
        if os.path.exists(private_metadata_file):
            with open(private_metadata_file, "r") as f:
                public_metadata = json.load(f)
            for i in range(len(self.random_images)):
                test_image_path = f"1979/tests/test_01/test_image_{i+1}"
                self.assertFalse(any(key.startswith(test_image_path) for key in public_metadata.keys()), 
                                 f"Metadata found in private json file for {test_image_path}")
        
        logging.info("All tests passed successfully!")

if __name__ == "__main__":
    unittest.main()