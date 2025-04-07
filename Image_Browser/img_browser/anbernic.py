import os
from pathlib import Path


class Anbernic:
    
    def __init__(self):
        self.__sd1_rom_storage_path = "/mnt/mmc"
        self.__sd2_rom_storage_path = "/mnt/sdcard"

        self.__current_sd = 1


    def get_sd1_storage_path(self):
        return self.__sd1_rom_storage_path

    def get_sd2_storage_path(self):
        return self.__sd2_rom_storage_path
    
    def set_sd_storage(self, sd):
        if sd == 1 or sd == 2:
            self.__current_sd = sd
    
    def get_sd_storage(self):
        return self.__current_sd
    
    def switch_sd_storage(self):
        if self.__current_sd == 1:
            self.__current_sd = 2
        else:
            self.__current_sd = 1
    
    def get_sd_storage_path(self):
        if self.__current_sd == 1 or not any(Path("/mnt/sdcard").iterdir()):
            self.__current_sd = 1
            return self.get_sd1_storage_path()
        else:
            return self.get_sd2_storage_path()
    
    @staticmethod
    def get_current_path_files(path):
        try:
            entries = os.listdir(path)
            dirs = []
            images = []
            for entry in entries:
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path):
                    dirs.append(("[+] " + entry, full_path, "dir", entry.lower()))
                elif entry.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                    images.append((entry, full_path, "image", entry.lower()))
            dirs.sort(key=lambda x: x[3])  # 按原始名称排序
            images.sort(key=lambda x: x[3])
            return dirs + images
        except Exception as e:
            print(f"Error reading path {path}: {str(e)}")
            return []