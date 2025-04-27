import yaml
from pathlib import Path

def load_config(config_path):
    """加载YAML配置文件（强制使用UTF-8编码）"""
    with open(config_path, 'r', encoding='utf-8') as f:  # 关键修改处
        config = yaml.safe_load(f)
    return config