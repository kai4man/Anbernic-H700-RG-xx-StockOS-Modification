import time
import os
import logging
from graphic import draw_clear, draw_text, draw_paint, screen_width, screen_height
from language import Translator
import input
from main import system_lang
import threading

translator = Translator(system_lang)

log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log.txt')
logging.basicConfig(filename=log_path, level=logging.INFO, format='%(asctime)s %(message)s')

def get_sensors():
    sensor_names = {
        'cpu_thermal_zone': translator.translate('cpu_thermal_zone'),
        'gpu_thermal_zone': translator.translate('gpu_thermal_zone'),
        've_thermal_zone': translator.translate('ve_thermal_zone'),
        'ddr_thermal_zone': translator.translate('ddr_thermal_zone'),
    }
    sensors = []
    for zone in sorted(os.listdir('/sys/class/thermal')):
        zone_path = f'/sys/class/thermal/{zone}'
        temp_path = os.path.join(zone_path, 'temp')
        type_path = os.path.join(zone_path, 'type')
        if os.path.isfile(temp_path) and os.path.isfile(type_path):
            with open(type_path) as f:
                name = f.read().strip()
            if name in ['axp2202-battery']:
                continue
            with open(temp_path) as f:
                temp = int(f.read().strip())
            temp_c_int = temp // 1000
            temp_c_frac = (temp % 1000) // 100
            rus_name = sensor_names.get(name, name)
            line = f"{rus_name}: {temp_c_int}.{temp_c_frac}°C"
            sensors.append(line)
            logging.info(line)
    return sensors

def get_battery_info():
    battery_info = []
    
    try:
        for supply in os.listdir('/sys/class/power_supply'):
            supply_path = f'/sys/class/power_supply/{supply}'
            if os.path.isdir(supply_path):
                type_path = os.path.join(supply_path, 'type')
                if os.path.isfile(type_path):
                    with open(type_path) as f:
                        supply_type = f.read().strip()
                    if supply_type == 'Battery':
                        temp_path = os.path.join(supply_path, 'temp')
                        if os.path.isfile(temp_path):
                            with open(temp_path) as f:
                                temp = int(f.read().strip())
                            temp_c = temp / 10 
                            battery_info.append(f"{translator.translate('battery_temp')}: {temp_c:.1f}°C")
                            logging.info(f"Battery temperature: {temp_c:.1f}°C")
                        
                        capacity_path = os.path.join(supply_path, 'capacity')
                        if os.path.isfile(capacity_path):
                            with open(capacity_path) as f:
                                capacity = f.read().strip()
                            battery_info.append(f"{translator.translate('battery_level')}: {capacity}%")
                            logging.info(f"Battery level: {capacity}%")
                        
                        voltage_path = os.path.join(supply_path, 'voltage_now')
                        if os.path.isfile(voltage_path):
                            with open(voltage_path) as f:
                                voltage = int(f.read().strip())
                            voltage_v = voltage / 1000000
                            battery_info.append(f"{translator.translate('battery_voltage')}: {voltage_v:.2f}V")
                            logging.info(f"Battery voltage: {voltage_v:.2f}V")
                        break
    except Exception as e:
        logging.error(f"Error reading power supply info: {e}")
    
    return battery_info

def start():
    pass

def update():
    draw_clear()
    draw_text((40, 30), translator.translate('Sensors list'), font=17, anchor="lm")
    
    sensors = get_sensors()
    y_offset = 70
    for i, line in enumerate(sensors):
        draw_text((40, y_offset + i * 30), line, font=15, anchor="lm")
    
    battery_info = get_battery_info()
    if battery_info:
        y_offset += len(sensors) * 30 + 20
        draw_text((40, y_offset), translator.translate('Battery info'), font=17, anchor="lm")
        y_offset += 40
        for i, line in enumerate(battery_info):
            draw_text((40, y_offset + i * 30), line, font=15, anchor="lm")

    draw_paint()
    time.sleep(1)

def fn_watcher():
    while True:
        input.check()
        if input.codeName:
            os._exit(0)