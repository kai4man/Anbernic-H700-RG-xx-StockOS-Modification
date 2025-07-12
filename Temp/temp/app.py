import time
import os
import logging
from graphic import draw_clear, draw_text, draw_paint, screen_width, screen_height, draw_line, draw_rectangle_r, draw_rectangle
from language import Translator
import input
from main import system_lang, hw_info


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
    
    draw_background_grid()
    y_base = 0
    if hw_info == 1:
        y_base = 120
    draw_rectangle_r([10, 30 + y_base, screen_width-10, 80 + y_base], 8, fill="#0a0a1a", outline="#7f4f00")
    draw_text((screen_width//2, 55 + y_base), translator.translate('System Monitor'), font=17, anchor="mm", color="#00ffff")
    
    draw_rectangle_r([20, 90 + y_base, screen_width-20, 270 + y_base], 10, fill="#0a0a1a", outline="#7f4f00")
    draw_text((40, 110 + y_base), translator.translate('Sensors list'), font=16, anchor="lm", color="#00ffff")
    
    sensors = get_sensors()
    y_offset = 140 + y_base
    for i, line in enumerate(sensors):
        draw_text((40, y_offset + i*30), line, font=15, anchor="lm", color="#ffffff")
    
    battery_info = get_battery_info()
    if battery_info:
        bat_height = 40 + len(battery_info)*30
        draw_rectangle_r([20, 290 + y_base, screen_width-20, 310 + bat_height + y_base], 10, fill="#0a0a1a", outline="#7f4f00")
        draw_text((40, 310 + y_base), translator.translate('Battery info'), font=16, anchor="lm", color="#00ffff")
        
        y_offset = 340 + y_base
        for i, line in enumerate(battery_info):
            draw_text((40, y_offset + i*30), line, font=15, anchor="lm", color="#ffffff")
    
    draw_rectangle([0, 0, screen_width, 15], fill="#7f4f00")
    draw_rectangle([0, screen_height-15, screen_width, screen_height], fill="#7f4f00")
    
    draw_paint()
    time.sleep(1)

def draw_background_grid():
    for x in range(0, screen_width, 40):
        draw_line([x - 1, 0, x - 1, screen_height], fill="#bb7200", width=1)
    
    for y in range(0, screen_height, 40):
        draw_line([0, y, screen_width, y], fill="#bb7200", width=1)

def fn_watcher():
    while True:
        input.check()
        if input.codeName:
            os._exit(0)