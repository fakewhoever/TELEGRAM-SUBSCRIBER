import asyncio
import logging
from datetime import datetime
from pyrogram import Client
from pyrogram.errors import FloodWait, ChannelPrivate, UserAlreadyParticipant, AuthKeyUnregistered, SessionRevoked, UserDeactivated
import pandas as pd
import random
import config
import os
import platform
import json

# Отключаем логи Pyrogram
logging.getLogger("pyrogram").setLevel(logging.ERROR)

# ANSI цвета для логирования
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'

# Список возможных устройств и версий
DEVICES = [
    # Samsung
    {"device_model": "Samsung Galaxy S21", "system_version": "Android 11.0"},
    {"device_model": "Samsung Galaxy S22", "system_version": "Android 12.0"},
    {"device_model": "Samsung Galaxy S23", "system_version": "Android 13.0"},
    {"device_model": "Samsung Galaxy Note 20", "system_version": "Android 11.0"},
    {"device_model": "Samsung Galaxy A52", "system_version": "Android 11.0"},
    {"device_model": "Samsung Galaxy A73", "system_version": "Android 12.0"},
    
    # iPhone
    {"device_model": "iPhone 12", "system_version": "iOS 14.4"},
    {"device_model": "iPhone 13", "system_version": "iOS 15.0"},
    {"device_model": "iPhone 14", "system_version": "iOS 16.0"},
    {"device_model": "iPhone 14 Pro", "system_version": "iOS 16.0"},
    {"device_model": "iPhone 13 Pro", "system_version": "iOS 15.0"},
    {"device_model": "iPhone 12 Pro", "system_version": "iOS 14.4"},
    
    # Google Pixel
    {"device_model": "Google Pixel 5", "system_version": "Android 11.0"},
    {"device_model": "Google Pixel 6", "system_version": "Android 12.0"},
    {"device_model": "Google Pixel 7", "system_version": "Android 13.0"},
    {"device_model": "Google Pixel 6a", "system_version": "Android 12.0"},
    {"device_model": "Google Pixel 7 Pro", "system_version": "Android 13.0"},
    
    # OnePlus
    {"device_model": "OnePlus 9", "system_version": "Android 11.0"},
    {"device_model": "OnePlus 10", "system_version": "Android 12.0"},
    {"device_model": "OnePlus 11", "system_version": "Android 13.0"},
    {"device_model": "OnePlus 9 Pro", "system_version": "Android 11.0"},
    {"device_model": "OnePlus 10 Pro", "system_version": "Android 12.0"},
    
    # Xiaomi
    {"device_model": "Xiaomi Mi 11", "system_version": "Android 11.0"},
    {"device_model": "Xiaomi 12", "system_version": "Android 12.0"},
    {"device_model": "Xiaomi 13", "system_version": "Android 13.0"},
    {"device_model": "Xiaomi 12T", "system_version": "Android 12.0"},
    {"device_model": "Xiaomi 12 Pro", "system_version": "Android 12.0"},
    
    # Huawei
    {"device_model": "Huawei P40 Pro", "system_version": "Android 10.0"},
    {"device_model": "Huawei P50 Pro", "system_version": "Android 11.0"},
    {"device_model": "Huawei Mate 40 Pro", "system_version": "Android 10.0"},
    {"device_model": "Huawei Mate 50 Pro", "system_version": "Android 12.0"},
    
    # Realme
    {"device_model": "Realme GT 2", "system_version": "Android 12.0"},
    {"device_model": "Realme GT 2 Pro", "system_version": "Android 12.0"},
    {"device_model": "Realme 10 Pro+", "system_version": "Android 13.0"},
    
    # Vivo
    {"device_model": "Vivo X80", "system_version": "Android 12.0"},
    {"device_model": "Vivo X90", "system_version": "Android 13.0"},
    {"device_model": "Vivo X80 Pro", "system_version": "Android 12.0"},
    
    # Oppo
    {"device_model": "Oppo Find X5", "system_version": "Android 12.0"},
    {"device_model": "Oppo Find X5 Pro", "system_version": "Android 12.0"},
    {"device_model": "Oppo Reno 8 Pro", "system_version": "Android 12.0"}
]

# Настройка логирования
if config.LOGGING['enabled']:
    logging.basicConfig(
        level=config.LOGGING['level'],
        format='%(asctime)s - %(message)s',
        datefmt='%H:%M:%S'
    )
logger = logging.getLogger(__name__)

class TelegramSubscriber:
    def __init__(self):
        # Создаем необходимые директории
        config.setup_directories()
        
        self.api_id = config.API_ID
        self.api_hash = config.API_HASH
        self.proxies = self._load_proxies() if config.PROXY['enabled'] else []
        
        # Инициализация DataFrame для результатов
        if not config.RESULTS_FILE.exists():
            pd.DataFrame(columns=['session', 'channel', 'status', 'timestamp']).to_csv(
                config.RESULTS_FILE, index=False
            )

    def _load_proxies(self):
        proxies = []
        if config.PROXIES_FILE.exists():
            with open(config.PROXIES_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        proxies.append(line)
        return proxies

    def get_random_proxy(self):
        if not self.proxies:
            return None
        
        proxy = random.choice(self.proxies)
        if config.PROXY['auth_required']:
            # Формат: username:password@host:port
            auth, host_port = proxy.split('@')
            username, password = auth.split(':')
            host, port = host_port.split(':')
            return {
                "scheme": config.PROXY['type'],
                "hostname": host,
                "port": int(port),
                "username": username,
                "password": password
            }
        else:
            # Формат: host:port
            host, port = proxy.split(':')
            return {
                "scheme": config.PROXY['type'],
                "hostname": host,
                "port": int(port)
            }

    def get_random_device(self):
        device = random.choice(DEVICES)
        app_version = f"{random.randint(7, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        return {
            "device_model": device["device_model"],
            "system_version": device["system_version"],
            "app_version": app_version,
            "lang_code": random.choice(["en", "ru", "es", "fr", "de"])
        }

    def get_session_info(self, session_name):
        session_info_file = config.SESSIONS_DIR / f"{session_name}.json"
        if session_info_file.exists():
            try:
                with open(session_info_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # Если файл не существует или ошибка чтения, создаем новую информацию
        device_info = self.get_random_device()
        proxy_info = self.get_random_proxy() if config.PROXY['enabled'] else None
        
        session_info = {
            "device_info": device_info,
            "proxy_info": proxy_info,
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "last_used": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Сохраняем информацию
        with open(session_info_file, 'w', encoding='utf-8') as f:
            json.dump(session_info, f, indent=4, ensure_ascii=False)
        
        return session_info

    def update_last_used(self, session_name):
        session_info_file = config.SESSIONS_DIR / f"{session_name}.json"
        if session_info_file.exists():
            try:
                with open(session_info_file, 'r', encoding='utf-8') as f:
                    session_info = json.load(f)
                session_info["last_used"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                with open(session_info_file, 'w', encoding='utf-8') as f:
                    json.dump(session_info, f, indent=4, ensure_ascii=False)
            except:
                pass

    async def check_subscription(self, client, channel):
        try:
            # Пробуем получить информацию о чате
            try:
                chat = await client.get_chat(channel)
                logger.info(f"{Colors.BLUE}Информация о канале получена: {chat.title}{Colors.END}")
            except Exception as e:
                logger.error(f"{Colors.RED}[ERROR] Не удалось получить информацию о канале {channel}: {str(e)}{Colors.END}")
                return False, "Channel not found"
            
            # Получаем себя как участника
            me = await client.get_me()
            
            # Метод 1: Проверка через get_chat_member
            try:
                participant = await client.get_chat_member(channel, me.id)
                logger.info(f"{Colors.BLUE}Статус участника (get_chat_member): {participant.status}{Colors.END}")
                
                if participant.status in ["member", "administrator", "creator"]:
                    logger.info(f"{Colors.GREEN}[SUCCESS] Подтверждена подписка на канал {channel} (метод 1){Colors.END}")
                    return True, "Already subscribed"
            except Exception as e:
                logger.info(f"{Colors.YELLOW}Метод 1 не сработал: {str(e)}{Colors.END}")
            
            # Метод 2: Проверка через get_dialogs
            try:
                async for dialog in client.get_dialogs():
                    if dialog.chat.id == chat.id:
                        logger.info(f"{Colors.GREEN}[SUCCESS] Подтверждена подписка на канал {channel} (метод 2){Colors.END}")
                        return True, "Already subscribed"
            except Exception as e:
                logger.info(f"{Colors.YELLOW}Метод 2 не сработал: {str(e)}{Colors.END}")
            
            # Если оба метода не подтвердили подписку
            logger.info(f"{Colors.YELLOW}Оба метода проверки не подтвердили подписку{Colors.END}")
            return False, "Not subscribed"
                
        except Exception as e:
            logger.error(f"{Colors.RED}[ERROR] Ошибка при проверке подписки на канал {channel}: {str(e)}{Colors.END}")
            return False, str(e)

    async def join_channel(self, client, channel):
        try:
            # Проверяем, подписан ли уже
            is_subscribed, status = await self.check_subscription(client, channel)
            if is_subscribed:
                return True, status

            # Пробуем подписаться
            logger.info(f"{Colors.BLUE}Попытка подписки на канал {channel}...{Colors.END}")
            try:
                await client.join_chat(channel)
                logger.info(f"{Colors.GREEN}[SUCCESS] Запрос на подписку отправлен{Colors.END}")
            except Exception as e:
                logger.error(f"{Colors.RED}[ERROR] Ошибка при отправке запроса на подписку: {str(e)}{Colors.END}")
                return False, str(e)
            
            # Ждем немного перед проверкой
            logger.info(f"{Colors.YELLOW}Ожидание 10 секунд перед проверкой подписки...{Colors.END}")
            await asyncio.sleep(10)  # Увеличиваем задержку до 10 секунд
            
            # Проверяем подписку после попытки
            is_subscribed, status = await self.check_subscription(client, channel)
            if is_subscribed:
                logger.info(f"{Colors.GREEN}[SUCCESS] Успешно подписался на канал {channel}{Colors.END}")
                return True, "Success"
            else:
                logger.error(f"{Colors.RED}[ERROR] Не удалось подтвердить подписку на канал {channel}. Статус: {status}{Colors.END}")
                return False, status
                
        except UserAlreadyParticipant:
            logger.info(f"{Colors.GREEN}[SUCCESS] Уже подписан на канал {channel}{Colors.END}")
            return True, "Already subscribed"
        except FloodWait as e:
            wait_time = e.value
            logger.warning(f"{Colors.YELLOW}Необходимо подождать {wait_time} секунд перед следующей попыткой{Colors.END}")
            return False, f"Flood wait: {wait_time} seconds"
        except ChannelPrivate:
            logger.warning(f"{Colors.YELLOW}Канал {channel} является приватным{Colors.END}")
            return False, "Channel is private"
        except Exception as e:
            logger.error(f"{Colors.RED}[ERROR] Ошибка при подписке на канал {channel}: {str(e)}{Colors.END}")
            return False, str(e)

    def save_blocked_session(self, session_file, reason):
        # Сохраняем информацию о заблокированной сессии
        result = {
            'session': session_file,
            'channel': 'SYSTEM',
            'status': f'BLOCKED: {reason}',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        df = pd.DataFrame([result])
        df.to_csv(config.RESULTS_FILE, mode='a', header=False, index=False)
        logger.error(f"{Colors.RED}[FAIL] Сессия {session_file} заблокирована: {reason}{Colors.END}")

    async def check_proxy(self, proxy_info):
        """Проверяет работоспособность прокси"""
        import aiohttp
        import asyncio

        try:
            logger.info(f"{Colors.BLUE}Проверка прокси {proxy_info['hostname']}:{proxy_info['port']}...{Colors.END}")
            
            proxy_url = f"{proxy_info['scheme']}://"
            if 'username' in proxy_info:
                proxy_url += f"{proxy_info['username']}:{proxy_info['password']}@"
            proxy_url += f"{proxy_info['hostname']}:{proxy_info['port']}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.telegram.org', proxy=proxy_url, timeout=10) as response:
                    if response.status == 200:
                        logger.info(f"{Colors.GREEN}[SUCCESS] Прокси {proxy_info['hostname']}:{proxy_info['port']} работает{Colors.END}")
                        return True
                    else:
                        logger.error(f"{Colors.RED}[FAIL] Прокси {proxy_info['hostname']}:{proxy_info['port']} не отвечает (статус {response.status}){Colors.END}")
                        return False
        except Exception as e:
            logger.error(f"{Colors.RED}[FAIL] Ошибка проверки прокси {proxy_info['hostname']}:{proxy_info['port']}: {str(e)}{Colors.END}")
            return False

    async def process_session(self, session_file):
        # Убираем расширение .session из имени файла
        session_name = os.path.splitext(session_file)[0]
        
        # Получаем информацию о сессии
        session_info = self.get_session_info(session_name)
        device_info = session_info["device_info"]
        proxy_info = session_info["proxy_info"]
        
        # Проверяем прокси если он включен
        if config.PROXY['enabled'] and proxy_info:
            proxy_working = await self.check_proxy(proxy_info)
            if not proxy_working:
                logger.error(f"{Colors.RED}[ERROR] Пропуск сессии {session_name} из-за неработающего прокси{Colors.END}")
                return
        
        # Создаем клиент
        client_params = {
            "name": session_name,
            "api_id": self.api_id,
            "api_hash": self.api_hash,
            "workdir": str(config.SESSIONS_DIR),
            **device_info
        }
        
        if proxy_info:
            client_params["proxy"] = proxy_info
        
        client = Client(**client_params)
        
        try:
            logger.info(f"{Colors.BLUE}Подключение к аккаунту {session_name}...{Colors.END}")
            await client.start()
            me = await client.get_me()
            logger.info(f"{Colors.BLUE}Аккаунт: @{me.username} (ID: {me.id}){Colors.END}")
            logger.info(f"{Colors.BLUE}Устройство: {device_info['device_model']} ({device_info['system_version']}){Colors.END}")
            if proxy_info:
                logger.info(f"{Colors.BLUE}Прокси: {proxy_info['hostname']}:{proxy_info['port']}{Colors.END}")
            
            # Обновляем время последнего использования
            self.update_last_used(session_name)
            
            # Читаем список каналов
            with open(config.CHANNELS_FILE, 'r', encoding='utf-8') as f:
                channels = []
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Извлекаем имя канала из ссылки
                        if 't.me/' in line:
                            channel = line.split('t.me/')[-1]
                        else:
                            channel = line
                        channels.append(channel)
            
            total_channels = len(channels)
            logger.info(f"{Colors.BLUE}Найдено {total_channels} каналов для обработки{Colors.END}")
            
            results = []
            for i, channel in enumerate(channels, 1):
                logger.info(f"{Colors.BLUE}Обработка канала {i}/{total_channels}: {channel}{Colors.END}")
                success, status = await self.join_channel(client, channel)
                results.append({
                    'session': session_file,
                    'channel': channel,
                    'status': status,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                
                # Задержка между подписками на каналы
                if i < total_channels:  # Если это не последний канал
                    delay = random.uniform(
                        config.DELAYS['between_channels']['min'],
                        config.DELAYS['between_channels']['max']
                    )
                    logger.info(f"{Colors.YELLOW}Ожидание {delay:.1f} секунд перед следующей подпиской{Colors.END}")
                    await asyncio.sleep(delay)
            
            # Сохраняем результаты
            df = pd.DataFrame(results)
            df.to_csv(config.RESULTS_FILE, mode='a', header=False, index=False)
            logger.info(f"{Colors.GREEN}[SUCCESS] Результаты сохранены в {config.RESULTS_FILE}{Colors.END}")
            
        except (AuthKeyUnregistered, SessionRevoked, UserDeactivated) as e:
            error_msg = str(e)
            if isinstance(e, AuthKeyUnregistered):
                reason = "Ключ авторизации не зарегистрирован"
            elif isinstance(e, SessionRevoked):
                reason = "Сессия отозвана"
            else:
                reason = "Аккаунт деактивирован"
            self.save_blocked_session(session_file, reason)
            logger.error(f"{Colors.RED}[FAIL] Сессия {session_file} заблокирована: {reason}{Colors.END}")
        except Exception as e:
            logger.error(f"{Colors.RED}[ERROR] Ошибка в сессии {session_file}: {str(e)}{Colors.END}")
        finally:
            try:
                await client.stop()
                logger.info(f"{Colors.GREEN}[SUCCESS] Сессия {session_name} успешно завершена{Colors.END}")
            except:
                pass

    async def run(self):
        # Получаем список сессий
        sessions = [f for f in os.listdir(config.SESSIONS_DIR) if f.endswith('.session')]
        
        if not sessions:
            logger.error(f"{Colors.RED}[ERROR] Сессии не найдены в директории sessions{Colors.END}")
            return
        
        total_sessions = len(sessions)
        logger.info(f"{Colors.BLUE}Найдено {total_sessions} сессий для обработки{Colors.END}")
        
        # Обрабатываем сессии последовательно
        for i, session in enumerate(sessions, 1):
            logger.info(f"{Colors.BLUE}Обработка сессии {i}/{total_sessions}: {session}{Colors.END}")
            await self.process_session(session)
            
            if i < total_sessions:  # Если это не последняя сессия
                delay = random.uniform(
                    config.DELAYS['between_sessions']['min'],
                    config.DELAYS['between_sessions']['max']
                )
                logger.info(f"{Colors.YELLOW}Ожидание {delay:.1f} секунд перед следующей сессией{Colors.END}")
                await asyncio.sleep(delay)

def main():
    logger.info(f"{Colors.BLUE}Запуск скрипта подписки на каналы{Colors.END}")
    subscriber = TelegramSubscriber()
    asyncio.run(subscriber.run())
    logger.info(f"{Colors.GREEN}[SUCCESS] Скрипт успешно завершил работу{Colors.END}")

if __name__ == "__main__":
    main()