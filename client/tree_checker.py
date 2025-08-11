
class TreeChecker:
    def __init__(self, init_tree_dict):
        self.added_items = []
        self.modified_items = []
        self.deleted_items = []
        self.previous_tree = init_tree_dict.copy()
        self.current_tree = init_tree_dict.copy()
    
    def update_current_state(self, current_tree_dict):
        self.previous_tree = self.current_tree.copy()
        self.current_tree = current_tree_dict.copy()
        self._calculate_changes()
    
    def _calculate_changes(self):
        """
        計算新增、修改、刪除的項目
        """
        self.added_items = []
        self.modified_items = []
        self.deleted_items = []
        self._find_added_and_modified("", self.previous_tree, self.current_tree)
        self._find_deleted("", self.previous_tree, self.current_tree)
    
    def _collect_all_items(self, tree_dict, current_path, result_list):
        """
        收集字典中的所有項目路徑
        """
        for item_name, item_value in tree_dict.items():
            item_path = f"{current_path}/{item_name}" if current_path else item_name
            if isinstance(item_value, dict):
                # 是資料夾
                result_list.append({"type": "folder", "path": item_path})
                self._collect_all_items(item_value, item_path, result_list)
            else:
                # 是檔案
                result_list.append({"type": "file", "path": item_path, "hash": item_value})
    
    def _find_added_and_modified(self, current_path, old_tree, new_tree):
        """
        遞迴尋找新增和修改的項目
        """
        for item_name, new_value in new_tree.items():
            item_path = f"{current_path}/{item_name}" if current_path else item_name
            
            if item_name not in old_tree:
                # 新增的項目
                if isinstance(new_value, dict):
                    self.added_items.append({"type": "folder", "path": item_path})
                    self._collect_all_items(new_value, item_path, self.added_items)
                else:
                    self.added_items.append({"type": "file", "path": item_path, "hash": new_value})
            else:
                old_value = old_tree[item_name]
                if isinstance(new_value, dict) and isinstance(old_value, dict):
                    # 都是資料夾，遞迴檢查
                    self._find_added_and_modified(item_path, old_value, new_value)
                elif not isinstance(new_value, dict) and not isinstance(old_value, dict):
                    # 都是檔案，檢查是否修改
                    if new_value != old_value:
                        self.modified_items.append({"type": "file", "path": item_path, "hash": new_value})
                else:
                    # 類型改變（檔案變資料夾或反之），視為新增
                    if isinstance(new_value, dict):
                        self.added_items.append({"type": "folder", "path": item_path})
                        self._collect_all_items(new_value, item_path, self.added_items)
                    else:
                        self.added_items.append({"type": "file", "path": item_path, "hash": new_value})
    
    def _find_deleted(self, current_path, old_tree, new_tree):
        """
        遞迴尋找刪除的項目
        """
        for item_name, old_value in old_tree.items():
            item_path = f"{current_path}/{item_name}" if current_path else item_name
            
            if item_name not in new_tree:
                if isinstance(old_value, dict):
                    self.deleted_items.append({"type": "folder", "path": item_path})
                    self._collect_all_items(old_value, item_path, self.deleted_items)
                else:
                    self.deleted_items.append({"type": "file", "path": item_path, "hash": old_value})
            else:
                new_value = new_tree[item_name]
                if isinstance(old_value, dict) and isinstance(new_value, dict):
                    self._find_deleted(item_path, old_value, new_value)
    
    def get_add_list(self):
        return self.added_items
    
    def get_modified_list(self):
        return self.modified_items
    
    def get_deleted_list(self):
        return self.deleted_items