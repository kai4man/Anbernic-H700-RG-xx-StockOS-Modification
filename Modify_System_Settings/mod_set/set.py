import os
import re
import shutil
from language import Translator
from systems import systems
from pathlib import Path
import subprocess

translator = Translator()
HW_MODEL = Path("/mnt/vendor/oem/board.ini").read_text().splitlines()[0].strip()
APPS_DIR = "/mnt/mmc/Roms/APPS"
G_DIR = "/mnt/mod/ctrl/configs"
G_CONF = Path(G_DIR) / "system.cfg"


def get_setting(key):
    """获取配置项的值"""
    try:
        with open(G_CONF, 'r') as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error reading setting {key}: {str(e)}")
    return None


def del_setting(key):
    """删除配置项"""
    if not re.match(r'^[a-zA-Z0-9]', key):
        return

    try:
        tmp_file = G_CONF.with_suffix('.tmp')
        with open(G_CONF, 'r') as fin, open(tmp_file, 'w') as fout:
            for line in fin:
                if not line.startswith(f"{key}="):
                    fout.write(line)
        shutil.move(tmp_file, G_CONF)
    except Exception as e:
        print(f"Error deleting setting {key}: {str(e)}")


def sort_setting():
    """排序配置文件"""
    try:
        lines = []
        with open(G_CONF, 'r') as f:
            for line in f:
                if re.match(r'^[a-z0-9]', line):
                    lines.append(line.strip())
        lines.sort()
        with open(G_CONF, 'w') as f:
            f.write("\n".join(lines) + "\n")
    except Exception as e:
        print(f"Error sorting settings: {str(e)}")


def set_setting(key, value):
    """设置配置项"""
    if not re.match(r'^[a-zA-Z0-9]', key):
        return

    del_setting(key)
    if value != "default":
        try:
            with open(G_CONF, 'a') as f:
                f.write(f"{key}={value}\n")
            sort_setting()
            os.sync()
        except Exception as e:
            print(f"Error setting {key}={value}: {str(e)}")


def run_command(cmd, check=True):
    """安全执行命令"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=check,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {cmd}\nError: {e.stderr}")
        return False
    except Exception as e:
        print(f"Error executing command: {cmd}\n{str(e)}")
        return False


def handle_lang(value):
    """处理语言设置"""
    ra_lang = [12, 11, 0, 1, 10, 3, 9, 4, 2, 7]
    psp_lang = ["zh_CN", "zh_TW", "en_US", "ja_JP", "ko_KR", "es_LA", "ru_RU", "de_DE", "fr_FR", "pt_BR"]

    try:
        lang_index = psp_lang.index(value)
        lang_num = ra_lang[lang_index]

        # 执行设置命令
        run_command(f"/mnt/vendor/ctrl/setRA.sh language {lang_num}")
        run_command(f"/mnt/vendor/ctrl/setPSP.sh language {value}")

        # 更新语言文件
        Path("/mnt/vendor/oem/language.ini").write_text(str(lang_index))
        src = Path(f"/mnt/mod/ctrl/res/{lang_index}")
        dest = Path("/mnt/data/dmenu/dmenu_attr.ini")
        if src.exists():
            shutil.copy(src, dest)
        else:
            print(f"Warning: Language resource file not found: {src}")
    except ValueError:
        print(f"Invalid language code: {value}")
    except IndexError:
        print("Language index out of range")
    except Exception as e:
        print(f"Error setting language: {str(e)}")


def handle_timezone(value):
    """处理时区设置"""
    if not Path("/usr/share/zoneinfo", value).exists():
        print(f"Invalid timezone: {value}")
        return
    run_command(f"timedatectl set-timezone {value}")


def handle_ra_hot(value):
    """处理 RetroArch 热键"""
    if value in ("0", "1"):
        set_setting("ra.hotkey", value)
    else:
        print(f"Invalid ra_hot value: {value}")


def handle_rtgg(value):
    """处理实时游戏指南"""
    if value in ("0", "1"):
        set_setting("global.spy", value)
    else:
        print(f"Invalid rtgg value: {value}")


def handle_shader(value):
    """处理着色器设置"""
    if value in ("0", "1", "2"):
        set_setting("global.shader", value)
    else:
        print(f"Invalid shader value: {value}")


def handle_dark(value):
    """处理暗黑模式"""
    if value in ("0", "1"):
        set_setting("global.dark", value)
    else:
        print(f"Invalid dark value: {value}")


def handle_varc(value):
    """处理竖版街机"""
    if value in ("0", "1"):
        set_setting("varcade.vertical", value)
    else:
        print(f"Invalid varc value: {value}")


def handle_als(value):
    """处理自动加载存档"""
    if value in ("0", "1"):
        set_setting("global.load", value)
        if value == "0":
            del_setting("tips.load")
    else:
        print(f"Invalid als value: {value}")


def handle_aca(value):
    """处理街机核心自动"""
    if value in ("0", "1"):
        set_setting("arcade.auto", value)
    else:
        print(f"Invalid aca value: {value}")


def handle_bezel(value):
    """处理边框设置"""
    if value in ("0", "1", "2"):
        set_setting("global.bezel", value)
    else:
        print(f"Invalid bezel value: {value}")


def handle_ra_com(value):
    """处理 RetroArch 组合键"""
    lr_cfg = Path("/mnt/mod/ctrl/configs/lr.cfg")
    mapping = {
        "0": "5:0",  # R=A+B
        "1": "5:1",  # R=A+Y
        "2": "4:0",  # L=A+B
        "3": "4:1",  # L=A+Y
        "4": ""  # Disable
    }
    if value in mapping:
        if value == "4":
            if lr_cfg.exists():
                lr_cfg.unlink()
        else:
            lr_cfg.write_text(mapping[value])
    else:
        print(f"Invalid ra_com value: {value}")


def handle_ra_turbo(value):
    """处理 RetroArch 连发键"""
    hw_key = 1 if HW_MODEL in ["RG35xxH", "RG40xxH", "RG40xxV", "RGcubexx", "RG34xxSP", "RG35xxPRO"] else 0
    key_map = {
        "0": "0",  # A
        "1": "1",  # B
        "2": "2",  # Y
        "3": "3",  # X
        "4": "4",  # L1
        "5": "5",  # R1
        "6": "10" if hw_key else "9",  # L2
        "7": "11" if hw_key else "10",  # R2
        "8": "9",  # L3
        "9": "12"  # R3
    }
    tk_cfg = Path("/mnt/mod/ctrl/configs/tk.cfg")
    retroarch_cfg = Path("/.config/retroarch/retroarch.cfg")

    if value == "10":  # Disable
        if tk_cfg.exists():
            tk_cfg.unlink()
        # 更新 RetroArch 配置
        try:
            content = retroarch_cfg.read_text()
            content = re.sub(r'input_player1_turbo_btn\s*=\s*".*?"\n', '', content)
            content += 'input_player1_turbo_btn = "nul"\n'
            retroarch_cfg.write_text(content)
        except Exception as e:
            print(f"Error updating retroarch.cfg: {str(e)}")
    elif value in key_map:
        tk_cfg.write_text(key_map[value])
    else:
        print(f"Invalid ra_turbo value: {value}")


def handle_service(service, action, setting_key=None):
    """通用服务处理函数"""
    if action not in ("0", "1", "2"):
        print(f"Invalid action for {service}: {action}")
        return

    if setting_key:
        if action == "0":  # Disable
            set_setting(setting_key, "0")
            run_command(f"systemctl stop {service}")
            run_command(f"systemctl disable {service}")
        elif action == "1":  # Enable
            set_setting(setting_key, "1")
            run_command(f"systemctl enable {service}")
            run_command(f"systemctl start {service}")
        elif action == "2":  # Temporary enable
            set_setting(setting_key, "0")
            run_command(f"systemctl enable {service}")
            run_command(f"systemctl start {service}")


def handle_font(value):
    """处理字体切换"""
    font_map = {
        "0": "default.ttf",
        "1": "big.ttf"
    }
    if value in font_map:
        src = Path(G_DIR) / font_map[value]
        dest = Path("/mnt/vendor/bin/default.ttf")
        if src.exists():
            shutil.copy(src, dest)
        else:
            print(f"Font file not found: {src}")
    else:
        print(f"Invalid font value: {value}")


def handle_led(value):
    """处理 LED 控制"""
    led_file = Path("/sys/class/power_supply/axp2202-battery/work_led")
    boot_cfg = Path(G_DIR) / "led_boot.cfg"
    launch_cfg = Path(G_DIR) / "led_launch.cfg"
    exit_cfg = Path(G_DIR) / "led_exit.cfg"

    try:
        if value == "0":  # OFF
            led_file.write_text("0")
            boot_cfg.write_text("0")
            for cfg in [launch_cfg, exit_cfg]:
                if cfg.exists():
                    cfg.unlink()
        elif value == "1":  # ON
            led_file.write_text("1")
            for cfg in [boot_cfg, launch_cfg, exit_cfg]:
                if cfg.exists():
                    cfg.unlink()
        elif value == "2":  # AUTO
            led_file.write_text("0")
            if boot_cfg.exists():
                boot_cfg.unlink()
            launch_cfg.write_text("0")
            exit_cfg.write_text("1")
    except Exception as e:
        print(f"Error setting LED: {str(e)}")


def handle_power(key, value):
    """处理电源相关设置"""
    valid_values = {"0", "1", "2"}
    if key == "key" and value in valid_values:
        set_setting("power.key", value)
    elif key == "lock" and value in {"0", "1"}:
        set_setting("power.lock", value)
    elif key == "hdmi" and value in {"0", "1"}:
        set_setting("power.hdmi", value)
    else:
        print(f"Invalid power {key} value: {value}")




class Set:
    def __init__(self):
        self.user = ""

    def get_all_menus(self) -> list[str]:
        all_menu = [system["menu"] for system in systems]
        return all_menu

    def get_menu_help(self, menu_name: str):
        for system in systems:
            if system["menu"] == menu_name:
                return system["menu_help"]
        return None

    def get_menu_option(self, menu_name: str) -> list[str]:
        for system in systems:
            if system["menu"] == menu_name:
                return system["options"]
        return []

    def get_opt_help(self, opt_select, menu_name: str) -> list[str]:
        for system in systems:
            if system["menu"] == menu_name:
                help_list = system["opt_help"]
                return help_list[opt_select]
        return []

    def get_menu_operation(self, opt_select, menu_name: str) -> list[str]:
        for system in systems:
            if system["menu"] == menu_name:
                operation_list = system["operations"]
                return operation_list[opt_select]
        return []

    def execute_command(self, command):
        if not command:
            return False, "No valid command!"

        # 命令到处理函数的映射
        command_handlers = {
            "lang": handle_lang,
            "timezone": handle_timezone,
            "ra_hot": handle_ra_hot,
            "rtgg": handle_rtgg,
            "shader": handle_shader,
            "dark": handle_dark,
            "varc": handle_varc,
            "als": handle_als,
            "aca": handle_aca,
            "bezel": handle_bezel,
            "ra_com": handle_ra_com,
            "ra_turbo": handle_ra_turbo,
            "samba": lambda v: handle_service("smbd nmbd", v, "global.samba"),
            "ssh": lambda v: handle_service("ssh.service", v, "global.ssh"),
            "syn": lambda v: handle_service("syncthing@root.service", v, "global.syncthing"),
            "font": handle_font,
            "led": handle_led,
        }

        # 处理带冒号的命令
        if ":" in command:
            prefix, value = command.split(":", 1)

            # 处理 p_ 前缀的特殊命令
            if prefix.startswith("p_"):
                power_type = prefix.split("_", 1)[1] if "_" in prefix else ""
                if power_type:
                    handle_power(power_type, value)
                    return True, ""
                return False, "Invalid power command"

            # 处理其他带冒号的命令
            if prefix in command_handlers:
                command_handlers[prefix](value)
                return True, ""

        # 处理不带冒号的命令
        if command in command_handlers:
            # 获取值（如果有第二个参数）
            value = command.split(":", 1)[1] if ":" in command else ""
            command_handlers[command](value)
            return True, ""

        return False, "No valid command!"
