import os
import binascii
import json
import base64
from pathlib import Path
import ssl
from urllib.request import urlopen, Request
import urllib.parse
from systems import get_system_extension, systems
from typing import Dict, Any, Optional


class Rom:
    def __init__(self, name, filename, crc=""):
        self.name = name
        self.filename = filename
        self.crc = crc

    def set_crc(self, crc):
        self.crc = crc


class Scraper:
    def __init__(self):
        self.user = ""
        self.password = ""
        self.devid = "cmVhdmVu"
        self.devpassword = "MDZXZUY5bTBldWs="
        self.media_type = "ss"
        self.region = "wor"
        self.resize = False
        self.ports_data: Optional[Dict[str, Any]] = None

    def load_config_from_json(self, filepath) -> bool:
        if not os.path.exists(filepath):
            print(f"Config file {filepath} not found")
            return False

        with open(filepath, "r") as file:
            config = json.load(file)
            self.user = config.get("user")
            self.password = config.get("password")
            self.media_type = config.get("media_type") or "ss"
            self.region = config.get("region") or "wor"
            self.resize = config.get("resize") is True
        return True

    def load_ports_data(self) -> bool:
        """Load ports data from PortsMaster JSON"""
        if self.ports_data is not None:
            return True
            
        ports_url = "https://raw.githubusercontent.com/PortsMaster/PortMaster-Info/main/ports.json"
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        try:
            request = Request(ports_url)
            with urlopen(request, context=ctx) as response:
                if response.status == 200:
                    data = json.loads(response.read())
                    self.ports_data = data.get("ports", {})
                    return True
                else:
                    self.ports_data = {}
                    return False
        except Exception as e:
            print(f"Error loading ports data: {e}")
            self.ports_data = {}
            return False

    def get_port_info(self, sh_filename):
        """Get port information from the PortsMaster data"""
        if not self.ports_data and not self.load_ports_data():
            return None
            
        if not self.ports_data:
            return None
            
        # Look for the port by matching the .sh filename in items[0]
        for port_key, port_data in self.ports_data.items():
            items = port_data.get("items", [])
            if items and len(items) > 0:
                # Check if the first item matches our .sh filename
                if items[0] == sh_filename:
                    return port_data
        return None

    def get_port_screenshot_url(self, port_info):
        """Extract screenshot URL from port information"""
        if not port_info:
            return None
            
        attr = port_info.get("attr", {})
        image = attr.get("image", {})
        screenshot = image.get("screenshot")
        
        if screenshot:
            # Construct the full URL for the screenshot
            # Screenshots are stored in the main repository under images/
            return f"https://raw.githubusercontent.com/PortsMaster/PortMaster-Info/main/images/{port_info.get('name', '').replace('.zip', '')}/{screenshot}"
        return None

    def download_port_screenshot(self, screenshot_url):
        """Download screenshot for a port"""
        if not screenshot_url:
            return None
            
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        try:
            request = Request(screenshot_url)
            with urlopen(request, context=ctx) as response:
                if response.status == 200:
                    return response.read()
        except Exception as e:
            print(f"Error downloading port screenshot: {e}")
        return None

    def get_crc32_from_file(self, rom, chunk_size = 65536):
        crc32 = 0
        with rom.open(mode="rb") as file:
            while chunk := file.read(chunk_size):
                crc32 = binascii.crc32(chunk, crc32)
        crc32 = crc32 & 0xFFFFFFFF
        return "%08X" % crc32

    def get_files_without_extension(self, folder):
        return [f.stem for f in Path(folder).glob("*") if f.is_file()]

    def get_image_files_without_extension(self, folder):
        image_extensions = (".jpg", ".jpeg", ".png")
        return [
            f.stem for f in folder.glob("*") if f.suffix.lower() in image_extensions
        ]

    def get_roms(self, path, system: str) -> list[Rom]:
        roms = []
        system_path = Path(path) / system
        system_extensions = get_system_extension(system)
        if not system_extensions:
            print(f"No extensions found for system: {system}")
            return roms

        # Special handling for PORTS system
        if system == "PORTS":
            for file_path in system_path.rglob("*"):
                if file_path.name.startswith(".") or file_path.name.startswith("-"):
                    continue
                if file_path.is_file():
                    file_extension = file_path.suffix.lower().lstrip(".")
                    if file_extension in system_extensions:
                        # For ports, the name should be the full filename since it needs to match exactly
                        name = file_path.name  # Keep the full name including .sh extension for matching
                        rel_path = file_path.relative_to(system_path)
                        rom = Rom(filename=str(rel_path), name=name)
                        roms.append(rom)
            return roms

        # Regular handling for other systems
        for file_path in system_path.rglob("*"):
            if file_path.name.startswith(".") or file_path.name.startswith("-"):
                continue
            if file_path.is_file():
                file_extension = file_path.suffix.lower().lstrip(".")
                if file_extension in system_extensions:
                    name = file_path.stem
                    rel_path = file_path.relative_to(system_path)
                    rom = Rom(filename=str(rel_path), name=name)
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

    def scrape_screenshot(
        self, crc: str, game_name: str, system_id: int, system_name: str = ""
    ) -> bytes | None:
        # Special handling for PORTS system
        if system_name == "PORTS":
            print(f"Scraping screenshot for port {game_name}...")
            port_info = self.get_port_info(game_name)  # game_name is the .sh filename for ports
            if not port_info:
                print(f"No port info found for {game_name}")
                return None
                
            screenshot_url = self.get_port_screenshot_url(port_info)
            if not screenshot_url:
                print(f"No screenshot URL found for port {game_name}")
                return None
                
            # Try to download the screenshot
            screenshot = self.download_port_screenshot(screenshot_url)
            if screenshot:
                print(f"Successfully downloaded screenshot for port {game_name}")
                return screenshot
            else:
                print(f"Failed to download screenshot for port {game_name}")
                return None

        # Regular handling for other systems
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        decoded_devid = base64.b64decode(self.devid).decode()
        decoded_devpassword = base64.b64decode(self.devpassword).decode()
        encoded_game_name = urllib.parse.quote(game_name)
        url = f"https://api.screenscraper.fr/api2/jeuInfos.php?devid={decoded_devid}&devpassword={decoded_devpassword}&softname=tiny-scraper&output=json&ssid={self.user}&sspassword={self.password}&crc={crc}&systemeid={system_id}&romtype=rom&romnom={encoded_game_name}"

        print(f"Scraping screenshot for {game_name}...")
        request = Request(url)
        try:
            with urlopen(request, context=ctx) as response:
                if response.status == 200:
                    try:
                        data = json.loads(response.read())
                        game_data = data.get("response").get("jeu")

                        screenshot_url = ""
                        for media in game_data.get("medias"):
                            if media["type"] == self.media_type:
                                if media["region"] == self.region:
                                    screenshot_url = media["url"]
                                    break
                                elif (
                                    not screenshot_url
                                ):  # Keep the first one as fallback
                                    print(f"No media found for this region {self.region} and type {self.media_type} combination for {game_name}")
                                    screenshot_url = media["url"]

                        if screenshot_url:
                            img_request = Request(screenshot_url)
                            with urlopen(img_request, context=ctx) as img_response:
                                if (
                                    img_response.headers.get("Content-Type")
                                    == "image/png"
                                ):
                                    return img_response.read()
                                else:
                                    print(f"Invalid image format for {game_name}")
                        else:
                            print(f"No screenshot URL found for {game_name}")
                    except ValueError:
                        print(f"Invalid JSON response for {game_name}")
                else:
                    print(f"Failed to get screenshot for {game_name}")
            return None
        except Exception as e:
            print(f"Error scraping screenshot for {game_name}: {e}")
            print(f"URL used: {url}")
            return None