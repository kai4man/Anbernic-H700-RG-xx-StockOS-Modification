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
1. Place the following files in your device's `/mnt/mmc/Emu/JAVA/` directory:
   - `app.py`
   - `config.py`
   - `graphic.py`
   - `input.py`
   - `language.py`
   - `main.py`
   - `lang/` directory with translation files

2. Create game directories (will be auto-created on first run if missing):
   ```bash
   /mnt/mmc/Roms/JAVA/240x320
   /mnt/mmc/Roms/JAVA/320x240
   /mnt/sdcard/Roms/JAVA/240x320 (if SD card present)
   /mnt/sdcard/Roms/JAVA/320x240 (if SD card present)
   ```

## Usage Instructions

### Starting the Application
- Execute `main.py` to launch the program

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
/mnt/mmc/
├── Emu/
│   └── JAVA/            # Main application folder
│       ├── app.py
│       ├── config.py
│       ├── graphic.py
│       ├── input.py
│       ├── language.py
│       ├── main.py
│       └── lang/        # Language files
├── Roms/
│   └── JAVA/            # Game storage
│       ├── 240x320/     # Portrait games
│       ├── 320x240/     # Landscape games
│       └── Imgs/        # Game preview images
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

## Customization
Modify `config.py` to adjust:
```python
PADDING = 5                   # UI element spacing
BORDER_RADIUS = 8             # Corner rounding
LIST_WIDTH_RATIO = 0.6        # Game list width
FONT_PATH = "/path/to/font"   # Custom font
JAVA_CMD = "/path/to/java"    # Custom Java path
```

## Technical Notes
- Java environment is installed to `/mnt/mmc/Emu/JAVA/jdk/`
- Game launch command:
  ```bash
  java -jar freej2me-sdl.jar game.jar [width] [height] [fps]
  ```
- Language files use JSON format in `lang/` directory

## Uninstallation
1. Delete the `/mnt/mmc/Emu/JAVA/` directory
2. Optional: Remove Java environment at `/mnt/mmc/Emu/JAVA/jdk/`
```

This documentation covers all essential aspects of the application including installation, usage, troubleshooting, and customization options. The Markdown format makes it easy to read and can be directly used in GitHub or any Markdown viewer.
