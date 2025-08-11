import os
import time

from client_request import *
import dir_lister
from config_manager import *
from tree_checker import *
import json

if __name__ == "__main__":
    config = load_config()
    monitor_path = config["client"]["MONITOR_PATH"]
    refresh_time = int(config["client"]["REFRESH_TIME"])

    try:
        old_tree = dir_lister.dfs_directory(monitor_path)
        print(f"開始監控資料夾: {monitor_path}")
        tc = TreeChecker(old_tree)
    except FileNotFoundError as e:
        print(f"錯誤: {e}")
        print("請確保監控路徑存在且可存取")
        exit(1)
    except PermissionError as e:
        print(f"權限錯誤: {e}")
        print("請檢查監控路徑的存取權限")
        exit(1)
    except Exception as e:
        print(f"初始化錯誤: {e}")
        exit(1)

    while True:
        try:
            new_tree = dir_lister.dfs_directory(monitor_path)
            tc.update_current_state(new_tree)
        except FileNotFoundError as e:
            print(f"監控路徑被刪除: {e}")
            print("程式停止")
            break
        except PermissionError as e:
            print(f"權限錯誤: {e}")
            print("程式停止")
            break
        except Exception as e:
            print(f"掃描錯誤: {e}")
            print("程式停止")
            break
        
        # 取得變更結果
        added_items = tc.get_add_list()
        modified_items = tc.get_modified_list()
        deleted_items = tc.get_deleted_list()
        os.system("clear")

        print("=== 當前檔案樹狀結構 ===")
        print(json.dumps(new_tree, indent=2, ensure_ascii=False))

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

        time.sleep(refresh_time)

    print("監控結束")
