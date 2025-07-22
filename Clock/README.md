# Clock Program User Manual

## 1. Introduction
The Clock program is a multi - functional time - management application that offers clock, timer, and stopwatch features, along with real - time weather information. This manual provides detailed instructions on how to use the program effectively.

## 2. Prerequisites
- The program is designed to run on specific hardware platforms such as RGcubexx, RG34xx, etc.
- A stable network connection is required to fetch weather information.

## 3. Installation
There is no specific installation process mentioned in the provided code. It is assumed that the program is pre - installed on the target device.

## 4. Starting the Program
The program can be started by running the `main.py` file. When the program starts, it will display a welcome message and then enter the console window.

```bash
python main.py
```

## 5. Program Interface and Functionality

### 5.1 Console Window
- **Navigation**:
    - Use the `DY` key (up/down) to select different functions. There are three available functions: `Clock`, `Timer`, and `Stopwatch`.
    - Press the `A` key to open the selected function.
    - Press the `MENUF` key to exit the program.
- **Visual Elements**:
    - The window shows a title bar with the program name and version.
    - A list of available functions is displayed, and the currently selected function is highlighted.
    - Two buttons are provided: one for opening the selected function and one for exiting the program.

### 5.2 Clock Window
- **Display**:
    - The current date and time are displayed prominently in the center of the screen.
    - Real - time weather information is also shown, including temperature, humidity, weather condition, and the city name.
- **Navigation**:
    - Slide any key to return to the console window.

### 5.3 Timer Window
#### 5.3.1 Setting the Timer
- **Adjusting Time**:
    - Use the `DY` key (up/down) to adjust the hours, minutes, and seconds of the timer.
    - Use the `DX` key (left/right) to switch between setting hours, minutes, seconds, and the end - action.
- **Selecting End - Action**:
    - The end - action can be either `Sound` or `Vibrate`. Press the `DY` key when the end - action setting is selected to toggle between the two options.
- **Starting the Timer**:
    - Press the `START` key to start the timer if the set duration is greater than 1 second.
- **Exiting the Timer Setup**:
    - Press the `MENUF` key to return to the console window.

#### 5.3.2 Running the Timer
- **Display**:
    - The remaining time of the timer is displayed in the center of the screen.
- **Navigation**:
    - There is no specific navigation option during the timer countdown. Once the timer finishes, appropriate actions (sound or vibration) will be triggered according to the setting.


## 6. Language Support
The program supports multiple languages, including English (`en_US`), Chinese (`zh_CN`, `zh_TW`), Japanese (`ja_JP`), Korean (`ko_KR`), Spanish (`es_LA`), Russian (`ru_RU`), German (`de_DE`), French (`fr_FR`), and Portuguese (`pt_BR`). The language is automatically detected based on the system settings.

## 7. Troubleshooting
- **Weather Information Not Loading**:
    - Check your network connection.
    - Ensure that the IP - API and wttr.in services are accessible from your location.
- **Program Freezing or Crashing**:
    - Try restarting the program.
    - If the problem persists, check the system log for error messages.