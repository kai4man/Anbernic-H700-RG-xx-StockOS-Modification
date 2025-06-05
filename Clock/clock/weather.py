import urllib.request
import json
import time
import threading
from datetime import datetime

class WeatherManager:
    def __init__(self):
        self.cache = {'time': 0, 'data': None, 'city': 'Unknown'}
        self.lock = threading.Lock()
        self.running = True
        threading.Thread(target=self._update_loop, daemon=True).start()

    def _get_location(self):
        try:
            with urllib.request.urlopen('http://ip-api.com/json/?fields=status,city', timeout=3) as res:
                if res.status == 200:
                    data = json.loads(res.read().decode())
                    if data.get('status') == 'success':
                        return data['city']
        except Exception as e:
            print(f"[Weather] Location error: {str(e)}")
        return None

    def _get_weather(self, city):
        try:
            url = f'http://wttr.in/{city}?format=%t+%h+%C'
            with urllib.request.urlopen(url, timeout=5) as res:
                if res.status == 200:
                    data = res.read().decode().strip().split(' ')
                    if len(data) == 3:
                        temp, humidity, condition = data
                        return {
                            'temp': temp,
                            'humidity': humidity.rstrip('%'),
                            'condition': condition,
                            'updated': datetime.now().strftime("%H:%M")
                        }
        except Exception as e:
            print(f"[Weather] API error: {str(e)}")
        return None

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

weather = WeatherManager()
