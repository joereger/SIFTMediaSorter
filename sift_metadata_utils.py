# IMPORTANT: This module should only be imported and used by sift_io_utils.py
# Other parts of the application should interact with metadata through the methods provided by SiftIOUtils

import os
import json
from datetime import datetime, timedelta
from constants import PUBLIC_ROOT, PRIVATE_ROOT, METADATA_FOLDER

class SiftMetadataUtils:
    def __init__(self, public_root, private_root):
        self.public_root = public_root
        self.private_root = private_root
        self.metadata = {'public': {}, 'private': {}}
        self.index_files = {
            'public': os.path.join(METADATA_FOLDER, 'index', 'public_index.json'),
            'private': os.path.join(METADATA_FOLDER, 'index', 'private_index.json')
        }
        self.metadata_cache = {}
        self.load_index()

    def load_index(self):
        for status, index_file in self.index_files.items():
            if os.path.exists(index_file):
                try:
                    with open(index_file, 'r') as f:
                        self.metadata[status] = json.load(f)
                except json.JSONDecodeError:
                    print(f"Error decoding index file for {status}. Starting with empty index.")
                    self.metadata[status] = {}
            else:
                print(f"No existing index file found for {status}. Starting with empty index.")

    def save_index(self):
        for status, index_file in self.index_files.items():
            os.makedirs(os.path.dirname(index_file), exist_ok=True)
            with open(index_file, 'w') as f:
                json.dump(self.metadata[status], f, indent=2)
            print(f"Index saved to {index_file}")

    def load_metadata_file(self, year, status):
        file_path = os.path.join(METADATA_FOLDER, status, f"{status}_{year}.json")
        if file_path in self.metadata_cache:
            return self.metadata_cache[file_path]

        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                self.metadata_cache[file_path] = data
                return data
            except json.JSONDecodeError:
                print(f"Error decoding metadata file: {file_path}. Starting with empty metadata.")
        return {}

    def save_metadata_file(self, year, status, metadata):
        file_path = os.path.join(METADATA_FOLDER, status, f"{status}_{year}.json")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        self.metadata_cache[file_path] = metadata
        print(f"Metadata for {year} ({status}) saved to {file_path}")

    def get_year_from_path(self, path):
        parts = path.split(os.sep)
        for part in parts:
            if part.isdigit() and len(part) == 4:
                return part
        return None

    def get_file_status(self, file_path):
        root = self.public_root if self.public_root in file_path else self.private_root
        relative_path = os.path.relpath(file_path, root)
        year = self.get_year_from_path(relative_path)
        if year:
            status = 'public' if root == self.public_root else 'private'
            metadata = self.load_metadata_file(year, status)
            file_data = metadata.get(relative_path, {})
            return file_data.get('status'), file_data.get('reviewed', False)
        return None, False

    def update_manual_review_status(self, file_path, new_status):
        root = self.public_root if self.public_root in file_path else self.private_root
        relative_path = os.path.relpath(file_path, root)
        year = self.get_year_from_path(relative_path)
        if year:
            current_status = 'public' if root == self.public_root else 'private'
            metadata = self.load_metadata_file(year, current_status)
            metadata[relative_path] = {
                'status': new_status,
                'last_reviewed': datetime.now().isoformat(),
                'reviewed': True
            }
            self.save_metadata_file(year, current_status, metadata)
            print(f"Updated manual review status for {file_path}: {new_status}")

    def update_file_path(self, old_path, new_path):
        root = self.public_root if self.public_root in old_path else self.private_root
        old_relative_path = os.path.relpath(old_path, root)
        new_relative_path = os.path.relpath(new_path, root)
        year = self.get_year_from_path(old_relative_path)
        if year:
            status = 'public' if root == self.public_root else 'private'
            metadata = self.load_metadata_file(year, status)
            if old_relative_path in metadata:
                metadata[new_relative_path] = metadata.pop(old_relative_path)
                self.save_metadata_file(year, status, metadata)
                print(f"Updated file path in metadata: {old_path} -> {new_path}")

# Initialize metadata (run this only once if needed)
# SiftMetadataUtils(PUBLIC_ROOT, PRIVATE_ROOT).update_existing_metadata()