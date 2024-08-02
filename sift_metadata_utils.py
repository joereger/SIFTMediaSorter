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

    def initialize_metadata_for_directory(self, directory):
        file_count = 0
        status = 'public' if directory.startswith(self.public_root) else 'private'
        for dirpath, _, filenames in os.walk(directory):
            for filename in filenames:
                if filename.startswith('.'):  # Skip hidden files
                    continue
                filepath = os.path.join(dirpath, filename)
                relative_path = os.path.relpath(filepath, self.public_root if status == 'public' else self.private_root)
                year = self.get_year_from_path(relative_path)
                if year:
                    metadata = self.load_metadata_file(year, status)
                    if relative_path not in metadata:
                        metadata[relative_path] = {'status': status, 'last_reviewed': None, 'reviewed': False}
                        file_count += 1
                        self.save_metadata_file(year, status, metadata)
        print(f"Metadata initialized for directory {directory}, Total files processed: {file_count}")

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

    def get_directory_status(self, dir_path):
        status = {'public': 0, 'private': 0, 'reviewed': 0, 'unreviewed': 0}
        self.initialize_metadata_for_directory(dir_path)
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.startswith('.'):  # Skip hidden files
                    continue
                file_path = os.path.join(root, file)
                file_status, is_reviewed = self.get_file_status(file_path)
                if file_status == 'public':
                    status['public'] += 1
                elif file_status == 'private':
                    status['private'] += 1
                
                if is_reviewed:
                    status['reviewed'] += 1
                else:
                    status['unreviewed'] += 1
        return status

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

    def get_sorting_statistics(self):
        stats = {
            'public': 0,
            'private': 0,
            'reviewed': 0,
            'unreviewed': 0,
            'total': 0
        }
        for status in ['public', 'private']:
            for year in self.metadata[status].keys():
                metadata = self.load_metadata_file(year, status)
                for relative_path, file_data in metadata.items():
                    if relative_path.split(os.sep)[-1].startswith('.'):  # Skip hidden files
                        continue
                    stats['total'] += 1
                    if file_data['status'] == 'public':
                        stats['public'] += 1
                    elif file_data['status'] == 'private':
                        stats['private'] += 1
                    
                    if file_data.get('reviewed', False):
                        stats['reviewed'] += 1
                    else:
                        stats['unreviewed'] += 1
        
        if stats['total'] > 0:
            stats['percent_reviewed'] = (stats['reviewed'] / stats['total']) * 100
        else:
            stats['percent_reviewed'] = 0

        print(f"Sorting statistics: {stats}")
        return stats

    def get_recent_changes(self, days):
        cutoff = datetime.now() - timedelta(days=days)
        recent_changes = []
        for status in ['public', 'private']:
            for year in self.metadata[status].keys():
                metadata = self.load_metadata_file(year, status)
                for file, data in metadata.items():
                    if data['last_reviewed'] and datetime.fromisoformat(data['last_reviewed']) > cutoff:
                        recent_changes.append(file)
        print(f"Recent changes in the last {days} days: {len(recent_changes)} files")
        return recent_changes

    def export_sorting_data(self, output_file):
        full_metadata = {}
        for status in ['public', 'private']:
            for year in self.metadata[status].keys():
                full_metadata.update(self.load_metadata_file(year, status))
        with open(output_file, 'w') as f:
            json.dump(full_metadata, f, indent=2)
        print(f"Exported sorting data to {output_file}")

    def import_sorting_data(self, input_file):
        with open(input_file, 'r') as f:
            full_metadata = json.load(f)
        for file_path, data in full_metadata.items():
            root = self.public_root if data['status'] == 'public' else self.private_root
            relative_path = os.path.relpath(file_path, root)
            year = self.get_year_from_path(relative_path)
            if year:
                status = data['status']
                metadata = self.load_metadata_file(year, status)
                metadata[relative_path] = data
                self.save_metadata_file(year, status, metadata)
        self.save_index()
        print(f"Imported sorting data from {input_file}")

    def validate_file_paths(self):
        invalid_paths = []
        for status in ['public', 'private']:
            for year in list(self.metadata[status].keys()):
                metadata = self.load_metadata_file(year, status)
                for relative_path in list(metadata.keys()):
                    file_path = os.path.join(self.public_root if status == 'public' else self.private_root, relative_path)
                    if not os.path.exists(file_path):
                        invalid_paths.append(file_path)
                        del metadata[relative_path]
                self.save_metadata_file(year, status, metadata)
        self.save_index()
        print(f"Validated file paths. Found {len(invalid_paths)} invalid paths")
        return invalid_paths

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

    def update_existing_metadata(self):
        for status in ['public', 'private']:
            for year in self.metadata[status].keys():
                metadata = self.load_metadata_file(year, status)
                updated = False
                for relative_path, file_data in metadata.items():
                    if 'reviewed' not in file_data:
                        file_data['reviewed'] = file_data.get('last_reviewed') is not None
                        updated = True
                if updated:
                    self.save_metadata_file(year, status, metadata)
        print("Updated existing metadata with 'reviewed' field")

# Initialize metadata (run this only once if needed)
# SiftMetadataUtils(PUBLIC_ROOT, PRIVATE_ROOT).update_existing_metadata()