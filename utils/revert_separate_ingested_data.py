import os
import shutil
import argparse
from pathlib import Path

def revert_split_files(output_parent_dir, subdirectory_prefix='chunk_', action='move'):
    """
    Moves files from subdirectories back to the parent directory and removes empty subdirectories.

    Parameters:
        output_parent_dir (str): Path to the parent directory containing subdirectories.
        subdirectory_prefix (str): Prefix of subdirectories to process (default is 'chunk_').
        action (str): 'copy' to copy files, 'move' to move files.
    """
    parent = Path(output_parent_dir)

    # Validate parent directory
    if not parent.is_dir():
        print(f"Error: Parent directory '{parent}' does not exist or is not a directory.")
        return

    # Identify subdirectories to process
    subdirs = [d for d in parent.iterdir() if d.is_dir() and d.name.startswith(subdirectory_prefix)]

    if not subdirs:
        print(f"No subdirectories starting with '{subdirectory_prefix}' found in '{parent}'.")
        return

    print(f"Found {len(subdirs)} subdirectories to process.")

    for subdir in subdirs:
        print(f"\nProcessing subdirectory: {subdir}")
        files = [f for f in subdir.iterdir() if f.is_file()]
        if not files:
            print(f" - No files found in '{subdir}'. Skipping.")
            continue

        for file_path in files:
            destination = parent / file_path.name

            # Check for name collisions
            if destination.exists():
                print(f" - Warning: '{destination.name}' already exists in the parent directory. Skipping file.")
                continue

            try:
                if action == 'move':
                    shutil.move(str(file_path), str(destination))
                else:
                    shutil.copy2(str(file_path), str(destination))
                print(f" - {'Moved' if action == 'move' else 'Copied'}: {file_path.name}")
            except Exception as e:
                print(f" - Error processing file '{file_path}': {e}")

        # After moving/copying files, remove the empty subdirectory
        try:
            subdir.rmdir()
            print(f" - Removed empty subdirectory: {subdir.name}")
        except OSError as e:
            print(f" - Error removing subdirectory '{subdir.name}': {e}")

    print("\nReversion of file splitting completed successfully.")

def main():
    parser = argparse.ArgumentParser(description="Revert split files by moving them from subdirectories back to the parent directory.")
    parser.add_argument('output_parent_dir', type=str, help="Path to the parent directory containing the subdirectories.")
    parser.add_argument('--subdirectory_prefix', type=str, default='chunk_', help="Prefix of subdirectories to process. Default is 'chunk_'.")
    parser.add_argument('--action', type=str, choices=['copy', 'move'], default='move', help="Action to perform on files: 'copy' or 'move'. Default is 'move'.")

    args = parser.parse_args()

    revert_split_files(
        output_parent_dir=args.output_parent_dir,
        subdirectory_prefix=args.subdirectory_prefix,
        action=args.action
    )

if __name__ == "__main__":
    main()
