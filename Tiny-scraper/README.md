# Tiny Scraper for Anbernic Devices

## Overview
Tiny Scraper is a tool designed for Anbernic handheld gaming devices that automatically downloads game screenshots from the ScreenScraper.fr database. It helps enhance your gaming experience by adding visual media to your ROM collections.

## Key Features
- Automatic screenshot downloading for missing media
- Support for multiple game systems (PSP, PS, GBA, etc.)
- Dual SD card support (TF1 and TF2)
- Batch downloading capabilities
- Multi-language interface
- Simple navigation using device controls

## Supported Anbernic Devices
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

## Installation
1. Ensure your device is running supported firmware
2. Place the application files in the appropriate directory (typically `/mnt/mmc/Roms/APPS/`)
3. The application will automatically detect your hardware model

## Configuration
Edit `config.json` with your ScreenScraper.fr credentials:

```json
{
    "user": "your_screenscraper_username",
    "password": "your_screenscraper_password",
    "media_type": "ss",
    "region": "wor"
}
```

- `media_type`: Media type to download (default: `ss` for screenshots)
- `region`: Region preference (default: `wor` for worldwide)

## Running the Application
1. Connect your device to WiFi
2. Navigate to the directory containing the files
3. Run the application:
   ```
   tiny-scraper
   ```

## Controls

### System Selection Screen
| Button | Action |
|--------|--------|
| **D-pad Up/Down** | Navigate through systems |
| **L1/R1** | Page up/down |
| **L2/R2** | Jump 100 systems |
| **Y** | Switch between TF1 and TF2 |
| **A** | Select system |
| **M** | Exit application |

### Game Selection Screen
| Button | Action |
|--------|--------|
| **D-pad Up/Down** | Navigate through games |
| **L1/R1** | Page up/down |
| **L2/R2** | Jump 100 games |
| **A** | Download screenshot for selected game |
| **START** | Download all missing screenshots |
| **B** | Return to system selection |
| **M** | Exit application |

## Workflow
1. **System Selection**: 
   - The app scans your SD card for available game systems
   - Use D-pad to select a system and press A

2. **Game Selection**:
   - The app identifies games missing screenshots
   - Select a game and press A to download its screenshot
   - Press START to download all missing screenshots

3. **Media Storage**:
   - Screenshots are saved in the game's folder under `Imgs/`
   - Files are named as `[game_name].png`

## Troubleshooting
- **No internet connection**: Ensure WiFi is connected and working
- **Scraping failed**: Verify ScreenScraper.fr credentials in config.json
- **No roms found**: Check your SD card path configuration in anbernic.py
- **Invalid media**: Try changing `media_type` in config.json

## Notes
- Screenshots are downloaded at 320x240 resolution by default
- The app prioritizes region-specific media when available
- Batch downloading may take significant time for large collections

## Support
For additional help, refer to the source code comments or visit the Anbernic community forums.

**Enjoy your visually enhanced gaming experience!**
