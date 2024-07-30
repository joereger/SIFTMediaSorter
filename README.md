# Photo Sorter

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

## Contributing

This is a personal project, but I'm open to suggestions and ideas. Feel free to open an issue if you have any recommendations for improving the sorting process or app functionality.

## License

This project is private and not open for public use or distribution at this time.