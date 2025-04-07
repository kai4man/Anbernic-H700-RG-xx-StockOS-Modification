from collections import OrderedDict
from pathlib import Path

config_file = '/mnt/mod/ctrl/configs/system.cfg'

file_path = Path(config_file)
file_path.parent.mkdir(parents=True, exist_ok=True)
file_path.touch()

def read_config(filename):
    config = OrderedDict()
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    except FileNotFoundError:
        print("file does not exist")
    return config

def write_config(filename, config):
    with open(filename, 'w', encoding='utf-8') as f:
        for key, value in config.items():
            f.write(f"{key}={value}\n")

def update_config(config, new_entries):
    for key, value in new_entries.items():
        if key in config:
            del config[key]
        config[key] = value

def remove_config(config, key_to_delete):
    if key_to_delete in config:
        del config[key_to_delete]

def get_value(config, keys):
    for key, value in config.items():
        print(key, value)
        if key == keys:
            return value
    return None

def set_config(keys, value):
    config = read_config(config_file)
    new_settings = {keys: value}
    update_config(config, new_settings)
    write_config(config_file, config)

def del_config(keys):
    config = read_config(config_file)
    remove_config(config, keys)
    write_config(config_file, config)

def get_config(keys):
    config = read_config(config_file)
    values = get_value(config, keys)
    print(f"values: {values}")
    if values == "0":
        return "OFF"
    elif values == "1":
        return "ON"
    elif values == "2":
        return "AUTO"

def switch_config(keys, max):
    config = read_config(config_file)
    cur_value = get_value(config, keys)
    if cur_value is not None:
        cur_value = int(cur_value) + 1
        if cur_value == max:
            cur_value = 0
        set_config(keys, cur_value)
