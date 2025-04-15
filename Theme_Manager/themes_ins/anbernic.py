from pathlib import Path


class Anbernic:
    
    def __init__(self):
        self.__sd1_rom_storage_path = "/mnt/mmc/anbernic"
        self.__sd2_rom_storage_path = "/mnt/sdcard/anbernic"
        self.__current_sd = 1

    def get_sd_storage(self):
        return self.__current_sd

    def get_sd_storage_path(self):
        if self.__current_sd == 1 or not any(Path("/mnt/sdcard").iterdir()):
            self.__current_sd = 1
            return self.__sd1_rom_storage_path
        else:
            return self.__sd2_rom_storage_path

    def switch_sd_storage(self):
        if self.__current_sd == 1 and any(Path("/mnt/sdcard").iterdir()):
            self.__current_sd = 2
        else:
            self.__current_sd = 1
