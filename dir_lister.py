import os
import hashlib
import json

def compute_sha256(file_path):
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        return f"<error: {e}>"

def dfs_directory(path):
    tree = {}
    try:
        for entry in os.listdir(path):
            # 忽略開頭帶有"~"的檔案
            if entry.startswith("~"):
                continue
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                tree[entry] = dfs_directory(full_path)
            elif os.path.isfile(full_path):
                tree[entry] = compute_sha256(full_path)
    except Exception as e:
        return f"<error: {e}>"
    return tree

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="List files in directory with SHA-256 hash.")
    parser.add_argument("directory", help="Root directory to scan")
    parser.add_argument("--output", default="output.json", help="Output JSON file name")
    args = parser.parse_args()

    result = dfs_directory(args.directory)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Output written to {args.output}")
