import os
from pathlib import Path
import json

# Определяем базовую директорию (где находится скрипт)
BASE_DIR = Path(__file__).parent.absolute()

# Пути к важным файлам и папкам
SESSIONS_DIR = BASE_DIR / "sessions"
CHANNELS_FILE = BASE_DIR / "channels.txt"
RESULTS_FILE = BASE_DIR / "results.csv"
PROXIES_FILE = BASE_DIR / "proxies.txt"
SESSIONS_INFO_FILE = BASE_DIR / "sessions_info.json"

# Telegram API настройки
API_ID = 12345  # Замените на ваш API_ID (число)
API_HASH = "ваш_api_hash"  # Замените на ваш API_HASH

# Настройки прокси
PROXY = {
    "enabled": False,  # True/False использование прокси
    "type": "socks5",  # Тип прокси: socks5 или http
    "auth_required": False  # True/False требуется ли аутентификация для прокси
}

# Настройки задержек (в секундах)
DELAYS = {
    'between_channels': {  # между каналами
        'min': 5,
        'max': 30
    },
    'between_sessions': {  # между сессиями
        'min': 30,
        'max': 60
    }
}

# Настройки логирования
LOGGING = {
    'enabled': True,
    'level': 'INFO',
    'format': '%(asctime)s - %(levelname)s - %(message)s'
}

# Создание необходимых директорий и файлов
def setup_directories():
    # Создаем директорию для сессий
    SESSIONS_DIR.mkdir(exist_ok=True)
    
    # Создаем пустой файл каналов, если его нет
    if not CHANNELS_FILE.exists():
        with open(CHANNELS_FILE, 'w', encoding='utf-8') as f:
            f.write('# Вставьте ссылки на каналы по одной на строку\n')
            f.write('# Например:\n')
            f.write('# https://t.me/channel1\n')
            f.write('# https://t.me/channel2\n')
    
    # Создаем пустой файл прокси, если его нет
    if PROXY['enabled'] and not PROXIES_FILE.exists():
        with open(PROXIES_FILE, 'w', encoding='utf-8') as f:
            f.write('# Формат прокси:\n')
            if PROXY['auth_required']:
                f.write('# username:password@host:port\n')
            else:
                f.write('# host:port\n')
    
    # Создаем пустой файл результатов, если его нет
    if not RESULTS_FILE.exists():
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            f.write('session,channel,status,timestamp\n')

# Вызываем функцию создания директорий при импорте модуля
setup_directories()