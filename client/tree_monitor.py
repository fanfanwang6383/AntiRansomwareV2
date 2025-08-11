import os
import time
import json

from client_request import *
import dir_lister

# 查看兩個json檔之間是否有不同(數量增加及檔案hash有更動會返回true)
def is_different_tree(first_tree_dict, second_tree_dict):
    if len(second_tree_dict) > len(first_tree_dict):
        return True
    for i in second_tree_dict:
        # hash有更動
        if first_tree_dict[i] != second_tree_dict[i]:
            return True
        # 偵測為dictionary，代表為內層資料夾，需遞迴進去檢查
        if isinstance(second_tree_dict[i], dict) == True:
            is_different_tree(first_tree_dict[i], second_tree_dict[i])
    return False

# 比較第二個json檔與第一個json檔之間多了哪些檔案，並回傳需要新增上傳到server端的檔案list
# 比較第二個json檔與第一個json檔之間修改了哪些檔案，並回傳需要新增上傳到server端的被修改檔案list
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


if __name__ == "__main__":
    # 要監控的目錄
    path_to_watch = "/Users/shaneliu/Documents/GitHub/AntiRansomwareV2/monitor"

    old_tree_dict = dir_lister.dfs_directory(path_to_watch)
    print(old_tree_dict)
    print(f"開始監控資料夾: {path_to_watch}")

    while True:
        # 每秒檢查一次（也可做其他工作）
        time.sleep(10)
        new_tree_dict = dir_lister.dfs_directory(path_to_watch)
        print(new_tree_dict)

        if is_different_tree(old_tree_dict, new_tree_dict):
            (add_file_list, modified_file_list) = find_added_file_in_two_dict(path_to_watch, old_tree_dict, new_tree_dict)
            upload_all_added_file(add_file_list)
            upload_all_added_file(modified_file_list)
            
        old_tree_dict = new_tree_dict

    print("監控結束")
