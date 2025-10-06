# Java Game Launcher for Anbernic Devices

## Overview
This application is a Java game launcher designed for Anbernic handheld gaming devices. It provides a graphical interface to browse and launch Java games (.jar files) stored on your device. The launcher supports multiple languages and automatically handles Java environment setup.

## Key Features
- Game browser with preview images
- Automatic Java environment installation
- Multi-language support (English, Chinese, Japanese, etc.)
- A user-friendly interface specifically designed for small screens
- Support for multiple screen resolutions
- Game directory auto-creation

## System Requirements
- Anbernic RGxx series device (RG35xx, RG40xx, etc.)
- Stock OS firmware
- Internet connection (for initial Java setup)

## Installation
1. Place the following files in your device's `/mnt/mmc/Roms/APPS/` directory:
   - `Java.sh`
   - `java/app.py`
   - `java/config.py`
   - `java/graphic.py`
   - `java/input.py`
   - `java/language.py`
   - `java/main.py`
   - `java/lang/` directory with translation files

2. Create game directories (will be auto-created on first run if missing):
   ```
   /mnt/mmc/Roms/JAVA/240x320
   /mnt/mmc/Roms/JAVA/320x240
   /mnt/sdcard/Roms/JAVA/240x320 (if SD card present)
   /mnt/sdcard/Roms/JAVA/320x240 (if SD card present)
   ```

## Usage Instructions

### Starting the Application
- Execute `Java` to launch the program

### Interface Navigation
- **UP/DOWN buttons**: Scroll through game list
- **A button**: Launch selected game
- **B button**: Exit application

### Adding Games
1. Place `.jar` game files in the appropriate resolution folder:
   - `240x320` for portrait games
   - `320x240` for landscape games
2. Optional: Add preview images in `Imgs/` folder (same name as .jar file with .jpg/.png extension)

### First-Time Setup
1. On first run, the application will:
   - Check for Java installation
   - Download and install Java if missing (requires internet)
   - Create required game directories
2. Internet connection is required for initial Java setup

## Supported Resolutions
The launcher supports these game resolutions:
- 240×320 (default)
- 320×240
- 128×128
- 176×208
- 640×360

## Directory Structure
```
/mnt/mmc/Roms/
├── APPS/
│   ├── Java.sh
│   └── java/            # Main application folder
│       ├── app.py
│       ├── config.py
│       ├── graphic.py
│       ├── input.py
│       ├── language.py
│       ├── main.py
│       └── lang/        # Language files
├── JAVA/            # Game storage
│   ├── 240x320/     # Portrait games
│   ├── 320x240/     # Landscape games
│   └── Imgs/        # Game preview images
```

## Troubleshooting
- **No games appearing**:
  - Ensure games are in correct directories
  - Verify games have `.jar` extension
  - Check `config.py` for correct GAME_DIRS paths

- **Java download issues**:
  - Confirm internet connection
  - Check available storage space (>100MB required)
  - Verify GitHub URL in `download_and_extract_java()` function

- **Preview images not showing**:
  - Images must be in game directory's `Imgs/` folder
  - Supported formats: JPG or PNG
  - Filename must match game name (e.g., `GameName.jpg`)

- **Application crashes**:
  - Check `debug.log` for error details
  - Verify all required files are present
  - Ensure correct file permissions

## Supported Devices
- RGcubexx
- RG34xx
- RG34xxSP
- RG28xx
- RG35xx+_P
- RG35xxH
- RG35xxSP
- RG40xxH
- RG40xxV
- RG35xxPRO
```

This documentation covers all essential aspects of the application including installation, usage, troubleshooting, and customization options. The Markdown format makes it easy to read and can be directly used in GitHub or any Markdown viewer.
