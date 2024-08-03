import os
import shutil
import hashlib
import logging
from datetime import datetime, timedelta
from sift_metadata_utils import SiftMetadataUtils

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SiftIOUtils:
    def __init__(self, public_root, private_root, safe_delete_root, gui_refresh_callback=None):
        self.public_root = public_root
        self.private_root = private_root
        self.safe_delete_root = safe_delete_root
        self.metadata_utils = SiftMetadataUtils(public_root, private_root)
        self.gui_refresh_callback = gui_refresh_callback

    def list_directory(self, directory):
        contents = os.listdir(directory)
        logging.info(f"Listed directory {directory}: {len(contents)} items found")
        return contents

    def sort_file(self, path, is_public):
        if os.path.isdir(path):
            logging.info(f"Sorting directory: {path}")
            self.batch_sort_directory(path, is_public)
        else:
            logging.info(f"Sorting file: {path}")
            current_status = self.metadata_utils.get_file_status(path)
            new_status = 'public' if is_public else 'private'
            if current_status != new_status:
                new_path, _, _ = self.move_file(path, is_public)
                self.metadata_utils.update_manual_review_status(new_path, new_status)
            else:
                self.metadata_utils.update_manual_review_status(path, new_status)

    def move_file(self, file_path, is_public):
        if os.path.isdir(file_path):
            logging.info(f"Skipping directory in move_file: {file_path}")
            return file_path, False, []

        source_root = self.public_root if file_path.startswith(self.public_root) else self.private_root
        dest_root = self.public_root if is_public else self.private_root
        rel_path = os.path.relpath(file_path, source_root)
        dest_path = os.path.join(dest_root, rel_path)

        logging.info(f"Moving file from {file_path} to {dest_path}")

        new_dir_created = self.create_directory_if_not_exists(os.path.dirname(dest_path))

        if os.path.exists(dest_path):
            base, ext = os.path.splitext(dest_path)
            counter = 1
            while os.path.exists(f"{base}_{counter}{ext}"):
                counter += 1
            dest_path = f"{base}_{counter}{ext}"
            logging.info(f"Destination file already exists. Renamed to {dest_path}")

        self.create_backup(file_path)
        shutil.copy2(file_path, dest_path)

        if self.verify_file_integrity(file_path, dest_path):
            os.remove(file_path)
            logging.info(f"File moved successfully: {file_path} -> {dest_path}")
            self.metadata_utils.update_file_path(file_path, dest_path)
            removed_dirs = self.remove_empty_directories(os.path.dirname(file_path))
            return dest_path, new_dir_created, removed_dirs
        else:
            logging.error(f"File integrity check failed for {file_path}")
            raise Exception("File integrity check failed")

    def create_directory_if_not_exists(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)
            logging.info(f"Created new directory: {directory}")
            return True
        return False

    def remove_empty_directories(self, path):
        removed_dirs = []
        for root, dirs, files in os.walk(path, topdown=False):
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    removed_dirs.append(dir_path)
                    logging.info(f"Removed empty directory: {dir_path}")

        if not os.listdir(path):
            os.rmdir(path)
            removed_dirs.append(path)
            logging.info(f"Removed empty directory: {path}")

        return removed_dirs

    def batch_sort_directory(self, dir_path, is_public, progress_callback=None):
        logging.info(f"Batch sorting directory: {dir_path}")
        files_to_sort = []
        for root, _, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                current_status = self.metadata_utils.get_file_status(file_path)
                new_status = 'public' if is_public else 'private'
                if current_status != new_status:
                    files_to_sort.append(file_path)

        total_files = len(files_to_sort)
        for i, file_path in enumerate(files_to_sort):
            self.sort_file(file_path, is_public)
            if progress_callback:
                progress_callback(int((i + 1) / total_files * 100))

        self.refresh_directory_stats(dir_path)
        logging.info(f"Completed batch sorting of directory: {dir_path}. {total_files} files sorted.")

    def undo_sort(self, file_path):
        logging.info(f"Undo sort not implemented for: {file_path}")
        # Implementation depends on how you want to handle undo
        pass

    def get_file_metadata(self, file_path):
        metadata = {
            'creation_time': os.path.getctime(file_path),
            'modification_time': os.path.getmtime(file_path),
            'size': os.path.getsize(file_path)
        }
        logging.info(f"Retrieved metadata for {file_path}: {metadata}")
        return metadata

    def generate_file_checksum(self, file_path):
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        checksum = hasher.hexdigest()
        logging.info(f"Generated checksum for {file_path}: {checksum}")
        return checksum

    def verify_file_integrity(self, source_path, destination_path):
        result = self.generate_file_checksum(source_path) == self.generate_file_checksum(destination_path)
        logging.info(f"File integrity verification: {source_path} -> {destination_path}: {'Passed' if result else 'Failed'}")
        return result

    def search_files(self, query, root_directory):
        results = []
        for root, _, files in os.walk(root_directory):
            for file in files:
                if query.lower() in file.lower():
                    results.append(os.path.join(root, file))
        logging.info(f"Search for '{query}' in {root_directory}: {len(results)} results found")
        return results

    def create_backup(self, file_path):
        if os.path.isdir(file_path):
            logging.info(f"Skipping backup for directory: {file_path}")
            return
        backup_dir = os.path.join(self.safe_delete_root, 'public' if self.metadata_utils.get_file_status(file_path) == 'public' else 'private')
        os.makedirs(backup_dir, exist_ok=True)
        backup_path = shutil.copy2(file_path, backup_dir)
        logging.info(f"Created backup: {file_path} -> {backup_path}")

    def restore_from_backup(self, file_path):
        logging.info(f"Restore from backup not implemented for: {file_path}")
        # Implementation depends on how you want to handle backups
        pass

    def cleanup_safe_delete_folder(self, days_old):
        cutoff = datetime.now() - timedelta(days=days_old)
        cleaned_files = 0
        for root, _, files in os.walk(self.safe_delete_root):
            for file in files:
                file_path = os.path.join(root, file)
                if datetime.fromtimestamp(os.path.getctime(file_path)) < cutoff:
                    os.remove(file_path)
                    cleaned_files += 1
        logging.info(f"Cleaned up {cleaned_files} files older than {days_old} days from safe delete folder")

    def get_directory_status(self, dir_path):
        status = {'public': 0, 'private': 0, 'reviewed': 0, 'unreviewed': 0, 'total': 0}
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.startswith('.'):
                    continue
                file_path = os.path.join(root, file)
                file_status, is_reviewed = self.metadata_utils.get_file_status(file_path)
                status['total'] += 1
                if file_status == 'public':
                    status['public'] += 1
                elif file_status == 'private':
                    status['private'] += 1
                if is_reviewed:
                    status['reviewed'] += 1
                else:
                    status['unreviewed'] += 1
        logging.info(f"Directory status for {dir_path}: {status}")
        return status

    def refresh_directory_stats(self, start_path):
        paths_to_refresh = []
        current_path = start_path
        while current_path != self.public_root and current_path != self.private_root:
            paths_to_refresh.append(current_path)
            current_path = os.path.dirname(current_path)
        paths_to_refresh.append(current_path)  # Add root directory

        for path in reversed(paths_to_refresh):
            status = self.get_directory_status(path)
            logging.info(f"Refreshed stats for {path}: {status}")
            if self.gui_refresh_callback:
                self.gui_refresh_callback(path)

    # New wrapper method for accessing review status
    def get_file_review_status(self, file_path):
        status, is_reviewed = self.metadata_utils.get_file_status(file_path)
        return is_reviewed

    # New wrapper method for updating review status
    def update_file_review_status(self, file_path, is_public):
        new_status = 'public' if is_public else 'private'
        self.metadata_utils.update_manual_review_status(file_path, new_status)