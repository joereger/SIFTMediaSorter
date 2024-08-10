import os
import shutil
import hashlib
import logging
from datetime import datetime, timedelta
from sift_metadata_utils import SiftMetadataUtils
from constants import PUBLIC_ROOT, PRIVATE_ROOT, METADATA_FOLDER, SAFE_DELETE_ROOT
import pdb  # Add this import at the top of the file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SiftIOUtils:
    def __init__(self, gui_refresh_callback=None):
        self.metadata_utils = SiftMetadataUtils()
        self.gui_refresh_callback = gui_refresh_callback

    def list_directory(self, directory):
        contents = os.listdir(directory)
        logging.debug(f"Listed directory {directory}: {len(contents)} items found")
        return contents

    def sort(self, path, is_public):
        if os.path.isdir(path):
            logging.debug(f"sort() called on a directory: {path}")
            pdb.set_trace() 
            self.batch_sort_directory(path, is_public)
        else:
            logging.debug(f"sort() called on a file: {path}")
            pdb.set_trace()
            current_root = PRIVATE_ROOT if path.startswith(PRIVATE_ROOT) else PUBLIC_ROOT
            target_root = PUBLIC_ROOT if is_public else PRIVATE_ROOT
            
            if current_root == target_root:
                logging.debug(f"sort() current_root == target_root so just updating metadata")
                pdb.set_trace()
                # File is already in the correct root, just update metadata
                self.update_file_metadata(path, is_public)
                new_path = path
            else:
                logging.debug(f"sort() current_root is not target_root so file must be moved.")
                pdb.set_trace()
                # File needs to be moved
                new_path, _, _ = self.move_file(path, is_public)
            
            self.refresh_directory_stats(os.path.dirname(new_path))
            
            return new_path

    def update_file_metadata(self, path, is_public):
        new_status = 'public' if is_public else 'private'
        self.metadata_utils.update_manual_review_status(path, new_status)
        logging.debug(f"Updated metadata for {path}: status={new_status}, reviewed=True")

    def move_file(self, file_path, is_public):
        logging.debug(f"move_file() called file_path: {file_path}")
        pdb.set_trace()
        if os.path.isdir(file_path):
            logging.debug(f"Skipping directory in move_file: {file_path}")
            return file_path, False, []

        source_root = PUBLIC_ROOT if file_path.startswith(PUBLIC_ROOT) else PRIVATE_ROOT
        dest_root = PUBLIC_ROOT if is_public else PRIVATE_ROOT
        rel_path = os.path.relpath(file_path, source_root)
        dest_path = os.path.join(dest_root, rel_path)

        logging.debug(f"Moving file from {file_path} to {dest_path}")
        new_dir_created = self.create_directory_if_not_exists(os.path.dirname(dest_path))

        if os.path.exists(dest_path):
            base, ext = os.path.splitext(dest_path)
            counter = 1
            while os.path.exists(f"{base}_{counter}{ext}"):
                counter += 1
            dest_path = f"{base}_{counter}{ext}"
            logging.debug(f"Destination file already exists. Renamed to {dest_path}")

        self.create_backup(file_path)
        shutil.copy2(file_path, dest_path)

        logging.debug(f"File moved, will start cleanup: {dest_path}")
        pdb.set_trace()

        if self.verify_file_integrity(file_path, dest_path):
            os.remove(file_path)
            logging.debug(f"File removed successfully: {file_path} -> {dest_path}")
            self.metadata_utils.update_file_path(file_path, dest_path)
            
            original_dir = os.path.dirname(file_path)
            dir_removed = self.check_and_remove_empty_directory(original_dir)

            logging.debug(f"move_file() done: {file_path}")
            pdb.set_trace()
            
            return dest_path, new_dir_created, dir_removed
        else:
            logging.error(f"move_file() File integrity check failed for {file_path}")
            pdb.set_trace()
            raise Exception("File integrity check failed")
        
        

    def create_directory_if_not_exists(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)
            logging.debug(f"Created new directory: {directory}")
            pdb.set_trace()
            return True
        return False

    def check_and_remove_empty_directory(self, directory):
        logging.debug(f"Checking directory for removal: {directory}")
        if directory == PUBLIC_ROOT or directory == PRIVATE_ROOT:
            logging.debug(f"Skipping root directory: {directory}")
            return False  # Don't remove root directories
        
        try:
            # Remove .DS_Store if present
            ds_store_path = os.path.join(directory, '.DS_Store')
            if os.path.exists(ds_store_path):
                os.remove(ds_store_path)
                logging.debug(f"Removed .DS_Store file from {directory}")

            # Get contents, ignoring .DS_Store
            contents = [item for item in os.listdir(directory) if item != '.DS_Store']
            logging.debug(f"Directory contents (excluding .DS_Store): {contents}")
            
            if not contents:
                logging.debug(f"Directory appears empty, double-checking: {directory}")
                # Double-check for any hidden files, ignoring .DS_Store
                scanned_contents = [entry for entry in os.scandir(directory) if entry.name != '.DS_Store']
                logging.debug(f"Scanned directory contents (excluding .DS_Store): {[entry.name for entry in scanned_contents]}")
                
                if not scanned_contents:
                    logging.debug(f"Attempting to remove empty directory: {directory}")
                    os.rmdir(directory)
                    logging.debug(f"Successfully removed empty directory: {directory}")
                    return True
                else:
                    logging.debug(f"Directory not empty after scan, skipping removal: {directory}")
            else:
                logging.debug(f"Directory not empty, skipping removal: {directory}")
        except Exception as e:
            logging.error(f"Error checking/removing directory {directory}: {str(e)}")
        
        return False

    # NOTE: This method should only be called from within sift_io_utils.py.
    # For external sorting operations, use the sort() method instead.
    def batch_sort_directory(self, dir_path, is_public, progress_callback=None):
        logging.debug(f"batch_sort_directory() called on: {dir_path}")
        files_to_process = []
        for root, _, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                files_to_process.append(file_path)

        total_files = len(files_to_process)
        logging.debug(f"Found {total_files} files to process")

        for i, file_path in enumerate(files_to_process):
            logging.debug(f"Processing file {i+1}/{total_files}: {file_path}")
            self.sort(file_path, is_public)
            if progress_callback:
                progress_callback(int((i + 1) / total_files * 100))

        logging.debug("All files processed, starting cleanup")
        self.batch_cleanup_empty_directories(dir_path)
        
        logging.debug("Saving all metadata")
        self.metadata_utils.save_all_metadata()
        
        logging.debug("Saving index")
        self.metadata_utils.save_index()
        
        logging.debug("Refreshing directory stats")
        self.refresh_directory_stats(dir_path)
        
        logging.debug(f"Completed batch sorting of directory: {dir_path}. {total_files} files processed.")

    def cleanup_empty_directories(self, directory):
        logging.debug(f"Starting cleanup of empty directories in: {directory}")
        for root, dirs, files in os.walk(directory, topdown=False):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                self.check_and_remove_empty_directory(dir_path)
        
        # Check the root directory itself
        self.check_and_remove_empty_directory(directory)
        logging.debug(f"Completed cleanup of empty directories in: {directory}")

    def batch_cleanup_empty_directories(self, dir_path):
        logging.debug(f"Starting batch cleanup of empty directories for: {dir_path}")
        self.cleanup_empty_directories(dir_path)
        logging.debug(f"Completed batch cleanup of empty directories for: {dir_path}")

    def undo_sort(self, file_path):
        logging.debug(f"Undo sort not implemented for: {file_path}")
        # Implementation depends on how you want to handle undo
        pass

    def get_file_metadata(self, file_path):
        # Get basic file system metadata
        basic_metadata = {
            'creation_time': os.path.getctime(file_path),
            'modification_time': os.path.getmtime(file_path),
            'size': os.path.getsize(file_path)
        }
        
        # Get custom metadata using SiftMetadataUtils
        status, is_reviewed = self.metadata_utils.get_file_status(file_path)
        custom_metadata = {
            'status': status,
            'reviewed': is_reviewed
        }
        
        # Merge basic and custom metadata
        metadata = {**basic_metadata, **custom_metadata}
        
        logging.debug(f"Retrieved metadata for {file_path}: {metadata}")
        return metadata

    def generate_file_checksum(self, file_path):
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        checksum = hasher.hexdigest()
        logging.debug(f"Generated checksum for {file_path}: {checksum}")
        return checksum

    def verify_file_integrity(self, source_path, destination_path):
        result = self.generate_file_checksum(source_path) == self.generate_file_checksum(destination_path)
        logging.debug(f"File integrity verification: {source_path} -> {destination_path}: {'Passed' if result else 'Failed'}")
        return result

    def search_files(self, query, root_directory):
        results = []
        for root, _, files in os.walk(root_directory):
            for file in files:
                if query.lower() in file.lower():
                    results.append(os.path.join(root, file))
        logging.debug(f"Search for '{query}' in {root_directory}: {len(results)} results found")
        return results

    def create_backup(self, file_path):
        if os.path.isdir(file_path):
            logging.debug(f"Skipping backup for directory: {file_path}")
            return
        backup_dir = os.path.join(SAFE_DELETE_ROOT, 'public' if self.metadata_utils.get_file_status(file_path)[0] == 'public' else 'private')
        os.makedirs(backup_dir, exist_ok=True)
        backup_path = shutil.copy2(file_path, backup_dir)
        logging.debug(f"Created backup: {file_path} -> {backup_path}")

    def restore_from_backup(self, file_path):
        logging.debug(f"Restore from backup not implemented for: {file_path}")
        # Implementation depends on how you want to handle backups
        pass

    def cleanup_safe_delete_folder(self, days_old):
        cutoff = datetime.now() - timedelta(days=days_old)
        cleaned_files = 0
        for root, _, files in os.walk(SAFE_DELETE_ROOT):
            for file in files:
                file_path = os.path.join(root, file)
                if datetime.fromtimestamp(os.path.getctime(file_path)) < cutoff:
                    os.remove(file_path)
                    cleaned_files += 1
        logging.debug(f"Cleaned up {cleaned_files} files older than {days_old} days from safe delete folder")

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
        logging.debug(f"Directory status for {dir_path}: {status}")
        return status

    def refresh_directory_stats(self, start_path):
        paths_to_refresh = []
        current_path = start_path
        while current_path != PUBLIC_ROOT and current_path != PRIVATE_ROOT:
            paths_to_refresh.append(current_path)
            current_path = os.path.dirname(current_path)
        paths_to_refresh.append(current_path)  # Add root directory

        for path in reversed(paths_to_refresh):
            status = self.get_directory_status(path)
            logging.debug(f"Refreshed stats for {path}: {status}")
            if self.gui_refresh_callback:
                self.gui_refresh_callback(path)

    def get_file_review_status(self, file_path):
        status, is_reviewed = self.metadata_utils.get_file_status(file_path)
        return is_reviewed

    def update_file_review_status(self, file_path, is_public):
        new_status = 'public' if is_public else 'private'
        self.metadata_utils.update_manual_review_status(file_path, new_status)