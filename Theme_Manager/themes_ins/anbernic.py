import os


class Anbernic:
    
    def __init__(self):
        self.__sd_rom_storage_path = "/mnt/mmc/anbernic"
        self.__current_sd = 1

    def get_sd_storage(self):
        return self.__current_sd

    def get_sd_storage_path(self):
        return self.__sd_rom_storage_path

