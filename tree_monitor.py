import os
import time
import json

from client_request import *

# 比較第兩個json檔與第一個json檔之間多了哪些檔案，並回傳需要新增上傳到server端的檔案list
# 比較第兩個json檔與第一個json檔之間修改了哪些檔案，並回傳需要新增上傳到server端的被修改檔案list
def find_added_file_in_two_dict(root, first_tree_dict, second_tree_dict):
    # 新增的檔案list
    file_name_add_list = []
    # 被修改的檔案list
    file_name_modified_list = []
    for i in second_tree_dict:
        # 若為dictionary則往內遞迴繼續尋找
        if isinstance(second_tree_dict[i], dict) == True:
            # 記錄此目錄的名稱root
            file_name_add_list.append(find_added_file_in_two_dict(root + "/" + i, first_tree_dict[i], second_tree_dict[i])[0])
            file_name_modified_list.append(find_added_file_in_two_dict(root + "/" + i, first_tree_dict[i], second_tree_dict[i])[1])
            continue
        # 若此檔案不在第一個json中
        if (i in first_tree_dict) == False:
            # 將目錄+檔案名稱加入add_list
            file_name_add_list.append(root + "/" + i)
            continue
        # 若檔案hash不一樣則視為檔案被修改過
        if first_tree_dict[i] != second_tree_dict[i]:
            # 將目錄+檔案名稱加入modified_list
            file_name_modified_list.append(root + "/" + i)
    return file_name_add_list, file_name_modified_list

# 將file_list中的所有檔案上傳至server
def upload_all_added_file(file_list):
    for i in file_list:
        # file_list中可能有dictionary，代表為內層資料夾的新增檔案，則需遞迴進去新增
        if isinstance(i, (list)) == True:
            upload_all_added_file(i)
            continue
        upload_file(i)
    return

# 查看兩個json檔之間是否有不同(數量增加及檔案hash有更動會返回true)
def check_diff_tree(first_tree_dict, second_tree_dict):
    if len(second_tree_dict) > len(first_tree_dict):
        return True
    for i in second_tree_dict:
        # hash有更動
        if first_tree_dict[i] != second_tree_dict[i]:
            return True
        # 偵測為dictionary，代表為內層資料夾，需遞迴進去檢查
        if isinstance(second_tree_dict[i], dict) == True:
            check_diff_tree(first_tree_dict[i], second_tree_dict[i])
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

    print(f"開始監控資料夾: {path_to_watch}")

    while True:
        # 每秒檢查一次（也可做其他工作）
        time.sleep(10)
        # 創建新的comparsion.json來進行比對
        os.system(f"python .\\dir_lister.py " + path_to_watch + " --output " + comparsion_json)

        with open(comparsion_json, 'r', encoding='utf-8') as new_tree:
            new_tree_dict = json.load(new_tree)
        
        # trace
        # print(check_diff_tree(old_tree_dict, new_tree_dict))

        if check_diff_tree(old_tree_dict, new_tree_dict):
            (add_file_list, modified_file_list) = find_added_file_in_two_dict(path_to_watch, old_tree_dict, new_tree_dict)
            upload_all_added_file(add_file_list)
            upload_all_added_file(modified_file_list)
            # trace
            print(add_file_list)
            print(modified_file_list)

        #trace
        # for i in tree:
        #     print(i, tree[i])
        # print(next(iter(old_tree_dict)), old_tree_dict[next(iter(old_tree_dict))])

        # 將comparsion.json覆蓋成新的output.json
        os.replace(comparsion_json, director_tree_json)
        old_tree_dict = new_tree_dict

    print("監控結束")