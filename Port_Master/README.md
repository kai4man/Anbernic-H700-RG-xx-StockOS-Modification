PortMaster-GUI is a graphical interface application designed for Anbernic handheld gaming devices running StockOS. It provides an easy way to manage and install game ports from the PortMaster repository.

## Key Features
- **Automatic Updates**: Checks for and installs the latest PortMaster version
- **Runtime Management**: Downloads and installs required runtime libraries
- **Multi-language Support**: Supports multiple system languages
- **Configuration Management**: Handles various system configurations automatically
- **Network Connectivity Check**: Verifies internet connection before operations

## Supported Devices
The application supports the following Anbernic devices:
- RG28XX-H
- RG34XX-H
- RG34XX-SP
- RG35XX-PLUS
- RG35XX-H
- RG35XX-SP
- RG35XX-PRO
- RG40XX-H
- RG40XX-V
- RGCUBEXX-H

## Installation
1. Place the application files in the `/roms/ports/PortMaster` directory
2. Ensure you have internet connectivity
3. Run the application

## Usage
When launched, the application will:
1. Check internet connectivity
2. Verify if a newer PortMaster version is available
3. Prompt to download and install updates if available
4. Check for required runtime libraries
5. Configure system settings automatically

### Main Functions
- **PortMaster Update**: Automatically checks GitHub for the latest version and updates if needed
- **Runtime Installation**: Downloads missing runtime libraries for game ports
- **System Configuration**: Sets up required system files and permissions
- **Language Setup**: Matches the system language with PortMaster's interface

## Controls
The application uses the following device controls:
- **A Button**: Confirm selection
- **B Button**: Cancel/Go back
- **Menu Button**: Exit application

## Troubleshooting
1. **No Internet Connection**: 
   - Ensure your device is connected to WiFi
   - The app tests multiple DNS servers (Google, Cloudflare, Ali, Baidu)

2. **Update Failures**:
   - Check available storage space
   - Verify GitHub API accessibility

3. **Permission Issues**:
   - Ensure the application has proper permissions to write to `/roms/ports`

## File Locations
- Main application: `/roms/ports/PortMaster`
- Configuration files: `/roms/ports/PortMaster/config`
- Log files: `/roms/ports/PortMaster/logs`
- Temporary files: `/tmp/PortMaster*`

## Supported Languages
The application supports these system languages:
- English (en_US)
- Chinese Simplified (zh_CN)
- Chinese Traditional (zh_TW)
- Japanese (ja_JP)
- Korean (ko_KR)
- Spanish (es_LA)
- Russian (ru_RU)
- German (de_DE)
- French (fr_FR)
- Portuguese (pt_BR)

## Technical Details
- Uses Python 3 for the main application
- Implements low-level framebuffer access for graphics
- Handles input through Linux event system
- Maintains compatibility with StockOS file structure

## Credits
- Uses PortMaster core functionality
- Includes community-developed runtime libraries


## Disclaimer
This software is provided as-is. The developers are not responsible for any device issues that may occur from its use. Always back up your data before installation.
```
