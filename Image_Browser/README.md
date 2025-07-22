# Image Browser for Anbernic Devices

## Overview
Image Browser is a lightweight image viewer application designed specifically for Anbernic handheld gaming devices. It allows users to browse and view images stored on their device's storage cards. Key features include:

- Browse image files (PNG, JPG, JPEG, BMP)
- Fullscreen image viewing
- Slideshow mode
- Dual TF card support
- Intuitive controller-based navigation
- Multi-language support

## Supported Devices
The application is compatible with various Anbernic models including:
- RGcubexx
- RG34xx/RG34xxSP
- RG28xx
- RG35xx+_P
- RG35xxH
- RG35xxSP
- RG40xxH/RG40xxV
- RG35xxPRO

## Installation
1. Ensure your device is running supported firmware
2. Place the application files in the appropriate directory (typically `/mnt/mmc/Roms/APPS/`)
3. The application will automatically detect your hardware model

## Basic Navigation

### Browser Mode
This is the main file browsing interface:
```
[Path: /mnt/mmc]                       [1/15]
[+] Pictures        [Preview of selected image]
[+] Screenshots
[+] Wallpapers
image1.jpg
image2.png
```

### Controls in Browser Mode
| Button | Function |
|--------|----------|
| **D-Pad Up/Down** | Navigate file list |
| **A Button** | Open selected folder/image |
| **B Button** | Go back to previous directory |
| **Y Button** | Switch between TF cards (SD1/SD2) |
| **X Button** | Start slideshow from current position |
| **L1/R1** | Page up/down through file list |
| **Menu Button** | Exit application |

### Image Viewing Mode
- Opens images in fullscreen
- Navigation controls:
  - **D-Pad Up/Down**: Previous/next image
  - **L1/R1**: Jump to previous/next page of images
  - **B Button**: Return to browser

### Slideshow Mode
- Automatically cycles through all images in current directory
- Default interval: 3 seconds per image
- **Any button press**: Exit slideshow and return to browser

## Advanced Features

### TF Card Switching
The application supports dual storage cards:
- SD1: Mounted at `/mnt/mmc`
- SD2: Mounted at `/mnt/sdcard`
- Press **Y Button** to toggle between storage cards

### Language Support
The application automatically detects your system language and supports:
- English (en_US)
- Chinese (zh_CN, zh_TW)
- Japanese (ja_JP)
- Korean (ko_KR)
- Spanish (es_LA)
- Russian (ru_RU)
- German (de_DE)
- French (fr_FR)
- Portuguese (pt_BR)

### Technical Notes
- Image formats supported: PNG, JPG, JPEG, BMP
- Automatic screen rotation handling for vertical screen devices
- Custom font rendering for better readability
- Hardware-accelerated display through framebuffer

## Troubleshooting
- **No valid file found!**: The current directory contains no images or accessible folders
- **Error reading path**: Check directory permissions or storage card connection
- **Preview not showing**: Ensure images are in supported formats and not corrupted

## Exiting the Application
Press the **Menu Button** at any time to exit the Image Browser. A confirmation message "Exiting..." will appear before the application closes.

---

*Image Browser v1.2 - Designed for Anbernic Handheld Devices*
