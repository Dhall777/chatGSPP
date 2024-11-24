import os
import shutil
import math
import argparse
import random
from pathlib import Path

def split_files_into_chunks(source_dir, output_parent_dir, num_chunks=4272, shuffle=True, action='copy'):
    """
    Splits files from source_dir into num_chunks subdirectories within output_parent_dir.

    Parameters:
        source_dir (str): Path to the directory containing all files.
        output_parent_dir (str): Path where the subdirectories will be created.
        num_chunks (int): Number of subdirectories to create.
        shuffle (bool): Whether to shuffle files before splitting.
        action (str): 'copy' to copy files, 'move' to move files.
    """
    source = Path(source_dir)
    output_parent = Path(output_parent_dir)

    # Validate source directory
    if not source.is_dir():
        print(f"Error: Source directory '{source}' does not exist or is not a directory.")
        return

    # Create output parent directory if it doesn't exist
    output_parent.mkdir(parents=True, exist_ok=True)

    # List all files in source directory
    all_files = [f for f in source.iterdir() if f.is_file()]
    total_files = len(all_files)

    if total_files == 0:
        print(f"No files found in the source directory '{source}'.")
        return

    # Calculate files per chunk
    files_per_chunk = math.ceil(total_files / num_chunks)

    print(f"Total files found: {total_files}")
    print(f"Number of chunks: {num_chunks}")
    print(f"Files per chunk: {files_per_chunk}")

    # Shuffle files if required
    if shuffle:
        random.shuffle(all_files)
        print("Files have been shuffled for random distribution.")
    else:
        print("Files will be split in the order they appear.")

    # Create and populate subdirectories
    for i in range(num_chunks):
        chunk_dir = output_parent / f"chunk_{i+1}"
        chunk_dir.mkdir(parents=True, exist_ok=True)
        print(f"\nCreating directory: {chunk_dir}")

        # Determine the range of files for this chunk
        start_idx = i * files_per_chunk
        end_idx = start_idx + files_per_chunk
        chunk_files = all_files[start_idx:end_idx]

        # Move or copy files
        for file_path in chunk_files:
            destination = chunk_dir / file_path.name
            try:
                if action == 'move':
                    shutil.move(str(file_path), str(destination))
                else:
                    shutil.copy2(str(file_path), str(destination))
            except Exception as e:
                print(f"Error processing file '{file_path}': {e}")

        print(f"Moved/Copied {len(chunk_files)} files to '{chunk_dir}'.")

    print("\nFile splitting completed successfully.")

def main():
    parser = argparse.ArgumentParser(description="Split files into multiple subdirectories.")
    parser.add_argument('source_dir', type=str, help="Path to the source directory containing all files.")
    parser.add_argument('output_parent_dir', type=str, help="Path to the parent directory where chunks will be created.")
    parser.add_argument('--num_chunks', type=int, default=4272, help="Number of subdirectories to create. Default is 4272.")
    parser.add_argument('--shuffle', action='store_true', help="Shuffle files before splitting for random distribution.")
    parser.add_argument('--action', type=str, choices=['copy', 'move'], default='copy', help="Action to perform on files: 'copy' or 'move'. Default is 'copy'.")

    args = parser.parse_args()

    split_files_into_chunks(
        source_dir=args.source_dir,
        output_parent_dir=args.output_parent_dir,
        num_chunks=args.num_chunks,
        shuffle=args.shuffle,
        action=args.action
    )

if __name__ == "__main__":
    main()

