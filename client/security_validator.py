def findTamperedFiles(added_items, modified_items):
    """
    找出被竄改的檔案
    """
    tampered_files = []
    for item in added_items:
        if item['type'] == 'file':
            if is_suspicious_file(item['path']):
                tampered_files.append(item['path'])
        elif item['type'] == 'folder':
            print(f"新增資料夾: {item['path']}")

    for item in modified_items:
        if item['type'] == 'file':
            if is_suspicious_file(item['path']):
                tampered_files.append(item['path'])

    return tampered_files


def is_suspicious_file(file_path):
    """檢查是否為可疑檔案"""
    # TODO: 實作可疑檔案檢查邏輯
    return False