#!/bin/bash

# ========================
# КОНФИГУРАЦИОННЫЕ ПЕРЕМЕННЫЕ
# ========================

program="$(cd $(dirname "$0"); pwd)"

# URL для загрузки и информации о версии
GITHUB_API_URL="https://api.github.com/repos/PortsMaster/PortMaster-GUI/releases/latest"
GITHUB_DOWNLOAD_URL="https://github.com/PortsMaster/PortMaster-GUI/releases/latest/download/PortMaster.zip"

# Параметры языка
sys_lang=(zh_CN zh_CN en_US ja_JP ko_KR es_ES ru_RU de_DE fr_FR pt_BR)
set_lang=${sys_lang[$(head -n 1 /mnt/vendor/oem/language.ini)]}

# Основные пути
if mountpoint -q /mnt/sdcard; then
    BASE_INSTALL_DIR="/mnt/sdcard/Roms/PORTS"
else
    BASE_INSTALL_DIR="/mnt/mmc/Roms/PORTS"
fi
LEGACY_PORTMASTER_DIR="/roms/ports/PortMaster"

# Служебные пути
TEMP_FILE="/tmp/PortMaster.zip"
TEMP_DIR="/tmp/PortMaster_Update"
LOG_FILE="$LEGACY_PORTMASTER_DIR/update.log"
PYLIBS_DIR="$LEGACY_PORTMASTER_DIR/pylibs/harbourmaster"
CONFIG_FILE="$PYLIBS_DIR/config.py"
HARBOUR_FILE="$PYLIBS_DIR/harbour.py"
HARDWARE_FILE="$PYLIBS_DIR/hardware.py"
LANG_FILE="$LEGACY_PORTMASTER_DIR/config/config.json"

# Быстрая проверка интернета (без таймаутов)
PING_TEST_HOST="8.8.8.8"  # Google DNS

# ========================
# ФУНКЦИИ
# ========================

# Инициализация лог-файла
init_logs() {
    mkdir -p "$LEGACY_PORTMASTER_DIR"
    : > "$LOG_FILE"
    exec 3>>"$LOG_FILE"
    exec 2>&3
}

# Логирование
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >&3
}

# Автоматические настройки языка
auto_set_lang() {
    [ -f "$LANG_FILE" ] || return 0  # Если файла нет - ничего не делаем
    
    if grep -q 'language' "$LANG_FILE"; then
        if ! grep -q "$set_lang" "$LANG_FILE"; then
            temp_file="$LANG_FILE.tmp"
            sed -E "s/\"language\": \"[^\"]+\"/\"language\": \"$set_lang\"/" "$LANG_FILE" > "$temp_file"
            if [ $? -eq 0 ]; then
                mv "$temp_file" "$LANG_FILE"
                log "Язык изменен успешно"
            else
                rm -f "$temp_file"
                return 1
            fi
        fi
    else
        sed -i -e "3i\    \"language\": \""$set_lang"\"," "$LANG_FILE"
    fi
    return 0

}

# Другие повышения
other_update() {
    # Шрифт
    if [ ! -f "$LEGACY_PORTMASTER_DIR/default.ttf" ]; then
        cp -f "/mnt/vendor/bin/default.ttf" "$LEGACY_PORTMASTER_DIR/default.ttf"
    fi
    if [ ! -L "$LEGACY_PORTMASTER_DIR/pylibs/resources/NotoSansSC-Regular.ttf" ]; then
        rm -f "$LEGACY_PORTMASTER_DIR/pylibs/resources/NotoSansSC-Regular.ttf"
        ln -sf "$LEGACY_PORTMASTER_DIR/default.ttf" "$LEGACY_PORTMASTER_DIR/pylibs/resources/NotoSansSC-Regular.ttf"
    fi
    if [ -f "$LEGACY_PORTMASTER_DIR/pugwash.txt" ]; then
        rm -f "$LEGACY_PORTMASTER_DIR/pugwash.txt"
    fi
    "$program/ports_fix"
}

# Мгновенная проверка интернета (без ожидания)
check_internet() {
    # Проверяем через ping (1 пакет, без ожидания)
    if ping -c 1 -W 1 "$PING_TEST_HOST" >/dev/null 2>&1; then
        return 0
    fi
    
    # Альтернативная проверка через wget (быстрая)
    if command -v wget >/dev/null 2>&1; then
        if wget -q --spider --timeout=1 --tries=1 "$PING_TEST_HOST"; then
            return 0
        fi
    fi
    
    # Последний вариант - проверка через /proc/net/route
    if [ -f /proc/net/route ]; then
        if grep -q -E '\w+[[:space:]]+00000000' /proc/net/route; then
            return 0
        fi
    fi
    
    return 1
}

# Проверка и обновление конфигурации
check_and_update_config() {
    [ -f "$CONFIG_FILE" ] || return 0  # Если файла нет - ничего не делаем
    
    log "Проверка конфигурации harbourmaster..."
    
    local current_ports_dir=$(grep -E '^HM_PORTS_DIR=' "$CONFIG_FILE" | cut -d'"' -f2 2>/dev/null)
    local current_scripts_dir=$(grep -E '^HM_SCRIPTS_DIR=' "$CONFIG_FILE" | cut -d'"' -f2 2>/dev/null)
    
    if [ "$current_ports_dir" = "None" ] || 
       [ "$current_scripts_dir" = "None" ] || 
       [ "$current_ports_dir" != "$BASE_INSTALL_DIR" ] || 
       [ "$current_scripts_dir" != "$BASE_INSTALL_DIR" ]; then
        
        log "Обновление конфигурации..."
        mkdir -p "$PYLIBS_DIR" || return 1
        
        # Создаем временный файл для нового конфига
        local temp_conf=$(mktemp)
        echo "HM_PORTS_DIR=\"$BASE_INSTALL_DIR\"" > "$temp_conf"
        echo "HM_SCRIPTS_DIR=\"$BASE_INSTALL_DIR\"" >> "$temp_conf"
        
        # Копируем остальные параметры из старого конфига (если есть)
        grep -v -E '^(HM_PORTS_DIR|HM_SCRIPTS_DIR)=' "$CONFIG_FILE" >> "$temp_conf" 2>/dev/null
        
        # Заменяем конфиг
        mv "$temp_conf" "$CONFIG_FILE" || {
            rm -f "$temp_conf"
            return 1
        }
        
        log "Конфигурация обновлена"
    else
        log "Конфигурация актуальна"
    fi
    
    return 0
}

# Проверка и обновление конфигурации
check_and_update_harbour() {
    [ -f "$HARBOUR_FILE" ] || return 0  # Если файла нет - ничего не делаем
    
    log "Проверка конфигурации harbourmaster..."
    if ! grep -q 'self.install_image(port_info)' "$HARBOUR_FILE"; then
        line1=$(grep -n 'self.callback.message_box(_("Port {download_name!r} installed successfully.").format(download_name=port_nice_name))' "$HARBOUR_FILE" | cut -d ":" -f 1)
        line2=$(expr $line1 + 2)
        sed -i ''${line2}'i\        self.install_image(port_info)' "$HARBOUR_FILE"
    fi
    if ! grep -q 'self.uninstall_image(port_info)' "$HARBOUR_FILE"; then
        line1=$(grep -n 'self.callback.message_box(_("Successfully uninstalled {port_name}").format(port_name=port_info_name))' "$HARBOUR_FILE" | cut -d ":" -f 1)
        line2=$(expr $line1 + 1)
        sed -i ''${line2}'i\        self.uninstall_image(port_info)' "$HARBOUR_FILE"
    fi
    if ! grep -q 'def install_image(self, port_info_list):' "$HARBOUR_FILE"; then
        new_code='    def install_image(self, port_info_list):
        logger.info(f"install_image-->port_info_list: {port_info_list}")
        port_dir = f"{self.ports_dir}"
        port_image_dir = self.ports_dir / "Imgs"
        port_script_filename = None
        for item in port_info_list["items"]:
            if self._ports_dir_exists(item):
                if item.casefold().endswith("/"):
                    part = item.rsplit("/")
                    port_dir = Path(port_dir) / part[0]
                if item.casefold().endswith(".sh"):
                    port_script_filename = os.path.splitext(item)
        port_image_list = port_info_list.get("attr", {}).get("image")
        if isinstance(port_image_list, dict):
            for key, port_image in port_image_list.items():
                if port_image.lower().endswith(".png") or port_image.lower().endswith(".jpg"):
                    port_image_filename = os.path.splitext(port_image)
                    break
                else:
                    return 1
        elif isinstance(port_image_list, str):
            port_image = port_image_list
            port_image_filename = os.path.splitext(port_image)
        if not port_image_dir.exists():
            os.makedirs(port_image_dir, exist_ok=True)
        source_image_path = Path(port_dir) / port_image
        target_image_path = Path(port_image_dir) / f"{port_script_filename[0]}{port_image_filename[1]}"
        logger.info(f"source_image_path: {source_image_path}, target_image_path: {target_image_path}")
        shutil.copy2(source_image_path, target_image_path)
'
        line1=$(grep -n '__all__ = (' "$HARBOUR_FILE" | cut -d ":" -f 1)
        line2=$(expr $line1 - 1)
        sed -i ''${line2}'r /dev/stdin' <<< "$new_code" "$HARBOUR_FILE"
    fi
    if ! grep -q 'def uninstall_image(self, port_info):' "$HARBOUR_FILE"; then
        new_code='    def uninstall_image(self, port_info):
        logger.info(f"uninstall_image-->port_info: {port_info}")
        port_image_dir = self.ports_dir / "Imgs"
        for item in port_info["items"]:
            if item.casefold().endswith(".sh"):
                port_script_filename = os.path.splitext(item)
        port_image_list = port_info.get("attr", {}).get("image")
        if isinstance(port_image_list, dict):
            for key, port_image in port_image_list.items():
                if port_image.lower().endswith(".png") or port_image.lower().endswith(".jpg"):
                    port_image_filename = os.path.splitext(port_image)
                    break
                else:
                    return 1
        elif isinstance(port_image_list, str):
            port_image = port_image_list
            port_image_filename = os.path.splitext(port_image)
        target_image_path = Path(port_image_dir) / f"{port_script_filename[0]}{port_image_filename[1]}"
        logger.info(f"target_image_path: {target_image_path}")
        if target_image_path.exists():
            target_image_path.unlink()
'
        line1=$(grep -n '__all__ = (' "$HARBOUR_FILE" | cut -d ":" -f 1)
        line2=$(expr $line1 - 1)
        sed -i ''${line2}'r /dev/stdin' <<< "$new_code" "$HARBOUR_FILE"
    fi
    
    old_text="https://github.com/PortsMaster/PortMaster-Info/raw/main/"
    new_text="https://github.com/PortsMaster/PortMaster-Info/blob/main/"

    if grep -q "$old_text" "$HARBOUR_FILE"; then

        log "Обновление конфигурации..."

        temp_file="$HARBOUR_FILE.tmp"
        sed "s|$old_text|$new_text|g" "$HARBOUR_FILE" > "$temp_file"
        if [ $? -eq 0 ]; then
            mv "$temp_file" "$HARBOUR_FILE"
            log "Конфигурация обновлена"
        else
            rm -f "$temp_file"
            log "Ошибка настройки обновления"
            return 1
        fi
        
    else
        log "Конфигурация актуальна"
    fi
    
    return 0
}

# Проверка и обновление конфигурации
check_and_update_hardware() {
    if ! grep -q "h700_info = safe_cat('/mnt/vendor/oem/board.ini')" "$HARDWARE_FILE"; then
        new_code="        h700_info = safe_cat('/mnt/vendor/oem/board.ini')
        if h700_info != '':
            hw_list = {
                'RGcubexx': 'sun50iw9',
                'RG34xx': 'anbernic rg34xx',
                'RG34xxSP': 'anbernic rg34xx',
                'RG28xx': 'anbernic rg28xx',
                'RG35xx+_P': 'anbernic rg35xx plus',
                'RG35xxH': 'anbernic rg35xx h',
                'RG35xxSP': 'anbernic rg35xx sp',
                'RG40xxH': 'anbernic rg40xx h',
                'RG40xxV': 'anbernic rg40xx v'
            }
            sfdbm = hw_list.get(h700_info, 'sun50iw9')"
        line1=$(grep -n "if sfdbm != '':" "$HARDWARE_FILE" | cut -d ":" -f 1)
        sed -i ''${line1}'r /dev/stdin' <<< "$new_code" "$HARDWARE_FILE"
    fi
}

# Получение последней версии с GitHub (только если есть интернет)
get_latest_version() {
    if ! check_internet; then
        log "Интернет недоступен, пропускаем проверку обновлений"
        return 1
    fi
    
    log "Получение информации о последней версии..."
    
    local version_info
    if command -v curl >/dev/null 2>&1; then
        version_info=$(curl -s --connect-timeout 3 "$GITHUB_API_URL")
    elif command -v wget >/dev/null 2>&1; then
        version_info=$(wget -qO- --timeout=3 "$GITHUB_API_URL")
    else
        version_info=$(python3 -c "
import urllib.request, json, sys
try:
    with urllib.request.urlopen('$GITHUB_API_URL', timeout=3) as response:
        print(response.read().decode())
except:
    sys.exit(1)
" 2>/dev/null)
    fi
    
    LATEST_VERSION=$(echo "$version_info" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
    
    if [ -z "$LATEST_VERSION" ]; then
        log "Не удалось получить информацию о версии"
        return 1
    fi
    
    log "Последняя версия на GitHub: $LATEST_VERSION"
    echo "$LATEST_VERSION"
    return 0
}

# Выход с очисткой
clean_exit() {
    local code=$1
    local message=$2
    
    [ -n "$message" ] && log "$message"
    [ -d "$TEMP_DIR" ] && rm -rf "$TEMP_DIR"
    [ -f "$TEMP_FILE" ] && rm -f "$TEMP_FILE"

    sudo rm /usr/lib/aarch64-linux-gnu/libEGL.so*
    sudo rm /usr/lib/aarch64-linux-gnu/libGLES*
    sudo ln -s /usr/lib/aarch64-linux-gnu/libmali.so /usr/lib/aarch64-linux-gnu/libEGL.so.1
    sudo ln -s /usr/lib/aarch64-linux-gnu/libmali.so /usr/lib/aarch64-linux-gnu/libGLESv2.so.2
    sudo ldconfig

    log "Запуск PortMaster..."
    exec "$LEGACY_PORTMASTER_DIR"/PortMaster.sh "$@"
    exit $code
}

# Проверка версии
check_version() {
    local version_file="$LEGACY_PORTMASTER_DIR/version"
    [ -f "$version_file" ] || return 0  # Нет файла версии - требуется обновление
    
    local current_version=$(cat "$version_file" 2>/dev/null | tr -d '\n\r')
    [ "$current_version" != "$LATEST_VERSION" ] && return 0  # Версии не совпадают
    
    return 1  # Версии совпадают
}

# Распаковка архива через Python
unpack_archive() {
    log "Распаковка архива через Python..."
    
    mkdir -p "$TEMP_DIR" || return 1
    
    python3 -c "
import os
import sys
import zipfile
try:
    with zipfile.ZipFile('$TEMP_FILE') as z:
        z.extractall('$TEMP_DIR')
    # Нормализация структуры каталогов
    portmaster_dir = os.path.join('$TEMP_DIR', 'PortMaster')
    if os.path.isdir(portmaster_dir):
        for item in os.listdir(portmaster_dir):
            os.rename(os.path.join(portmaster_dir, item), 
                      os.path.join('$TEMP_DIR', item))
        os.rmdir(portmaster_dir)
    # Установка прав
    for root, _, files in os.walk('$TEMP_DIR'):
        for f in files:
            if f.endswith(('.sh', '.py')) or f == 'PortMaster':
                os.chmod(os.path.join(root, f), 0o755)
    sys.exit(0)
except Exception as e:
    sys.stderr.write(f'Ошибка распаковки: {e}\n')
    sys.exit(1)
" >> "$LOG_FILE" 2>&1 || return 1
    
    return 0
}

# Процесс обновления
update_portmaster() {
    log "Загрузка обновления..."
    if ! wget -q --timeout=10 --tries=1 --show-progress "$GITHUB_DOWNLOAD_URL" -O "$TEMP_FILE"; then
        log "Ошибка загрузки!"
        return 1
    fi
    
    if ! unpack_archive; then
        log "Ошибка распаковки!"
        return 1
    fi
    
    log "Установка файлов..."
    pkill -f "PortMaster.sh" 2>/dev/null || log "PortMaster не запущен"
    
    if ! cp -rf "$TEMP_DIR"/* "$LEGACY_PORTMASTER_DIR"/; then
        log "Ошибка копирования файлов!"
        return 1
    fi
    
    # Обновление конфигурации
    check_and_update_config || log "Предупреждение: проблемы с конфигурацией"
    
    log "Установка прав..."
    chmod +x "$LEGACY_PORTMASTER_DIR"/PortMaster.sh
    [ -f "$LEGACY_PORTMASTER_DIR/PortMaster" ] && chmod +x "$LEGACY_PORTMASTER_DIR/PortMaster"
    
    # Записываем новую версию
    echo "$LATEST_VERSION" > "$LEGACY_PORTMASTER_DIR/version"
    
    return 0
}

# ========================
# ОСНОВНОЙ ПРОЦЕСС
# ========================

init_logs
log "=== Начало процесса обновления ==="

# Всегда проверяем конфигурацию
check_and_update_config || log "Предупреждение: проблемы с конфигурацией"
check_and_update_harbour || log "Предупреждение: проблемы с конфигурацией"
#check_and_update_hardware || log "Предупреждение: проблемы с конфигурацией"
auto_set_lang || log "Ошибка настройки языка"
other_update || log "Другие ошибки обновления"

# Пытаемся получить последнюю версию (если есть интернет)
if LATEST_VERSION=$(get_latest_version); then
    if check_version; then
        if update_portmaster; then
            clean_exit 0 "Успешно обновлено до $LATEST_VERSION" "$@"
        else
            clean_exit 0 "Ошибка обновления, запуск текущей версии" "$@"
        fi
    else
        clean_exit 0 "Версия актуальна ($LATEST_VERSION), запуск" "$@"
    fi
else
    clean_exit 0 "Интернет недоступен, запуск текущей версии" "$@"
fi
