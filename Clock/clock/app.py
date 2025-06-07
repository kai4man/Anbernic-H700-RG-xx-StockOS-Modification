from main import hw_info, system_lang
from graphic import screen_resolutions
from language import Translator
import graphic as gr
import input
import sys
from weather import weather
import threading
import datetime
import time
import subprocess
import os

ver = "v1.2"
translator = Translator(system_lang)
skip_input_check = False
current_window = "console"
selected_index = 0

x_size, y_size, max_elem = screen_resolutions.get(hw_info, (640, 480, 11))

button_x = x_size - 120
button_y = y_size - 30
ratio = y_size / x_size

script_dir = os.path.dirname(os.path.abspath(__file__))
clock_sound_file = os.path.join(script_dir, 'sound', 'sound.wav')


def start():
    print("[INFO]Starting Time...")
    gr.draw_log(
        f"{translator.translate('welcome')}", fill=gr.colorBlue, outline=gr.colorBlueD1
    )
    gr.draw_paint()
    time.sleep(2)
    handle_console_input()


def update() -> None:
    global current_window, skip_input_check

    if skip_input_check:
        input.reset_input()
        skip_input_check = False
    else:
        input.check()

    if input.key("MENUF"):
        gr.draw_log(
            f"{translator.translate('Exiting...')}", fill=gr.colorBlue, outline=gr.colorBlueD1
        )
        gr.draw_paint()
        time.sleep(2)
        gr.draw_end()
        print("[INFO]Exiting Time...")
        sys.exit()

    if current_window == "console":
        handle_console_input()
    elif current_window == "CLOCK":
        handle_clock_input()
    elif current_window == "TIMER":
        handle_timer_input()
    elif current_window == "STOPWATCH":
        handle_stopwatch_input()
    else:
        handle_console_input()


def handle_console_input() -> None:
    global current_window, selected_index, skip_input_check

    file_list = ["CLOCK", "TIMER", "STOPWATCH"]

    if input.key("DY"):
        selected_index = (selected_index + input.value) % len(file_list)
    elif input.key("A"):
        current_window = file_list[selected_index]
        skip_input_check = True
        return

    gr.draw_clear()
    gr.draw_rectangle_r([10, 40, x_size - 10, y_size - 40], 15, fill=gr.colorGrayD2, outline=None)
    gr.draw_text((x_size / 2, 20), f"{translator.translate('CLOCK')} {ver}", font=17, anchor="mm")

    if selected_index >= len(file_list):
        selected_index = 0
    start_idx = int(selected_index / max_elem) * max_elem
    end_idx = start_idx + max_elem

    for i, entry in enumerate(file_list[start_idx:end_idx]):
        row_list(
            f"{translator.translate(entry)}",
            (20, 50 + (i * 35)),
            x_size - 40,
            i == (selected_index % max_elem),
        )

    button_circle((30, button_y), "A", f"{translator.translate('Open')}")
    button_circle((button_x, button_y), "M", f"{translator.translate('Exit')}")

    gr.draw_paint()


def handle_clock_input() -> None:
    global current_window, skip_input_check

    x_pos = x_size // 2
    y_pos = y_size // 2
    time_text_width = gr.get_text_width("00:00:00", font=100)
    x_time_pos = (x_size - time_text_width) // 2
    
    input.reset_input()
    thread = threading.Thread(target=input.check)
    thread.start()
    
    weather_font = 18 if hw_info in [2,3] else 20
    info_spacing = 28
    
    while True:
        now = datetime.datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M:%S")
        weather_data, city = weather.get_weather()
        gr.draw_clear()
        gr.draw_text((x_pos, y_pos - 80), current_date, clock=1, font=40, color=gr.colorGreen, anchor="mm")
        gr.draw_text((x_time_pos, y_pos), current_time, clock=1, font=100, color=gr.colorGreen, anchor="lm")
        
        weather_x = 20
        weather_y = 50
        if weather_data:
            cond_info = weather_data['condition']
            info_lines1 = [
                f"{translator.translate('TEMP')}: {weather_data['temp']}",
                f"{translator.translate('HUMIDITY')}: {weather_data['humidity']}%",
                f"{translator.translate('CONDITION')}: {translator.translate(cond_info)}"
            ]
            info_lines2 = f"({city} @ {weather_data['updated']})"
        else:
            info_lines1 = [translator.translate("FETCHING")]
            info_lines2 = translator.translate("Unknown")
        
        for idx, line in enumerate(info_lines1):
            color = gr.colorYellow if idx < 3 else gr.colorGrayL2
            gr.draw_text(
                (weather_x, weather_y + idx*info_spacing),
                line,
                font=weather_font,
                color=color,
                anchor="lm"
            )
        gr.draw_text(
                (weather_x, weather_y + idx*info_spacing + info_spacing),
                info_lines2,
                font=weather_font,
                color=gr.colorGrayL2,
                anchor="lm"
            )
        gr.draw_paint()
        
        if input.slide_key():
            current_window = "console"
            skip_input_check = True
            gr.draw_clear()
            return


def handle_timer_input() -> None:
    global current_window, skip_input_check

    x_pos = x_size // 2
    y_pos = y_size // 2

    timer_duration = 0
    hours = 0
    minutes = 0
    seconds = 0
    end_time = "Sound"
    setting_index = 0
    set_list= ["Seconds", "Minutes", "Hours", "At the end"]
    current_set = set_list[setting_index]
    start_time = None
    countdown_finished = False
    gr.draw_clear()
    gr.draw_text((x_pos, y_pos - 100), f"{translator.translate('Set')}: {translator.translate(current_set)}", font=30, anchor="mm")
    gr.draw_text((x_pos, y_pos - 25), f"{hours:02d}:{minutes:02d}:{seconds:02d}", font=60, anchor="mm")
    gr.draw_text((x_pos, y_pos + 50), f"{translator.translate('At the end')}: {translator.translate(end_time)}", font=30, anchor="mm")
    gr.draw_text((x_pos, y_pos + 100), f"{translator.translate('Press DY to adjust, DX to switch setting')}", font=15, anchor="mm")
    gr.draw_text((x_pos, y_pos + 150), f"{translator.translate('Press START to start, M/F to Exit')}", font=15, anchor="mm")
    gr.draw_paint()
    
    while start_time is None:
        input.check()
        if input.key("DY"):
            if setting_index == 3:
                if end_time == "Sound":
                    end_time = "Vibrate"
                else:
                    end_time = "Sound"
            elif setting_index == 2:
                if input.value == -1:
                    hours = min(99, hours - input.value)
                elif input.value == 1:
                    hours = max(0, hours - 1)
                    if hours == 0 and minutes > 0:
                        minutes = 59
                        seconds = 59
            elif setting_index == 1:
                if input.value == -1:
                    minutes = (minutes - input.value) % 60
                    if minutes == 0:
                        hours = min(99, hours + 1)
                elif input.value == 1:
                    if minutes > 0:
                        minutes = max(0, minutes - 1)
                    elif hours > 0:
                        hours -= 1
                        minutes = 59
                        seconds = 59
            elif setting_index == 0:
                if input.value == -1:
                    seconds = (seconds - input.value) % 60
                    if seconds == 0:
                        minutes = (minutes + 1) % 60
                        if minutes == 0:
                            hours = min(99, hours + 1)
                elif input.value == 1:
                    if seconds > 0:
                        seconds = max(0, seconds - 1)
                    elif minutes > 0:
                        minutes -= 1
                        seconds = 59
                    elif hours > 0:
                        hours -= 1
                        minutes = 59
                        seconds = 59
        elif input.key("DX"):
            setting_index = (setting_index - input.value) % 4
            current_set = set_list[setting_index]
        elif input.key("START"):
            timer_duration = hours * 3600 + minutes * 60 + seconds + 1
            if timer_duration > 1:
                start_time = time.time()
        elif input.key("MENUF"):
            current_window = "console"
            skip_input_check = True
            gr.draw_clear()
            return

        gr.draw_clear()
        gr.draw_text((x_pos, y_pos - 100), f"{translator.translate('Set')}: {translator.translate(current_set)}", font=30, anchor="mm")
        gr.draw_text((x_pos, y_pos - 25), f"{hours:02d}:{minutes:02d}:{seconds:02d}", font=60, anchor="mm")
        gr.draw_text((x_pos, y_pos + 50), f"{translator.translate('At the end')}: {translator.translate(end_time)}", font=30, anchor="mm")
        gr.draw_text((x_pos, y_pos + 100), f"{translator.translate('Press DY to adjust, DX to switch setting')}", font=15, anchor="mm")
        gr.draw_text((x_pos, y_pos + 150), f"{translator.translate('Press START to start, M/F to Exit')}", font=15, anchor="mm")
        gr.draw_paint()

    time_text_width = gr.get_text_width("00:00:00", font=100)
    x_time_pos = (x_size - time_text_width) // 2

    input.reset_input()
    thread = threading.Thread(target=input.check)
    thread.start()

    while True:
        elapsed_time = time.time() - start_time
        remaining_time = max(0, timer_duration - elapsed_time)
        if remaining_time > 0:
            remaining_minutes = int(remaining_time // 60)
            remaining_seconds = int(remaining_time % 60)
            remaining_hours = int(remaining_minutes // 60)
            remaining_minutes = remaining_minutes % 60
            time_str = f"{remaining_hours:02d}:{remaining_minutes:02d}:{remaining_seconds:02d}"
        
            gr.draw_clear()
            gr.draw_text((x_pos, y_pos-100), f"{translator.translate('TIMER')}", font=30, anchor="mm")
            gr.draw_text((x_time_pos, y_pos), time_str, clock=1, font=100, color=gr.colorBlue, anchor="lm")
            gr.draw_paint()
        
        if remaining_time == 0 and not countdown_finished:
            countdown_finished = True
            gr.draw_text((x_pos, y_pos+100), f"{translator.translate('Timer finished!')}", font=30, anchor="mm")
            gr.draw_paint()
        elif input.slide_key():
            current_window = "console"
            skip_input_check = True
            gr.draw_clear()
            return
        elif countdown_finished:
            try:
                if end_time == "Vibrate":
                    subprocess.run("echo 1 > /sys/class/power_supply/axp2202-battery/moto && sleep 0.3 && echo 0 > /sys/class/power_supply/axp2202-battery/moto && sleep 0.1", shell=True, check=True)
                else:
                    subprocess.run(["aplay", clock_sound_file], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error: {e}")


def handle_stopwatch_input() -> None:
    global current_window, skip_input_check

    x_pos = x_size // 2
    y_pos = y_size // 2
    time_text_width = gr.get_text_width("00:00:00", font=100)
    time_text_width2 = gr.get_text_width(".00", font=50)
    x_time_pos = (x_size - time_text_width) // 2

    start_time = None
    elapsed_time = 0
    running = False
    
    input.reset_input()
    thread = threading.Thread(target=input.check)
    thread.start()

    while True:

        if input.key("START"):
            if running:
                elapsed_time += time.time() - start_time
                running = False
                input.reset_input()
                thread = threading.Thread(target=input.check)
                thread.start()

            else:
                start_time = time.time()
                running = True
                input.reset_input()
                thread = threading.Thread(target=input.check)
                thread.start()

        elif input.key("SELECT"):
            elapsed_time = 0
            start_time = None
            running = False
            input.reset_input()
            thread = threading.Thread(target=input.check)
            thread.start()

        elif input.key("MENUF"):
            if running:
                elapsed_time += time.time() - start_time
                running = False
                input.reset_input()
                thread = threading.Thread(target=input.check)
                thread.start()
            else:
                current_window = "console"
                skip_input_check = True
                gr.draw_clear()
                return

        elif input.slide_key():
            input.reset_input()
            thread = threading.Thread(target=input.check)
            thread.start()

        if running:
            total_elapsed = elapsed_time + (time.time() - start_time)
        else:
            total_elapsed = elapsed_time

        hours = int(total_elapsed // 3600)
        minutes = int((total_elapsed % 3600) // 60)
        seconds = int(total_elapsed % 60)
        milliseconds = int((total_elapsed - int(total_elapsed)) * 100)
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        gr.draw_clear()
        gr.draw_text((x_pos, y_pos - 150), f"{translator.translate('STOPWATCH')}", font=30, anchor="mm")
        gr.draw_text((x_time_pos, y_pos-50), time_str, clock=1, font=100, color=gr.colorRed, anchor="lm")
        gr.draw_text((x_time_pos+time_text_width - time_text_width2, y_pos+50), f"{milliseconds:02d}", clock=1, font=50, color=gr.colorRed, anchor="lm")

        gr.draw_text((x_pos, y_pos + 100), f"{translator.translate('Press START to start/stop, SELECT to reset')}", font=15, anchor="mm")
        gr.draw_text((x_pos, y_pos + 150), f"{translator.translate('Press M/F to Exit')}", font=15, anchor="mm")

        gr.draw_paint()


def button_circle(pos: tuple[int, int], button: str, text: str, color=gr.colorBlueD1) -> None:
    gr.draw_circle(pos, 25, fill=color)
    gr.draw_text((pos[0] + 12, pos[1] + 12), button, anchor="mm")
    gr.draw_text((pos[0] + 30, pos[1] + 12), text, font=13, anchor="lm")


def button_rectangle(pos: tuple[int, int], button: str, text: str) -> None:
    gr.draw_rectangle_r(
        (pos[0], pos[1], pos[0] + 60, pos[1] + 25), 5, fill=gr.colorGrayL1
    )
    gr.draw_text((pos[0] + 30, pos[1] + 12), button, anchor="mm")
    gr.draw_text((pos[0] + 65, pos[1] + 12), text, font=13, anchor="lm")


def row_list(text: str, pos: tuple[int, int], width: int, selected: bool) -> None:
    gr.draw_rectangle_r(
        [pos[0], pos[1], pos[0] + width, pos[1] + 32],
        5,
        fill=(gr.colorBlue if selected else gr.colorGrayL1),
    )
    gr.draw_text((pos[0] + 5, pos[1] + 5), text)
