import math
import olefile

from msoffcrypto import OfficeFile

def file_entropy_bits(path: str, chunk_size: int = 4 * 1024 * 1024):
    """
    計算檔案的位元組層級 Shannon 熵（bits/byte）。
    回傳 (entropy_bits_per_byte, total_bytes)。
    """
    counts = [0] * 256
    total = 0

    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            total += len(chunk)
            for b in chunk:
                counts[b] += 1

    if total == 0:
        return 0.0, 0

    inv_total = 1.0 / total
    H = 0.0
    for c in counts:
        if c:
            p = c * inv_total
            H -= p * math.log2(p)
    return H, total

def test_ole_and_ooxml(file):
    file.seek(0)
    office_file = OfficeFile(file)
    return office_file.is_encrypted()

def is_encrypted(file_path):
    try:
        ext = file_path.lower().split('.')[-1]
        with open(file_path, "rb") as f:
            is_OLE = olefile.isOleFile(f)
            if  is_OLE or ext in ['docx', 'dotx', 'docm', 'dotm', 'xlsx', 'xltx', 'xlsm', 'xltm', 'xlam', 'pptx',
                                  'potx', 'ppsx', '.sldx', 'pptm', 'potm', 'ppsm', 'sldm', 'ppam', 'thmx']:
                if is_OLE :
                    print("偵測為 OLE 檔案")
                else:
                    print("偵測為 OOXML 檔案")
                is_healthy = test_ole_and_ooxml(f)
                return is_healthy
            else:
                H, size = file_entropy_bits(f)
                print(f"File Size: {size} bytes\nEntropy: {H:.4f} bits/byte")
                if H < 7.5:
                    print("熵值較低，偵測為未加密檔案")
                    return False
                else:
                    print("熵值較高，偵測為加密檔案")
                    return True
    except Exception as e:
        print(f"檢查加密時發生錯誤: {e}")
        return True

def findTamperedFiles(root_path, added_items, modified_items):
    """
    找出被竄改的檔案
    """
    tampered_files = []
    for item in added_items:
        if item['type'] == 'file':
            if is_suspicious_file(root_path +'/'+ item['path']):
                tampered_files.append(item['path'])
        elif item['type'] == 'folder':
            print(f"新增資料夾: {item['path']}")

    for item in modified_items:
        if item['type'] == 'file':
            if is_suspicious_file(root_path +'/'+ item['path']):
                tampered_files.append(item['path'])

    return tampered_files


def is_suspicious_file(file_path):
    """檢查是否為可疑檔案"""
    # TODO: 實作可疑檔案檢查邏輯
    if not is_encrypted(file_path):
        print(f"{file_path}: 未加密")
        return False
    else:
        print(f"{file_path}: 已加密")
        return True