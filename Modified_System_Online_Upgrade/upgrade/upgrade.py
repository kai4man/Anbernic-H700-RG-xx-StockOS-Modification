#!/usr/bin/env python3

"""
Stock OS Mod Updater - Professional Edition
"""
from __future__ import annotations

# =========================
# Standard Library Imports
# =========================
import hashlib
import json
import logging
import mmap
import os
import shutil
import socket
import struct
import sys
import time
import zipfile
from dataclasses import dataclass
from fcntl import ioctl
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.error import ContentTooShortError, URLError
from urllib.request import urlretrieve

# =========================
# Third-Party Imports
# =========================
from PIL import Image, ImageDraw, ImageFont

cur_app_ver = "1.0.6"
base_ver = "3.7.0"

def ensure_requests():
    try:
        import requests
        import urllib3
        from urllib3.util import Retry
        from requests.adapters import HTTPAdapter
        return True
    except ImportError:
        try:
            program = os.path.dirname(os.path.abspath(__file__))
            module_file = os.path.join(program, "module.zip")
            with zipfile.ZipFile(module_file, 'r') as zip_ref:
                zip_ref.extractall("/")
            print("Successfully installed requests and urllib3")
            return True
        except Exception as e:
            print(f"Failed to install requests: {e}")
            return False


if ensure_requests():
    import requests
    import urllib3
    from urllib3.util import Retry
    from requests.adapters import HTTPAdapter

# =========================
# Logging Setup
# =========================
APP_PATH = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(APP_PATH, "update.log")
if os.path.exists(LOG_FILE):
    try:
        os.remove(LOG_FILE)
    except Exception:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler(sys.stdout)],
)
LOGGER = logging.getLogger("upgrade")
LOGGER.info(f"Start Log")


# =========================
# Configuration
# =========================
@dataclass
class Config:

    board_mapping: Dict[str, int] = None
    system_list: Tuple[str, ...] = (
        "zh_CN",
        "zh_TW",
        "en_US",
        "ja_JP",
        "ko_KR",
        "es_LA",
        "ru_RU",
        "de_DE",
        "fr_FR",
        "pt_BR",
    )

    COLOR_PRIMARY: str = "#eb6325"  # Primary hue - Professional blue
    COLOR_PRIMARY_LIGHT: str = "#f6823b"  # light blue
    COLOR_PRIMARY_DARK: str = "#d84e1d"  # dark blue
    COLOR_SECONDARY: str = "#0b9ef5"  # Secondary color - amber
    COLOR_ACCENT: str = "#81b910"  # accent color - green
    COLOR_DANGER: str = "#4444ef"  # DANGER/ERROR COLOR - RED

    COLOR_BG: str = "#271811"  # Background color - dark blue grey
    COLOR_BG_LIGHT: str = "#37291f"  # Light background color
    COLOR_CARD: str = "#35241a"  # CARD BACKGROUND
    COLOR_CARD_LIGHT: str = "#473224"  # Bright card background

    COLOR_TEXT: str = "#f6f4f3"  # Main text color
    COLOR_TEXT_SECONDARY: str = "#afa39c"  # Secondary text color
    COLOR_BORDER: str = "#514137"  # Border color

    COLOR_SHADOW: str = "#120a07"  # Shadow color
    COLOR_OVERLAY: str = "#00000080"  # Overlay color

    font_file: str = os.path.join(APP_PATH, "font", "font.ttf")
    if not os.path.exists(font_file):
        font_file: str = "/mnt/vendor/bin/default.ttf"

    ver_cfg_path: str = "/mnt/mod/ctrl/configs/ver.cfg"
    os_ver_cfg_path: str = "/mnt/vendor/oem/version.ini"
    fb_cfg_path: str = "/mnt/mod/ctrl/configs/fb.cfg"

    tmp_app_update: str = "/tmp/app.tar.gz"
    tmp_app_md5: str = "/tmp/app.tar.gz.md5"

    tmp_list = [
        "/dev/shm",
        "/tmp",
        "/mnt/mmc",
        "/mnt/sdcard"
    ]

    free_space = []
    for tmp in tmp_list:
        if os.path.exists(tmp):
            usage = shutil.disk_usage(tmp)
            free_num = usage.free + 1 if tmp == "/tmp" else usage.free
            free_space.append((free_num, tmp))
    free_space.sort(key=lambda x: x[0], reverse=True)
    tmp_path: str = free_space[0][1] if free_space[0][1] else "/tmp"
    LOGGER.info(f"Using: {tmp_path}")

    tmp_info: str = os.path.join(tmp_path, "info.txt")
    tmp_update: str = os.path.join(tmp_path, "update.dep")
    tmp_md5: str = os.path.join(tmp_path, "update.dep.MD5")

    bytes_per_pixel: int = 4
    keymap: Dict[int, str] = None

    retry_config = {
        'total': 3,  # Total retry count
        'backoff_factor': 0.5,  # backoff factor
        'status_forcelist': [500, 502, 503, 504],  # HTTP status code that requires a retry
        'allowed_methods': ['GET', 'HEAD']  # HTTP methods that allow retries
    }

    mirrors = [
        {
            "name": "GitHub",
            "url": "https://github.com/cbepx-me/upgrade/releases/download/source/update.txt",
            "region": "Global"
        },
        {
            "name": "GitCode (China)",
            "url": "https://gitcode.com/cbepx/upgrade/releases/download/source/update.txt",
            "region": "CN"
        }
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
    }

    fallback_mirror = mirrors[0]
    speeds = []
    for mirror in mirrors:
        try:
            start = time.time()
            requests.head(mirror["url"], timeout=3, headers=headers)
            end = time.time() - start
        except:
            end = float('inf')
        speeds.append((end, mirror))
    speeds.sort(key=lambda x: x[0])
    info_url = speeds[0][1]["url"] if speeds[0][0] != float('inf') else fallback_mirror["url"]
    #LOGGER.info(f"Server List is: {speeds}")
    LOGGER.info(f"Using: {info_url}")

    def __post_init__(self):
        if self.board_mapping is None:
            self.board_mapping = {
                "RGcubexx": 1,
                "RG34xx": 2,
                "RG34xxSP": 2,
                "RG28xx": 3,
                "RG35xx+_P": 4,
                "RG35xxH": 5,
                "RG35xxSP": 6,
                "RG40xxH": 7,
                "RG40xxV": 8,
                "RG35xxPRO": 9,
            }
        if self.keymap is None:
            self.keymap = {
                304: "A",
                305: "B",
                306: "Y",
                307: "X",
                308: "L1",
                309: "R1",
                314: "L2",
                315: "R2",
                17: "DY",
                16: "DX",
                310: "SELECT",
                311: "START",
                312: "MENUF",
                114: "V+",
                115: "V-",
            }

    @staticmethod
    def screen_resolutions() -> Dict[int, Tuple[int, int, int]]:
        return {
            1: (720, 720, 18),
            2: (720, 480, 11),
            3: (640, 480, 11),
            4: (640, 480, 11),
            5: (640, 480, 11),
            6: (640, 480, 11),
            7: (640, 480, 11),
            8: (640, 480, 11),
            9: (640, 480, 11),
        }


# =========================
# Translator (mostly preserved, with minor polish)
# =========================
class Translator:
    def __init__(self, lang_code: str = "en_US"):
        self.lang_data: Dict[str, str] = {}
        self.lang_code = lang_code
        self.load_language(lang_code)

    def load_language(self, lang_code: str) -> None:
        base = os.path.dirname(os.path.abspath(__file__))
        lang_file = os.path.join(base, "lang", f"{lang_code}.json")
        if not os.path.exists(lang_file):
            lang_file = os.path.join(base, "lang", "en_US.json")
            LOGGER.warning(
                "Language file %s.json not found, using default en_US", lang_code
            )
        try:
            with open(lang_file, "r", encoding="utf-8") as f:
                self.lang_data = json.load(f)
            LOGGER.info("Loaded language file: %s", lang_file)
        except FileNotFoundError:
            LOGGER.error("Language file %s not found!", lang_file)
            raise
        except json.JSONDecodeError as e:
            LOGGER.error("Error parsing language file %s: %s", lang_file, e)
            raise

    def t(self, key: str, **kwargs) -> str:
        message = self.lang_data.get(key, key)
        try:
            return message.format(**kwargs)
        except KeyError as e:
            LOGGER.warning("Missing key in translation: %s", e)
            return message


# =========================
# Input Handling
# =========================
class InputHandler:

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.code_name: str = ""
        self.value: int = 0

    def poll(self) -> None:
        try:
            with open("/dev/input/event1", "rb") as f:
                while True:
                    event = f.read(24)
                    if not event:
                        break
                    (tv_sec, tv_usec, etype, kcode, kvalue) = struct.unpack(
                        "llHHI", event
                    )
                    if kvalue != 0:
                        if kvalue != 1:
                            kvalue = -1
                        self.code_name = self.cfg.keymap.get(kcode, str(kcode))
                        self.value = kvalue
                        LOGGER.debug(
                            "Key pressed: %s (code: %s, value: %s)",
                            self.code_name,
                            kcode,
                            self.value,
                        )
                        return
        except Exception as e:
            LOGGER.error("Error reading input: %s", e)
            self.code_name = ""
            self.value = 0

    def is_key(self, name: str, key_value: int = 99) -> bool:
        if self.code_name == name:
            if key_value != 99:
                return self.value == key_value
            return True
        return False

    def reset(self) -> None:
        self.code_name = ""
        self.value = 0


# =========================
# UI Renderer
# =========================
class UIRenderer:

    def __init__(self, cfg: Config, translator: Translator, hw_info: int):
        self.cfg = cfg
        self.t = translator
        self.hw_info = hw_info

        x_size, y_size, _ = Config.screen_resolutions().get(hw_info, (640, 480, 11))
        self.x_size = x_size
        self.y_size = y_size
        self.screen_size = x_size * y_size * cfg.bytes_per_pixel

        self.fb: Optional[int] = None
        self.mm: Optional[mmap.mmap] = None

        self.active_image: Optional[Image.Image] = None
        self.active_draw: Optional[ImageDraw.ImageDraw] = None

        self.button_y = self.y_size - 40
        self.button_x = self.x_size - 120

        self.fb_screeninfo = self._get_fb_screeninfo(hw_info)
        self._draw_start()
        self.screen_reset()
        self.set_active(self.create_image())

    def _get_fb_screeninfo(self, hw_info: int) -> Optional[bytes]:
        fb_cfg_path = self.cfg.fb_cfg_path
        if os.path.exists(fb_cfg_path):
            with open(fb_cfg_path, "rb") as f:
                LOGGER.info("Using custom fb config from %s", fb_cfg_path)
                return f.read()

        blobs: Dict[int, bytes] = {
            1: b"\xd0\x02\x00\x00\xd0\x02\x00\x00\xd0\x02\x00\x00\xa0\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x18\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00^\x00\x00\x00\x96\x00\x00\x00\x00\x00\x00\x00F_\x00\x008\x00\x00\x00J\x00\x00\x00\x0f\x00\x00\x00<\x00\x00\x00\n\x00\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            2: b"\xd0\x02\x00\x00\xe0\x01\x00\x00\xd0\x02\x00\x00\xc0\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x18\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00^\x00\x00\x00\x96\x00\x00\x00\x00\x00\x00\x00=\x96\x00\x00,\x00\x00\x006\x00\x00\x00\x0f\x00\x00\x00$\x00\x00\x00\x02\x00\x00\x00\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            3: b"\xe0\x01\x00\x00\x80\x02\x00\x00\xe0\x01\x00\x00\x80\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x18\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00^\x00\x00\x00\x96\x00\x00\x00\x00\x00\x00\x00\xc2\xa2\x00\x00\x1a\x00\x00\x00T\x00\x00\x00\x0c\x00\x00\x00\x1e\x00\x00\x00\x14\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            4: b"\x80\x02\x00\x00\xe0\x01\x00\x00\x80\x02\x00\x00\xc0\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x18\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00^\x00\x00\x00\x96\x00\x00\x00\x00\x00\x00\x00\xc2\xa2\x00\x00\x1a\x00\x00\x00T\x00\x00\x00\x0c\x00\x00\x00\x1e\x00\x00\x00\x14\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            5: b"\x80\x02\x00\x00\xe0\x01\x00\x00\x80\x02\x00\x00\xc0\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x18\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00^\x00\x00\x00\x96\x00\x00\x00\x00\x00\x00\x00\xc2\xa2\x00\x00\x1a\x00\x00\x00T\x00\x00\x00\n\x00\x00\x00\"\x00\x00\x00\x14\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            6: b"\x80\x02\x00\x00\xe0\x01\x00\x00\x80\x02\x00\x00\xc0\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x18\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00^\x00\x00\x00\x96\x00\x00\x00\x00\x00\x00\x00\xc2\xa2\x00\x00(\x00\x00\x00 \x00\x00\x00,\x00\x00\x00 \x00\x00\x00\x08\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            7: b"\x80\x02\x00\x00\xe0\x01\x00\x00\x80\x02\x00\x00\xc0\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x18\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00^\x00\x00\x00\x96\x00\x00\x00\x00\x00\x00\x00\xc2\xa2\x00\x00\x1a\x00\x00\x00T\x00\x00\x00\x0b\x00\x00\x00\x1b\x00\x00\x00\x14\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            8: b"\x80\x02\x00\x00\xe0\x01\x00\x00\x80\x02\x00\x00\xc0\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x18\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00^\x00\x00\x00\x96\x00\x00\x00\x00\x00\x00\x00\xc2\xa2\x00\x00\x1a\x00\x00\x00T\x00\x00\x00\x0b\x00\x00\x00\x1b\x00\x00\x00\x14\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
            9: b"\x80\x02\x00\x00\xe0\x01\x00\x00\x80\x02\x00\x00\xc0\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x18\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00^\x00\x00\x00\x96\x00\x00\x00\x00\x00\x00\x00\xc2\xa2\x00\x00\x1a\x00\x00\x00T\x00\x00\x00\x0c\x00\x00\x00\x1e\x00\x00\x00\x14\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
        }

        blob = blobs.get(hw_info)
        if blob:
            return blob

        try:
            fb_fd = os.open("/dev/fb0", os.O_RDWR)
            try:
                fb_info = bytearray(160)
                ioctl(fb_fd, 0x4600, fb_info)
                LOGGER.info("Read fb config from device /dev/fb0")
                return bytes(fb_info)
            finally:
                os.close(fb_fd)
        except Exception as e:
            LOGGER.error("Error reading fb config from device: %s", e)
            return None

    def screen_reset(self) -> None:
        if self.fb_screeninfo is not None:
            try:
                ioctl(self.fb, 0x4601, bytearray(self.fb_screeninfo))
                LOGGER.info("Screen reset with custom config")
            except Exception as e:
                LOGGER.error("Error resetting screen with custom config: %s", e)
        try:
            ioctl(self.fb, 0x4611, 0)
            LOGGER.info("Screen reset with default config")
        except Exception as e:
            LOGGER.error("Error resetting screen: %s", e)

    def _draw_start(self) -> None:
        try:
            self.fb = os.open("/dev/fb0", os.O_RDWR)
            self.mm = mmap.mmap(self.fb, self.screen_size)
            LOGGER.info("Framebuffer initialized successfully (%sx%s)", self.x_size, self.y_size)
        except Exception as e:
            LOGGER.error("Error initializing framebuffer: %s", e)
            raise

    def draw_end(self) -> None:
        try:
            if self.mm:
                self.mm.close()
            if self.fb:
                os.close(self.fb)
            LOGGER.info("Framebuffer closed successfully")
        except Exception as e:
            LOGGER.error("Error closing framebuffer: %s", e)

    def create_image(self) -> Image.Image:
        try:
            return Image.new("RGBA", (self.x_size, self.y_size), color=self.cfg.COLOR_BG)
        except Exception as e:
            LOGGER.error("Error creating image: %s", e)
            raise

    def set_active(self, image: Image.Image) -> None:
        self.active_image = image
        self.active_draw = ImageDraw.Draw(self.active_image)

    def paint(self) -> None:
        try:
            if self.hw_info == 3:
                img = self.active_image.rotate(90, expand=True)
                self.mm.seek(0)
                self.mm.write(img.tobytes())
            else:
                self.mm.seek(0)
                self.mm.write(self.active_image.tobytes())
        except Exception as e:
            LOGGER.error("Error painting to screen: %s", e)

    def clear(self) -> None:
        self.active_draw.rectangle((0, 0, self.x_size, self.y_size), fill=self.cfg.COLOR_BG)

    def text(self, pos, text, font=22, color=None, anchor=None, bold=False) -> None:
        color = color or self.cfg.COLOR_TEXT
        font_path = self.cfg.font_file
        try:
            font_size = font
            if bold and hasattr(ImageFont, 'FreeTypeFont'):
                try:
                    fnt = ImageFont.truetype(font_path, font_size)
                    self.active_draw.text((pos[0] + 1, pos[1] + 1), text, font=fnt, fill=self.cfg.COLOR_SHADOW,
                                          anchor=anchor)
                except:
                    fnt = ImageFont.load_default()
            else:
                fnt = ImageFont.truetype(font_path, font_size)

            self.active_draw.text(pos, text, font=fnt, fill=color, anchor=anchor)
        except Exception:
            fnt = ImageFont.load_default()
            self.active_draw.text(pos, text, font=fnt, fill=color, anchor=anchor)

    def rect(self, xy, fill=None, outline=None, width: int = 1, radius: int = 0) -> None:
        if radius > 0:
            self.active_draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)
        else:
            self.active_draw.rectangle(xy, fill=fill, outline=outline, width=width)

    def circle(self, center: Tuple[int, int], radius: int, fill=None, outline=None) -> None:
        x, y = center
        self.active_draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=fill, outline=outline)

    def panel(self, xy, title: Optional[str] = None, shadow=True) -> None:
        if shadow:
            shadow_xy = [xy[0] + 3, xy[1] + 3, xy[2] + 3, xy[3] + 3]
            self.rect(shadow_xy, fill=self.cfg.COLOR_SHADOW, radius=12)

        self.rect(xy, fill=self.cfg.COLOR_CARD, outline=self.cfg.COLOR_BORDER, width=1, radius=12)

        if title:
            title_bg = [xy[0], xy[1], xy[2], xy[1] + 30]
            self.rect(title_bg, fill=self.cfg.COLOR_PRIMARY_DARK, radius=12)
            self.text((self.x_size // 2, xy[1] + 15), title, font=20, anchor="mm", bold=True)

    def button(self, xy, label: str, icon: str = None, primary: bool = False) -> None:
        fill_color = self.cfg.COLOR_PRIMARY if primary else self.cfg.COLOR_CARD_LIGHT
        self.rect(xy, fill=fill_color, outline=self.cfg.COLOR_BORDER, radius=8)

        font_path = self.cfg.font_file
        try:
            fnt = ImageFont.truetype(font_path, 18)
        except Exception:
            fnt = ImageFont.load_default()

        bbox = self.active_draw.textbbox((0, 0), label, font=fnt)
        text_width = bbox[2] - bbox[0]

        button_width = xy[2] - xy[0]
        text_x = (xy[0] + xy[2]) // 2
        text_y = (xy[1] + xy[3]) // 2

        font_size = 18
        if text_width > button_width * 0.7:
            font_size = max(12, int(18 * (button_width * 0.7) / text_width))
            try:
                fnt = ImageFont.truetype(font_path, font_size)
            except Exception:
                fnt = ImageFont.load_default()

        if icon:
            self.text((text_x - 50, text_y), icon, font=20, anchor="mm")
            self.text((text_x + 10, text_y), label, font=font_size, anchor="mm", bold=primary)
        else:
            self.text((text_x, text_y), label, font=font_size, anchor="mm", bold=primary)

    def info_header(self, title: str, subtitle: str = None) -> None:
        for i in range(60):
            ratio = i / 50
            r = self._blend_colors(self.cfg.COLOR_PRIMARY_DARK, self.cfg.COLOR_PRIMARY, ratio)
            self.rect([0, i, self.x_size, i + 1], fill=r)

        self.text((self.x_size // 2, 20), title, font=26, anchor="mm", bold=True)

        if subtitle:
            self.text((self.x_size // 2, 45), subtitle, font=18, anchor="mm", color=self.cfg.COLOR_TEXT_SECONDARY)

    def status_badge(self, center: Tuple[int, int], text: str, status: str = "info") -> None:
        colors = {
            "success": self.cfg.COLOR_ACCENT,
            "warning": self.cfg.COLOR_SECONDARY,
            "error": self.cfg.COLOR_DANGER,
            "info": self.cfg.COLOR_PRIMARY_LIGHT
        }
        color = colors.get(status, self.cfg.COLOR_PRIMARY_LIGHT)

        font_path = self.cfg.font_file
        try:
            fnt = ImageFont.truetype(font_path, 18)
        except Exception:
            fnt = ImageFont.load_default()

        bbox = self.active_draw.textbbox((0, 0), text, font=fnt)
        text_width = bbox[2] - bbox[0] + 20
        text_height = bbox[3] - bbox[1] + 10

        x, y = center
        badge_rect = [x - text_width // 2, y - text_height // 2, x + text_width // 2, y + text_height // 2]
        self.rect(badge_rect, fill=color, radius=text_height // 2)

        self.text((x, y), text, font=18, anchor="mm", color=self.cfg.COLOR_TEXT, bold=True)

    def progress_bar(self, y_center: int, percent: float, label_top: Optional[str] = None,
                     label_bottom: Optional[str] = None) -> None:
        bar_left = 40
        bar_right = self.x_size - 40
        bar_top = y_center - 12
        bar_bottom = y_center + 12
        bar_height = bar_bottom - bar_top

        self.rect([bar_left, bar_top, bar_right, bar_bottom], fill=self.cfg.COLOR_BG_LIGHT, radius=bar_height // 2)

        pct = max(0, min(100, percent)) / 100.0
        filled = int((bar_right - bar_left) * pct) - 20
        filled_right = bar_left + int((bar_right - bar_left) * pct)
        if filled_right > bar_left:
            for i in range(bar_left, filled_right, 2):
                color_ratio = (i - bar_left) / (filled_right - bar_left)
                color = self._blend_colors(self.cfg.COLOR_PRIMARY, self.cfg.COLOR_ACCENT, color_ratio)
                self.rect([i, bar_top, min(i + 2, filled_right), bar_bottom], fill=color, radius=bar_height // 2)

            progress_text = f"{int(percent)}%"
            self.text((bar_left + filled, y_center), progress_text, font=19, anchor="mm", color=self.cfg.COLOR_TEXT)

        if label_top:
            self.text((self.x_size // 2, bar_top - 20), label_top, font=23, anchor="mm")
        if label_bottom:
            self.text((self.x_size // 2, bar_bottom + 20), label_bottom, font=19, anchor="mm",
                      color=self.cfg.COLOR_TEXT_SECONDARY)

    def _blend_colors(self, color1: str, color2: str, ratio: float) -> str:
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)

        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)

        return f"#{r:02x}{g:02x}{b:02x}"

# =========================
# Updater (network + verify + unzip)
# =========================
class Updater:
    def __init__(self, cfg: Config, ui: UIRenderer, translator: Translator):
        self.cfg = Config()
        self.input = InputHandler(self.cfg)
        self.skip_first_input = True
        self.cfg = cfg
        self.ui = ui
        self.t = translator
        self.update_url: str = ""
        self.md5_url: str = ""
        self.session = requests.Session()
        self.session.headers.update(self.cfg.headers)

        # Configure retry mechanism
        retry = Retry(
            total=self.cfg.retry_config['total'],
            backoff_factor=self.cfg.retry_config['backoff_factor'],
            status_forcelist=self.cfg.retry_config['status_forcelist'],
            allowed_methods=self.cfg.retry_config['allowed_methods']
        )

        # Create an adapter and configure retry
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

        self.session.headers.update(self.cfg.headers)

    def _download_file(self, url, local_path, progress_hook=None):
        try:
            file_size = 0
            if os.path.exists(local_path):
                file_size = os.path.getsize(local_path)

            headers = self.cfg.headers.copy()
            if file_size > 0:
                headers['Range'] = f'bytes={file_size}-'
                LOGGER.info("Resuming download from byte %s", file_size)

            response = self.session.get(url, stream=True, timeout=(60, 300), headers=headers)

            if file_size > 0 and response.status_code == 416:  # Range Not Satisfiable
                LOGGER.warning("Server doesn't support range requests, restarting download")
                os.remove(local_path)
                file_size = 0
                headers.pop('Range', None)
                response = self.session.get(url, stream=True, timeout=(60, 300), headers=headers)

            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            if 'content-range' in response.headers:
                content_range = response.headers['content-range']
                if '/' in content_range:
                    total_size = int(content_range.split('/')[-1])

            if file_size > 0 and total_size > file_size:
                total_size = total_size - file_size
            elif file_size > 0:
                total_size = total_size  # The server may return the remaining size

            block_size = 512 * 1024  # 512KB block
            downloaded = file_size
            retry_count = 0
            max_retries = 3

            mode = 'ab' if file_size > 0 else 'wb'

            with open(local_path, mode) as f:
                while retry_count <= max_retries:
                    try:
                        for data in response.iter_content(block_size):
                            downloaded += len(data)
                            f.write(data)
                            f.flush()

                            if progress_hook and total_size > 0:
                                percent = (downloaded / (file_size + total_size)) * 100
                                progress_hook(
                                    (downloaded - file_size) // block_size,
                                    block_size,
                                    total_size
                                )
                        break
                    except (requests.exceptions.ChunkedEncodingError,
                            requests.exceptions.ConnectionError) as e:
                        retry_count += 1
                        if retry_count > max_retries:
                            raise e
                        LOGGER.warning("Download interrupted, retrying (%s/%s): %s",
                                       retry_count, max_retries, e)

                        current_size = os.path.getsize(local_path)
                        headers['Range'] = f'bytes={current_size}-'

                        time.sleep(2 * retry_count)

                        response = self.session.get(url, stream=True, timeout=(60, 300), headers=headers)
                        response.raise_for_status()
                        continue

            return True
        except requests.exceptions.Timeout:
            LOGGER.error("Timeout error downloading file: %s", url)
            return False
        except requests.exceptions.HTTPError as e:
            LOGGER.error("HTTP error downloading file: %s - %s", url, e)
            return False
        except requests.exceptions.RequestException as e:
            LOGGER.error("Error downloading file: %s - %s", url, e)
            return False
        except Exception as e:
            LOGGER.error("Unexpected error downloading file: %s - %s", url, e)
            return False

    @staticmethod
    def is_connected() -> bool:
        test_servers = [
            ("8.8.8.8", 53),
            ("1.1.1.1", 53),
            ("223.5.5.5", 53),
            ("220.181.38.148", 80),
            ("114.114.114.114", 53),
        ]
        try:
            socket.gethostbyname("github.com")
            LOGGER.info("DNS resolution successful")
            return True
        except socket.gaierror:
            LOGGER.warning("DNS resolution failed")
        for host, port in test_servers:
            try:
                socket.setdefaulttimeout(3)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((host, port))
                s.close()
                LOGGER.info("Network connection test passed with %s:%s", host, port)
                return True
            except (socket.timeout, socket.error) as e:
                LOGGER.warning("Connection test failed for %s:%s: %s", host, port, e)
                continue
        LOGGER.error("All network connection tests failed")
        return False

    def read_current_version(self) -> str:
        try:
            ver_file = Path(self.cfg.ver_cfg_path)
            if ver_file.exists():
                ver = ver_file.read_text().splitlines()[0]
                LOGGER.info("Current version: %s", ver)
                return ver
            LOGGER.warning("Version file not found")
        except Exception as e:
            LOGGER.error("Error reading version file: %s", e)
        return "Unknown"

    def read_current_os_version(self) -> str:
        try:
            ver_file = Path(self.cfg.os_ver_cfg_path)
            if ver_file.exists():
                ver = ver_file.read_text().splitlines()[0]
                LOGGER.info("Current OS version: %s", ver)
                return ver
            LOGGER.warning("OS version file not found")
        except Exception as e:
            LOGGER.error("Error reading OS version file: %s", e)
        return "Unknown"

    def fetch_remote_info(self) -> dict:
        dit = {}
        update_info = ""
        max_retries = 3
        retry_count = 0

        while retry_count <= max_retries:
            try:
                LOGGER.info("Downloading version info from %s (attempt %s/%s)",
                            self.cfg.info_url, retry_count + 1, max_retries + 1)
                response = self.session.get(self.cfg.info_url, timeout=10)
                response.raise_for_status()

                with open(self.cfg.tmp_info, "w", encoding="utf-8") as f:
                    f.write(response.text)

                if os.path.exists(self.cfg.tmp_info):
                    with open(self.cfg.tmp_info, "r", encoding="utf-8") as f:
                        for line in f:
                            parts = line.split("=")
                            if len(parts) > 1:
                                dit[parts[0].strip()] = parts[1].strip()

                info_filename = "info_zh_CN.txt" if self.t.lang_code in ["zh_CN", "zh_TW"] else "info_en_US.txt"
                info_url = f"{self.cfg.info_url.rsplit('/', 1)[0]}/{info_filename}"

                LOGGER.info("Downloading update info from %s (attempt %s/%s)",
                            info_url, retry_count + 1, max_retries + 1)
                response = self.session.get(info_url, timeout=10)
                response.raise_for_status()

                with open(self.cfg.tmp_info, "wb") as f:
                    f.write(response.content)

                if os.path.exists(self.cfg.tmp_info):
                    with open(self.cfg.tmp_info, "r", encoding="utf-8") as f:
                        update_info = f.read()
                        dit['update_info'] = update_info

                break

            except (ContentTooShortError, URLError) as e:
                retry_count += 1
                if retry_count > max_retries:
                    LOGGER.error("Error downloading version info after %s attempts: %s", max_retries + 1, e)
                    break
                LOGGER.warning("Attempt %s failed, retrying in %s seconds: %s",
                               retry_count, retry_count * 2, e)
                time.sleep(retry_count * 2)

            except Exception as e:
                LOGGER.error("Unexpected error processing version info: %s", e)
                break

        return dit

    def draw_home(self, model: str, cur_ver: str, new_ver: str, os_cur_ver: str,
                  actions_enabled: bool, append_enabled: bool) -> None:
        ui = self.ui
        t = self.t

        ui.clear()
        ui.info_header(f"{t.t('Stock OS Mod Updater')} v{cur_app_ver}", t.t("Professional Edition"))

        content_top = 90
        content_height = ui.y_size - content_top - 50

        panel_padding = 20
        panel_width = ui.x_size - panel_padding * 2
        panel_height = content_height - 60
        ui.panel([panel_padding, content_top, panel_padding + panel_width, content_top + panel_height],
                 title=t.t("System Information"))

        info_x = ui.x_size // 2
        y_start = content_top + 70
        line_height = 32

        ui.text((info_x, y_start), f"{t.t('Device Model')}: {model}", font=22, anchor="mm")

        ui.text((info_x, y_start + line_height), f"{t.t('Current Version')}: {cur_ver}", font=20, anchor="mm")
        ui.text((info_x, y_start + line_height * 2), f"{t.t('Available Version')}: {new_ver}", font=20, anchor="mm")
        ui.text((info_x, y_start + line_height * 3), f"{t.t('OS date')}: {os_cur_ver}", font=20, anchor="mm")

        status_y = y_start + line_height * 3 + 40
        if append_enabled:
            status_text = t.t("UPDATE AVAILABLE")
            ui.status_badge((info_x, status_y), f"{status_text} +", "success")
        elif actions_enabled:
            status_text = t.t("UPDATE AVAILABLE")
            ui.status_badge((info_x, status_y), status_text, "success")
        else:
            status_text = t.t("NO UPDATE AVAILABLE")
            ui.status_badge((info_x, status_y), status_text, "info")

        button_y = ui.y_size - 50
        button_width = 140
        button_height = 36

        info_x = ui.x_size - button_width - 20
        exit_x = ui.x_size // 2 - button_width
        ui.button([info_x, button_y, info_x + button_width, button_y + button_height],
                  t.t("Info"), "Y", True)
        ui.button([exit_x, button_y, exit_x + button_width, button_y + button_height],
                  t.t("Exit"), "B", True)

        if actions_enabled:
            update_x = 20
            ui.button([update_x, button_y, update_x + button_width, button_y + button_height],
                      t.t("Update"), "A", True)

            ui.text((ui.x_size // 2, status_y + 50),
                    t.t("Tip: Press A to start update"),
                    font=20, anchor="mm", color=ui.cfg.COLOR_TEXT_SECONDARY)
        else:
            ui.text((ui.x_size // 2, status_y + 50),
                    t.t("Tip: Version information not obtained or no available updates."),
                    font=20, anchor="mm", color=ui.cfg.COLOR_TEXT_SECONDARY)

        ui.paint()

    def draw_message_center(self, title: str, subtitle: Optional[str] = None,
                            icon: Optional[str] = None, status: str = "info") -> None:
        ui = self.ui
        ui.clear()

        max_panel_width = min(ui.x_size - 80, 600)
        padding = 20

        title_font_size = 23
        subtitle_font_size = 21

        title_lines = self._wrap_text(ui, title, title_font_size, max_panel_width - 2 * padding - (50 if icon else 0))
        title_height = len(title_lines) * 30

        subtitle_height = 0
        if subtitle:
            subtitle_lines = self._wrap_text(ui, subtitle, subtitle_font_size,
                                             max_panel_width - 2 * padding - (50 if icon else 0))
            subtitle_height = len(subtitle_lines) * 25

        panel_height = 40 + title_height + subtitle_height + 20

        panel_height = min(panel_height, ui.y_size - 100)

        panel_width = max_panel_width
        panel_x = (ui.x_size - panel_width) // 2
        panel_y = (ui.y_size - panel_height) // 2 - 20

        ui.panel([panel_x, panel_y, panel_x + panel_width, panel_y + panel_height],
                 title=None if icon else title)

        icon_x = panel_x + 30
        icon_y = panel_y + panel_height // 2

        if icon:
            icon_size = 40
            ui.circle((icon_x, icon_y), icon_size // 2, fill=ui.cfg.COLOR_PRIMARY)
            ui.text((icon_x, icon_y), icon, font=30, anchor="mm", color=ui.cfg.COLOR_TEXT)

            text_x = icon_x + icon_size + 20
            text_start_y = panel_y + 30

            for i, line in enumerate(title_lines):
                ui.text((text_x, text_start_y + i * 30), line, font=title_font_size,
                        anchor="lm", bold=True)
        else:
            text_x = panel_x + panel_width // 2
            text_start_y = panel_y + 30

            for i, line in enumerate(title_lines):
                ui.text((text_x, text_start_y + i * 30), line, font=title_font_size,
                        anchor="mm", bold=True)

        if subtitle:
            subtitle_start_y = panel_y + 30 + title_height + 10

            if icon:
                subtitle_x = icon_x + icon_size + 20
                anchor = "lm"
            else:
                subtitle_x = panel_x + panel_width // 2
                anchor = "mm"

            for i, line in enumerate(subtitle_lines):
                ui.text((subtitle_x, subtitle_start_y + i * 25), line, font=subtitle_font_size,
                        anchor=anchor, color=ui.cfg.COLOR_TEXT_SECONDARY)

        if status != "info":
            status_colors = {
                "success": ui.cfg.COLOR_ACCENT,
                "warning": ui.cfg.COLOR_SECONDARY,
                "error": ui.cfg.COLOR_DANGER
            }
            status_color = status_colors.get(status, ui.cfg.COLOR_PRIMARY)
            indicator_x = panel_x + panel_width - 15
            indicator_y = panel_y + 20
            ui.circle((indicator_x, indicator_y), 8, fill=status_color)

        if status == "error":
            button_y = ui.y_size - 50
            button_width = 140
            button_height = 36
            exit_x = ui.x_size - button_width - 20
            ui.button([exit_x, button_y, exit_x + button_width, button_y + button_height],
                      self.t.t("Exit"), "B", True)
        ui.paint()

        while status == "error":
            if self.skip_first_input:
                self.input.reset()
                self.skip_first_input = False
            else:
                self.input.poll()

            if self.input.is_key("B"):
                break

    def _wrap_text(self, ui: UIRenderer, text: str, font_size: int, max_width: int) -> list:
        if not text:
            return []

        try:
            font = ImageFont.truetype(ui.cfg.font_file, font_size)
        except:
            font = ImageFont.load_default()

        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = ui.active_draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]

            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                if ui.active_draw.textbbox((0, 0), word, font=font)[2] > max_width:
                    chars = list(word)
                    split_word = []
                    current_chars = []

                    for char in chars:
                        test_chars = ''.join(current_chars + [char])
                        char_width = ui.active_draw.textbbox((0, 0), test_chars, font=font)[2]

                        if char_width <= max_width:
                            current_chars.append(char)
                        else:
                            if current_chars:
                                split_word.append(''.join(current_chars))
                            current_chars = [char]

                    if current_chars:
                        split_word.append(''.join(current_chars))

                    lines.extend(split_word)
                else:
                    current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return lines

    def _calculate_speed(self, downloaded: int) -> Tuple[str, str]:
        current_time = time.time()
        
        if not hasattr(self, '_speed_data'):
            self._speed_data = {
                'start_time': current_time,
                'last_time': current_time,
                'last_downloaded': 0,
                'speed_text': "..."
            }
        
        time_diff = current_time - self._speed_data['last_time']
        if time_diff >= 1.0:
            downloaded_diff = downloaded - self._speed_data['last_downloaded']
            download_speed = downloaded_diff / time_diff
            
            if download_speed >= 1024 * 1024:
                speed_text = f"{download_speed / (1024 * 1024):.1f} MB/s"
            elif download_speed >= 1024:
                speed_text = f"{download_speed / 1024:.1f} KB/s"
            else:
                speed_text = f"{download_speed:.1f} B/s"
            
            self._speed_data['last_time'] = current_time
            self._speed_data['last_downloaded'] = downloaded
            self._speed_data['speed_text'] = speed_text
        
        return self._speed_data['speed_text']
    
    def update_app(self, new_ver: str) -> None:
        ui = self.ui
        t = self.t

        ui.clear()
        self.ui.text((self.ui.x_size // 2, self.ui.y_size // 2),
                     f"{t.t('Update the application')} v{cur_app_ver} -> v{new_ver}", font=26, anchor="mm", bold=True)
        ui.paint()
        time.sleep(3)

        def progress_hook(block_num: int, block_size: int, total_size: int):
            try:
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = min(100, downloaded * 100 // total_size)
                    label_top = t.t("Downloading App Files...")
                    if total_size >= 1024*1024:
                        unit_num = 1024*1024
                        unit = "MB"
                    else:
                        unit_num = 1024
                        unit = "KB"
                    speed_display = self._calculate_speed(downloaded)
                    label_bottom = f"{(downloaded / unit_num):.1f}{unit} / {(total_size / unit_num):.2f}{unit} | {speed_display}"
                    ui.clear()
                    ui.info_header(t.t("Update application"), t.t("Downloading update package"))
                    ui.progress_bar(ui.y_size // 2 + 20, percent, label_top=label_top, label_bottom=label_bottom)
                    ui.paint()
            except Exception as e:
                LOGGER.error("Error updating progress: %s", e)

        LOGGER.info("Starting App update process")
        self.draw_message_center(t.t("Downloading"), t.t("Fetching verification data..."), "㊙", "info")

        if not self._download_file(self.md5_url, self.cfg.tmp_app_md5, progress_hook):
            LOGGER.error("Error downloading MD5 file")
            self.draw_message_center(t.t("Download Error"), t.t("Failed to download verification file."), "✖", "error")
            MainApp.exit_cleanup(2, self.ui, self.cfg)

        if not self._download_file(self.update_url, self.cfg.tmp_app_update, progress_hook):
            LOGGER.error("Error downloading update file")
            self.draw_message_center(t.t("Download Error"), t.t("Failed to download update file."), "✖", "error")
            MainApp.exit_cleanup(2, self.ui, self.cfg)

        LOGGER.info("Verifying downloaded files")
        self.draw_message_center(t.t("Verifying"), t.t("Checking file integrity..."), "✪", "info")

        down_md5 = ""
        check_md5 = ""

        if os.path.exists(self.cfg.tmp_app_update):
            try:
                md5_hash = hashlib.md5()
                with open(self.cfg.tmp_app_update, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        md5_hash.update(chunk)
                down_md5 = md5_hash.hexdigest().lower()
                LOGGER.info("Calculated MD5 of update file: %s", down_md5)
            except Exception as e:
                LOGGER.error("Error calculating MD5: %s", e)
                down_md5 = ""

        if os.path.exists(self.cfg.tmp_app_md5):
            try:
                with open(self.cfg.tmp_app_md5, "r", encoding="utf-8") as f:
                    check_md5 = f.readline().strip().lower()
                LOGGER.info("Expected MD5 from file: %s", check_md5)
            except Exception as e:
                LOGGER.error("Error reading MD5 file: %s", e)
                check_md5 = ""

        if down_md5 and check_md5 and down_md5 == check_md5:
            LOGGER.info("MD5 verification successful")
            LOGGER.info("Application restart")
            self.draw_message_center(t.t("Prompt message"), t.t("Updating, restart later..."), "㊙", "info")
            time.sleep(3)
            MainApp.exit_not_cleanup(36)
        else:
            LOGGER.error("MD5 verification failed. Expected: %s, Got: %s", check_md5, down_md5)
            self.draw_message_center(t.t("Verification Failed"), t.t("File integrity check failed."), "✖", "error")
            MainApp.exit_cleanup(3, self.ui, self.cfg)

    def show_info(self, info: str) -> None:
        ui = self.ui
        t = self.t

        current_page = 0

        def prepare_lines():
            ui.clear()
            content_top = 0
            content_height = ui.y_size - content_top

            panel_padding = 0
            panel_width = ui.x_size - panel_padding * 2
            panel_height = content_height - 60

            text_padding = 15
            text_width = panel_width - text_padding * 2
            text_x = panel_padding + text_padding

            font_size = 22
            try:
                font = ImageFont.truetype(ui.cfg.font_file, font_size)
            except:
                font = ImageFont.load_default()

            lines = []

            paragraphs = info.split('\n')

            for paragraph in paragraphs:
                if not paragraph.strip():
                    lines.append('')
                    continue

                words = paragraph.split()
                current_line = []

                for word in words:
                    test_line = ' '.join(current_line + [word]) if current_line else word
                    bbox = ui.active_draw.textbbox((0, 0), test_line, font=font)
                    line_width = bbox[2] - bbox[0]

                    if line_width <= text_width:
                        current_line.append(word)
                    else:
                        if current_line:
                            lines.append(' '.join(current_line))

                        word_bbox = ui.active_draw.textbbox((0, 0), word, font=font)
                        word_width = word_bbox[2] - word_bbox[0]

                        if word_width > text_width:
                            chars = list(word)
                            current_chars = []

                            for char in chars:
                                test_chars = ''.join(current_chars + [char])
                                char_bbox = ui.active_draw.textbbox((0, 0), test_chars, font=font)
                                char_width = char_bbox[2] - char_bbox[0]

                                if char_width <= text_width:
                                    current_chars.append(char)
                                else:
                                    if current_chars:
                                        lines.append(''.join(current_chars))
                                    current_chars = [char]

                            if current_chars:
                                current_line = [''.join(current_chars)]
                            else:
                                current_line = []
                        else:
                            current_line = [word]

                if current_line:
                    lines.append(' '.join(current_line))

            return lines, text_x, panel_height, text_width, font

        def render_page(lines, text_x, panel_height, text_width, font, page):
            ui.clear()
            content_top = 0
            content_height = ui.y_size - content_top

            panel_padding = 0
            panel_width = ui.x_size - panel_padding * 2
            panel_height_val = content_height - 60

            ui.panel([panel_padding, content_top, panel_padding + panel_width, content_top + panel_height_val],
                     title=t.t("Update Information"))

            text_y = content_top + 60

            line_height = 30
            max_lines_per_page = (panel_height_val - 80) // line_height
            total_pages = (len(lines) + max_lines_per_page - 1) // max_lines_per_page

            page = max(0, min(page, total_pages - 1))

            start_line = page * max_lines_per_page
            end_line = min(start_line + max_lines_per_page, len(lines))

            for i, line in enumerate(lines[start_line:end_line]):
                y_pos = text_y + i * line_height

                if line:
                    bbox = ui.active_draw.textbbox((0, 0), line, font=font)
                    line_width = bbox[2] - bbox[0]
                    if line_width > text_width:
                        truncated_line = line
                        while truncated_line and ui.active_draw.textbbox((0, 0), truncated_line + "...", font=font)[
                            2] > text_width:
                            truncated_line = truncated_line[:-1]
                        line = truncated_line + "..."

                ui.text((text_x, y_pos), line, font=22, anchor="lm")

            if total_pages > 1:
                page_info = f"{page + 1}/{total_pages}"
                page_x = ui.x_size - 20
                ui.text((page_x, text_y - 15), page_info, font=18,
                        color=ui.cfg.COLOR_TEXT_SECONDARY, anchor="rm")

            button_y = ui.y_size - 50
            button_width = 140
            button_height = 36

            if total_pages > 1:
                prev_x = 20
                ui.button([prev_x, button_y, prev_x + button_width, button_y + button_height],
                              t.t("Previous"), "L1", True)

                next_x = 30 + button_width
                ui.button([next_x, button_y, next_x + button_width, button_y + button_height],
                              t.t("Next"), "R1", True)
                exit_x = ui.x_size - button_width - 20
                ui.button([exit_x, button_y, exit_x + button_width, button_y + button_height],
                              t.t("Exit"), "B", True)
            else:
                exit_x = ui.x_size - button_width - 20
                ui.button([exit_x, button_y, exit_x + button_width, button_y + button_height],
                          t.t("Exit"), "B", True)

            ui.paint()
            return max_lines_per_page, total_pages, page

        lines, text_x, panel_height, text_width, font = prepare_lines()
        lines_per_page, total_pages, current_page = render_page(
            lines, text_x, panel_height, text_width, font, current_page
        )

        while True:
            if self.skip_first_input:
                self.input.reset()
                self.skip_first_input = False
            else:
                self.input.poll()

            if self.input.is_key("B"):
                return
            elif total_pages > 1:
                if self.input.is_key("L1") and current_page > 0:
                    current_page -= 1
                    lines_per_page, total_pages, current_page = render_page(
                        lines, text_x, panel_height, text_width, font, current_page
                    )
                elif self.input.is_key("R1") and current_page < total_pages - 1:
                    current_page += 1
                    lines_per_page, total_pages, current_page = render_page(
                        lines, text_x, panel_height, text_width, font, current_page
                    )

    def start_update(self, append_active = False) -> None:
        ui = self.ui
        t = self.t

        def progress_hook(block_num: int, block_size: int, total_size: int):
            try:
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = min(100, downloaded * 100 // total_size)
                    label_top = t.t("Downloading Update Files...")
                    if total_size >= 1024*1024:
                        unit_num = 1024*1024
                        unit = "MB"
                    else:
                        unit_num = 1024
                        unit = "KB"
                    speed_display = self._calculate_speed(downloaded)
                    label_bottom = f"{(downloaded / unit_num):.1f}{unit} / {(total_size / unit_num):.2f}{unit} | {speed_display}"
                    ui.clear()
                    ui.info_header(t.t("System Update"), t.t("Downloading update package"))
                    ui.progress_bar(ui.y_size // 2 + 20, percent, label_top=label_top, label_bottom=label_bottom)
                    ui.paint()
            except Exception as e:
                LOGGER.error("Error updating progress: %s", e)

        LOGGER.info("Starting OS update process")
        self.draw_message_center(t.t("Downloading"), t.t("Fetching verification data..."), "㊙", "info")

        if not self._download_file(self.md5_url, self.cfg.tmp_md5, progress_hook):
            LOGGER.error("Error downloading MD5 file")
            self.draw_message_center(t.t("Download Error"), t.t("Failed to download verification file."), "✖", "error")
            MainApp.exit_cleanup(2, self.ui, self.cfg)

        if not self._download_file(self.update_url, self.cfg.tmp_update, progress_hook):
            LOGGER.error("Error downloading update file")
            self.draw_message_center(t.t("Download Error"), t.t("Failed to download update file."), "✖", "error")
            MainApp.exit_cleanup(2, self.ui, self.cfg)

        LOGGER.info("Verifying downloaded files")
        self.draw_message_center(t.t("Verifying"), t.t("Checking file integrity..."), "✪", "info")

        down_md5 = ""
        check_md5 = ""

        if os.path.exists(self.cfg.tmp_update):
            try:
                md5_hash = hashlib.md5()
                with open(self.cfg.tmp_update, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        md5_hash.update(chunk)
                down_md5 = md5_hash.hexdigest().lower()
                LOGGER.info("Calculated MD5 of update file: %s", down_md5)
            except Exception as e:
                LOGGER.error("Error calculating MD5: %s", e)
                down_md5 = ""

        if os.path.exists(self.cfg.tmp_md5):
            try:
                with open(self.cfg.tmp_md5, "r", encoding="utf-8") as f:
                    check_md5 = f.readline().strip().lower()
                LOGGER.info("Expected MD5 from file: %s", check_md5)
            except Exception as e:
                LOGGER.error("Error reading MD5 file: %s", e)
                check_md5 = ""

        if down_md5 and check_md5 and down_md5 == check_md5:
            LOGGER.info("MD5 verification successful")
            target_path = "/mnt/mmc" if append_active else "/mnt/mod"
            autostart = False if append_active else True
            if self.unpack_zip(self.cfg.tmp_update, target_path) == 0:
                self.draw_message_center(t.t("System Update"), t.t("Ready, start upgrading..."), "✔", "success")
                time.sleep(3)
                MainApp.reboot(self.ui, self.cfg, autostart)
            else:
                LOGGER.error("Error unpacking update file")
                self.draw_message_center(t.t("Extraction Error"), t.t("Failed to extract update files."), "✖", "error")
                MainApp.exit_cleanup(4, self.ui, self.cfg)
        else:
            LOGGER.error("MD5 verification failed. Expected: %s, Got: %s", check_md5, down_md5)
            self.draw_message_center(t.t("Verification Failed"), t.t("File integrity check failed."), "✖", "error")
            MainApp.exit_cleanup(3, self.ui, self.cfg)

    def unpack_zip(self, dep_path: str, target_path: str) -> int:
        if not os.path.exists(dep_path):
            LOGGER.error("Update file not found: %s", dep_path)
            return 1
        update_path = os.path.join(target_path, "update")
        if os.path.isdir(update_path):
            shutil.rmtree(update_path)
        os.makedirs(update_path, exist_ok=True)
        try:
            with zipfile.ZipFile(dep_path, "r") as zip_ref:
                namelist = zip_ref.namelist()
                total_files = len(namelist)
                LOGGER.info("Unpacking %s files from %s", total_files, dep_path)
                for i, file in enumerate(namelist):
                    zip_ref.extract(file, target_path)
                    percent = (i + 1) * 100 / max(1, total_files)

                    ui = self.ui
                    ui.clear()
                    ui.info_header(self.t.t("System Update"), self.t.t("Extracting files..."))

                    file_name = os.path.basename(file)
                    if len(file_name) > 30:
                        file_name = file_name[:27] + "..."

                    ui.text((ui.x_size // 2, ui.y_size // 2 - 20), f"{self.t.t('File')}: {file_name}", font=18,
                            anchor="mm")

                    progress_text = f"{i + 1} / {total_files} {self.t.t('files')}"
                    ui.text((ui.x_size // 2, ui.y_size // 2 + 40), progress_text,
                            font=16, anchor="mm", color=ui.cfg.COLOR_TEXT_SECONDARY)

                    ui.progress_bar(ui.y_size // 2 + 10, percent)
                    ui.paint()
            LOGGER.info("Unpacking completed successfully")
            return 0
        except zipfile.BadZipFile:
            LOGGER.error("Invalid zip file: %s", dep_path)
            return 1
        except Exception as e:
            LOGGER.error("Error unpacking zip file: %s", e)
            return 1


# =========================
# Main Application
# =========================
class MainApp:
    def __init__(self):
        self.cfg = Config()

        try:
            board_info = Path("/mnt/vendor/oem/board.ini").read_text().splitlines()[0]
            LOGGER.info("Detected board: %s", board_info)
        except (FileNotFoundError, IndexError) as e:
            LOGGER.warning("Board detection failed: %s, using default RG35xxH", e)
            board_info = "RG35xxH"
        self.board_info = board_info

        try:
            lang_index_raw = Path("/mnt/vendor/oem/language.ini").read_text().splitlines()[0]
            lang_index = int(lang_index_raw)
            LOGGER.info("Detected language index: %s", lang_index)
        except (FileNotFoundError, IndexError, ValueError) as e:
            LOGGER.warning("Language detection failed: %s, using default index 2", e)
            lang_index = 2

        self.hw_info = self.cfg.board_mapping.get(self.board_info, 0)
        self.system_lang = self.cfg.system_list[lang_index if 0 <= lang_index < len(self.cfg.system_list) else 2]
        LOGGER.info("Hardware info: %s, System language: %s", self.hw_info, self.system_lang)

        self.t = Translator(self.system_lang)
        self.ui = UIRenderer(self.cfg, self.t, self.hw_info)
        self.input = InputHandler(self.cfg)
        self.updater = Updater(self.cfg, self.ui, self.t)

        self.skip_first_input = True

    @staticmethod
    def exit_not_cleanup(code: int) -> None:
        LOGGER.info("Exiting with code %s", code)
        sys.exit(code)

    @staticmethod
    def exit_cleanup(code: int, ui: UIRenderer, cfg: Config) -> None:
        LOGGER.info("Exiting with code %s", code)
        try:
            for p in (cfg.tmp_info, cfg.tmp_update, cfg.tmp_md5):
                if os.path.exists(p):
                    os.remove(p)
            ui.draw_end()
        except Exception as e:
            LOGGER.error("Error during exit cleanup: %s", e)
        finally:
            sys.exit(code)

    @staticmethod
    def reboot(ui: UIRenderer, cfg: Config, auto = False) -> None:
        LOGGER.info("Rebooting system")
        try:
            for p in (cfg.tmp_info, cfg.tmp_update, cfg.tmp_md5, "/mnt/mod/update.dep"):
                if os.path.exists(p):
                    os.remove(p)
            if auto:
                update_dir = "/mnt/mod/ctrl"
                os.makedirs(update_dir, exist_ok=True)
                update_script_path = os.path.join(update_dir, "autostart")
                update_script_content = """#!/bin/bash

if [ -f /mnt/mod/update/update.sh ]; then
  chmod +x /mnt/mod/update/update.sh
  /mnt/mod/update/update.sh
fi
"""
                with open(update_script_path, "w") as f:
                    f.write(update_script_content)

            ui.draw_end()
            os.sync()
            os.system("reboot")
            sys.exit(0)
        except Exception as e:
            LOGGER.error("Error during reboot: %s", e)
            MainApp.exit_cleanup(1, ui, cfg)

    def run(self) -> None:

        self.ui.clear()

        for i in range(self.ui.y_size):
            ratio = i / self.ui.y_size
            color = self.ui._blend_colors(self.cfg.COLOR_PRIMARY_DARK, self.cfg.COLOR_BG, ratio)
            self.ui.rect([0, i, self.ui.x_size, i + 1], fill=color)

        self.ui.text((self.ui.x_size // 2, self.ui.y_size // 2 - 70), "☯", font=50, anchor="mm")
        self.ui.text((self.ui.x_size // 2, self.ui.y_size // 2 - 20), self.t.t("Stock OS Mod Updater"), font=26,
                     anchor="mm",
                     bold=True)
        self.ui.text((self.ui.x_size // 2, self.ui.y_size // 2 + 30), self.t.t("Professional Edition"), font=20,
                     anchor="mm", color=self.ui.cfg.COLOR_TEXT_SECONDARY)
        self.ui.text((self.ui.x_size // 2, self.ui.y_size - 90), self.t.t("Initializing..."), font=18, anchor="mm",
                     color=self.ui.cfg.COLOR_TEXT_SECONDARY)

        self.ui.paint()
        time.sleep(2)

        cur_ver = "Unknown"
        cur_ver = self.updater.read_current_version()

        if not self.updater.is_connected():
            self.updater.draw_message_center(
                self.t.t("No Internet Connection"),
                self.t.t("Please check your network settings"),
                "✈", "error"
            )
            self.updater.draw_message_center(
                self.t.t("Current Version"),
                cur_ver,
                "☯", "error"
            )
            MainApp.exit_cleanup(1, self.ui, self.cfg)

        self.updater.draw_message_center(
            self.t.t("Checking for updates..."),
            self.t.t("Please wait..."),
            "☯", "info"
        )

        update_active = False
        append_active = False

        url_dit = self.updater.fetch_remote_info()
        for key, value in url_dit.items():
            if key != "update_info":
                LOGGER.info("%s -> %s", key, value)

        app_ver = url_dit.get('app_ver', 'Unknown')
        app_update_url = url_dit.get('app_update_url')
        app_md5_url = url_dit.get('app_md5_url')
        update_ver = url_dit.get('update_ver', 'Unknown')
        update_url = url_dit.get('update_url')
        md5_url = url_dit.get('md5_url')
        data_ver = url_dit.get('data_ver', 'Unknown')
        data_update_url = url_dit.get('data_update_url')
        data_md5_url = url_dit.get('data_md5_url')
        update_info = url_dit.get('update_info', 'Unknown')

        if app_ver != "Unknown" and cur_app_ver < app_ver and bool(app_update_url):
            self.updater.update_url = app_update_url
            self.updater.md5_url = app_md5_url
            self.updater.update_app(app_ver)


        os_cur_ver = self.updater.read_current_os_version()
        if (
            cur_ver != "Unknown" and update_ver != "Unknown" and cur_ver < base_ver and bool(update_url)
        ) or (
            cur_ver == "Unknown" and os_cur_ver >= "20250211" and update_ver != "Unknown" and bool(update_url)
        ):
            update_active = True
            self.updater.update_url = update_url
            self.updater.md5_url = md5_url
            new_ver = update_ver
        elif cur_ver != "Unknown" and data_ver != "Unknown" and cur_ver < data_ver and bool(data_update_url):
            update_active = True
            append_active = True
            self.updater.update_url = data_update_url
            self.updater.md5_url = data_md5_url
            new_ver = data_ver
        else:
            self.updater.update_url = data_update_url
            self.updater.md5_url = data_md5_url
            new_ver = data_ver

        while True:
            try:
                self.updater.draw_home(self.board_info, cur_ver, new_ver, os_cur_ver,
                                       actions_enabled=update_active, append_enabled=append_active)

                if self.skip_first_input:
                    self.input.reset()
                    self.skip_first_input = False
                else:
                    self.input.poll()

                if self.input.is_key("B"):
                    MainApp.exit_cleanup(0, self.ui, self.cfg)

                elif update_active and self.input.is_key("A"):
                    self.updater.start_update(append_active)

                elif self.input.is_key("Y"):
                    self.updater.show_info(update_info)

                time.sleep(0.1)

            except Exception as e:
                LOGGER.error("Unexpected error in main loop: %s", e)
                self.updater.draw_message_center(
                    self.t.t("An error occurred"),
                    self.t.t("Restarting application..."),
                    "☠", "error"
                )
                self.ui.draw_end()
                sys.exit(1)


# =========================
# Entrypoint
# =========================
if __name__ == "__main__":
    try:
        MainApp().run()
    except KeyboardInterrupt:
        LOGGER.info("Program interrupted by user")
        sys.exit(0)
    except Exception as e:
        LOGGER.error("Unexpected error: %s", e)
        sys.exit(1)
