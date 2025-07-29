import os
import time
import json

from client_request import *

def find_added_file_in_two_dict(root, first_tree_dict, second_tree_dict):
    file_name_list = []
    for i in second_tree_dict:
        if isinstance(second_tree_dict[i], dict) == True:
            file_name_list.append(find_added_file_in_two_dict(root + "/" + i, first_tree_dict[i], second_tree_dict[i]))
        if (i in first_tree_dict) == False:
            file_name_list.append(root + "/" + i)
    return file_name_list

def upload_all_added_file(file_list):
    for i in file_list:
        if isinstance(i, list) == True:
            upload_all_added_file(i)
            continue
        print(i)
        upload_file(i)
    return

def check_diff_tree(first_tree_dict, second_tree_dict):
    if len(second_tree_dict) > len(first_tree_dict):
        return True
    for i in second_tree_dict:
        if isinstance(second_tree_dict[i], dict) == True:
            return check_diff_tree(first_tree_dict[i], second_tree_dict[i])
    return False

if __name__ == "__main__":
    # 要監控的目錄
    path_to_watch = "monitor"
    comparsion_json = "comparsion.json"
    director_tree_json = "directory_tree.json"

    # 創建監控目錄的tree結構並存入directory_tree.json
    os.system(f"python .\\dir_lister.py " + path_to_watch + " --output " + director_tree_json)
    with open(director_tree_json, 'r', encoding='utf-8') as old_tree:
        old_tree_dict = json.load(old_tree)

    try:
        while True:
            # 每秒檢查一次（也可做其他工作）
            time.sleep(10)
            # 創建新的comparsion.json來進行比對
            os.system(f"python .\\dir_lister.py " + path_to_watch + " --output " + comparsion_json)

            with open(comparsion_json, 'r', encoding='utf-8') as new_tree:
                new_tree_dict = json.load(new_tree)
            if check_diff_tree(old_tree_dict, new_tree_dict):
                add_file_list = find_added_file_in_two_dict(path_to_watch, old_tree_dict, new_tree_dict)
                upload_all_added_file(add_file_list)
                print(add_file_list)

            # for i in tree:
            #     print(i, tree[i])
            # print(next(iter(old_tree_dict)), old_tree_dict[next(iter(old_tree_dict))])

            # 將comparsion.json覆蓋成新的output.json
            os.replace(comparsion_json, director_tree_json)
            old_tree_dict = new_tree_dict
    except KeyboardInterrupt:
        # Ctrl+C 停止
        pass
    print("監控結束")