import subprocess
import json

import os
import sys
# Get the current working directory and add the parent directory to the Python path
current_working_directory = os.getcwd()
print(current_working_directory)
# sys.path.append(os.path.join(current_working_directory, "./.."))

def generate_table_of_content(file_path):
    
    toc_dict = {
        'page': [],
        'title': []
    }
    
    # running command to get table of content in the form a string
    toc = subprocess.run(['pdftocio', file_path], shell=False, capture_output=True, text=True, check=True).stdout
    toc_list = toc.split('\n')
    
    for val in toc_list:
        val_list = val.split("\"")
        if len(val_list) < 3:
            continue
        toc_dict['page'].append(val_list[2].strip()) # extract page of section in toc
        toc_dict['title'].append(val_list[1].strip().replace("\t"," ").replace("\u2019", "\'")) # extract title of section in toc
        
    return toc_dict

def run_toc_command(file_path):
    toc_dict = generate_table_of_content(file_path)
    return toc_dict