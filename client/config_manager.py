import os
import configparser
from pathlib import Path

CONFIG_FILE = Path(os.path.dirname(os.path.abspath(__file__))) / "config.ini"

def load_config():
    config = configparser.ConfigParser()
    if CONFIG_FILE.exists():
        config.read(CONFIG_FILE, encoding="utf-8")
    return config

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        config.write(f)
