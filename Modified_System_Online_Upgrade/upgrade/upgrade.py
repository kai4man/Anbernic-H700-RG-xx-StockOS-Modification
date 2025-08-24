#!/usr/bin/env python3

"""
Stock OS Mod Updater - Professional Edition
"""
from __future__ import annotations

# =========
# 标准库导入
# =========
import hashlib
import json
import logging
import mmap
import os
import socket
import struct
import sys
import time
import urllib.request
import zipfile
from dataclasses import dataclass
from fcntl import ioctl
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.error import ContentTooShortError, URLError
from urllib.request import urlretrieve

# =========
# 第三方进口
# =========
from PIL import Image, ImageDraw, ImageFont

cur_app_ver = "1.0.0"

# ========
# 日志设置
# ========
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


# ====
# 配置
# ====
@dataclass
class Config:
    """集中式配置和常量."""

    # 硬件+语言
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

    # 专业配色方案 - 深色专业主题
    COLOR_PRIMARY: str = "#eb6325"      # 主色调 - 专业蓝色
    COLOR_PRIMARY_LIGHT: str = "#f6823b" # 浅蓝色
    COLOR_PRIMARY_DARK: str = "#d84e1d"  # 深蓝色
    COLOR_SECONDARY: str = "#0b9ef5"    # 辅助色 - 琥珀色
    COLOR_ACCENT: str = "#81b910"       # 强调色 - 翠绿色
    COLOR_DANGER: str = "#4444ef"       # 危险/错误色 - 红色
    
    COLOR_BG: str = "#271811"           # 背景色 - 深蓝灰色
    COLOR_BG_LIGHT: str = "#37291f"     # 浅背景色
    COLOR_CARD: str = "#35241a"         # 卡片背景
    COLOR_CARD_LIGHT: str = "#473224"   # 亮卡片背景
    
    COLOR_TEXT: str = "#f6f4f3"         # 主文本颜色
    COLOR_TEXT_SECONDARY: str = "#afa39c" # 次要文本颜色
    COLOR_BORDER: str = "#514137"       # 边框颜色
    
    COLOR_SHADOW: str = "#120a07"       # 阴影颜色
    COLOR_OVERLAY: str = "#00000080"    # 叠加层颜色

    # 字体
    font_file: str = os.path.join(APP_PATH, "font", "font.ttf")
    if not os.path.exists(font_file):
        font_file: str = "/mnt/vendor/bin/default.ttf"

    # 文件/路径
    ver_cfg_path: str = "/mnt/mod/ctrl/configs/ver.cfg"
    fb_cfg_path: str = "/mnt/mod/ctrl/configs/fb.cfg"

    # 临时文件
    tmp_info: str = "/tmp/info.txt"
    tmp_app_update: str = "/tmp/app.tar.gz"
    tmp_app_md5: str = "/tmp/app.tar.gz.md5"
    tmp_update: str = "/tmp/update.dep"
    tmp_md5: str = "/tmp/update.dep.MD5"

    # 远程
    info_url: str = (
        "https://github.com/cbepx-me/upgrade/releases/download/source/update.txt"
    )

    # 屏幕/FB
    bytes_per_pixel: int = 4

    # 输入映射
    keymap: Dict[int, str] = None

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


# ==========
# 多语言支持
# ==========
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


# ========
# 输入处理
# ========
class InputHandler:
    """用于/dev/input/event1的类似evdev的简单读取器."""

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


# =========
# UI 渲染器
# =========
class UIRenderer:
    """使用PIL封装对帧缓冲区的所有绘图操作."""

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

    # ---------- 帧缓冲区/设备 ----------
    def _get_fb_screeninfo(self, hw_info: int) -> Optional[bytes]:
        """获取自定义fb配置或设备信息."""
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
                # 尝试加载粗体字体
                try:
                    fnt = ImageFont.truetype(font_path, font_size)
                    # 使用描边模拟粗体效果
                    self.active_draw.text((pos[0]+1, pos[1]+1), text, font=fnt, fill=self.cfg.COLOR_SHADOW, anchor=anchor)
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
        self.active_draw.ellipse([x-radius, y-radius, x+radius, y+radius], fill=fill, outline=outline)

    # ---------- 用户界面组件 ----------
    def panel(self, xy, title: Optional[str] = None, shadow=True) -> None:
        if shadow:
            # 添加阴影效果
            shadow_xy = [xy[0] + 3, xy[1] + 3, xy[2] + 3, xy[3] + 3]
            self.rect(shadow_xy, fill=self.cfg.COLOR_SHADOW, radius=12)
        
        # 主面板
        self.rect(xy, fill=self.cfg.COLOR_CARD, outline=self.cfg.COLOR_BORDER, width=1, radius=12)
        
        if title:
            # 标题栏
            title_bg = [xy[0], xy[1], xy[2], xy[1] + 30]
            self.rect(title_bg, fill=self.cfg.COLOR_PRIMARY_DARK, radius=12)
            self.text((self.x_size // 2, xy[1] + 15), title, font=20, anchor="mm", bold=True)

    def button(self, xy, label: str, icon: str = None, primary: bool = False) -> None:
        # 按钮背景
        fill_color = self.cfg.COLOR_PRIMARY if primary else self.cfg.COLOR_CARD_LIGHT
        self.rect(xy, fill=fill_color, outline=self.cfg.COLOR_BORDER, radius=8)
        
        # 按钮文本
        text_x = (xy[0] + xy[2]) // 2
        text_y = (xy[1] + xy[3]) // 2
        
        if icon:
            # 如果有图标，显示图标和文本
            self.text((text_x - 25, text_y), icon, font=20, anchor="mm")
            self.text((text_x, text_y), label, font=18, anchor="lm")
        else:
            # 只有文本
            self.text((text_x, text_y), label, font=18, anchor="mm", bold=primary)

    def info_header(self, title: str, subtitle: str = None) -> None:
        # 顶部标题栏 - 渐变效果
        for i in range(60):
            ratio = i / 50
            r = self._blend_colors(self.cfg.COLOR_PRIMARY_DARK, self.cfg.COLOR_PRIMARY, ratio)
            self.rect([0, i, self.x_size, i+1], fill=r)
        
        # 标题
        self.text((self.x_size // 2, 20), title, font=26, anchor="mm", bold=True)
        
        # 副标题
        if subtitle:
            self.text((self.x_size // 2, 45), subtitle, font=18, anchor="mm", color=self.cfg.COLOR_TEXT_SECONDARY)

    def status_badge(self, center: Tuple[int, int], text: str, status: str = "info") -> None:
        # 状态徽章
        colors = {
            "success": self.cfg.COLOR_ACCENT,
            "warning": self.cfg.COLOR_SECONDARY,
            "error": self.cfg.COLOR_DANGER,
            "info": self.cfg.COLOR_PRIMARY_LIGHT
        }
        color = colors.get(status, self.cfg.COLOR_PRIMARY_LIGHT)
        
        # 测量文本尺寸
        font_path = self.cfg.font_file
        try:
            fnt = ImageFont.truetype(font_path, 18)
        except Exception:
            fnt = ImageFont.load_default()
        
        bbox = self.active_draw.textbbox((0, 0), text, font=fnt)
        text_width = bbox[2] - bbox[0] + 20
        text_height = bbox[3] - bbox[1] + 10
        
        # 绘制徽章背景
        x, y = center
        badge_rect = [x - text_width//2, y - text_height//2, x + text_width//2, y + text_height//2]
        self.rect(badge_rect, fill=color, radius=text_height//2)
        
        # 绘制文本
        self.text((x, y), text, font=18, anchor="mm", color=self.cfg.COLOR_TEXT, bold=True)

    def progress_bar(self, y_center: int, percent: float, label_top: Optional[str] = None, label_bottom: Optional[str] = None) -> None:
        bar_left = 40
        bar_right = self.x_size - 40
        bar_top = y_center - 12
        bar_bottom = y_center + 12
        bar_height = bar_bottom - bar_top

        # 背景轨道
        self.rect([bar_left, bar_top, bar_right, bar_bottom], fill=self.cfg.COLOR_BG_LIGHT, radius=bar_height//2)

        # 进度填充
        pct = max(0, min(100, percent)) / 100.0
        filled_right = bar_left + int((bar_right - bar_left) * pct)
        if filled_right > bar_left:
            # 渐变效果
            for i in range(bar_left, filled_right, 2):
                color_ratio = (i - bar_left) / (filled_right - bar_left)
                color = self._blend_colors(self.cfg.COLOR_PRIMARY, self.cfg.COLOR_ACCENT, color_ratio)
                self.rect([i, bar_top, min(i+2, filled_right), bar_bottom], fill=color, radius=bar_height//2)
            
            # 进度文本
            progress_text = f"{int(percent)}%"
            self.text((self.x_size // 2, y_center), progress_text, font=19, anchor="mm", color=self.cfg.COLOR_TEXT)

        # 标签
        if label_top:
            self.text((self.x_size // 2, bar_top - 20), label_top, font=20, anchor="mm")
        if label_bottom:
            self.text((self.x_size // 2, bar_bottom + 15), label_bottom, font=16, anchor="mm", color=self.cfg.COLOR_TEXT_SECONDARY)

    def _blend_colors(self, color1: str, color2: str, ratio: float) -> str:
        """混合两种颜色"""
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
        
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        
        return f"#{r:02x}{g:02x}{b:02x}"


# =========================
# 更新程序（网络+验证+解压缩）
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

    def fetch_remote_info(self, key: str = "update_ver", update_url_key: str = "update_url", md5_url_key: str = "md5_url") -> Tuple[str, str, str]:
        """返回 (new_ver, update_url, md5_url)."""
        new_ver = "Unknown"
        update_url = ""
        md5_url = ""
        try:
            LOGGER.info("Downloading version info from %s", self.cfg.info_url)
            urlretrieve(self.cfg.info_url, self.cfg.tmp_info)
            if os.path.exists(self.cfg.tmp_info):
                with open(self.cfg.tmp_info, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith(key):
                            parts = line.split("=")
                            if len(parts) > 1:
                                new_ver = parts[1].strip()
                        elif line.startswith(update_url_key):
                            parts = line.split("=")
                            if len(parts) > 1:
                                update_url = parts[1].strip()
                        elif line.startswith(md5_url_key):
                            parts = line.split("=")
                            if len(parts) > 1:
                                md5_url = parts[1].strip()
            LOGGER.info("Remote info -> ver: %s, update: %s, md5: %s", new_ver, update_url, md5_url)
        except (ContentTooShortError, URLError) as e:
            LOGGER.error("Error downloading version info: %s", e)
        except Exception as e:
            LOGGER.error("Unexpected error processing version info: %s", e)
        self.update_url = update_url
        self.md5_url = md5_url
        return new_ver, update_url, md5_url

    # ------- 用户界面屏幕 -------
    def update_app(self, new_ver: str) -> None:
        ui = self.ui
        t = self.t

        ui.clear()
        self.ui.text((self.ui.x_size // 2, self.ui.y_size // 2), f"{t.t('Update the application')} v{cur_app_ver} -> v{new_ver}", font=26, anchor="mm", bold=True)
        ui.paint()
        time.sleep(3)
        
        def progress_hook(block_num: int, block_size: int, total_size: int):
            try:
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = min(100, downloaded * 100 / total_size)
                    label_top = t.t("Downloading Update Files...")
                    label_bottom = f"{downloaded // 1024}KB / {max(1, total_size // 1024)}KB"
                    ui.clear()
                    ui.info_header(t.t("Update application"), t.t("Downloading update package"))
                    ui.progress_bar(ui.y_size // 2 + 20, percent, label_top=label_top, label_bottom=label_bottom)
                    ui.paint()
            except Exception as e:
                LOGGER.error("Error updating progress: %s", e)

        # 阶段：下载 MD5
        LOGGER.info("Starting App update process")
        self.draw_message_center(t.t("Downloading"), t.t("Fetching verification data..."), "⏬", "info")
        
        try:
            socket.setdefaulttimeout(30)
            urllib.request.urlretrieve(self.md5_url, self.cfg.tmp_app_md5, progress_hook)
        except (ContentTooShortError, URLError) as e:
            LOGGER.error("Error downloading MD5 file: %s", e)
            self.draw_message_center(t.t("Download Error"), t.t("Failed to download verification file."), "❌", "error")
            MainApp.exit_cleanup(2, self.ui, self.cfg)
        except Exception as e:
            LOGGER.error("Unexpected error downloading MD5 file: %s", e)
            self.draw_message_center(t.t("Unexpected Error"), t.t("An error occurred during download."), "⚠️", "error")
            MainApp.exit_cleanup(2, self.ui, self.cfg)

        # 阶段：下载更新压缩包
        try:
            urllib.request.urlretrieve(self.update_url, self.cfg.tmp_app_update, progress_hook)
        except (ContentTooShortError, URLError) as e:
            LOGGER.error("Error downloading update file: %s", e)
            self.draw_message_center(t.t("Download Error"), t.t("Failed to download update file."), "❌", "error")
            MainApp.exit_cleanup(2, self.ui, self.cfg)
        except Exception as e:
            LOGGER.error("Unexpected error downloading update file: %s", e)
            self.draw_message_center(t.t("Unexpected Error"), t.t("An error occurred during download."), "⚠️", "error")
            MainApp.exit_cleanup(2, self.ui, self.cfg)

        # 阶段：验证
        LOGGER.info("Verifying downloaded files")
        self.draw_message_center(t.t("Verifying"), t.t("Checking file integrity..."), "🔍", "info")

        down_md5 = ""
        check_md5 = ""

        # 计算 MD5
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

        # 读取预期的 MD5 值
        if os.path.exists(self.cfg.tmp_app_md5):
            try:
                with open(self.cfg.tmp_app_md5, "r", encoding="utf-8") as f:
                    check_md5 = f.readline().strip().lower()
                LOGGER.info("Expected MD5 from file: %s", check_md5)
            except Exception as e:
                LOGGER.error("Error reading MD5 file: %s", e)
                check_md5 = ""

        # 验证
        if down_md5 and check_md5 and down_md5 == check_md5:
            LOGGER.info("MD5 verification successful")
            LOGGER.info("Application restart")
            self.draw_message_center(t.t("Prompt message"), t.t("Updating, restart later..."), "⏬", "info")
            time.sleep(3)
            MainApp.exit_not_cleanup(36)
        else:
            LOGGER.error("MD5 verification failed. Expected: %s, Got: %s", check_md5, down_md5)
            self.draw_message_center(t.t("Verification Failed"), t.t("File integrity check failed."), "❌", "error")
            MainApp.exit_cleanup(3, self.ui, self.cfg)

    def draw_home(self, model: str, cur_ver: str, new_ver: str, actions_enabled: bool) -> None:
        ui = self.ui
        t = self.t

        ui.clear()
        ui.info_header(f"{t.t('Stock OS Mod Updater')} v{cur_app_ver}", t.t("Professional Edition"))
        
        # 主内容区域
        content_top = 90
        content_height = ui.y_size - content_top - 50
        
        # 系统信息面板
        panel_padding = 20
        panel_width = ui.x_size - panel_padding * 2
        panel_height = content_height - 60
        ui.panel([panel_padding, content_top, panel_padding + panel_width, content_top + panel_height], 
                title=t.t("System Information"))
        
        # 信息文本
        info_x = ui.x_size // 2
        y_start = content_top + 70
        line_height = 32
        
        # 模型信息
        ui.text((info_x, y_start), f"{t.t('Device Model')}: {model}", font=22, anchor="mm")
        
        # 版本信息
        ui.text((info_x, y_start + line_height), f"{t.t('Current Version')}: {cur_ver}", font=20, anchor="mm")
        ui.text((info_x, y_start + line_height * 2), f"{t.t('Available Version')}: {new_ver}", font=20, anchor="mm")
        
        # 状态指示器
        status_y = y_start + line_height * 3 + 20
        if actions_enabled:
            status_text = t.t("UPDATE AVAILABLE")
            ui.status_badge((info_x, status_y), status_text, "success")
        else:
            status_text = t.t("NO UPDATE AVAILABLE")
            ui.status_badge((info_x, status_y), status_text, "info")

        # 底部按钮区域
        button_y = ui.y_size - 50
        button_width = 140
        button_height = 36
        
        # 退出按钮
        exit_x = ui.x_size - button_width - 20
        ui.button([exit_x, button_y, exit_x + button_width, button_y + button_height], 
                 t.t("Exit"), "B", True)
        
        # 更新按钮 (如果可用)
        if actions_enabled:
            update_x = 20
            ui.button([update_x, button_y, update_x + button_width, button_y + button_height], 
                     t.t("Update"), "A", True)
            
            # 提示文本
            ui.text((ui.x_size // 2, status_y + 50), 
                   t.t("Press A to start update"), 
                   font=20, anchor="mm", color=ui.cfg.COLOR_TEXT_SECONDARY)
        else:
            ui.text((ui.x_size // 2, status_y + 50), 
                   t.t("Unable to obtain version information or no update available."), 
                   font=20, anchor="mm", color=ui.cfg.COLOR_TEXT_SECONDARY)

        ui.paint()

    def draw_message_center(self, title: str, subtitle: Optional[str] = None, 
                           icon: Optional[str] = None, status: str = "info") -> None:
        ui = self.ui
        ui.clear()
        
        # 添加背景面板
        panel_width = min(ui.x_size - 60, 500)
        panel_height = 140
        panel_x = (ui.x_size - panel_width) // 2
        panel_y = (ui.y_size - panel_height) // 2 - 20
        
        ui.panel([panel_x, panel_y, panel_x + panel_width, panel_y + panel_height], 
                title=title if not icon else None)
        
        # 图标 (如果有)
        if icon:
            icon_size = 40
            icon_x = panel_x + 50
            icon_y = panel_y + panel_height // 2
            
            # 绘制图标背景
            ui.circle((icon_x, icon_y), icon_size//2, fill=ui.cfg.COLOR_PRIMARY)
            ui.text((icon_x, icon_y), icon, font=30, anchor="mm", color=ui.cfg.COLOR_TEXT)
            
            # 标题文本
            ui.text((icon_x + icon_size + 20, panel_y + 20), title, font=23, anchor="lm", bold=True)
        else:
            icon_x = panel_x + 20
        
        # 副标题
        if subtitle:
            text_y = panel_y + 70 if icon else panel_y + 60
            ui.text((icon_x + (70 if icon else 50), text_y), subtitle, font=21, anchor="lm", 
                   color=ui.cfg.COLOR_TEXT_SECONDARY)
        
        # 状态指示器
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
        
        # 底部按钮区域
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


    # ------- 更新流程 -------
    def start_update(self) -> None:
        ui = self.ui
        t = self.t

        def progress_hook(block_num: int, block_size: int, total_size: int):
            try:
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = min(100, downloaded * 100 / total_size)
                    label_top = t.t("Downloading Update Files...")
                    label_bottom = f"{downloaded // 1024}KB / {max(1, total_size // 1024)}KB"
                    ui.clear()
                    ui.info_header(t.t("System Update"), t.t("Downloading update package"))
                    ui.progress_bar(ui.y_size // 2 + 20, percent, label_top=label_top, label_bottom=label_bottom)
                    ui.paint()
            except Exception as e:
                LOGGER.error("Error updating progress: %s", e)

        # 阶段：下载 MD5
        LOGGER.info("Starting OS update process")
        self.draw_message_center(t.t("Downloading"), t.t("Fetching verification data..."), "⏬", "info")
        
        try:
            socket.setdefaulttimeout(30)
            urllib.request.urlretrieve(self.md5_url, self.cfg.tmp_md5, progress_hook)
        except (ContentTooShortError, URLError) as e:
            LOGGER.error("Error downloading MD5 file: %s", e)
            self.draw_message_center(t.t("Download Error"), t.t("Failed to download verification file."), "❌", "error")
            MainApp.exit_cleanup(2, self.ui, self.cfg)
        except Exception as e:
            LOGGER.error("Unexpected error downloading MD5 file: %s", e)
            self.draw_message_center(t.t("Unexpected Error"), t.t("An error occurred during download."), "⚠️", "error")
            MainApp.exit_cleanup(2, self.ui, self.cfg)

        # 阶段：下载更新压缩包
        try:
            urllib.request.urlretrieve(self.update_url, self.cfg.tmp_update, progress_hook)
        except (ContentTooShortError, URLError) as e:
            LOGGER.error("Error downloading update file: %s", e)
            self.draw_message_center(t.t("Download Error"), t.t("Failed to download update file."), "❌", "error")
            MainApp.exit_cleanup(2, self.ui, self.cfg)
        except Exception as e:
            LOGGER.error("Unexpected error downloading update file: %s", e)
            self.draw_message_center(t.t("Unexpected Error"), t.t("An error occurred during download."), "⚠️", "error")
            MainApp.exit_cleanup(2, self.ui, self.cfg)

        # 阶段：验证
        LOGGER.info("Verifying downloaded files")
        self.draw_message_center(t.t("Verifying"), t.t("Checking file integrity..."), "🔍", "info")

        down_md5 = ""
        check_md5 = ""

        # 计算 MD5
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

        # 读取预期的 MD5 值
        if os.path.exists(self.cfg.tmp_md5):
            try:
                with open(self.cfg.tmp_md5, "r", encoding="utf-8") as f:
                    check_md5 = f.readline().strip().lower()
                LOGGER.info("Expected MD5 from file: %s", check_md5)
            except Exception as e:
                LOGGER.error("Error reading MD5 file: %s", e)
                check_md5 = ""

        # 验证
        if down_md5 and check_md5 and down_md5 == check_md5:
            LOGGER.info("MD5 verification successful")
            if self.unpack_zip(self.cfg.tmp_update, "/mnt/mmc") == 0:
                self.draw_message_center(t.t("Update Completed"), t.t("System will reboot shortly..."), "✅", "success")
                time.sleep(3)
                MainApp.reboot(self.ui, self.cfg)
            else:
                LOGGER.error("Error unpacking update file")
                self.draw_message_center(t.t("Extraction Error"), t.t("Failed to extract update files."), "❌", "error")
                MainApp.exit_cleanup(4, self.ui, self.cfg)
        else:
            LOGGER.error("MD5 verification failed. Expected: %s, Got: %s", check_md5, down_md5)
            self.draw_message_center(t.t("Verification Failed"), t.t("File integrity check failed."), "❌", "error")
            MainApp.exit_cleanup(3, self.ui, self.cfg)

    def unpack_zip(self, dep_path: str, target_path: str) -> int:
        os.makedirs(target_path, exist_ok=True)
        if not os.path.exists(dep_path):
            LOGGER.error("Update file not found: %s", dep_path)
            return 1
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
                    
                    # 文件名显示
                    file_name = os.path.basename(file)
                    if len(file_name) > 30:
                        file_name = file_name[:27] + "..."
                    
                    ui.text((ui.x_size // 2, ui.y_size // 2 - 20), f"{self.t.t('File')}: {file_name}", font=18, anchor="mm")
                    
                    # 进度信息
                    progress_text = f"{i+1}/{total_files} files"
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


# ===========
# 主要应用程序
# ===========
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
    def reboot(ui: UIRenderer, cfg: Config) -> None:
        LOGGER.info("Rebooting system")
        try:
            for p in (cfg.tmp_info, cfg.tmp_update, cfg.tmp_md5):
                if os.path.exists(p):
                    os.remove(p)
            ui.draw_end()
            os.sync()
            os.system("reboot")
            sys.exit(0)
        except Exception as e:
            LOGGER.error("Error during reboot: %s", e)
            MainApp.exit_cleanup(1, ui, cfg)

    def run(self) -> None:
        # 启动画面
        self.ui.clear()
        
        # 渐变背景
        for i in range(self.ui.y_size):
            ratio = i / self.ui.y_size
            color = self.ui._blend_colors(self.cfg.COLOR_PRIMARY_DARK, self.cfg.COLOR_BG, ratio)
            self.ui.rect([0, i, self.ui.x_size, i+1], fill=color)
        
        # 应用图标和标题
        self.ui.text((self.ui.x_size // 2, self.ui.y_size // 2 - 50), "🔄", font=50, anchor="mm")
        self.ui.text((self.ui.x_size // 2, self.ui.y_size // 2), self.t.t("Stock OS Mod Updater"), font=26, anchor="mm", bold=True)
        self.ui.text((self.ui.x_size // 2, self.ui.y_size // 2 + 30), self.t.t("Professional Edition"), font=20, anchor="mm", color=self.ui.cfg.COLOR_TEXT_SECONDARY)
        self.ui.text((self.ui.x_size // 2, self.ui.y_size - 90), self.t.t("Initializing..."), font=18, anchor="mm", color=self.ui.cfg.COLOR_TEXT_SECONDARY)
        
        self.ui.paint()
        time.sleep(2)

        if not self.updater.is_connected():
            self.updater.draw_message_center(
                self.t.t("No Internet Connection"), 
                self.t.t("Please check your network settings"), 
                "🌐", "error"
            )
            MainApp.exit_cleanup(1, self.ui, self.cfg)

        self.updater.draw_message_center(
            self.t.t("Checking for updates..."), 
            self.t.t("Please wait..."), 
            "⏳", "info"
        )

        update_active = False
        new_app_ver = "Unknown"
        cur_ver = "Unknown"
        new_ver = "Unknown"

        while True:
            try:
                if self.skip_first_input:
                    self.input.reset()
                    self.skip_first_input = False
                else:
                    self.input.poll()

                if self.input.is_key("B"):
                    MainApp.exit_cleanup(0, self.ui, self.cfg)

                new_app_ver, app_update_url, app_md5_url = self.updater.fetch_remote_info("app_ver", "app_update_url", "app_md5_url")
                if new_app_ver != "Unknown" and cur_app_ver != new_app_ver and bool(app_update_url):
                    self.updater.update_url = app_update_url
                    self.updater.md5_url = app_md5_url
                    self.updater.update_app(new_app_ver)
                
                cur_ver = self.updater.read_current_version()
                new_ver, update_url, md5_url = self.updater.fetch_remote_info()
                update_active = (
                    cur_ver != "Unknown" and new_ver != "Unknown" and bool(update_url)
                )
                self.updater.update_url = update_url
                self.updater.md5_url = md5_url

                self.updater.draw_home(self.board_info, cur_ver, new_ver, actions_enabled=update_active)

                if update_active and self.input.is_key("A"):
                    self.updater.start_update()

                time.sleep(0.1)  # 降低 CPU 使用率

            except Exception as e:
                LOGGER.error("Unexpected error in main loop: %s", e)
                self.updater.draw_message_center(
                    self.t.t("An error occurred"), 
                    self.t.t("Restarting application..."), 
                    "⚠️", "error"
                )
                self.ui.draw_end()
                sys.exit(1)


# ======
# 入口点
# ======
if __name__ == "__main__":
    try:
        MainApp().run()
    except KeyboardInterrupt:
        LOGGER.info("Program interrupted by user")
        sys.exit(0)
    except Exception as e:
        LOGGER.error("Unexpected error: %s", e)
        sys.exit(1)