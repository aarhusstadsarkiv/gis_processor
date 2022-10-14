from logging import root
from re import template
import sqlite3
from gis_utils import MAIN_EXTENSIONS
from gis_utils import EXTENSION_MAPPING
from pathlib import Path
import json
import shutil
import sys


FILE_ID = 0
NOTES_TEMPLATE_ID = 1
NOTES_TEMPLATE_NAME = 2
FILENAME = 3
DOC_COLLECTION_ID = 4
 
def find_main_files(av_db_file_path):
    connection = sqlite3.connect(av_db_file_path)
    cursor = connection.cursor()
    main_files = []
    
    for extention in MAIN_EXTENSIONS:
        result = cursor.execute(f"SELECT * FROM fil WHERE filename LIKE '%{extention}'")
        rows = result.fetchall()
        main_files.extend(rows)
    
    connection.close()
    return main_files


def group_notes_template_id(template_id, cursor):
    result = cursor.execute(f"SELECT * FROM fil WHERE notes_template_id = {template_id}")
    rows = result.fetchall()
    return rows


def find_aux_files(file, cursor):
    aux_files = []
    files_by_template_id = group_notes_template_id(file[1], cursor)
    for possible_aux_file in files_by_template_id:
        file_as_path = Path(possible_aux_file[FILENAME])
        main_file_path = Path(file[FILENAME])
        if file_as_path.stem == main_file_path.stem and file_as_path.suffix in EXTENSION_MAPPING[main_file_path.suffix]:
            aux_files.append((possible_aux_file[FILE_ID], possible_aux_file[DOC_COLLECTION_ID], possible_aux_file[FILENAME]))
    return aux_files
    
def _place_template(folder_path, moved_to_folder):
    template_file_path = folder_path / "template.txt"
    with open(template_file_path, "w") as file_handle:
        template_content = "This file was part of a gis project.\n It was moved to: {}".format(moved_to_folder)
        file_handle.write(template_content)

def move_files(aux_files_map, root_dir):
    log_file_path = root_dir / "log_file.txt"
    log_file = open(log_file_path, "w", encoding="utf-8")
    
    for master_file_folder in aux_files_map:
        # The folder consists of docCollectionID;docID.
        # so we split it on ";" to get the elements.
        folder_info = master_file_folder.split(";")
        
        # relative_destination is the last part of the destination (i.e. destination relative to root_dir).
        relative_destination = "docCollection{}/{}".format(folder_info[0], folder_info[1])
        destination = root_dir / relative_destination
        
        # Each aux_file is a triplet (docCollectionID, docID, filename)
        for aux_file in aux_files_map[master_file_folder]:
            absolute_file_path: Path = root_dir / (f"docCollection{aux_file[1]}") / aux_file[0] / aux_file[2]
            if absolute_file_path.exists():
                shutil.move(absolute_file_path, destination)
                _place_template(absolute_file_path.parent, relative_destination)
                
            else:
                log_file.write(f"File already moved: docCollection{aux_file[1]}/{aux_file[0]}/{aux_file[2]}")


            # log_file.write("Moving file {} to folder {}\n".format(str(absolute_file_path), str(destination)))
    log_file.close()

if __name__ == "__main__":
    command = None
    
    command = sys.argv[1]
    # db_file_path = "/mnt/e/Staging/Processing/AVID.AARS.80.1/_metadata/AVID.AARS.80.av_with_index.db"

    # main_files = find_main_files(db_file_path)
    # print(f"Found main files: {len(main_files)}")
    #aux_files_map = {}

    # connection = sqlite3.connect(db_file_path)
    # cursor = connection.cursor()
    #for file in main_files:
        # aux_files = find_aux_files(file, cursor)
        # key = f"{file[DOC_COLLECTION_ID]};{file[FILE_ID]}"
        # aux_files_map[key] = aux_files
    
    if command == "move":
        json_file = input("Enter full path to json file: ")
        
        aux_files_map = None
        with open(json_file, "r", encoding="utf-8") as f:
            aux_files_map = json.load(f)
        
        root_dir = input("Enter full path to root folder (OriginalFiles): ")
        root_dir_path = Path(root_dir)
        move_files(aux_files_map, root_dir_path)

        print("Finished moving the gis files.")
    
    # connection.close()
    # output_file = "/mnt/e/Staging/Processing/AVID.AARS.80.1/_metadata/gis_info.json"
    # with open (output_file, "w", encoding="utf8") as file_handle:
        # json.dump(aux_files_map, file_handle, indent=4, ensure_ascii=False)

    