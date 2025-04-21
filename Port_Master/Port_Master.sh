#!/bin/sh

# ========================
# КОНФИГУРАЦИОННЫЕ ПЕРЕМЕННЫЕ
# ========================

# URL для загрузки и информации о версии
GITHUB_API_URL="https://api.github.com/repos/PortsMaster/PortMaster-GUI/releases/latest"
GITHUB_DOWNLOAD_URL="https://github.com/PortsMaster/PortMaster-GUI/releases/latest/download/PortMaster.zip"

# Основные пути
BASE_INSTALL_DIR="/mnt/sdcard/roms/PORTS"
LEGACY_PORTMASTER_DIR="/roms/ports/PortMaster"

# Служебные пути
TEMP_FILE="/tmp/PortMaster.zip"
TEMP_DIR="/tmp/PortMaster_Update"
LOG_FILE="$LEGACY_PORTMASTER_DIR/update.log"
PYLIBS_DIR="$LEGACY_PORTMASTER_DIR/pylibs/harbourmaster"
CONFIG_FILE="$PYLIBS_DIR/config.py"

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