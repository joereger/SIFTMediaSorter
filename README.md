# Photo Sorter

## UPDATE 2024-08-10 ABANDONING PYQT GUI
Tired of fighting the GUI.  Going to implement this logic in MacOS's Automations scripting environment.  See /MacOSAutomation/JoeregerMediaArchiveMirroringScript.sh

## Overview

This project aims to create an application with a graphical user interface (GUI) to help me sort through my large collection of photos (approximately 2,000,000 images/videos) efficiently. The goal is to categorize these images as either "Public," "Private," or "Unsure" for eventual publication of a subset.

## Background

My photo collection consists of:
- Roughly 2,000,000 images and videos
- A mix of dSLR and cameraphone photos
- Organized in a single master directory
- Subdirectories based on years, life events, months, etc.

## Project Goals

1. Create a GUI application for efficient photo sorting
2. Allow for incremental progress over weeks or months
3. Achieve completeness in sorting all images
4. Prepare for eventual public sharing of selected photos

## Key Features

1. Directory and Image Views: The app will present both directory and individual image views for sorting.
2. Quick Categorization: Users can quickly categorize images as "Public," "Private," or "Unsure."
3. Progress Tracking: The app will maintain a list of sorted and unsorted files.
4. Completeness: The app will continue presenting unsorted images until all are categorized.
5. Non-destructive: Initial sorting will not move or alter original files.

## Workflow

1. App presents a directory or image view
2. User selects a categorization option (Public, Private, Unsure)
3. App records the decision and moves to the next unsorted item
4. Process repeats until all images are sorted

## Future Enhancements

- Implement file moving functionality based on categorization
- Add machine learning for automatic categorization suggestions
- Integrate with cloud storage or photo management services

## Technical Considerations

- Choose a suitable GUI framework (e.g., PyQt, Tkinter, Electron)
- Implement efficient file system scanning and metadata reading
- Design a database or file-based system to store sorting progress
- Ensure the app can handle large numbers of files without performance issues

## Example constants.py (in root dir)

PUBLIC_ROOT = "test_public"
PRIVATE_ROOT = "test_private"
SAFE_DELETE_ROOT = "test_safe_delete"
METADATA_FOLDER = "test_metadata"

# Photo and Video Collection Management System

## Overview
This system manages and sorts a large collection of photos and videos between public and private directories, tracking review status and maintaining file integrity.

## Storage Structure
1. Two root directories:
   - `public_root`: for publicly accessible photos/videos
   - `private_root`: for private photos/videos
2. Root directory paths stored in `constants.py`
3. Year-based organization:
   - First-level subdirectories named by year (e.g., 2003, 2004, 2005)
   - Each year directory may contain multiple files, subdirectories, and nested subdirectories

## Sorting Functionality
1. `sort(path: str, is_public: bool) -> None` function in `sift_io_utils.py`
2. Handles individual files and directories
3. Sorting process:
   - Moves files/directories between public and private roots as needed
   - Preserves original directory structure
   - Resolves filename conflicts by incrementing
   - Verifies file integrity before deleting originals
   - Deletes empty directories (except year directories)

## File Safety Measures
1. Files are moved to `SAFE_DELETE_ROOT` instead of permanent deletion
2. `SAFE_DELETE_ROOT` has `public/` and `private/` subdirectories
3. Files in `SAFE_DELETE_ROOT` are kept indefinitely
4. Checksum verification after copying, before deleting original

## Metadata Management
1. JSON format, one file per year in each root directory
2. Fields for each file:
   - `status`: "public" or "private"
   - `last_reviewed`: timestamp of last review (ISO 8601 format)
   - `reviewed`: boolean indicating manual review status

## Progress Tracking
1. Directory-level progress bars
2. Shows percentage of reviewed files to total files

## Error Handling and Logging
1. Permission issues: Error and abort
2. Symbolic/hard links: Console error and abort
3. Failed operations logged to console and recorded in metadata

## Performance Considerations
1. One JSON metadata file per year in each root directory

## User Interface
1. Python Qt application (details to be provided separately)

## Edge Case Handling
1. Files with no extension: Processed normally
2. Long file names:
   - Max length: 255 characters
   - Truncation and unique identifier appending if exceeded
   - Logging of modifications

## Specific Requirements
1. `sort()` updates `last_reviewed` timestamp
2. Checksum verification errors: Log to console, abort, preserve original file
3. `sort()` handles multiple files/folders within given path, but not multiple sibling directories

## Limitations
1. Designed for local storage only
2. No summary statistics provided
3. No batch operations across multiple sibling directories

## File Operations
The `sort()` function is the primary operation, updating the `last_reviewed` timestamp in the metadata.

## Error Handling
Checksum verification errors are logged to the console, the operation is aborted, and the original file is preserved.

## Batch Operations
The `sort()` function accepts a single path, which may contain multiple files and folders to be processed.

## Project Structure and Key Components

### 1. gui_directory_details.py
This file contains the `DirectoryDetailsPane` class, which displays information about the selected directory and provides sorting options.

Key methods:
- `update_directory(path)`: Updates the displayed directory information
- `refresh_stats()`: Refreshes the statistics for the current directory
- `batch_sort(is_public)`: Initiates batch sorting of files in the current directory

### 2. gui_directory_tree.py
This file implements the `DirectoryTreePane` class, which displays a tree view of the directory structure.

Key methods:
- `populate_tree()`: Builds the directory tree structure
- `refresh_directory_structure()`: Refreshes the entire directory tree
- `refresh_stats(path)`: Updates the progress statistics for a specific directory

### 3. gui_file_grid_item.py
This file contains the `FileGridItem` class, which represents individual files in the grid view.

Key methods:
- `update_border()`: Updates the border color based on the file's review status
- `sort_public()` and `sort_private()`: Sort the file as public or private

### 4. gui_files_grid.py
This file implements the `FilesGridPane` class, which displays a grid of files in the selected directory.

Key methods:
- `update_directory(path)`: Updates the displayed files for the given directory
- `show_zoomed(file_path)`: Displays a zoomed view of the selected file
- `sort_public(file_path)` and `sort_private(file_path)`: Sort a file as public or private

### 5. gui_start.py
This file contains the `MainWindow` class, which is the main application window.

Key methods:
- `on_directory_selected(path)`: Handles directory selection events
- `on_directory_sorted(path)`: Handles directory sorting events

### 6. gui_video_widgets.py
This file implements video-related widgets, including `VideoThumbnailWidget` and `VideoPlayerWidget`.

Key methods:
- `play()` and `stop()`: Control video playback
- `set_position(position)`: Sets the video playback position

### 7. gui_zoomed_view.py
This file contains the `ZoomedView` class, which displays a zoomed view of selected files.

Key methods:
- `show_zoomed(file_path, sift_io, sift_metadata)`: Displays a zoomed view of the file
- `sort_public()` and `sort_private()`: Sort the current file as public or private

### 8. scroll_position_manager.py
This file implements the `ScrollPositionManager` class, which manages scroll positions for different views.

Key methods:
- `save_scroll_position(path, position)`: Saves the scroll position for a specific path
- `get_scroll_position(path)`: Retrieves the saved scroll position for a path

### 9. sift_io_utils.py
This file contains the `SiftIOUtils` class, which handles file operations and sorting.

Key methods:
- `sort(path, is_public)`: Sorts a file or directory as public or private
- `move_file(file_path, is_public)`: Moves a file between public and private directories
- `get_directory_status(dir_path)`: Retrieves the status of files in a directory

### 10. sift_metadata_utils.py
This file implements the `SiftMetadataUtils` class, which manages metadata for sorted files.

Key methods:
- `get_file_status(file_path)`: Retrieves the status of a file
- `update_manual_review_status(file_path, new_status)`: Updates the review status of a file
- `update_file_path(old_path, new_path)`: Updates metadata when a file is moved

example JSON metadata format:
 "1979/tests/test_01/test_image_2.jpg": {
    "year": "1979",
    "status": "public",
    "last_reviewed": "2024-08-09T08:43:57.732855",
    "reviewed": true
  }

These components work together to provide a comprehensive solution for managing and sorting a large collection of photos and videos, with a user-friendly interface and robust backend operations.

## Use Cases to Test

### Sort a folder in PUBLIC_ROOT as "private" (is_public=False)

example call: sort(PUBLIC_ROOT/1975/foo/, is_public=False)

assert:
1) PUBLIC_ROOT/1975/foo/, including all files and subfolders, is moved to PRIVATE_ROOT/1975/foo/
2) files collissions in PRIVATE_ROOT/1975/foo/ are handled gracefully and no data is lost
3) PUBLIC_ROOT/1975/foo/ is deleted
4) PUBLIC_ROOT/1975/foo/ is saved at SAFE_DELETE_ROOT/public/1975/foo/
5) if METADATA_FOLDER/public/1975/private_1975.json exists it contains no entries for the files that were moved
6) METADATA_FOLDER/public/1975/private_1975.json exists
7) METADATA_FOLDER/public/1975/private_1975.json contains entries for all files moved and they are recorded as "reviewed": true

### Sort a folder in PUBLIC_ROOT as "public" (is_public=True)

example call: sort(PUBLIC_ROOT/1975/foo/, is_public=True)

assert:
1) PUBLIC_ROOT/1975/foo/ exists and still includes all files and subfolders
2) no files are moved to PRIVATE_ROOT/1975/foo/
3) METADATA_FOLDER/public/1975/private_1975.json exists
4) METADATA_FOLDER/public/1975/private_1975.json contains entries for all files and they are recorded as "reviewed": true

### Sort a file in PUBLIC_ROOT as "private" (is_public=False)

example call: sort(PUBLIC_ROOT/1975/foo/bar.png, is_public=False)

assert:
1) PUBLIC_ROOT/1975/foo/bar.png is moved to PRIVATE_ROOT/1975/foo/bar.png
2) files collissions in PRIVATE_ROOT/1975/foo/bar.png are handled gracefully and no data is lost
3) PUBLIC_ROOT/1975/foo/bar.png is deleted
4) PUBLIC_ROOT/1975/foo/bar.png is saved at SAFE_DELETE_ROOT/public/1975/foo/bar.png
5) if METADATA_FOLDER/public/1975/private_1975.json exists it contains no entries for PUBLIC_ROOT/1975/foo/bar.png
6) METADATA_FOLDER/public/1975/private_1975.json exists
7) METADATA_FOLDER/public/1975/private_1975.json contains entries for PUBLIC_ROOT/1975/foo/bar.png and it is marked as "reviewed": true

### Sort a folder in PUBLIC_ROOT as "public" (is_public=True)

example call: sort(PUBLIC_ROOT/1975/foo/bar.png, is_public=True)

assert:
1) PUBLIC_ROOT/1975/foo/bar.png exists
2) no files are moved to PRIVATE_ROOT/1975/foo/bar.png
3) METADATA_FOLDER/public/1975/private_1975.json exists
4) METADATA_FOLDER/public/1975/private_1975.json contains entries for PUBLIC_ROOT/1975/foo/bar.png and it is recorded as "reviewed": true