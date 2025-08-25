
class TreeChecker:
    def __init__(self, init_tree_dict):
        self.added_items = []
        self.modified_items = []
        self.deleted_items = []
        self.current_tree = init_tree_dict.copy()
    
    def update_current_state(self, server_tree_dict, local_tree_dict):
        """
        使用server的tree作為previous_tree，local的tree作為current_tree來比對
        """
        self.previous_tree = server_tree_dict.copy()
        self.current_tree = local_tree_dict.copy()
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
        self._detect_renames()
    
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
    
    def _detect_renames(self):
        """
        檢測重命名的檔案，通過比較hash值
        """
        # 收集所有檔案的hash值
        old_files_by_hash = {}
        new_files_by_hash = {}
        
        def collect_files_by_hash(tree_dict, current_path, files_dict):
            for item_name, item_value in tree_dict.items():
                item_path = f"{current_path}/{item_name}" if current_path else item_name
                if isinstance(item_value, dict):
                    # 是資料夾，遞迴收集
                    collect_files_by_hash(item_value, item_path, files_dict)
                else:
                    # 是檔案，記錄hash值
                    if item_value not in files_dict:
                        files_dict[item_value] = []
                    files_dict[item_value].append(item_path)
        
        # 收集舊tree和新tree中的所有檔案
        collect_files_by_hash(self.previous_tree, "", old_files_by_hash)
        collect_files_by_hash(self.current_tree, "", new_files_by_hash)
        
        # 檢測重命名
        for hash_value in old_files_by_hash:
            if hash_value in new_files_by_hash:
                old_paths = old_files_by_hash[hash_value]
                new_paths = new_files_by_hash[hash_value]
                
                # 如果路徑不同，可能是重命名
                for old_path in old_paths:
                    for new_path in new_paths:
                        if old_path != new_path:
                            # 檢查是否已經在added或deleted列表中
                            old_in_deleted = any(item['path'] == old_path for item in self.deleted_items)
                            new_in_added = any(item['path'] == new_path for item in self.added_items)
                            
                            if old_in_deleted and new_in_added:
                                # 從deleted和added列表中移除
                                self.deleted_items = [item for item in self.deleted_items if item['path'] != old_path]
                                self.added_items = [item for item in self.added_items if item['path'] != new_path]
                                
                                # 加入modified列表（重命名）
                                self.modified_items.append({
                                    "type": "file", 
                                    "path": new_path, 
                                    "hash": hash_value,
                                    "old_path": old_path,
                                    "action": "renamed"
                                })