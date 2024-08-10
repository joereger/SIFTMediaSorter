# This test file requires the 'parameterized' package.
# Install it using: pip install parameterized

import unittest
import os
import shutil
import json
from parameterized import parameterized
from sift_io_utils import SiftIOUtils
from constants import PUBLIC_ROOT, PRIVATE_ROOT, SAFE_DELETE_ROOT, METADATA_FOLDER

class TestSort(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create test directories and sample files
        cls.test_dirs = [
            os.path.join(PUBLIC_ROOT, '1975', 'foo'),
            os.path.join(PUBLIC_ROOT, '1975', 'bar')
        ]
        for dir_path in cls.test_dirs:
            os.makedirs(dir_path, exist_ok=True)
            
        cls.test_files = [
            os.path.join(PUBLIC_ROOT, '1975', 'foo', 'test1.jpg'),
            os.path.join(PUBLIC_ROOT, '1975', 'foo', 'test2.jpg'),
            os.path.join(PUBLIC_ROOT, '1975', 'bar', 'test3.jpg')
        ]
        for file_path in cls.test_files:
            with open(file_path, 'w') as f:
                f.write('Test content')

    @classmethod
    def tearDownClass(cls):
        # Clean up test directories and files
        shutil.rmtree(os.path.join(PUBLIC_ROOT, '1975'), ignore_errors=True)
        shutil.rmtree(os.path.join(PRIVATE_ROOT, '1975'), ignore_errors=True)
        shutil.rmtree(os.path.join(SAFE_DELETE_ROOT, 'public', '1975'), ignore_errors=True)
        shutil.rmtree(os.path.join(SAFE_DELETE_ROOT, 'private', '1975'), ignore_errors=True)
        if os.path.exists(os.path.join(METADATA_FOLDER, 'public', '1975', 'public_1975.json')):
            os.remove(os.path.join(METADATA_FOLDER, 'public', '1975', 'public_1975.json'))
        if os.path.exists(os.path.join(METADATA_FOLDER, 'private', '1975', 'private_1975.json')):
            os.remove(os.path.join(METADATA_FOLDER, 'private', '1975', 'private_1975.json'))

    @parameterized.expand([
        (os.path.join(PUBLIC_ROOT, '1975', 'foo'), False),  # Sort folder as private
        (os.path.join(PUBLIC_ROOT, '1975', 'bar'), True),   # Sort folder as public
        (os.path.join(PUBLIC_ROOT, '1975', 'foo', 'test1.jpg'), False),  # Sort file as private
        (os.path.join(PUBLIC_ROOT, '1975', 'bar', 'test3.jpg'), True),   # Sort file as public
    ])
    def test_sort(self, path_to_sort, is_public):
        sift_io = SiftIOUtils()
        sift_io.sort(path_to_sort, is_public)

        if os.path.isdir(path_to_sort):
            self._assert_folder_sort(path_to_sort, is_public)
        else:
            self._assert_file_sort(path_to_sort, is_public)

    def _assert_folder_sort(self, path_to_sort, is_public):
        folder_name = os.path.basename(path_to_sort)
        year = os.path.basename(os.path.dirname(path_to_sort))

        if is_public:
            self.assertTrue(os.path.exists(path_to_sort))
            self.assertFalse(os.path.exists(os.path.join(PRIVATE_ROOT, year, folder_name)))
        else:
            self.assertFalse(os.path.exists(path_to_sort))
            self.assertTrue(os.path.exists(os.path.join(PRIVATE_ROOT, year, folder_name)))
            self.assertTrue(os.path.exists(os.path.join(SAFE_DELETE_ROOT, 'public', year, folder_name)))

        metadata_file = os.path.join(METADATA_FOLDER, 'public' if is_public else 'private', year, f"{'public' if is_public else 'private'}_{year}.json")
        self.assertTrue(os.path.exists(metadata_file))

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        for root, _, files in os.walk(path_to_sort if is_public else os.path.join(PRIVATE_ROOT, year, folder_name)):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, PUBLIC_ROOT if is_public else PRIVATE_ROOT)
                self.assertIn(relative_path, metadata)
                self.assertEqual(metadata[relative_path]['status'], 'public' if is_public else 'private')
                self.assertTrue(metadata[relative_path]['reviewed'])

    def _assert_file_sort(self, path_to_sort, is_public):
        file_name = os.path.basename(path_to_sort)
        year = os.path.basename(os.path.dirname(os.path.dirname(path_to_sort)))
        folder_name = os.path.basename(os.path.dirname(path_to_sort))

        if is_public:
            self.assertTrue(os.path.exists(path_to_sort))
            self.assertFalse(os.path.exists(os.path.join(PRIVATE_ROOT, year, folder_name, file_name)))
        else:
            self.assertFalse(os.path.exists(path_to_sort))
            self.assertTrue(os.path.exists(os.path.join(PRIVATE_ROOT, year, folder_name, file_name)))
            self.assertTrue(os.path.exists(os.path.join(SAFE_DELETE_ROOT, 'public', year, folder_name, file_name)))

        metadata_file = os.path.join(METADATA_FOLDER, 'public' if is_public else 'private', year, f"{'public' if is_public else 'private'}_{year}.json")
        self.assertTrue(os.path.exists(metadata_file))

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        relative_path = os.path.relpath(path_to_sort if is_public else os.path.join(PRIVATE_ROOT, year, folder_name, file_name), PUBLIC_ROOT if is_public else PRIVATE_ROOT)
        self.assertIn(relative_path, metadata)
        self.assertEqual(metadata[relative_path]['status'], 'public' if is_public else 'private')
        self.assertTrue(metadata[relative_path]['reviewed'])

if __name__ == '__main__':
    unittest.main()