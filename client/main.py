import os
import time


from client_request import *
import dir_lister
from config_manager import *

# 查看兩個tree之間是否有不同(數量增加及檔案hash有更動會返回true)
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

# 比對多了哪些檔案，並回傳需要新增上傳到server端的檔案list
# 比對修改了哪些檔案，並回傳需要新增上傳到server端的被修改檔案list
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

# 新增：比對刪除了哪些檔案，並回傳需要從server端恢復的檔案list
def find_deleted_file_in_two_dict(root, first_tree_dict, second_tree_dict):
    # 刪除的檔案list
    file_name_deleted_list = []
    for i in first_tree_dict:
        # 若為dictionary則往內遞迴繼續尋找
        if isinstance(first_tree_dict[i], dict) == True:
            # 如果第二個字典中沒有這個目錄，則整個目錄都被刪除了
            if i not in second_tree_dict:
                # 遍歷這個目錄中的所有文件，將它們添加到刪除列表中
                for file_path in get_all_files_in_dict(root + "/" + i, first_tree_dict[i]):
                    file_name_deleted_list.append(file_path)
                continue
            # 否則遞迴檢查這個目錄
            file_name_deleted_list.extend(find_deleted_file_in_two_dict(root + "/" + i, first_tree_dict[i], second_tree_dict[i]))
            continue
        # 若此檔案不在第二個json中，表示被刪除了
        if i not in second_tree_dict:
            # 將目錄+檔案名稱加入deleted_list
            file_name_deleted_list.append(root + "/" + i)
    return file_name_deleted_list

# 輔助函數：獲取字典中的所有文件路徑
def get_all_files_in_dict(root, tree_dict):
    file_paths = []
    for i in tree_dict:
        if isinstance(tree_dict[i], dict):
            file_paths.extend(get_all_files_in_dict(root + "/" + i, tree_dict[i]))
        else:
            file_paths.append(root + "/" + i)
    return file_paths

# 將file_list中的所有檔案上傳至server
def upload_all_added_file(file_list):
    for i in file_list:
        # file_list中可能有dictionary，代表為內層資料夾的新增檔案，則需遞迴進去新增
        if isinstance(i, (list)) == True:
            upload_all_added_file(i)
            continue
        upload_file(i)
    return

def recover_deleted_file(file_name):
    # TODO
    pass

def recover_all_deleted_file(file_list):
    for i in file_list:
        if isinstance(i, (list)) == True:
            recover_all_deleted_file(i)
            continue
        recover_deleted_file(i)
    return


if __name__ == "__main__":
    config = load_config()
    monitor_path = config["client"]["MONITOR_PATH"]
    refresh_time = int(config["client"]["REFRESH_TIME"])
    # 確保監控目錄存在
    os.makedirs(monitor_path, exist_ok=True)

    old_tree_dict = dir_lister.dfs_directory(monitor_path)
    print(old_tree_dict)
    print(f"開始監控資料夾: {monitor_path}")

    while True:
        time.sleep(refresh_time)
        new_tree_dict = dir_lister.dfs_directory(monitor_path)
        print(new_tree_dict)

        # 檢查文件新增和修改
        if is_different_tree(old_tree_dict, new_tree_dict):
            (add_file_list, modified_file_list) = find_added_file_in_two_dict(monitor_path, old_tree_dict, new_tree_dict)
            upload_all_added_file(add_file_list)
            upload_all_added_file(modified_file_list)
        
        # 檢查文件刪除
        deleted_file_list = find_deleted_file_in_two_dict(monitor_path, old_tree_dict, new_tree_dict)
        if deleted_file_list:
            print(f"檢測到刪除的文件: {deleted_file_list}")
            recover_all_deleted_file(deleted_file_list)
            
        old_tree_dict = new_tree_dict

    print("監控結束")
