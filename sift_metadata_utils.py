# IMPORTANT: This module should only be imported and used by sift_io_utils.py
# Other parts of the application should interact with metadata through the methods provided by SiftIOUtils

import os
import json
from datetime import datetime, timedelta
from constants import PUBLIC_ROOT, PRIVATE_ROOT, METADATA_FOLDER
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SiftMetadataUtils:
    def __init__(self):
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
                    logging.error(f"Error decoding index file for {status}. Starting with empty index.")
                    self.metadata[status] = {}
            else:
                logging.debug(f"No existing index file found for {status}. Starting with empty index.")

    def save_index(self):
        for status, index_file in self.index_files.items():
            os.makedirs(os.path.dirname(index_file), exist_ok=True)
            with open(index_file, 'w') as f:
                json.dump(self.metadata[status], f, indent=2)
            logging.debug(f"Index saved to {index_file}")

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
                logging.error(f"Error decoding metadata file: {file_path}. Starting with empty metadata.")
        return {}

    def save_metadata_file(self, year, status, metadata):
        file_path = os.path.join(METADATA_FOLDER, status, f"{status}_{year}.json")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        self.metadata_cache[file_path] = metadata
        logging.debug(f"Metadata for {year} ({status}) saved to {file_path}")

    def get_year_from_path(self, path):
        parts = path.split(os.sep)
        for part in parts:
            if part.isdigit() and len(part) == 4:
                return part
        return None

    def get_file_status(self, file_path):
        root = PUBLIC_ROOT if PUBLIC_ROOT in file_path else PRIVATE_ROOT
        relative_path = os.path.relpath(file_path, root)
        year = self.get_year_from_path(relative_path)
        if year:
            status = 'public' if root == PUBLIC_ROOT else 'private'
            metadata = self.load_metadata_file(year, status)
            file_data = metadata.get(relative_path, {})
            return file_data.get('status'), file_data.get('reviewed', False)
        return None, False

    def update_manual_review_status(self, file_path, new_status):
        root = PUBLIC_ROOT if PUBLIC_ROOT in file_path else PRIVATE_ROOT
        relative_path = os.path.relpath(file_path, root)
        year = self.get_year_from_path(relative_path)
        logging.debug(f"Updating manual review status for file: {file_path}")
        logging.debug(f"Extracted year from path: {year}")
        if year:
            current_status = 'public' if root == PUBLIC_ROOT else 'private'
            
            # Remove metadata from the old status file
            old_metadata = self.load_metadata_file(year, current_status)
            if relative_path in old_metadata:
                del old_metadata[relative_path]
                self.save_metadata_file(year, current_status, old_metadata)
            
            # Add metadata to the new status file
            new_metadata = self.load_metadata_file(year, new_status)
            new_metadata[relative_path] = {
                'status': new_status,
                'last_reviewed': datetime.now().isoformat(),
                'reviewed': True
            }
            self.save_metadata_file(year, new_status, new_metadata)
            
            # Update the index
            self.metadata[new_status][relative_path] = {
                'year': year,
                'status': new_status,
                'last_reviewed': datetime.now().isoformat(),
                'reviewed': True
            }
            
            logging.debug(f"Updated manual review status for {file_path}: {new_status}")
        else:
            logging.error(f"Could not extract year from file path: {file_path}")

    def update_file_path(self, old_path, new_path):
        old_root = PUBLIC_ROOT if PUBLIC_ROOT in old_path else PRIVATE_ROOT
        new_root = PUBLIC_ROOT if PUBLIC_ROOT in new_path else PRIVATE_ROOT
        old_relative_path = os.path.relpath(old_path, old_root)
        new_relative_path = os.path.relpath(new_path, new_root)
        old_year = self.get_year_from_path(old_relative_path)
        new_year = self.get_year_from_path(new_relative_path)
        
        logging.debug(f"Updating file path: {old_path} -> {new_path}")
        logging.debug(f"Old year: {old_year}, New year: {new_year}")
        
        if old_year and new_year:
            old_status = 'public' if old_root == PUBLIC_ROOT else 'private'
            new_status = 'public' if new_root == PUBLIC_ROOT else 'private'
            
            # Load old metadata
            old_metadata = self.load_metadata_file(old_year, old_status)
            
            # If old path not found, create a new entry
            if old_relative_path not in old_metadata:
                logging.warning(f"Old path {old_relative_path} not found in metadata. Creating new entry.")
                old_metadata[old_relative_path] = {
                    'status': old_status,
                    'last_reviewed': datetime.now().isoformat(),
                    'reviewed': False
                }
            
            # Move metadata to new location
            file_data = old_metadata.pop(old_relative_path)
            self.save_metadata_file(old_year, old_status, old_metadata)
            
            new_metadata = self.load_metadata_file(new_year, new_status)
            new_metadata[new_relative_path] = file_data
            new_metadata[new_relative_path]['status'] = new_status
            self.save_metadata_file(new_year, new_status, new_metadata)
            
            # Update the index
            if old_relative_path in self.metadata[old_status]:
                del self.metadata[old_status][old_relative_path]
            self.metadata[new_status][new_relative_path] = {
                'year': new_year,
                'status': new_status,
                'last_reviewed': datetime.now().isoformat(),
                'reviewed': True
            }
            
            logging.debug(f"Updated file path in metadata: {old_path} -> {new_path}")
        else:
            logging.error(f"Could not extract year from file paths: {old_path} -> {new_path}")

    def save_all_metadata(self):
        logging.debug(f"Saving all metadata. Cache size: {len(self.metadata_cache)}")
        for status in ['public', 'private']:
            metadata_by_year = {}
            for relative_path, file_data in self.metadata[status].items():
                year = file_data['year']
                if year not in metadata_by_year:
                    metadata_by_year[year] = {}
                metadata_by_year[year][relative_path] = file_data

            for year, metadata in metadata_by_year.items():
                file_path = os.path.join(METADATA_FOLDER, status, f"{status}_{year}.json")
                logging.debug(f"Attempting to save metadata file: {file_path}")
                try:
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, 'w') as f:
                        json.dump(metadata, f, indent=2)
                    logging.debug(f"Successfully saved metadata to {file_path}")
                except Exception as e:
                    logging.error(f"Error saving metadata file {file_path}: {str(e)}")

        self.metadata_cache.clear()
        logging.debug("All metadata files saved and cache cleared")

# Initialize metadata (run this only once if needed)
# SiftMetadataUtils(PUBLIC_ROOT, PRIVATE_ROOT).update_existing_metadata()