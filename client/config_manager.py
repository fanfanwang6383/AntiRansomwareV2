import os
import configparser
from pathlib import Path

CONFIG_FILE = Path(os.path.dirname(os.path.abspath(__file__))) / "config.ini"

def get_default_config():
    """
    取得預設設定
    """
    config = configparser.ConfigParser()
    
    # Client 設定
    config['client'] = {
        'MONITOR_PATH': './monitor',
        'REFRESH_TIME': '5'
    }
    
    # Server 設定
    config['server'] = {
        'SERVER_IP': 'localhost',
        'SERVER_PORT': '8000'
    }
    
    return config

def load_config():
    """
    載入設定檔，如果不存在則使用預設設定並建立檔案
    """
    config = configparser.ConfigParser()
    
    if CONFIG_FILE.exists():
        # 如果設定檔存在，載入它
        config.read(CONFIG_FILE, encoding="utf-8")
        print(f"已載入設定檔: {CONFIG_FILE}")
    else:
        # 如果設定檔不存在，使用預設設定
        config = get_default_config()
        save_config(config)
        print(f"設定檔不存在，已建立預設設定檔: {CONFIG_FILE}")
        print("請根據需要修改設定檔中的參數")
    
    return config

def save_config(config):
    """
    儲存設定檔
    """
    # 確保目錄存在
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        config.write(f)
    
    print(f"設定檔已儲存: {CONFIG_FILE}")

def create_default_config():
    """
    強制建立預設設定檔
    """
    config = get_default_config()
    save_config(config)
    return config
