import asyncio
import logging
import sys
import os
import socket
import subprocess
import re
import aiohttp

# Решение ошибки Windows WinError 121 / 1231 при работе с VPN/WARP: переключение на SelectorEventLoop
if sys.platform == "win32":
    try:
        import warnings
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramNetworkError

from config import BOT_TOKEN, ADMIN_IDS, is_owner_or_admin, DEFAULT_COOLDOWN_MINUTES, OWNER_USERNAMES
from database import (
    init_db, 
    upsert_user, 
    get_license_by_hwid, 
    save_license, 
    get_user_licenses, 
    get_stats,
    check_reissue_cooldown,
    reissue_license,
    deactivate_license,
    get_next_key_version,
    set_license_tier
)
from key_generator import is_valid_hwid, generate_key_for_hwid

# Решение проблемы кодировки символов и эмодзи на Windows консоли (cp1251 -> utf-8)
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logging.getLogger("aiogram.event").setLevel(logging.INFO)
logger = logging.getLogger("OptiCleanerBot")

def _detect_best_socket_family():
    """
    В РФ Telegram API (api.telegram.org) по IPv4 часто блокируется РКН (149.154.166.110).
    При этом IPv6 (2001:67c:4e8:f004::9) и WARP/VPN работают мгновенно и без задержек.
    Проверяем доступность IPv6: если он отвечает, форсируем AF_INET6 для обхода блокировок.
    """
    try:
        s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        s.settimeout(1.5)
        s.connect(('2001:67c:4e8:f004::9', 443))
        s.close()
        return socket.AF_INET6
    except Exception:
        return 0

best_family = _detect_best_socket_family()
bot_session = AiohttpSession()
if best_family != 0:
    bot_session._connector_init["family"] = best_family
    logger.info("IPv6 доступен — aiogram использует AF_INET6 для надежного обхода блокировок РКН.")
else:
    logger.info("aiogram использует стандартное семейство адресов (Auto/IPv4).")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN, session=bot_session)
dp = Dispatcher()


# ==============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ И ИНСТРУКЦИИ
# ==============================================================================

def extract_hwid(text: str) -> str:
    """
    Универсальное извлечение и нормализация HWID из любого текста:
    - OC-XXXX-XXXX-XXXX-XXXX
    - oc-xxxx-xxxx-xxxx-xxxx
    - XXXX-XXXX-XXXX-XXXX (без префикса OC-)
    """
    if not text or not isinstance(text, str):
        return ""
    text = text.strip()
    # 1. Поиск с префиксом OC-
    m1 = re.search(r'\bOC-([0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4})\b', text, re.IGNORECASE)
    if m1:
        return f"OC-{m1.group(1).upper()}"
    # 2. Поиск без префикса (4 шестнадцатеричных блока по 4 символа)
    m2 = re.search(r'\b([0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4})\b', text)
    if m2:
        return f"OC-{m2.group(1).upper()}"
    return ""


def make_start_text(user, is_owner: bool = False) -> tuple[str, types.InlineKeyboardMarkup]:
    """Главное приветственное меню бота"""
    greeting = (
        f"👑 <b>Здравствуйте, создатель @{user.username or 'oleg676725'}!</b>\n"
        "<i>Для вас включен безлимитный VIP-доступ PRO без кулдауна (0 сек).</i>\n\n"
    ) if is_owner else ""

    text = (
        f"{greeting}"
        "👋 <b>Добро пожаловать в официальный бот активации OptiCleaner!</b>\n\n"
        "Этот бот мгновенно генерирует и выдаёт лицензионные ключи, "
        "привязанные к аппаратному идентификатору вашего ПК (HWID).\n\n"
        "🚀 <b>Как получить ключ за 3 простых шага:</b>\n\n"
        "1️⃣ <b>Запустите OptiCleaner</b> на вашем компьютере (Windows или Linux).\n"
        "2️⃣ <b>В окне активации</b> нажмите синюю кнопку <b>«Открыть бота»</b>\n"
        "   <i>(Бот автоматически определит ваш ПК и сразу выдаст ключ!)</i>\n"
        "   <b>ИЛИ:</b> Нажмите «Скопировать» возле HWID и <b>отправьте код прямо в этот чат</b>.\n"
        "3️⃣ <b>Нажмите на выданный ключ</b> для копирования и вставьте его в окне программы.\n\n"
        "📌 <b>Тарифы программы:</b>\n"
        "💎 <b>BASE (Базовый)</b> — <i>100% бесплатно навсегда:</i>\n"
        "   • Экспресс и глубокая очистка дисков и кэша\n"
        "   • Мониторинг процессора, памяти, дисков и датчиков\n"
        "   • Диспетчер задач с заморозкой процессов\n"
        "   • Менеджер деинсталляции приложений\n\n"
        "👑 <b>PRO (Профессиональный)</b> — <i>Максимальная производительность:</i>\n"
        "   • Глубокая очистка и сжатие системного реестра\n"
        "   • Пакетное авто-обновление и резервирование драйверов\n"
        "   • Ультра-твики системы, отключение телеметрии и задержек\n"
        "   • Оптимизация оперативной памяти (Standby List) и SSD/NVMe\n\n"
        "👇 <b>Выберите действие в меню:</b>"
    )

    kb = InlineKeyboardBuilder()
    kb.button(text="📖 Подробная инструкция", callback_data="menu:guide")
    kb.button(text="❓ Частые вопросы (FAQ)", callback_data="menu:faq")
    kb.button(text="📋 Мои выданные ключи", callback_data="menu:mykey")
    kb.button(text="👑 Возможности тарифа PRO", callback_data="menu:pro")
    kb.button(text="💬 Написать автору @oleg676725", url="https://t.me/oleg676725")
    kb.adjust(2, 2, 1)

    return text, kb.as_markup()


def make_guide_text() -> str:
    """Полная подробная инструкция по активации"""
    return (
        "📖 <b>ПОДРОБНАЯ ИНСТРУКЦИЯ ПО АКТИВАЦИИ OPTICLEANER</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔹 <b>ШАГ 1: Что такое HWID и где его взять?</b>\n"
        "HWID (Hardware ID) — это уникальный идентификатор компонентов вашего ПК "
        "(материнская плата и системный накопитель). Он гарантирует безопасность вашей лицензии без логинов и паролей.\n\n"
        "1. Запустите приложение <b>OptiCleaner</b> на компьютере.\n"
        "2. В главном окне активации в первом блоке отобразится строка:\n"
        "   <b>«ВАШ АППАРАТНЫЙ ИДЕНТИФИКАТОР (HWID)»</b> вида:\n"
        "   <code>OC-XXXX-XXXX-XXXX-XXXX</code>\n"
        "3. Нажмите кнопку <b>«Скопировать»</b> справа от него.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔹 <b>ШАГ 2: Генерация лицензионного ключа</b>\n"
        "Есть два одинаково быстрых способа:\n"
        "• <b>Способ А (В 1 клик):</b> В окне OptiCleaner нажмите синюю кнопку <b>«Открыть бота»</b>. "
        "Бот откроется в Telegram с уже переданным HWID — ключ сгенерируется мгновенно!\n"
        "• <b>Способ Б:</b> Просто скопируйте HWID и отправьте его сообщением прямо в этот чат "
        "(например: <code>OC-9F2B-A1C8-73DE-8821</code>) или введите команду <code>/key &lt;HWID&gt;</code>.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔹 <b>ШАГ 3: Активация программы</b>\n"
        "1. Бот пришлёт вам ключ вида <code>BASE-XXXX-XXXX-XXXX-XXXX</code>.\n"
        "2. <b>Нажмите на строку с ключом</b> в сообщении — она автоматически скопируется в буфер.\n"
        "3. Вернитесь в программу OptiCleaner.\n"
        "4. Нажмите кнопку <b>«Вставить из буфера»</b> (или комбинацию клавиш <code>Ctrl + V</code>).\n"
        "5. Нажмите большую кнопку <b>«АКТИВИРОВАТЬ ЛИЦЕНЗИЮ»</b>.\n\n"
        "🎉 <i>Готово! Программа подтвердит подпись и сразу перейдёт к рабочему столу!</i>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔹 <b>РЕШЕНИЕ ВОЗМОЖНЫХ ОШИБОК:</b>\n"
        "• <i>«Ключ не соответствует сигнатуре»</i>: проверьте, что скопировали ключ полностью, "
        "включая префикс <code>BASE-</code> или <code>PRO-</code> и все 4 дефиса. "
        "Ключ работает строго на том компьютере, для которого он был сгенерирован!\n"
        "• <i>Сменили железо или переустановили систему?</i> Нажмите «Открыть бота» заново — "
        "бот сгенерирует новый ключ под обновленный профиль ПК."
    )


def make_faq_text() -> str:
    """Часто задаваемые вопросы"""
    return (
        "❓ <b>Часто задаваемые вопросы (FAQ)</b>\n\n"
        "<b>1. Платная ли базовая версия OptiCleaner?</b>\n"
        "💡 Нет! Базовый тариф <b>BASE</b> абсолютно бесплатен навсегда. "
        "Вам доступны очистка кэша и дисков, мониторинг железа, диспетчер задач и деинсталлятор без каких-либо оплат.\n\n"
        "<b>2. Зачем нужен HWID?</b>\n"
        "💡 HWID — аппаратный идентификатор материнской платы и системного диска. "
        "Он позволяет генерировать персональный криптографический ключ без необходимости ввода почты или паролей.\n\n"
        "<b>3. Можно ли активировать программу на нескольких компьютерах?</b>\n"
        "💡 Да! Каждый компьютер имеет свой собственный HWID. "
        "Запустите OptiCleaner на каждом ПК и нажмите «Открыть бота» — бот сгенерирует отдельный ключ для каждого устройства.\n\n"
        "<b>4. Как перевыпустить ключ, если я нажал «Выйти из аккаунта»?</b>\n"
        "💡 Просто отправьте ваш HWID в этот бот ещё раз или нажмите команду /reissue.\n\n"
        "<b>5. Есть ли кулдаун на перевыпуск ключа?</b>\n"
        "💡 В целях защиты от спама повторный перевыпуск базового ключа для одного и того же HWID доступен раз в 15 минут. "
        "Для создателя проекта (@oleg676725) кулдаун полностью отключен (0 секунд).\n\n"
        "<b>6. Что даёт тариф PRO и как его получить?</b>\n"
        "💡 Тариф PRO разблокирует глубокую очистку реестра, пакетное обновление драйверов, ультра-твики задержек и разгона. "
        "Для получения напишите создателю: @oleg676725."
    )


def make_pro_text() -> str:
    """Описание возможностей тарифа PRO"""
    return (
        "👑 <b>Тариф OptiCleaner PRO — Максимальная производительность</b>\n\n"
        "В версии PRO разблокированы профессиональные системные инструменты:\n\n"
        "🔥 <b>Глубокая очистка и оптимизация реестра</b>\n"
        "• Безопасное удаление недействительных веток, битых CLSID и устаревших записей MUI\n"
        "• Дефрагментация кустов реестра для ускорения отклика операционной системы\n\n"
        "🚀 <b>Пакетный менеджер и авто-обновление драйверов</b>\n"
        "• Автоматическое сканирование устаревших аппаратных драйверов\n"
        "• Резервное копирование и пакетная установка драйверов в один клик\n\n"
        "⚡ <b>Ультра-твики системы и снижение задержек (Latency Tweaks)</b>\n"
        "• Твики таймингов DPC и системного таймера (HPET / Platform Clock)\n"
        "• Отключение телеметрии, фоновых служб слежения и игровых задержек\n"
        "• Приоритезация процессов игр и профессионального софта\n\n"
        "🛡 <b>Интеллектуальная оптимизация SSD/NVMe и RAM</b>\n"
        "• Сброс кэша Standby List оперативной памяти в реальном времени\n"
        "• Форсированный TRIM и тонкая настройка очереди ввода-вывода (I/O)\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💎 Для перехода на PRO обратитесь к автору проекта: @oleg676725"
    )


async def send_license_card(
    message: types.Message, 
    hwid: str, 
    key: str, 
    tier: str, 
    is_owner: bool, 
    title: str = "Лицензия готова к активации!"
):
    """
    Красивое оформление карточки с лицензионным ключом
    """
    kb = InlineKeyboardBuilder()
    if is_owner:
        kb.button(text="👑 Перевыпустить PRO (0 сек)", callback_data=f"reissue_pro:{hwid}")
        kb.button(text="💎 Перевыпустить BASE (0 сек)", callback_data=f"reissue_base:{hwid}")
        kb.button(text="🚪 Деактивировать", callback_data=f"deact:{hwid}")
        tier_badge = "👑 <b>Тариф: PRO</b> <i>(Создатель @oleg676725 — Безлимитный доступ навсегда)</i>"
    else:
        kb.button(text="🔄 Перевыпустить ключ BASE", callback_data=f"reissue_base:{hwid}")
        kb.button(text="👑 Запросить PRO у @oleg676725", url="https://t.me/oleg676725")
        kb.button(text="🚪 Деактивировать", callback_data=f"deact:{hwid}")
        tier_badge = (
            "👑 <b>Тариф: PRO</b> <i>(Полный доступ без ограничений)</i>" 
            if tier == "PRO" else 
            "💎 <b>Тариф: BASE</b> <i>(Базовый тариф — Бесплатно навсегда)</i>"
        )
    
    kb.button(text="📖 Подробная инструкция", callback_data="menu:guide")
    kb.button(text="❓ Частые вопросы (FAQ)", callback_data="menu:faq")
    kb.button(text="◀️ В главное меню", callback_data="menu:main")
    kb.adjust(1)

    text = (
        f"🎉 <b>{title}</b>\n\n"
        f"🖥 <b>Ваш HWID (Идентификатор ПК):</b>\n<code>{hwid}</code>\n\n"
        f"🔑 <b>Лицензионный ключ:</b>\n<code>{key}</code>\n"
        "<i>👆 Нажмите на строку с ключом выше, чтобы мгновенно скопировать её в буфер!</i>\n\n"
        f"{tier_badge}\n\n"
        "⚡ <b>Как активировать OptiCleaner:</b>\n"
        "1️⃣ Нажмите на ключ выше для копирования.\n"
        "2️⃣ Перейдите в окно программы <b>OptiCleaner</b> на компьютере.\n"
        "3️⃣ Нажмите кнопку <b>«Вставить из буфера»</b> (или сочетание <code>Ctrl + V</code>).\n"
        "4️⃣ Нажмите большую кнопку <b>«АКТИВИРОВАТЬ ЛИЦЕНЗИЮ»</b>.\n\n"
        "✨ <i>Программа мгновенно перейдёт к работе со всеми функциями!</i>"
    )

    await message.answer(text, reply_markup=kb.as_markup(), parse_mode=ParseMode.HTML)


async def process_hwid_request(message: types.Message, hwid: str, user, is_owner: bool):
    """
    Централизованная генерация/выдача лицензионного ключа по HWID
    """
    logger.info(f"Processing HWID: {hwid} for user {user.id} (@{user.username}) [is_owner={is_owner}]")

    if not is_valid_hwid(hwid):
        await message.answer(
            "⚠️ <b>Некорректный формат HWID!</b>\n\n"
            f"Получен идентификатор: <code>{hwid}</code>\n\n"
            "HWID должен начинаться с <b>OC-</b> и содержать 4 блока шестнадцатеричных символов:\n"
            "<code>OC-XXXX-XXXX-XXXX-XXXX</code>\n\n"
            "💡 <b>Как отправить правильно:</b>\n"
            "1. Запустите <b>OptiCleaner</b> на вашем компьютере.\n"
            "2. Нажмите кнопку <b>«Скопировать»</b> рядом со строкой HWID.\n"
            "3. Отправьте скопированный код сюда в чат.",
            parse_mode=ParseMode.HTML
        )
        return

    # Проверка существующей лицензии
    existing = await get_license_by_hwid(hwid)
    if existing:
        status = existing.get("status", "active")
        key = existing["license_key"]
        created = existing["created_at"]
        tier = existing.get("tier", "PRO" if is_owner else "BASE")
        is_revoked = existing.get("is_revoked", 0)

        # СЛУЧАЙ А: Ключ отозван / деактивирован пользователем (выход из аккаунта)
        if status == "revoked" or is_revoked == 1:
            logger.info(f"User {user.id} requested reissue for revoked HWID: {hwid}")
            can_reissue, remaining_sec, last_time = await check_reissue_cooldown(hwid, user.id, username=user.username)
            
            if not can_reissue:
                mins = remaining_sec // 60
                secs = remaining_sec % 60
                logger.warning(f"Cooldown hit for HWID {hwid}: {mins}m {secs}s remaining")
                await message.answer(
                    "⏳ <b>Ограничение по частоте перевыпуска ключа!</b>\n\n"
                    f"🖥 <b>Ваш HWID:</b> <code>{hwid}</code>\n"
                    f"🔑 <b>Предыдущий ключ:</b> <code>{key}</code> <i>(отозван)</i>\n\n"
                    f"🛡 <i>В целях безопасности повторный перевыпуск лицензии разрешён не чаще 1 раза в {DEFAULT_COOLDOWN_MINUTES} минут.</i>\n\n"
                    f"Следующий перевыпуск будет доступен через: <b>{mins} мин. {secs} сек.</b>\n\n"
                    "Для срочной помощи или подключения тарифа PRO напишите @oleg676725.",
                    parse_mode=ParseMode.HTML
                )
                return

            target_tier = "PRO" if is_owner else tier
            new_key, version = await reissue_license(hwid, user.id, tier=target_tier)
            logger.info(f"Reissued new license v{version} for HWID {hwid} -> {new_key} (Tier: {target_tier})")
            
            await send_license_card(
                message, 
                hwid, 
                new_key, 
                target_tier, 
                is_owner, 
                title="Вам выдан новый лицензионный ключ!"
            )
            return

        # СЛУЧАЙ Б: Ключ развязан
        if status == "unbound":
            from database import _get_conn, _sync_log_action
            from datetime import datetime
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with _get_conn() as db:
                db.execute(
                    "UPDATE licenses SET hwid = ?, status = 'active', is_activated = 1, updated_at = ? WHERE id = ?",
                    (hwid, now, existing["id"])
                )
                db.commit()
            _sync_log_action("bot", "REBIND_KEY", hwid, f"Key {key} rebound to user {user.id}")
            logger.info(f"Unbound key rebound to HWID: {hwid} -> {key}")
            await send_license_card(
                message, 
                hwid, 
                key, 
                tier, 
                is_owner, 
                title="Лицензия успешно привязана к компьютеру!"
            )
            return

        # СЛУЧАЙ В: Активный ключ уже существует
        logger.info(f"Existing active key returned for HWID: {hwid} -> {key}")
        await send_license_card(
            message, 
            hwid, 
            key, 
            tier, 
            is_owner, 
            title="Для данного компьютера уже действует лицензия:"
        )
        return

    # СЛУЧАЙ Г: Создание новой лицензии
    version = await get_next_key_version(hwid)
    assigned_tier = "PRO" if is_owner else "BASE"
    key = generate_key_for_hwid(hwid, version=version, tier=assigned_tier)
    await save_license(hwid, key, user.id, tier=assigned_tier, version=version)
    logger.info(f"New license generated (v{version}) for HWID: {hwid} -> {key} [Tier: {assigned_tier}]")

    await send_license_card(
        message, 
        hwid, 
        key, 
        assigned_tier, 
        is_owner, 
        title="Лицензия успешно сгенерирована!"
    )


async def show_user_licenses(message: types.Message, user):
    """Отображение всех лицензий пользователя"""
    licenses = await get_user_licenses(user.id)

    kb = InlineKeyboardBuilder()
    kb.button(text="📖 Подробная инструкция", callback_data="menu:guide")
    kb.button(text="❓ Частые вопросы (FAQ)", callback_data="menu:faq")
    kb.button(text="◀️ В главное меню", callback_data="menu:main")
    kb.adjust(2, 1)

    if not licenses:
        await message.answer(
            "🔍 <b>У вас пока нет сгенерированных лицензий.</b>\n\n"
            "Чтобы получить ключ, запустите OptiCleaner и нажмите кнопку "
            "«<b>Открыть бота</b>» или пришлите ваш HWID сюда в чат!",
            reply_markup=kb.as_markup(),
            parse_mode=ParseMode.HTML
        )
        return

    text = "📋 <b>Ваши лицензионные ключи OptiCleaner:</b>\n\n"
    for idx, row in enumerate(licenses, 1):
        status = row.get("status", "active")
        status_badge = "✅ Активен"
        if status == "revoked":
            status_badge = "⛔ Отозван"
        elif status == "unbound":
            status_badge = "🔓 Развязан"

        t_val = str(row.get("tier", "BASE")).upper()
        t_badge = "👑 <b>PRO</b> (Полный доступ)" if t_val == "PRO" else "💎 <b>BASE</b> (Базовый)"

        text += (
            f"<b>#{idx}</b>\n"
            f"🖥 HWID: <code>{row['hwid']}</code>\n"
            f"🔑 Ключ: <code>{row['license_key']}</code>\n"
            f"Тариф: {t_badge}\n"
            f"📊 Статус: {status_badge}\n"
            f"📅 Дата: <i>{row['created_at']}</i>\n\n"
        )

    await message.answer(text, reply_markup=kb.as_markup(), parse_mode=ParseMode.HTML)


# ==============================================================================
# ОБРАБОТЧИКИ КОМАНД
# ==============================================================================

@dp.message(CommandStart())
async def handle_start_command(message: types.Message, command: CommandObject):
    """
    Обработка команды /start:
    - С аргументом HWID (deep-link): мгновенная генерация/выдача лицензии
    - Без аргумента: интерактивное главное меню
    """
    user = message.from_user
    args = (command.args or "").strip()
    is_owner = is_owner_or_admin(user=user)
    logger.info(f"⚡ [COMMAND] /start received from @{user.username} (ID: {user.id}) [Owner/Admin: {is_owner}] | args: '{args}'")

    try:
        await upsert_user(user.id, user.username, user.first_name)
    except Exception as e:
        logger.error(f"Error saving user to DB: {e}")

    # 1. Если передан аргумент HWID (через deep-link: /start OC-XXXX-XXXX-XXXX-XXXX)
    if args:
        hwid = extract_hwid(args)
        if hwid:
            await process_hwid_request(message, hwid, user, is_owner)
            return
        else:
            await message.answer(
                "⚠️ <b>Некорректный формат HWID!</b>\n\n"
                f"Получен идентификатор: <code>{args}</code>\n"
                "HWID должен начинаться с <b>OC-</b> и иметь вид: <code>OC-XXXX-XXXX-XXXX-XXXX</code>\n\n"
                "Запустите OptiCleaner и нажмите кнопку «<b>Открыть бота</b>» повторно.",
                parse_mode=ParseMode.HTML
            )
            return

    # 2. Обычный запуск без аргументов
    text, kb = make_start_text(user, is_owner)
    await message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)


@dp.message(Command("key"))
@dp.message(Command("activate"))
async def handle_key_command(message: types.Message, command: CommandObject):
    """Ручная генерация/получение ключа через /key <HWID>"""
    user = message.from_user
    args = (command.args or "").strip()
    is_owner = is_owner_or_admin(user=user)

    if not args:
        await message.answer(
            "🔑 <b>Использование:</b> <code>/key OC-XXXX-XXXX-XXXX-XXXX</code>\n\n"
            "Скопируйте ваш HWID в окне OptiCleaner и отправьте его вместе с командой:\n"
            "Пример: <code>/key OC-A1B2-C3D4-E5F6-7890</code>\n\n"
            "<i>(Или просто отправьте HWID отдельным сообщением в чат)</i>",
            parse_mode=ParseMode.HTML
        )
        return

    hwid = extract_hwid(args)
    if not hwid:
        await message.answer(
            "⚠️ <b>Некорректный HWID!</b>\n"
            "Формат: <code>OC-XXXX-XXXX-XXXX-XXXX</code>",
            parse_mode=ParseMode.HTML
        )
        return

    await process_hwid_request(message, hwid, user, is_owner)


@dp.message(Command("help"))
@dp.message(Command("guide"))
@dp.message(Command("instruction"))
@dp.message(Command("instructions"))
async def handle_help_command(message: types.Message):
    """Подробная пошаговая справка по активации"""
    kb = InlineKeyboardBuilder()
    kb.button(text="❓ Частые вопросы (FAQ)", callback_data="menu:faq")
    kb.button(text="📋 Мои ключи", callback_data="menu:mykey")
    kb.button(text="◀️ В главное меню", callback_data="menu:main")
    kb.adjust(2, 1)

    await message.answer(make_guide_text(), reply_markup=kb.as_markup(), parse_mode=ParseMode.HTML)


@dp.message(Command("faq"))
async def handle_faq_command(message: types.Message):
    """Часто задаваемые вопросы"""
    kb = InlineKeyboardBuilder()
    kb.button(text="📖 Подробная инструкция", callback_data="menu:guide")
    kb.button(text="👑 Возможности тарифа PRO", callback_data="menu:pro")
    kb.button(text="◀️ В главное меню", callback_data="menu:main")
    kb.adjust(2, 1)

    await message.answer(make_faq_text(), reply_markup=kb.as_markup(), parse_mode=ParseMode.HTML)


@dp.message(Command("pro"))
async def handle_pro_command(message: types.Message):
    """Информация о тарифе PRO"""
    kb = InlineKeyboardBuilder()
    kb.button(text="💬 Написать автору @oleg676725", url="https://t.me/oleg676725")
    kb.button(text="📖 Подробная инструкция", callback_data="menu:guide")
    kb.button(text="◀️ В главное меню", callback_data="menu:main")
    kb.adjust(1, 2)

    await message.answer(make_pro_text(), reply_markup=kb.as_markup(), parse_mode=ParseMode.HTML)


@dp.message(Command("mykey"))
async def handle_my_key_command(message: types.Message):
    """Просмотр всех ключей пользователя"""
    await show_user_licenses(message, message.from_user)


@dp.message(Command("reissue"))
async def handle_reissue_command(message: types.Message):
    """Команда /reissue для ручного перевыпуска"""
    user = message.from_user
    is_owner = is_owner_or_admin(user=user)
    licenses = await get_user_licenses(user.id)
    if not licenses:
        await message.answer(
            "🔍 У вас пока нет сгенерированных лицензий для перевыпуска.\n"
            "Запустите OptiCleaner и пришлите HWID для получения первого ключа.",
            parse_mode=ParseMode.HTML
        )
        return

    active_lic = [l for l in licenses if l.get("status") == "active"]
    target = active_lic[0] if active_lic else licenses[0]
    hwid = target["hwid"]

    can_reissue, remaining_sec, last_time = await check_reissue_cooldown(hwid, user.id, username=user.username)
    if not can_reissue:
        mins = remaining_sec // 60
        secs = remaining_sec % 60
        await message.answer(
            f"⏳ <b>Кулдаун {DEFAULT_COOLDOWN_MINUTES} минут!</b>\n\n"
            f"Следующий перевыпуск для HWID <code>{hwid}</code> доступен через: <b>{mins} мин. {secs} сек.</b>\n\n"
            "Для перехода на PRO напишите @oleg676725.",
            parse_mode=ParseMode.HTML
        )
        return

    target_tier = target.get("tier", "BASE") if target else ("PRO" if is_owner else "BASE")
    new_key, version = await reissue_license(hwid, user.id, tier=target_tier)
    await send_license_card(
        message, 
        hwid, 
        new_key, 
        target_tier, 
        is_owner, 
        title="Новый лицензионный ключ выпущен!"
    )


@dp.message(Command("deactivate"))
async def handle_deactivate_command(message: types.Message):
    """Команда /deactivate для отзыва лицензии"""
    user = message.from_user
    licenses = await get_user_licenses(user.id)
    active_lic = [l for l in licenses if l.get("status") == "active"]
    if not active_lic:
        await message.answer("ℹ️ У вас нет активных лицензий для деактивации.")
        return

    for l in active_lic:
        await deactivate_license(l["hwid"], l["license_key"], reason="tg_command_deactivate")

    await message.answer(
        "⛔ <b>Все ваши активные лицензии деактивированы.</b>\n\n"
        "Чтобы получить новый ключ, отправьте HWID через /start при необходимости.",
        parse_mode=ParseMode.HTML
    )


# ==============================================================================
# АДМИНИСТРАТИВНЫЕ КОМАНДЫ
# ==============================================================================

@dp.message(Command("stats"))
async def handle_admin_stats(message: types.Message):
    """Административная статистика"""
    if message.from_user.id not in ADMIN_IDS and ADMIN_IDS and not is_owner_or_admin(user=message.from_user):
        return

    stats = await get_stats()
    await message.answer(
        "📊 <b>Детальная статистика OptiCleaner:</b>\n\n"
        f"👥 Зарегистрировано пользователей: <b>{stats['users']}</b>\n"
        f"🔑 Всего активных лицензий: <b>{stats['licenses']}</b>\n"
        f"✅ Со статусом Active: <b>{stats.get('active', 0)}</b>\n"
        f"⛔ Отозванных (Revoked): <b>{stats.get('revoked', 0)}</b>\n"
        f"🔓 Отвязанных (Unbound): <b>{stats.get('unbound', 0)}</b>\n"
        f"📦 В архиве (Удаленных): <b>{stats.get('archived', 0)}</b>",
        parse_mode=ParseMode.HTML
    )


@dp.message(Command("gen_pro"))
async def handle_gen_pro_cmd(message: types.Message):
    """Выдача подписки PRO администратором"""
    user = message.from_user
    if user.id not in ADMIN_IDS and ADMIN_IDS and not is_owner_or_admin(user=user):
        await message.answer("⛔ Данная команда доступна только администраторам.")
        return

    parts = message.text.strip().split()
    if len(parts) < 2:
        await message.answer(
            "⚠️ <b>Использование:</b> <code>/gen_pro OC-XXXX-XXXX-XXXX-XXXX</code>\n\n"
            "Команда повышает тариф лицензии до <b>PRO</b>.",
            parse_mode=ParseMode.HTML
        )
        return

    hwid = extract_hwid(parts[1].strip())
    if not is_valid_hwid(hwid):
        await message.answer("⚠️ Неверный формат HWID! Должен быть <code>OC-XXXX-XXXX-XXXX-XXXX</code>", parse_mode=ParseMode.HTML)
        return

    existing = await get_license_by_hwid(hwid)
    if existing:
        await set_license_tier(hwid, "PRO", admin_user=f"admin_{user.id}")
        await message.answer(
            f"👑 <b>Тариф успешно повышен до PRO!</b>\n\n"
            f"🖥 <b>HWID:</b> <code>{hwid}</code>\n"
            f"🔑 <b>Ключ:</b> <code>{existing['license_key']}</code>\n"
            "💎 <b>Тариф:</b> PRO (Полный доступ бессрочно)\n\n"
            "Пользователь получил 100% доступ ко всем функциям OptiCleaner.",
            parse_mode=ParseMode.HTML
        )
    else:
        version = await get_next_key_version(hwid)
        key = generate_key_for_hwid(hwid, version=version, tier="PRO")
        await save_license(hwid, key, user.id, tier="PRO", version=version)
        await message.answer(
            f"👑 <b>Создана новая лицензия PRO администратором!</b>\n\n"
            f"🖥 <b>HWID:</b> <code>{hwid}</code>\n"
            f"🔑 <b>Лицензионный ключ:</b> <code>{key}</code>\n"
            "💎 <b>Тариф:</b> PRO (Полный доступ бессрочно)\n\n"
            "Передайте этот ключ пользователю для активации.",
            parse_mode=ParseMode.HTML
        )


@dp.message(Command("set_tier"))
async def handle_set_tier_cmd(message: types.Message):
    """Смена тарифа администратором"""
    user = message.from_user
    if user.id not in ADMIN_IDS and ADMIN_IDS and not is_owner_or_admin(user=user):
        await message.answer("⛔ Доступно только администраторам.")
        return

    parts = message.text.strip().split()
    if len(parts) < 3:
        await message.answer("⚠️ Использование: <code>/set_tier &lt;HWID&gt; &lt;BASE|PRO&gt;</code>", parse_mode=ParseMode.HTML)
        return

    hwid = extract_hwid(parts[1].strip())
    target_tier = parts[2].strip().upper()
    if target_tier not in ("BASE", "PRO"):
        await message.answer("⚠️ Тариф должен быть <b>BASE</b> или <b>PRO</b>", parse_mode=ParseMode.HTML)
        return

    await set_license_tier(hwid, target_tier, admin_user=f"admin_{user.id}")
    badge = "👑 PRO" if target_tier == "PRO" else "💎 BASE"
    await message.answer(
        f"✅ <b>Тариф успешно обновлен!</b>\n\n"
        f"🖥 HWID: <code>{hwid}</code>\n"
        f"Статус подписки: <b>{badge}</b>",
        parse_mode=ParseMode.HTML
    )


# ==============================================================================
# ОБРАБОТЧИКИ CALLBACK QUERY
# ==============================================================================

@dp.callback_query(F.data.startswith("menu:"))
async def handle_menu_callbacks(callback: types.CallbackQuery):
    """Обработка навигационных кнопок интерактивного меню"""
    action = callback.data.split(":", 1)[1]
    user = callback.from_user
    is_owner = is_owner_or_admin(user=user)

    if action == "main":
        text, kb = make_start_text(user, is_owner)
        try:
            await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
        except Exception:
            await callback.message.answer(text, reply_markup=kb, parse_mode=ParseMode.HTML)
        await callback.answer()

    elif action == "guide":
        kb = InlineKeyboardBuilder()
        kb.button(text="❓ Частые вопросы (FAQ)", callback_data="menu:faq")
        kb.button(text="📋 Мои ключи", callback_data="menu:mykey")
        kb.button(text="◀️ В главное меню", callback_data="menu:main")
        kb.adjust(2, 1)
        text = make_guide_text()
        try:
            await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode=ParseMode.HTML)
        except Exception:
            await callback.message.answer(text, reply_markup=kb.as_markup(), parse_mode=ParseMode.HTML)
        await callback.answer()

    elif action == "faq":
        kb = InlineKeyboardBuilder()
        kb.button(text="📖 Подробная инструкция", callback_data="menu:guide")
        kb.button(text="👑 Возможности тарифа PRO", callback_data="menu:pro")
        kb.button(text="◀️ В главное меню", callback_data="menu:main")
        kb.adjust(2, 1)
        text = make_faq_text()
        try:
            await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode=ParseMode.HTML)
        except Exception:
            await callback.message.answer(text, reply_markup=kb.as_markup(), parse_mode=ParseMode.HTML)
        await callback.answer()

    elif action == "pro":
        kb = InlineKeyboardBuilder()
        kb.button(text="💬 Написать автору @oleg676725", url="https://t.me/oleg676725")
        kb.button(text="📖 Подробная инструкция", callback_data="menu:guide")
        kb.button(text="◀️ В главное меню", callback_data="menu:main")
        kb.adjust(1, 2)
        text = make_pro_text()
        try:
            await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode=ParseMode.HTML)
        except Exception:
            await callback.message.answer(text, reply_markup=kb.as_markup(), parse_mode=ParseMode.HTML)
        await callback.answer()

    elif action == "mykey":
        await callback.answer()
        await show_user_licenses(callback.message, user)


@dp.callback_query(F.data.startswith("reissue_pro:"))
async def handle_callback_reissue_pro(callback: types.CallbackQuery):
    """Перевыпуск PRO ключа"""
    hwid = callback.data.split(":", 1)[1].strip().upper()
    user = callback.from_user
    is_owner = is_owner_or_admin(user=user)
    logger.info(f"User {user.id} clicked reissue PRO for HWID: {hwid} (is_owner={is_owner})")

    if not is_owner:
        await callback.answer(
            "👑 Тариф PRO выдается администратором @oleg676725. Напишите ему в Telegram для получения PRO!", 
            show_alert=True
        )
        return

    new_key, version = await reissue_license(hwid, user.id, tier="PRO")
    await callback.answer("👑 Новый ключ PRO сгенерирован мгновенно (0 сек КД)!", show_alert=False)
    await send_license_card(
        callback.message, 
        hwid, 
        new_key, 
        "PRO", 
        is_owner, 
        title="Лицензия PRO успешно перевыпущена!"
    )


@dp.callback_query(F.data.startswith("reissue_base:"))
async def handle_callback_reissue_base(callback: types.CallbackQuery):
    """Перевыпуск BASE ключа"""
    hwid = callback.data.split(":", 1)[1].strip().upper()
    user = callback.from_user
    is_owner = is_owner_or_admin(user=user)
    logger.info(f"User {user.id} clicked reissue BASE for HWID: {hwid} (is_owner={is_owner})")

    can_reissue, remaining_sec, last_time = await check_reissue_cooldown(hwid, user.id, username=user.username)
    if not can_reissue:
        mins = remaining_sec // 60
        secs = remaining_sec % 60
        await callback.answer(
            f"⏳ Кулдаун {DEFAULT_COOLDOWN_MINUTES} мин! Доступно через {mins}м {secs}с.", 
            show_alert=True
        )
        return

    new_key, version = await reissue_license(hwid, user.id, tier="BASE")
    await callback.answer("💎 Новый ключ BASE сгенерирован!", show_alert=False)
    await send_license_card(
        callback.message, 
        hwid, 
        new_key, 
        "BASE", 
        is_owner, 
        title="Лицензия BASE успешно перевыпущена!"
    )


@dp.callback_query(F.data.startswith("reissue:"))
async def handle_callback_reissue(callback: types.CallbackQuery):
    """Универсальный перевыпуск ключа"""
    hwid = callback.data.split(":", 1)[1].strip().upper()
    user = callback.from_user
    is_owner = is_owner_or_admin(user=user)

    can_reissue, remaining_sec, last_time = await check_reissue_cooldown(hwid, user.id, username=user.username)
    if not can_reissue:
        mins = remaining_sec // 60
        secs = remaining_sec % 60
        await callback.answer(f"⏳ Кулдаун {DEFAULT_COOLDOWN_MINUTES}м! Доступно через {mins}м {secs}с", show_alert=True)
        return

    existing = await get_license_by_hwid(hwid)
    target_tier = existing.get("tier", "BASE") if existing else ("PRO" if is_owner else "BASE")

    new_key, version = await reissue_license(hwid, user.id, tier=target_tier)
    await callback.answer("✅ Новый ключ сгенерирован!", show_alert=False)
    await send_license_card(
        callback.message, 
        hwid, 
        new_key, 
        target_tier, 
        is_owner, 
        title="Лицензия успешно перевыпущена!"
    )


@dp.callback_query(F.data.startswith("deact:"))
async def handle_callback_deactivate(callback: types.CallbackQuery):
    """Деактивация ключа"""
    hwid = callback.data.split(":", 1)[1].strip().upper()
    user = callback.from_user
    logger.info(f"User {user.id} requested deactivation for HWID: {hwid}")

    await deactivate_license(hwid, reason="tg_button_logout")
    await callback.answer("⛔ Лицензия деактивирована!", show_alert=True)

    kb = InlineKeyboardBuilder()
    kb.button(text="🔄 Получить новый ключ", callback_data=f"reissue_base:{hwid}")
    kb.button(text="◀️ В главное меню", callback_data="menu:main")
    kb.adjust(1)

    await callback.message.answer(
        "⛔ <b>Лицензия успешно отозвана!</b>\n\n"
        f"🖥 HWID: <code>{hwid}</code>\n\n"
        "Ключ деактивирован. Чтобы получить новый ключ, нажмите кнопку ниже или отправьте HWID повторно.",
        reply_markup=kb.as_markup(),
        parse_mode=ParseMode.HTML
    )


# ==============================================================================
# ПЕРЕХВАТ ТЕКСТОВЫХ СООБЩЕНИЙ (АВТОРАСПОЗНАВАНИЕ HWID)
# ==============================================================================

@dp.message()
async def handle_fallback_message(message: types.Message):
    """
    Перехват любых текстовых сообщений:
    1. Если пользователь прислал HWID -> мгновенно сгенерировать и выдать ключ!
    2. Если произвольный текст -> показать понятную подсказку с кнопками.
    """
    user = message.from_user
    text = (message.text or "").strip()
    is_owner = is_owner_or_admin(user=user)
    logger.info(f"📨 Incoming text from @{user.username} (ID: {user.id}): '{text}'")

    try:
        await upsert_user(user.id, user.username, user.first_name)
    except Exception:
        pass

    # 1. Проверяем наличие HWID в сообщении пользователя
    found_hwid = extract_hwid(text)
    if found_hwid and is_valid_hwid(found_hwid):
        logger.info(f"Auto-detected valid HWID '{found_hwid}' in user message.")
        await process_hwid_request(message, found_hwid, user, is_owner)
        return

    # 2. Если HWID не распознан, даем дружелюбную подсказку и меню
    kb = InlineKeyboardBuilder()
    kb.button(text="📖 Подробная инструкция", callback_data="menu:guide")
    kb.button(text="❓ Частые вопросы (FAQ)", callback_data="menu:faq")
    kb.button(text="📋 Мои лицензии", callback_data="menu:mykey")
    kb.button(text="👑 Возможности тарифа PRO", callback_data="menu:pro")
    kb.button(text="◀️ В главное меню", callback_data="menu:main")
    kb.adjust(2, 2, 1)

    await message.answer(
        "ℹ️ <b>Я получил ваше сообщение!</b>\n\n"
        "💡 <b>Чтобы получить лицензионный ключ:</b>\n"
        "1. Запустите <b>OptiCleaner</b> на компьютере.\n"
        "2. Нажмите кнопку <b>«Скопировать»</b> рядом со строкой HWID.\n"
        "3. Пришлите сюда скопированный код вида <code>OC-XXXX-XXXX-XXXX-XXXX</code>.\n\n"
        "Или воспользуйтесь разделами меню ниже:",
        reply_markup=kb.as_markup(),
        parse_mode=ParseMode.HTML
    )


# ==============================================================================
# ЗАПУСК И СЕТЕВОЙ МОНИТОРИНГ
# ==============================================================================

def ensure_network_online():
    """Проверяет доступность Cloudflare WARP и при необходимости включает его."""
    warp_cli = r"C:\Program Files\Cloudflare\Cloudflare WARP\warp-cli.exe"
    if os.path.isfile(warp_cli):
        try:
            res = subprocess.run([warp_cli, "status"], capture_output=True, text=True, timeout=3)
            if "Disconnected" in res.stdout:
                logger.warning("Cloudflare WARP отключен. Автоматически подключаем WARP для обхода блокировок Telegram API...")
                subprocess.run([warp_cli, "connect"], capture_output=True, text=True, timeout=5)
        except Exception as e:
            logger.debug(f"WARP check error: {e}")

async def main():
    logger.info("Starting OptiCleaner Telegram Bot (@analystSub_bot)...")
    await init_db()
    logger.info("Database initialized successfully.")
    
    ensure_network_online()
    
    # Рекурсивный цикл автоматического восстановления соединения
    retry_delay = 3
    while True:
        try:
            logger.info("Connecting to Telegram API...")
            await bot.delete_webhook(drop_pending_updates=False)

            # Регистрация меню команд в Telegram
            try:
                await bot.set_my_commands([
                    types.BotCommand(command="start", description="🚀 Главное меню / Активация"),
                    types.BotCommand(command="help", description="📖 Подробная пошаговая инструкция"),
                    types.BotCommand(command="key", description="🔑 Получить ключ по HWID"),
                    types.BotCommand(command="mykey", description="📋 Мои выданные лицензии"),
                    types.BotCommand(command="faq", description="❓ Частые вопросы и ответы"),
                    types.BotCommand(command="pro", description="👑 Преимущества тарифа PRO"),
                    types.BotCommand(command="reissue", description="🔄 Перевыпустить ключ"),
                ])
                logger.info("Registered bot commands in Telegram successfully.")
            except Exception as e:
                logger.warning(f"Could not register commands with Telegram: {e}")

            logger.info("Polling started! Waiting for messages...")
            retry_delay = 3
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
            break
        except (TelegramNetworkError, aiohttp.ClientError, OSError) as e:
            logger.warning(
                f"⚠️ Ошибка сети при связи с Telegram: {e}.\n"
                f"Подсказка: Проверьте интернет или убедитесь, что включен Cloudflare WARP/VPN.\n"
                f"Повторное подключение через {retry_delay} сек..."
            )
            ensure_network_online()
            await asyncio.sleep(retry_delay)
            retry_delay = min(30, int(retry_delay * 1.5))
        except Exception as e:
            logger.error(f"Непредвиденная ошибка в боте: {e}. Повтор через 5 сек...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
