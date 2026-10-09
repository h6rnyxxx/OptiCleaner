"""
OptiCleaner Telegram Bot Diagnostic Tool (Doctor)
Проверяет токен, вебхуки, очередь обновлений и тестовый приём сообщений.
"""
import sys
import os
import json
import asyncio
from pathlib import Path

# Загрузка конфигурации
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

from config import BOT_TOKEN, DB_PATH
import urllib.request
import urllib.error

def print_step(title):
    print(f"\n" + "=" * 60)
    print(f"🔍 {title}")
    print("=" * 60)

def tg_api(method, params=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    if params:
        data = json.dumps(params).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    else:
        req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        return {"ok": False, "error_code": e.code, "description": err_body}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def run_diagnostics():
    print("🚀 ЗАПУСК ДИАГНОСТИКИ TELEGRAM-БОТА OPTICLEANER")
    print(f"📁 Папка: {BASE_DIR}")
    
    # 1. Проверка токена в .env
    print_step("Шаг 1: Проверка токена")
    raw_token = os.getenv("BOT_TOKEN", "")
    print(f"Значение BOT_TOKEN: {raw_token[:10]}...{raw_token[-5:] if len(raw_token)>15 else ''}")
    if not raw_token:
        print("❌ ОШИБКА: BOT_TOKEN пуст! Проверьте файл .env")
        return
    if " " in raw_token or "'" in raw_token or '"' in raw_token:
        print("⚠️ ПРЕДУПРЕЖДЕНИЕ: В токене обнаружены пробелы или кавычки! Очистите значение в .env")

    # 2. Проверка через getMe
    print_step("Шаг 2: Проверка getMe (Связь с Telegram)")
    me = tg_api("getMe")
    if me.get("ok"):
        bot_info = me["result"]
        print("✅ Токен ВАЛИДЕН!")
        print(f"🤖 Имя бота: {bot_info.get('first_name')}")
        print(f"👤 Username бота: @{bot_info.get('username')}")
        print(f"🆔 ID бота: {bot_info.get('id')}")
        print(f"👉 ВНИМАНИЕ: Убедитесь, что вы отправляете /start именно боту @{bot_info.get('username')}!")
    else:
        print("❌ ОШИБКА getMe:", me)
        if me.get("error_code") == 401:
            print("🚨 401 Unauthorized: Токен недействителен или был отозван в @BotFather!")
        return

    # 3. Проверка Webhook
    print_step("Шаг 3: Проверка Webhook (Конфликт с Long Polling)")
    wh = tg_api("getWebhookInfo")
    if wh.get("ok"):
        wh_info = wh["result"]
        wh_url = wh_info.get("url", "")
        pending = wh_info.get("pending_update_count", 0)
        print(f"Текущий Webhook URL: '{wh_url}'")
        print(f"Необработанных обновлений (Pending updates): {pending}")
        
        if wh_url:
            print("🚨 ОБНАРУЖЕН АКТИВНЫЙ WEBHOOK!")
            print("При установленном Webhook Telegram НЕ отправляет сообщения через Long Polling!")
            print("Сбрасываю Webhook...")
            del_wh = tg_api("deleteWebhook", {"drop_pending_updates": False})
            if del_wh.get("ok"):
                print("✅ Webhook успешно удален! Теперь Polling сможет получать сообщения.")
            else:
                print("❌ Не удалось удалить Webhook:", del_wh)
        else:
            print("✅ Webhook отключен (чистый режим Long Polling).")

    # 4. Проверка очереди обновлений getUpdates
    print_step("Шаг 4: Проверка входящих сообщений (getUpdates)")
    updates = tg_api("getUpdates", {"limit": 5})
    if updates.get("ok"):
        res = updates["result"]
        print(f"Получено апдейтов в очереди: {len(res)}")
        if res:
            for u in res:
                msg = u.get("message", {})
                from_u = msg.get("from", {})
                print(f"  • Update ID {u.get('update_id')}: от @{from_u.get('username')} (ID: {from_u.get('id')}): '{msg.get('text')}'")
        else:
            print("ℹ️ Очередь обновлений пуста. (Сообщения уже прочитаны или не отправлялись)")
    else:
        print("⚠️ Ошибка при запросе getUpdates:", updates)

    # 5. Проверка базы данных
    print_step("Шаг 5: Проверка SQLite БД")
    if DB_PATH.exists():
        print(f"✅ Файл базы данных найден: {DB_PATH}")
        print(f"📊 Размер БД: {DB_PATH.stat().st_size} байт")
    else:
        print(f"ℹ️ База данных еще не создана. Она инициализируется при запуске.")

    print("\n" + "=" * 60)
    print("✨ ДИАГНОСТИКА ЗАВЕРШЕНА!")
    print("=" * 60)

if __name__ == "__main__":
    run_diagnostics()
