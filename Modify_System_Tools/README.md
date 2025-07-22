# Anbernic Modify System Tools - User Manual

## Overview
Modify System Tools is a utility application designed for Anbernic handheld gaming devices that provides system management, backup/restore functionality, and various customization options. The application features a graphical interface optimized for handheld devices.

## Supported Devices
The application supports the following Anbernic models:
- RGcubexx
- RG34xx / RG34xxSP
- RG28xx
- RG35xx+_P
- RG35xxH / RG35xxSP
- RG40xxH / RG40xxV
- RG35xxPRO

## Features
- System backup and restore functionality
- Emulator settings management
- Save file operations
- Theme management
- Kernel modification tools
- Multi-language support (10 languages available)
- SD card storage selection

## Installation
1. Place the application files in the appropriate directory (typically `/mnt/mmc/Roms/APPS/`)
2. The application will automatically detect your hardware model
3. Language settings are automatically loaded from system configuration

## Navigation Controls
- **D-Pad Up/Down**: Navigate menu items
- **A Button**: Select/Confirm
- **B Button**: Back
- **Y Button**: Switch SD card storage (in backup/restore menus)
- **Menu Button**: Exit application

## Main Menu Options

### 1. Backup System Settings
- Creates a compressed backup of system configuration files
- Stores backup on selected SD card (TF1 or TF2)
- Includes WiFi settings, menu configurations, and system files

### 2. Restore System Settings
- Restores system configuration from a previous backup
- Select backup file from chosen SD card storage

### 3. Backup Emulator Settings
- Backs up emulator configurations and customizations
- Includes RetroArch configs, core settings, and custom configurations

### 4. Restore Emulator Settings
- Restores emulator configurations from backup
- Preserves your customized emulator setups

### 5. Backup Save Files
- Creates backup of all game save files
- Includes save states, memory cards, and game progress

### 6. Restore Save Files
- Restores game progress from backup
- Recovers save states and memory card data

### 7. Backup Theme Files
- Backs up custom theme configurations
- Preserves your visual customization settings

### 8. Restore Theme Files
- Restores previously saved theme configurations
- Recovers your preferred visual style

### 9. System Tools
- Various system utilities and maintenance tools
- Includes options for advanced users

### 10. Randomizer Settings
- Configure random game selection options
- Customize random game behavior

### 11. Gamma Kernel
- Switch between stock and gamma kernel (advanced users only)
- **Warning**: Kernel modifications may affect system stability

## Backup Locations
The application supports backing up to either:
- **TF1**: `/mnt/mmc/anbernic/backup`
- **TF2**: `/mnt/sdcard/anbernic/backup`

Use the Y button to switch between storage locations when in backup/restore menus.

## Important Notes
1. Kernel modifications require a system reboot
2. Some operations may take several minutes to complete
3. Always ensure sufficient storage space before creating backups
4. The application automatically creates necessary directories
5. Backups are stored as compressed tar.gz files
6. System tools may require technical knowledge (use with caution)

## Version Information
Current version: v1.2

## Exit
Press the Menu button at any time to exit the application safely.

## Troubleshooting
- If backups fail, check available storage space
- Restore operations may require application restart
- Kernel modifications are device-specific
- Some features may not be available on all hardware models
- Check system logs for detailed error information
```
