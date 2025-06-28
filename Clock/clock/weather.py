import urllib.request
import json
import time
import threading
from datetime import datetime
from main import lang
import urllib.parse

class WeatherManager:
    def __init__(self):
        self.cache = {'time': 0, 'data': None, 'city': 'New York'}
        self.lock = threading.Lock()
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        self._trigger_update()

    def _trigger_update(self):
        self._do_update()

    def _get_location(self):
        try:
            with urllib.request.urlopen("http://ip-api.com/json/?fields=status,city", timeout=3) as res:
                if res.status == 200:
                    data = json.loads(res.read().decode())
                    if data.get('status') == 'success':
                        return data['city']
        except Exception as e:
            print(f"[Weather] Location error: {str(e)}")
        return None

    def _get_weather(self, city):
        try:
            encoded_city = urllib.parse.quote(city)
            url = f"https://wttr.in/{encoded_city}?format=%t+%h+%C&lang={lang}"
            with urllib.request.urlopen(url, timeout=5) as res:
                if res.status == 200:
                    data = res.read().decode().strip().split(' ', 2)
                    if len(data) == 3:
                        temp, humidity, condition = data
                        return {
                            'temp': temp,
                            'humidity': humidity.rstrip('%'),
                            'condition': condition,
                            'updated': datetime.now().isoformat(timespec='minutes')
                        }
        except Exception as e:
            print(f"[Weather] API error: {str(e)}")
        return None

    def _do_update(self):
        try:
            city = self._get_location() or self.cache['city']
            weather_data = self._get_weather(city)
            
            with self.lock:
                if weather_data:
                    self.cache = {
                        'time': time.time(),
                        'data': weather_data,
                        'city': city
                    }
        except Exception as e:
            print(f"[Weather] Update error: {str(e)}")

    def _trigger_update(self):
        self._do_update()

    def _update_loop(self):
        while self.running:
            try:
                city = self._get_location() or self.cache['city']
                weather_data = self._get_weather(city)
                
                with self.lock:
                    if weather_data:
                        self.cache = {
                            'time': time.time(),
                            'data': weather_data,
                            'city': city
                        }
            except Exception as e:
                print(f"[Weather] Update error: {str(e)}")
            time.sleep(300)  # 5分钟更新一次

    def get_weather(self):
        with self.lock:
            return self.cache['data'], self.cache['city']
    
    def stop(self):
        self.running = False
        self.update_thread.join(timeout=1.0)

weather = WeatherManager()