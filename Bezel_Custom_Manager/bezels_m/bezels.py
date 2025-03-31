import os
import binascii
import base64
from pathlib import Path
import ssl
from systems import get_system_extension, systems


class Rom:
    def __init__(self, name, filename, crc=""):
        self.name = name
        self.filename = filename
        self.crc = crc

    def set_crc(self, crc):
        self.crc = crc


class Bezels:
    def __init__(self):
        self.user = ""

    def get_roms(self, path, system: str) -> list[Rom]:
        roms = []
        system_path = Path(path) / system
        system_extensions = get_system_extension(system)
        if not system_extensions:
            print(f"Bezel config file not found: {system}")
            return roms

        for file in os.listdir(system_path):
            file_path = Path(system_path) / file
            if file.startswith("."):
                continue
            if file_path.is_file():
                file_extension = file_path.suffix.lower().lstrip(".")
                if file_extension in system_extensions:
                    name = file_path.stem
                    rom = Rom(filename=file, name=name)
                    roms.append(rom)

        return roms

    def get_available_systems(self, roms_path: str) -> list[str]:
        all_systems = [system["name"] for system in systems]
        available_systems = []
        for system in all_systems:
            system_path = Path(roms_path) / system
            if system_path.exists() and any(system_path.iterdir()):
                available_systems.append(system)

        return available_systems

