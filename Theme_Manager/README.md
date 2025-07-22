# Anbernic Themes Manager - User Manual

## Overview
The Anbernic Themes Manager is a Python application designed for Anbernic handheld gaming devices. It provides an intuitive interface to manage themes, boot logos, and system configurations on supported devices.

## Supported Devices
The application supports the following Anbernic models:
- RGcubexx
- RG34xx / RG34xxSP
- RG28xx
- RG35xx+_P
- RG35xxH
- RG35xxSP
- RG40xxH
- RG40xxV
- RG35xxPRO

## Features
1. **Theme Management**
   - Install custom themes from ZIP files
   - Backup and restore themes
   - Restore stock themes

2. **Boot Logo Management**
   - Set custom boot logos (BMP format)
   - Enable/disable random boot logo display

3. **System Configuration**
   - Switch between SD card storage
   - Backup and restore system configurations

## Installation
1. Ensure your device is running supported firmware
2. Place the application files in the appropriate directory (typically `/mnt/mmc/Roms/APPS/`)
3. The application will automatically detect your hardware model
4. Place theme files in `/mnt/mmc/anbernic/themes/` or `/mnt/sdcard/anbernic/themes/`
5. Place boot logo files in `/mnt/mmc/anbernic/bootlogo/` or `/mnt/sdcard/anbernic/bootlogo/`

## Usage

### Main Menu Navigation
- **Up/Down**: Navigate through menu options
- **A Button**: Select current option
- **B Button**: Go back
- **X Button**: Access help
- **Y Button**: Switch between SD cards
- **Menu Button**: Exit application

### Theme Installation
1. Select "themes" from the main menu
2. Browse available themes using Up/Down
3. Press A to install selected theme
4. The system will automatically apply the theme

### Boot Logo Configuration
1. Select "bootlogo" from the main menu
2. Browse available logo files
3. Press A to set selected logo
4. Use X button to toggle random logo display

### Backup and Restore
1. **Backup Themes**: Select "back.theme" to create a backup
2. **Restore Themes**: Select "restore.theme" to restore from backup
3. **Restore Stock**: Select "restore.stock" to restore original themes

## File Requirements
- **Themes**: Must be in ZIP format containing:
  - res1/ and res2/ folders
  - Optional font files (TTF format)
  - Optional boot logo (BMP format)
  
- **Boot Logos**: Must be in BMP format with correct dimensions for your device

## Troubleshooting
1. **Themes not appearing**:
   - Verify files are in correct directory
   - Check file extensions (.zip for themes, .bmp for logos)
   - Try switching SD cards (Y button)

2. **Installation fails**:
   - Ensure sufficient storage space
   - Verify ZIP file integrity
   - Check file permissions

3. **Display issues**:
   - Restart the application
   - Try a different theme

## Notes
- The application automatically detects your device model and adjusts the interface accordingly
- Theme installations may take several seconds to complete
- Some operations require root permissions

## Version Information
Current version: v1.2

For support or bug reports, please contact the developer.
```