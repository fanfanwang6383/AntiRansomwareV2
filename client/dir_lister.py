import os
import hashlib
import platform

def get_system_info():
    """
    獲取系統資訊，用於跨平台處理
    """
    return {
        "system": platform.system(),
        "platform": platform.platform(),
        "path_separator": os.sep,
        "is_windows": platform.system() == "Windows",
        "is_macos": platform.system() == "Darwin",
        "is_linux": platform.system() == "Linux"
    }

def compute_sha256(file_path):
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except (PermissionError, OSError) as e:
        # 權限不足或檔案被鎖定
        print(f"警告: 無法讀取檔案 {file_path}: {e}")
        return "unreadable"
    except Exception as e:
        print(f"警告: 計算檔案 hash 時發生錯誤 {file_path}: {e}")
        return "error"

def dfs_directory(path):
    tree = {}
    
    # 標準化路徑（處理相對路徑和絕對路徑）
    path = os.path.abspath(path)
    
    # 檢查路徑是否存在
    if not os.path.exists(path):
        raise FileNotFoundError(f"監控路徑不存在: {path}")
    
    try:
        for entry in os.listdir(path):
            # 忽略開頭帶有"~"的檔案
            if entry.startswith("~"):
                continue
            # 忽略隱藏檔案（Unix/Linux/macOS）
            if entry.startswith("."):
                continue
            # 忽略 Windows 系統檔案
            if platform.system() == "Windows":
                if entry.lower() in ["thumbs.db", "desktop.ini", "$recycle.bin"]:
                    continue
            
            full_path = os.path.join(path, entry)
            
            # 檢查是否為符號連結（避免無限遞迴）
            if os.path.islink(full_path):
                continue
                
            if os.path.isdir(full_path):
                tree[entry] = dfs_directory(full_path)
            elif os.path.isfile(full_path):
                tree[entry] = compute_sha256(full_path)
    except PermissionError:
        # 權限不足時跳過此目錄
        print(f"警告: 無法存取目錄 {path} (權限不足)")
        return {}
    
    return tree

def normalize_path_for_tree(path):
    """
    將系統路徑標準化為樹狀結構中使用的路徑格式
    統一使用正斜線 '/' 作為分隔符
    """
    # 將所有路徑分隔符統一為正斜線
    normalized = path.replace(os.sep, '/')
    # 移除開頭和結尾的斜線
    normalized = normalized.strip('/')
    return normalized
