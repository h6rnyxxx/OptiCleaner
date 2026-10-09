import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Опциональная загрузка переменных окружения из .env
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

# Токен Telegram-бота (загружается из переменной окружения или .env)
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Секретная криптографическая соль (СТРОГО совпадает с клиентом OptiCleaner)
SECRET_LIC_SALT = b"OptiCleaner-2026-Super-Secret-Master-Salt-Pro-1000"

# Путь к базе данных SQLite
DB_PATH = BASE_DIR / "licenses.db"

# Директория резервных копий БД
BACKUP_DIR = BASE_DIR / "backups"

# Файл журнала действий администратора
ADMIN_LOG_PATH = BASE_DIR / "admin_log.txt"

# Настройки REST API сервера
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "OptiCleaner-Admin-Secret-Key-2026")

# Создатель и владелец проекта (всегда без кулдауна, всегда PRO доступ)
OWNER_USERNAMES = ["oleg676725"]
OWNER_IDS = [7514540547]

# Список Telegram ID администраторов бота (через запятую в .env)
ADMIN_IDS = [
    int(x.strip()) 
    for x in os.getenv("ADMIN_IDS", "7514540547").split(",") 
    if x.strip().isdigit()
]
for oid in OWNER_IDS:
    if oid not in ADMIN_IDS:
        ADMIN_IDS.append(oid)

# Кулдаун для обычных пользователей в минутах (уменьшен с 24 часов до 15 минут)
DEFAULT_COOLDOWN_MINUTES = int(os.getenv("COOLDOWN_MINUTES", "15"))


def is_owner_or_admin(user=None, user_id=None, username=None):
    if user:
        u_id = getattr(user, 'id', None)
        u_name = str(getattr(user, 'username', '') or '').lower().lstrip('@')
        if u_id in OWNER_IDS or u_id in ADMIN_IDS:
            return True
        if u_name in [x.lower() for x in OWNER_USERNAMES]:
            return True
    if user_id and (user_id in OWNER_IDS or user_id in ADMIN_IDS):
        return True
    if username and str(username).lower().lstrip('@') in [x.lower() for x in OWNER_USERNAMES]:
        return True
    return False

