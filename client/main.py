import os
import time

from client_request import *
import dir_lister
from config_manager import *
from tree_checker import *
import json
from security_validator import *


if __name__ == "__main__":
    config = load_config()
    monitor_path = config["client"]["MONITOR_PATH"]
    refresh_time = int(config["client"]["REFRESH_TIME"])

    print(f"開始監控資料夾: {monitor_path}")
    
    tc = TreeChecker(dir_lister.dfs_directory(monitor_path))
    
    try:
        server_tree = get_tree_from_server()
        local_tree = dir_lister.dfs_directory(monitor_path)
        tc.update_current_state(server_tree, local_tree)
        print("已從server獲取初始檔案樹")
    except Exception as e:
        print(f"初始化錯誤: {e}")
        print("將使用空的檔案樹開始監控")

    while True:
        try:
            # 每次循環都從server獲取最新的tree資料
            server_tree = get_tree_from_server()
            local_tree = dir_lister.dfs_directory(monitor_path)
            tc.update_current_state(server_tree, local_tree)
        except FileNotFoundError as e:
            print(f"監控路徑被刪除: {e}")
            print("程式停止")
            break
        except PermissionError as e:
            print(f"權限錯誤: {e}")
            print("程式停止")
            break
        except Exception as e:
            print(f"無法連接到server: {e}")
            print("程式停止")
            break
        
        # 取得變更結果
        added_items = tc.get_add_list()
        modified_items = tc.get_modified_list()
        deleted_items = tc.get_deleted_list()

        print("=== 當前檔案樹狀結構 ===")
        print(json.dumps(local_tree, indent=2, ensure_ascii=False))

        print("\n=== 變更結果 ===")
        print(f"新增項目數量: {len(added_items)}")
        for item in added_items:
            print(f"  + {item['type']}: {item['path']}")
        
        print(f"\n修改項目數量: {len(modified_items)}")
        for item in modified_items:
            print(f"  ~ file: {item['path']} (新hash: {item['hash']})")
        
        print(f"\n刪除項目數量: {len(deleted_items)}")
        for item in deleted_items:
            print(f"  - {item['type']}: {item['path']}")


        tampered_files = findTamperedFiles(monitor_path, added_items, modified_items)
        if tampered_files or deleted_items:
            print("發現可疑檔案")
            print(tampered_files)
            print(deleted_items)
        else:
            # 只有在沒有可疑檔案時才嘗試發送變更事件
            try:
                # 分別發送不同類型的變更事件
                if added_items:
                    send_added_files_to_server(added_items)
                if modified_items:
                    send_modified_files_to_server(modified_items)
                if deleted_items:
                    send_deleted_files_to_server(deleted_items)
            except Exception as e:
                print(f"無法發送變更事件到server: {e}")
                print("變更事件將在server恢復後重新發送")
        time.sleep(refresh_time)
        

    print("監控結束")
