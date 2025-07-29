import os
import json

from tree_monitor import find_added_file_in_two_dict

if __name__ == "__main__":
    comparsion_json = "comparsion.json"
    director_tree_json = "directory_tree.json"

    old_tree = open(director_tree_json, 'r', encoding='utf-8')
    old_tree_dict = json.load(old_tree)
    new_tree = open(comparsion_json, 'r', encoding='utf-8')
    new_tree_dict = json.load(new_tree)
    if len(new_tree_dict) > len(old_tree_dict):
        print(find_added_file_in_two_dict("", old_tree_dict, new_tree_dict))