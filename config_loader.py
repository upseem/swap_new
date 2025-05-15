import yaml
import os

def load_config(config_path="config.yaml"):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(current_dir, config_path)
    with open(full_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()
