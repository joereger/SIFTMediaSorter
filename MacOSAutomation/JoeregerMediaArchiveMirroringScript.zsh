#!/bin/zsh

# Required jq to be installed.  Use 'brew install jq'
# Once installed, run 'which jq' to get the full path to the installed executable
# because MacOS Automator doesn't often have access to a full shell we need to hardcode the path to jq

# When creating the MacOS Quick Action:
# - Workflow receives current files or folders in Finder.app
# - make sure to set Pass Input "As Arguments"

# Set this variable to either "PUBLIC" or "PRIVATE" to determine the mirroring direction
MIRROR_DIRECTION="PRIVATE"

# Define the root directories
PUBLIC_ROOT="/Users/joereger/Dropbox (Personal)/SIFTMediaSorter/test_public"
PRIVATE_ROOT="/Users/joereger/Dropbox (Personal)/SIFTMediaSorter/test_private"

# Location of jq binary
JQ_PATH="/opt/homebrew/bin/jq"

# Enable error logging
exec 2>"$PUBLIC_ROOT/JoeregerMirroringScript_error_log.txt"
set -x
log_file="$PUBLIC_ROOT/JoeregerMirroringScript_script_log.txt"
echo "--- Script started at $(date) ---" > "$log_file"
echo "MIRROR_DIRECTION: $MIRROR_DIRECTION" >> "$log_file"
echo "PUBLIC_ROOT: $PUBLIC_ROOT" >> "$log_file"
echo "PRIVATE_ROOT: $PRIVATE_ROOT" >> "$log_file"

# Log information about the input file/folder
if [ $# -eq 0 ]; then
    echo "No file or folder was passed to the script" >> "$log_file"
else
    echo "Input item: $1" >> "$log_file"
    if [ -f "$1" ]; then
        echo "Input is a file" >> "$log_file"
        echo "File size: $(du -h "$1" | cut -f1)" >> "$log_file"
        echo "File type: $(file -b "$1")" >> "$log_file"
    elif [ -d "$1" ]; then
        echo "Input is a directory" >> "$log_file"
        echo "Number of items in directory: $(find "$1" | wc -l)" >> "$log_file"
    else
        echo "Input is neither a regular file nor a directory" >> "$log_file"
    fi
fi

# Set source and destination based on MIRROR_DIRECTION
if [ "$MIRROR_DIRECTION" = "PUBLIC" ]; then
    SOURCE_ROOT="$PRIVATE_ROOT"
    DEST_ROOT="$PUBLIC_ROOT"
elif [ "$MIRROR_DIRECTION" = "PRIVATE" ]; then
    SOURCE_ROOT="$PUBLIC_ROOT"
    DEST_ROOT="$PRIVATE_ROOT"
else
    echo "Error: MIRROR_DIRECTION must be set to either 'PUBLIC' or 'PRIVATE'"
    exit 1
fi

# Function to generate a unique name for file or directory
generate_unique_name() {
    local path="$1"
    local base_path="${path%.*}"
    local extension="${path##*.}"
    local counter=1
    local new_path

    if [ "$path" = "$extension" ]; then
        # It's a directory or a file without extension
        new_path="$path"
        while [ -e "$new_path" ]; do
            new_path="${path}*$(printf "%02d" $counter)"
            ((counter++))
        done
    else
        # It's a file with extension
        new_path="$path"
        while [ -e "$new_path" ]; do
            new_path="${base_path}*$(printf "%02d" $counter).$extension"
            ((counter++))
        done
    fi

    echo "$new_path"
}

# Function to update or create the JoeregerMediaArchiveMetadata.json file
update_metadata() {
    local root_dir="$1"
    local rel_path="$2"
    local is_file="$3"  # New parameter to distinguish between files and folders
    local year=$(echo "$rel_path" | cut -d'/' -f1)
    local metadata_file="$root_dir/$year/JoeregerMediaArchiveMetadata.json"

    # Create metadata file if it doesn't exist
    if [ ! -f "$metadata_file" ]; then
        mkdir -p "$(dirname "$metadata_file")"
        echo "{}" > "$metadata_file"
    fi

    # Only update metadata for files, not folders
    if [ "$is_file" = true ]; then
        # Use jq to update the JSON file, ensuring only one entry per path
        local updated_json=$("$JQ_PATH" --arg path "$rel_path" \
                               '.[$path] = {reviewed: true}' \
                               "$metadata_file")

        echo "$updated_json" > "$metadata_file"
        echo "Updated metadata for $rel_path"
    fi
}

# Function to remove an entry from the metadata file
remove_metadata_entry() {
    local root_dir="$1"
    local rel_path="$2"
    local year=$(echo "$rel_path" | cut -d'/' -f1)
    local metadata_file="$root_dir/$year/JoeregerMediaArchiveMetadata.json"

    if [ -f "$metadata_file" ]; then
        # Use jq to remove the entry from the JSON file
        local updated_json=$("$JQ_PATH" --arg path "$rel_path" \
                               'del(.[$path])' \
                               "$metadata_file")

        echo "$updated_json" > "$metadata_file"
    fi
}

# Function to mirror a single file
mirror_single_file() {
    local src="$1"
    local relative_path="${src#$SOURCE_ROOT/}"
    local dest="$DEST_ROOT/$relative_path"
    
    # Check if source file exists
    if [ ! -f "$src" ]; then
        echo "Error: Source file '$src' does not exist."
        return 1
    fi

    # Create the destination directory if it doesn't exist
    local dest_dir=$(dirname "$dest")
    if ! mkdir -p "$dest_dir"; then
        echo "Error: Failed to create destination directory for '$dest'."
        return 1
    fi
    
    # Generate a unique name for the destination file
    dest=$(generate_unique_name "$dest")

    # Move the file
    if mv "$src" "$dest"; then
        echo "Successfully moved $src to $dest"
        # Update metadata file in destination
        update_metadata "$DEST_ROOT" "${dest#$DEST_ROOT/}" true
        # Remove metadata entry from source
        remove_metadata_entry "$SOURCE_ROOT" "$relative_path"
    else
        echo "Error: Failed to move $src to $dest"
        return 1
    fi
}

# Function to recursively mirror files and directories
mirror_recursive() {
    local src="$1"

    if [ -d "$src" ]; then
        # If source and destination roots are the same, don't update metadata for the directory
        if [ "$SOURCE_ROOT" != "$DEST_ROOT" ]; then
            local relative_path="${src#$SOURCE_ROOT/}"
            local dest_dir="$DEST_ROOT/$relative_path"
            dest_dir=$(generate_unique_name "$dest_dir")
            
            if ! mkdir -p "$dest_dir"; then
                echo "Error: Failed to create destination directory '$dest_dir'."
                return 1
            fi
        fi

        # Recursively process directory contents
        for item in "$src"/*; do
            mirror_recursive "$item"
        done
    elif [ -f "$src" ]; then
        # If it's a file, mirror it and update metadata
        local relative_path="${src#$SOURCE_ROOT/}"
        if [ "$SOURCE_ROOT" = "$DEST_ROOT" ]; then
            update_metadata "$SOURCE_ROOT" "$relative_path" true
        else
            mirror_single_file "$src"
        fi
    else
        echo "Skipping $src: Not a file or directory"
    fi
}

# Function to check if a path is within another path
is_subpath() {
    case $2 in
        $1*) return 0 ;;
        *) return 1 ;;
    esac
}

if ! [ -x "$JQ_PATH" ]; then
    echo "Error: jq is required but not installed at $JQ_PATH. Please install jq or update the JQ_PATH variable to use this script."
    exit 1
fi

# Main loop to process all arguments
for item in "$@"; do
    if is_subpath "$SOURCE_ROOT" "$item"; then
        mirror_recursive "$item"
    else
        echo "Skipping $item: Not in source root"
    fi
done

# At the end of your script
echo "Script completed at $(date)" >> "$log_file"
set +x
