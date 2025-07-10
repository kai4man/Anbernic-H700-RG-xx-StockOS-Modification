import os
import traceback
import time
import sys
import socket
from graphic import *
from PIL import Image
from config import PADDING, PADDING_TOP, PADDING_BOTTOM, BORDER_RADIUS, BORDER_WIDTH, LIST_WIDTH_RATIO, BUTTONS_GAP, BOTTOM_PANEL_HEIGHT, JAVA_CMD, EMULATOR_JAR, FONT_PATH, GAME_DIRS
from input import check, key, reset_input
import urllib.request
import zipfile
import shutil
from language import Translator
from main import hw_info, system_lang

translator = Translator(system_lang)

selected = 0
menu_games = []

scroll_offset = 0

def log_event(message):
    with open("debug.log", "a") as f:
        f.write(message + "\n")

def find_games():
    games = []
    for dir in GAME_DIRS:
        for root, _, files in os.walk(dir):
            for file in files:
                if file.endswith(".jar"):
                    games.append(os.path.join(root, file))
    return games

def get_text_width(text, font):
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0]

def crop_text_to_width(text, max_width, font):
    for i in range(len(text), 0, -1):
        if get_text_width(text[:i] + '…', font) <= max_width:
            return text[:i] + '…'
    return text

def scroll_text(text, font, offset, max_width):
    width = get_text_width(text, font)
    if width <= max_width:
        return text
    acc = 0
    start = 0
    for i, ch in enumerate(text):
        w = get_text_width(text[i], font)
        if acc + w > offset:
            start = i
            break
        acc += w
    sub = text[start:]
    acc2 = 0
    end = 0
    for j, ch in enumerate(sub):
        w = get_text_width(sub[:j+1], font)
        if w > max_width:
            break
        end = j+1
    return sub[:end]

def draw_menu():
    global menu_games, selected, scroll_offset
    draw_clear()
    screen_w, screen_h = screen_width, screen_height
    list_w = int(screen_w * LIST_WIDTH_RATIO)
    preview_x = list_w + 10
    preview_w = screen_w - preview_x - 10
    padding = PADDING
    padding_top = PADDING_TOP
    padding_bottom = PADDING_BOTTOM

    font_height = fontFile[15].size
    line_height = font_height + padding_top + padding_bottom
    total_line = line_height
    EXTRA_BOTTOM_GAP = padding
    max_visible = (screen_h - 2 * padding - BOTTOM_PANEL_HEIGHT - EXTRA_BOTTOM_GAP) // total_line
    if selected < scroll_offset:
        scroll_offset = selected
    elif selected >= scroll_offset + max_visible:
        scroll_offset = selected - max_visible + 1

    for idx in range(scroll_offset, min(len(menu_games), scroll_offset + max_visible)):
        y = padding + 10 + (idx - scroll_offset) * total_line
        color = "white"
        name = os.path.basename(menu_games[idx])
        max_name_w = list_w - 2 * padding - 20
        text_x = padding + 16
        text_y = y + padding_top
        if idx == selected:
            draw_rectangle_r([padding, y, list_w - padding, y + line_height], BORDER_RADIUS, outline=colorBlue, fill=None, width=BORDER_WIDTH)
            if get_text_width(name, fontFile[15]) > max_name_w:
                display_name = crop_text_to_width(name, max_name_w, fontFile[15])
            else:
                display_name = name
        else:
            if get_text_width(name, fontFile[15]) > max_name_w:
                display_name = crop_text_to_width(name, max_name_w, fontFile[15])
            else:
                display_name = name
        draw_text((text_x, text_y), display_name, font=15, color=color)

    game_path = menu_games[selected]
    game_dir = os.path.dirname(game_path)
    game_name = os.path.splitext(os.path.basename(game_path))[0]
    img_dir = os.path.join(game_dir, "Imgs")
    img_path_jpg = os.path.join(img_dir, game_name + ".jpg")
    img_path_png = os.path.join(img_dir, game_name + ".png")
    img_path = img_path_jpg if os.path.exists(img_path_jpg) else (img_path_png if os.path.exists(img_path_png) else None)

    if img_path:
        try:
            img = Image.open(img_path).convert("RGBA")
            w, h = img.size
            scale = (preview_w - 2*padding) / w
            new_w = preview_w - 2*padding
            new_h = int(h * scale)
            if new_h > screen_h - 2*padding:
                new_h = screen_h - 2*padding
                new_w = int(w * (new_h / h))
            img = img.resize((int(new_w), int(new_h)), Image.LANCZOS)
            pos_x = preview_x + (preview_w - int(new_w)) // 2
            pos_y = padding + (screen_h - int(new_h)) // 2 
            pos_x = max(pos_x, preview_x + padding)
            pos_y = max(pos_y, padding)
            activeImage.paste(img, (pos_x, pos_y), img)
        except Exception:
            pass

    hint_y = screen_h - BOTTOM_PANEL_HEIGHT
    x_a = 20
    x_b = x_a + BUTTONS_GAP
    button_circle((x_a, hint_y), "A", f"{translator.translate('Select')}")
    button_circle((x_b, hint_y), "B", f"{translator.translate('Exit')}")

    draw_paint()

def update():
    global selected, menu_games
    check()
    if key("DY", 1):
        selected = (selected + 1) % len(menu_games)
        reset_input()
        draw_menu()
    elif key("DY", -1):
        selected = (selected - 1) % len(menu_games)
        reset_input()
        draw_menu()
    elif key("A"):
        log_event(f"A pressed! Запуск через launch.sh: {menu_games[selected]}")
        try:
            run_game(menu_games[selected])
        except Exception as e:
            log_event(f"Ошибка запуска: {e}")
            log_event(traceback.format_exc())
        reset_input()
    elif key("B"):
        os._exit(0)

def is_connected():
    test_servers = [
        ("8.8.8.8", 53),  # google
        ("1.1.1.1", 53),       # NTP DNS
        ("223.5.5.5", 53),       # ali DNS
        ("220.181.38.148", 80)   # baidu
    ]
    for host, port in test_servers:
        try:
            sock = socket.create_connection((host, port), timeout=3)
            sock.close()
            return True
        except (socket.timeout, socket.error):
            continue
    return False

def exit_program(error_message: str = "", time_sleep: int = 0) -> None:
    if error_message:
        draw_log(
            error_message, fill=colorBlue, outline=colorBlueD1
        )
    draw_paint()
    time.sleep(time_sleep)
    sys.exit(1)

def run_game(game_path):

    if not os.path.exists(JAVA_CMD):
        if not is_connected():
            exit_program(f"{translator.translate('No internet connection')}", 3)
        else:
            exit_program(f"{translator.translate('JAVA not found. Requires loading')}", 3)

    JAVA_BIN = JAVA_CMD
    EMULATOR = EMULATOR_JAR

    if "240x320" in game_path:
        res = ["240", "320", "30"]
    elif "320x240" in game_path:
        res = ["320", "240", "30"]
    elif "128x128" in game_path:
        res = ["128", "128", "30"]
    elif "176x208" in game_path:
        res = ["176", "208", "30"]
    elif "640x360" in game_path:
        res = ["640", "360", "30"]
    else:
        res = ["240", "320", "30"]

    env = os.environ.copy()
    env['JAVA_HOME'] = os.path.dirname(os.path.dirname(JAVA_CMD))
    env['PATH'] = f"{env['JAVA_HOME']}/bin:" + env.get('PATH', '')
    env['CLASSPATH'] = f"{env['JAVA_HOME']}/lib:" + env.get('CLASSPATH', '')
    env['LD_LIBRARY_PATH'] = f"{env['JAVA_HOME']}/lib:" + env.get('LD_LIBRARY_PATH', '')
    env['JAVA_TOOL_OPTIONS'] = "-Xverify:none -Djava.util.prefs.systemRoot=./.java -Djava.util.prefs.userRoot=./.java/.userPrefs -Djava.awt.headless=true -Dsun.jnu.encoding=UTF-8 -Dfile.encoding=UTF-8 -Djava.library.path=/mnt/mmc/Emu/JAVA/jdk/lib"
    env['TIMIDITY_CFG'] = "/mnt/mmc/Emu/JAVA/jdk/bin/timidity/timidity.cfg"

    os.makedirs('./.java/.systemPrefs', exist_ok=True)
    os.makedirs('./.java/.userPrefs', exist_ok=True)
    os.chmod('./.java', 0o755)

    os.chdir(os.path.dirname(EMULATOR))

    os.execvpe(
        JAVA_BIN,
        [JAVA_BIN, "-jar", EMULATOR, game_path] + res,
        env
    )

def show_download_progress(block_num, block_size, total_size):
    try:
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(100, downloaded * 100 / total_size)
        else:
            percent = 0
        
        draw_clear()
        draw_text((screen_width // 2, screen_height // 2 - 30), f"{translator.translate('Downloading JAVA')}", font=17, anchor="mm")
        bar_width = screen_width - 100
        draw_rectangle([50, screen_height // 2, 50 + bar_width, screen_height // 2 + 20], fill=colorGrayL1)
        filled_width = int(bar_width * percent / 100)
        if filled_width > 0:
            draw_rectangle([50, screen_height // 2, 50 + filled_width, screen_height // 2 + 20], fill=colorBlue)
        draw_text((screen_width // 2, screen_height // 2 + 30), f"{int(percent)}%", font=13, anchor="mm")
        draw_paint()
    except Exception as e:
        pass

def download_and_extract_java():
    JAVA_ZIP_URL = "https://github.com/kai4man/Anbernic-H700-RG-xx-StockOS-Modification-JAVA/archive/refs/heads/main.zip"
    TEMP_FILE = "/mnt/mmc/java_download.zip"
    EXTRACT_PATH = "/mnt/mmc/"
    MAIN_DIR = "/mnt/mmc/Anbernic-H700-RG-xx-StockOS-Modification-JAVA-main"
    EMU_SRC = os.path.join(MAIN_DIR, "Emu")
    EMU_DST = "/mnt/mmc/Emu"

    try:
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)

        if os.path.exists(TEMP_FILE):
            os.remove(TEMP_FILE)
        if os.path.exists(MAIN_DIR):
            shutil.rmtree(MAIN_DIR)

        draw_clear()
        draw_text((screen_width // 2, screen_height // 2 - 30), f"{translator.translate('Downloading JAVA')}", font=17, anchor="mm")
        draw_paint()
        time.sleep(0.05)
        socket.setdefaulttimeout(30)
        urllib.request.urlretrieve(JAVA_ZIP_URL, TEMP_FILE, show_download_progress)

        draw_clear()
        draw_text((screen_width // 2, screen_height // 2 - 30), f"{translator.translate('Unpacking JAVA')}", font=17, anchor="mm")
        draw_paint()
        with zipfile.ZipFile(TEMP_FILE, 'r') as zip_ref:
            files = zip_ref.namelist()
            total_files = len(files)
            for i, file in enumerate(files):
                zip_ref.extract(file, EXTRACT_PATH)
                percent = (i + 1) * 100 / total_files
                draw_clear()
                draw_text((screen_width // 2, screen_height // 2 - 30), f"{translator.translate('Unpacking JAVA')}", font=17, anchor="mm")
                bar_width = screen_width - 100
                draw_rectangle([50, screen_height // 2, 50 + bar_width, screen_height // 2 + 20], fill=colorGrayL1)
                filled_width = int(bar_width * percent / 100)
                if filled_width > 0:
                    draw_rectangle([50, screen_height // 2, 50 + filled_width, screen_height // 2 + 20], fill=colorBlue)
                draw_text((screen_width // 2, screen_height // 2 + 30), f"{int(percent)}%", font=13, anchor="mm")
                draw_paint()

        if os.path.exists(EMU_SRC):
            if os.path.exists(EMU_DST):
                shutil.rmtree(EMU_DST)
            shutil.move(EMU_SRC, EMU_DST)

        if os.path.exists(MAIN_DIR):
            shutil.rmtree(MAIN_DIR)
        if os.path.exists(TEMP_FILE):
            os.remove(TEMP_FILE)
        draw_clear()
        draw_text((screen_width // 2, screen_height // 2), f"{translator.translate('JAVA is installed')}", font=17, anchor="mm")
        draw_paint()
        time.sleep(2)
    except Exception as e:
        exit_program(f"{translator.translate('JAVA download or unpacking error')}: {e}", 3)

def create_java_directories():
    directories = [
        "/mnt/mmc/Roms/JAVA",
        "/mnt/mmc/Roms/JAVA/240x320", 
        "/mnt/mmc/Roms/JAVA/320x240"
    ]
    
    if os.path.exists("/mnt/sdcard"):
        sdcard_dirs = [
            "/mnt/sdcard/Roms/JAVA",
            "/mnt/sdcard/Roms/JAVA/240x320",
            "/mnt/sdcard/Roms/JAVA/320x240"
        ]
        directories.extend(sdcard_dirs)
    
    for directory in directories:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
                log_event(f"Создана папка: {directory}")
            except Exception as e:
                log_event(f"Ошибка создания папки {directory}: {e}")

def start():
    if not os.path.exists(JAVA_CMD):
        if not is_connected():
            exit_program(f"{translator.translate('No internet connection')}", 3)
        else:
            download_and_extract_java()
    
    create_java_directories()
    
    global menu_games, selected
    menu_games = sorted(find_games(), key=lambda x: os.path.basename(x).lower())
    selected = 0
    draw_menu()
    log_event("Меню запущено. Найдено игр: {}".format(len(menu_games))) 