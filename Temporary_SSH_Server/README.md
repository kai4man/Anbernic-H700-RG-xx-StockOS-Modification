# Temporary SSH Server - Usage Documentation

## Overview
This script creates a temporary SSH server on your device, displaying connection information on screen. It's designed for devices with limited interfaces, using button controls for interaction.

## Prerequisites
- `mpv` media player must be installed (`/usr/bin/mpv`)
- Requires root privileges for SSH operations
- Network interface (wlan0) must be available

## Features
- Automatically enables SSH service when activated
- Displays IP address, port, and credentials on screen
- Supports multiple language displays (based on `LANG_CUR` variable)
- Controller/button event handling for user interaction
- Automatic cleanup on supported hardware models (RG28xx)

## Usage Instructions

### Basic Operation
1. Execute the script with bash:  
   `bash Temporary_SSH_Server.sh`
2. The script will:
   - Enable SSH service if not active
   - Display connection information (IP: 22, user: root, pass: root)
   - Show an informational image (`sshtmp-${LANG_CUR}.png`)

### Connection Information
The script creates a subtitle file (`ip.srt`) containing:
```
IP address: [your_ip] Port: 22, User: root, Pass: root
```
This is displayed over the informational image for 6000 seconds (100 minutes).

### Termination
Press the designated function key (configured in system settings) to:
1. Close the information display
2. Disable SSH service (if `global.ssh=0` in system config)
3. Exit the script

## Technical Details

### Dependencies
- `mpv` for displaying information
- `evtest` for input device monitoring
- Systemd for SSH service management

### Configuration Variables
The script uses these external configurations (expected in `/mnt/mod/ctrl/configs/`):
- `functions` - Contains:
  - `user_quit()` function
  - `get_devices()` function
  - Device event patterns (`CONTROLLER_DISCONNECTED`, `DEVICE_DISCONNECTED`, `FUNC_KEY_EVENT`)
  - Button states (`PRESS`, `RELEASE`)
  - Display settings (`rotate_28`)
- `system.cfg` - Checks `global.ssh` setting

### Hardware Compatibility
Automatically exits on RG28xx hardware models (with exit code 2)

## Error Handling
- Displays error image (`noconn-${LANG_CUR}.png`) if no IP address is available
- Exits if required files are missing

## Security Notes
⚠️ **Important Security Warning**:
- Uses default credentials (root/root)
- SSH remains enabled until manually disabled or system reboot
- Intended for temporary use in controlled environments only
```