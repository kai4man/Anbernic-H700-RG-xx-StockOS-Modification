import time
import os
import logging
from graphic import draw_clear, draw_text, draw_paint, screen_width, screen_height
from language import Translator
import input
from main import system_lang

translator = Translator(system_lang)

log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log.txt')
logging.basicConfig(filename=log_path, level=logging.INFO, format='%(asctime)s %(message)s')

def get_sensors():
    sensor_names = {
        'cpu_thermal_zone': translator.translate('cpu_thermal_zone'),
        'gpu_thermal_zone': translator.translate('gpu_thermal_zone'),
        've_thermal_zone': translator.translate('ve_thermal_zone'),
        'ddr_thermal_zone': translator.translate('ddr_thermal_zone'),
        'axp2202-battery': translator.translate('axp2202-battery'),
    }
    sensors = []
    for zone in sorted(os.listdir('/sys/class/thermal')):
        zone_path = f'/sys/class/thermal/{zone}'
        temp_path = os.path.join(zone_path, 'temp')
        type_path = os.path.join(zone_path, 'type')
        if os.path.isfile(temp_path) and os.path.isfile(type_path):
            with open(type_path) as f:
                name = f.read().strip()
            with open(temp_path) as f:
                temp = int(f.read().strip())
            temp_c_int = temp // 1000
            temp_c_frac = (temp % 1000) // 100
            rus_name = sensor_names.get(name, name)
            line = f"{rus_name}: {temp_c_int}.{temp_c_frac}°C"
            sensors.append(line)
            logging.info(line)
    return sensors

def start():
    pass

def update():
    draw_clear()
    draw_text((40, 30), translator.translate('Sensors list'), font=17, anchor="lm")
    sensors = get_sensors()
    for i, line in enumerate(sensors):
        draw_text((40, 70 + i * 30), line, font=15, anchor="lm")
    draw_paint()
    time.sleep(1)
    input.check()
    if input.codeName:
        exit(0) 