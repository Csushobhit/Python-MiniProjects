import argparse
import pathlib
import shutil
import sys
import logging
import json
from tqdm import tqdm

'''
FILE_TYPE_MAP = {
    "Images": ['.jpeg', '.jpg', '.png', '.gif', '.svg'],
    "Documents": ['.pdf', '.docx', '.txt', '.pptx', '.xlsx'],
    "Audio": ['.mp3', '.wav', '.aac'],
    "Video": ['.mp4', '.mov', '.avi', '.mkv'],
    "Archives": ['.zip', '.rar', '.tar', '.gz'],
    "Other": []
}
'''

def load_config(config_path: pathlib.Path):
    try:
        with open(config_path, 'r') as config_file:
            config_data = json.load(config_file)
            return config_data
    except FileNotFoundError:
        logging.error(f"Configuration file not found at: {config_path}")
        logging.error("Please make sure 'config.json' exists in the same directory as the script.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing configuration file: {config_path}")
        logging.error(f"The file contains invalid JSON. Please check the syntax. Details: {e}")
        sys.exit(1)

        
def organize_directory(source_path: pathlib.Path, dry_run: bool, file_type_map: dict):
    logging.info(f"Starting to organize directory: {source_path}")

    if dry_run:
        logging.info("--- DRY RUN MODE ENABLED: No files will be moved. ---")
    else:
        logging.warning("--- LIVE RUN MODE ENABLED: File system changes will be made. ---")

    files_to_process = [item for item in source_path.iterdir() if item.is_file()]

    for item in tqdm(files_to_process, desc="Organizing Files"):
        file_extension = item.suffix.lower()

        destination_folder_name = 'Other'
        for category, extensions in file_type_map.items():
            if file_extension in extensions:
                destination_folder_name = category
                break

        destination_dir = source_path / destination_folder_name

        if dry_run:
            destination_file_path = destination_dir / item.name
            logging.info(f"[DRY RUN] Would move '{item.name}' -> '{destination_file_path}'")
        else:
            destination_dir.mkdir(parents=True, exist_ok=True)

            destination_file_path = destination_dir / item.name

            counter = 1
            while destination_file_path.exists():
                logging.warning(f"Conflict: '{destination_file_path}' already exists.")
                new_filename = f"{item.stem} ({counter}){item.suffix}"
                destination_file_path = destination_dir / new_filename
                counter += 1

            try:
                shutil.move(item, destination_file_path)
                logging.info(f"Moved: '{item.name}' -> '{destination_file_path}'")
            except PermissionError as e:
                logging.error(f"Could not move '{item.name}'. Error: {e}")
            except Exception as e:
                logging.error(f"An unexpected error occurred while moving '{item.name}'. Error: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Organize files in a directory by their type.")
    parser.add_argument('source_directory', help='The path to the directory you want to organize.')
    parser.add_argument('--dry-run', action='store_true', help='Simulate the organization without moving files.')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s -%(levelname)s -%(message)s',
        handlers=[
            logging.FileHandler("organizer.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

    config_file_path = pathlib.Path(__file__).parent / "config.json"
    file_type_map_from_config = load_config(config_file_path)

    source_path = pathlib.Path(args.source_directory)

    if not source_path.exists() or not source_path.is_dir():
        print(f"Error: The path '{source_path}' does not exist or is not a directory.")
        sys.exit(1)

    organize_directory(source_path, args.dry_run,file_type_map_from_config)