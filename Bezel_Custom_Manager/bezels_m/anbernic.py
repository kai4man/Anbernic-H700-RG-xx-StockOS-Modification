import os


class Anbernic:
    
    def __init__(self):
        self.__sd_rom_storage_path = "/mnt/mmc/anbernic/bezels"
        self.__bezels_cfg_path = "/mnt/mmc/anbernic/custom"
        self.__rom_folder_mapping = {
            "PS": "PS",
            "GBA": "GBA",
            "GBC": "GBC",
            "GB": "GB",
        }
        self.__current_sd = 1

    def get_sd1_storage_path(self):
        return self.__sd_rom_storage_path

    def get_bezels_cfg_path(self):
        return self.__bezels_cfg_path

    def get_sd1_storage_console_path(self, console):
        return os.path.join(self.__sd_rom_storage_path, self.__rom_folder_mapping[console])

    def get_sd_storage(self):
        return self.__current_sd

    def get_sd_storage_path(self):
        return self.get_sd1_storage_path()

    def get_sd_storage_console_path(self, console):
        return self.get_sd1_storage_console_path(console)
    