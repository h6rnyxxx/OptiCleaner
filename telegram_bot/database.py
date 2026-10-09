import sqlite3
import asyncio
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from config import DB_PATH, BACKUP_DIR, ADMIN_LOG_PATH

def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _ensure_dirs():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if not ADMIN_LOG_PATH.parent.exists():
        ADMIN_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

def _sync_log_action(admin_user: str, action: str, target_hwid: str = None, details: str = None):
    """Запись действия администратора в SQLite и в файл admin_log.txt"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _ensure_dirs()
    
    # 1. Запись в SQLite
    try:
        with _get_conn() as db:
            db.execute("""
                INSERT INTO admin_audit_log (timestamp, admin_user, action, target_hwid, details)
                VALUES (?, ?, ?, ?, ?)
            """, (now, admin_user or "admin", action, target_hwid or "-", details or "-"))
            db.commit()
    except Exception as e:
        print(f"Warning: Failed to log action to SQLite: {e}")

    # 2. Запись в текстовый файл admin_log.txt
    try:
        log_line = f"[{now}] [ADMIN: {admin_user or 'admin'}] ACTION: {action} | HWID: {target_hwid or '-'} | {details or '-'}\n"
        with open(ADMIN_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception as e:
        print(f"Warning: Failed to append to admin_log.txt: {e}")

def _sync_create_backup() -> str:
    """Создание резервной копии базы данных перед деструктивными операциями"""
    _ensure_dirs()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_file = BACKUP_DIR / f"licenses_backup_{timestamp}.db"
    
    # Используем atomic SQLite online backup API
    with _get_conn() as src_conn:
        with sqlite3.connect(backup_file) as dst_conn:
            src_conn.backup(dst_conn)
            
    # Ротация: оставляем последние 30 бэкапов
    try:
        backups = sorted(BACKUP_DIR.glob("licenses_backup_*.db"), key=lambda p: p.stat().st_mtime)
        if len(backups) > 30:
            for old in backups[:-30]:
                old.unlink(missing_ok=True)
    except Exception:
        pass
        
    return str(backup_file)

def _sync_init_db():
    _ensure_dirs()
    with _get_conn() as db:
        # Таблица пользователей Telegram
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                first_seen TEXT
            )
        """)
        
        # Основная таблица активных лицензий
        db.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hwid TEXT NOT NULL,
                license_key TEXT UNIQUE NOT NULL,
                telegram_id INTEGER,
                created_at TEXT NOT NULL,
                is_activated INTEGER DEFAULT 0,
                tier TEXT DEFAULT 'PRO',
                status TEXT DEFAULT 'active',
                key_version INTEGER DEFAULT 1,
                revoked_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
            )
        """)

        # Таблица архива / удаленных лицензий (для восстановления Undo и версионирования)
        db.execute("""
            CREATE TABLE IF NOT EXISTS licenses_archive (
                archive_id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_id INTEGER,
                hwid TEXT NOT NULL,
                license_key TEXT NOT NULL,
                telegram_id INTEGER,
                tier TEXT,
                status TEXT,
                key_version INTEGER,
                created_at TEXT,
                deleted_at TEXT NOT NULL,
                deleted_by TEXT DEFAULT 'admin',
                batch_id TEXT
            )
        """)

        # Таблица журнала аудита действий администраторов
        db.execute("""
            CREATE TABLE IF NOT EXISTS admin_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                admin_user TEXT NOT NULL,
                action TEXT NOT NULL,
                target_hwid TEXT,
                details TEXT
            )
        """)
        
        # Миграция колонок, если таблица была создана ранее
        cursor = db.execute("PRAGMA table_info(licenses)")
        cols = {row["name"] for row in cursor.fetchall()}
        if "tier" not in cols:
            db.execute("ALTER TABLE licenses ADD COLUMN tier TEXT DEFAULT 'PRO'")
        if "status" not in cols:
            db.execute("ALTER TABLE licenses ADD COLUMN status TEXT DEFAULT 'active'")
        if "key_version" not in cols:
            db.execute("ALTER TABLE licenses ADD COLUMN key_version INTEGER DEFAULT 1")
        if "is_revoked" not in cols:
            db.execute("ALTER TABLE licenses ADD COLUMN is_revoked INTEGER DEFAULT 0")
        if "revoked_at" not in cols:
            db.execute("ALTER TABLE licenses ADD COLUMN revoked_at TEXT")
        if "last_reissue_at" not in cols:
            db.execute("ALTER TABLE licenses ADD COLUMN last_reissue_at TEXT")
        if "updated_at" not in cols:
            db.execute("ALTER TABLE licenses ADD COLUMN updated_at TEXT")
            
        db.commit()

async def init_db():
    """Асинхронная инициализация таблиц и индексов"""
    await asyncio.to_thread(_sync_init_db)

def _sync_upsert_user(telegram_id: int, username: str = None, first_name: str = None):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _get_conn() as db:
        db.execute("""
            INSERT INTO users (telegram_id, username, first_name, first_seen)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name
        """, (telegram_id, username, first_name, now))
        db.commit()

async def upsert_user(telegram_id: int, username: str = None, first_name: str = None):
    await asyncio.to_thread(_sync_upsert_user, telegram_id, username, first_name)

def _sync_get_license_by_hwid(hwid: str):
    clean_hwid = hwid.strip().upper()
    with _get_conn() as db:
        cursor = db.execute("""
            SELECT l.*, u.username, u.first_name 
            FROM licenses l
            LEFT JOIN users u ON l.telegram_id = u.telegram_id
            WHERE l.hwid = ?
            ORDER BY l.id DESC LIMIT 1
        """, (clean_hwid,))
        row = cursor.fetchone()
        return dict(row) if row else None

async def get_license_by_hwid(hwid: str):
    return await asyncio.to_thread(_sync_get_license_by_hwid, hwid)

def _sync_get_license_by_key(license_key: str):
    clean_key = license_key.strip().upper()
    with _get_conn() as db:
        cursor = db.execute("""
            SELECT l.*, u.username, u.first_name 
            FROM licenses l
            LEFT JOIN users u ON l.telegram_id = u.telegram_id
            WHERE l.license_key = ?
            LIMIT 1
        """, (clean_key,))
        row = cursor.fetchone()
        return dict(row) if row else None

async def get_license_by_key(license_key: str):
    return await asyncio.to_thread(_sync_get_license_by_key, license_key)

def _sync_get_next_key_version(hwid: str) -> int:
    """Вычисляет следующую версию ключа на основе активных и удаленных записей"""
    clean_hwid = hwid.strip().upper()
    with _get_conn() as db:
        c1 = db.execute("SELECT MAX(key_version) FROM licenses WHERE hwid = ?", (clean_hwid,)).fetchone()[0] or 0
        c2 = db.execute("SELECT MAX(key_version) FROM licenses_archive WHERE hwid = ?", (clean_hwid,)).fetchone()[0] or 0
        max_ver = max(c1, c2)
        return max_ver + 1

async def get_next_key_version(hwid: str) -> int:
    return await asyncio.to_thread(_sync_get_next_key_version, hwid)

def _sync_save_license(hwid: str, license_key: str, telegram_id: int, tier: str = "BASE", version: int = 1):
    clean_hwid = hwid.strip().upper()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _get_conn() as db:
        db.execute("""
            INSERT INTO licenses (hwid, license_key, telegram_id, created_at, is_activated, tier, status, key_version, updated_at)
            VALUES (?, ?, ?, ?, 0, ?, 'active', ?, ?)
        """, (clean_hwid, license_key, telegram_id, now, tier, version, now))
        db.commit()
    _sync_log_action("bot", "GENERATE_KEY", clean_hwid, f"Key: {license_key} | Tier: {tier} | Version: {version} | TG: {telegram_id}")

async def save_license(hwid: str, license_key: str, telegram_id: int, tier: str = "BASE", version: int = 1):
    await asyncio.to_thread(_sync_save_license, hwid, license_key, telegram_id, tier, version)

def _sync_set_license_tier(hwid: str, new_tier: str, admin_user: str = "admin"):
    clean_hwid = hwid.strip().upper()
    clean_tier = new_tier.strip().upper()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _get_conn() as db:
        db.execute("UPDATE licenses SET tier = ?, updated_at = ? WHERE hwid = ?", (clean_tier, now, clean_hwid))
        db.commit()
    _sync_log_action(admin_user, "SET_TIER", clean_hwid, f"Changed tier to {clean_tier}")
    return {"success": True, "hwid": clean_hwid, "tier": clean_tier}

async def set_license_tier(hwid: str, new_tier: str, admin_user: str = "admin"):
    return await asyncio.to_thread(_sync_set_license_tier, hwid, new_tier, admin_user)


def _sync_check_reissue_cooldown(hwid: str, telegram_id: int = None, cooldown_minutes: int = None, username: str = None, **kwargs) -> tuple:
    """
    Проверяет, прошло ли время кулдауна с момента последнего перевыпуска ключа.
    Для владельца @oleg676725 (ID 7514540547) кулдаун ВСЕГДА 0 секунд (полный безлимит).
    Для обычных пользователей кулдаун составляет 15 минут.
    Возвращает (can_reissue: bool, seconds_remaining: int, last_time_str: str).
    """
    from config import is_owner_or_admin, DEFAULT_COOLDOWN_MINUTES

    # Владелец и администраторы: кулдаун ВСЕГДА ОТКЛЮЧЕН (0 секунд)
    if is_owner_or_admin(user_id=telegram_id, username=username):
        return True, 0, ""

    # Дополнительная проверка имени пользователя из БД, если username не был передан явно
    if telegram_id:
        with _get_conn() as db:
            u_row = db.execute("SELECT username FROM users WHERE telegram_id = ?", (telegram_id,)).fetchone()
            if u_row and u_row["username"]:
                if is_owner_or_admin(user_id=telegram_id, username=u_row["username"]):
                    return True, 0, ""

    clean_hwid = hwid.strip().upper()
    now = datetime.now()
    if cooldown_minutes is None:
        if "cooldown_hours" in kwargs and kwargs["cooldown_hours"] is not None:
            cooldown_minutes = kwargs["cooldown_hours"] * 60
        else:
            cooldown_minutes = DEFAULT_COOLDOWN_MINUTES
    cooldown_seconds = int(cooldown_minutes * 60)

    with _get_conn() as db:
        cursor = db.execute("""
            SELECT last_reissue_at, revoked_at, updated_at, created_at 
            FROM licenses 
            WHERE hwid = ? OR (telegram_id = ? AND telegram_id IS NOT NULL)
            ORDER BY id DESC LIMIT 1
        """, (clean_hwid, telegram_id))
        row = cursor.fetchone()

        if not row:
            cursor_arch = db.execute("""
                SELECT deleted_at as last_reissue_at, created_at
                FROM licenses_archive 
                WHERE hwid = ? OR (telegram_id = ? AND telegram_id IS NOT NULL)
                ORDER BY archive_id DESC LIMIT 1
            """, (clean_hwid, telegram_id))
            row = cursor_arch.fetchone()

        if not row:
            return True, 0, ""

        last_time_str = row["last_reissue_at"] or row["revoked_at"] or row.get("updated_at")
        if not last_time_str:
            return True, 0, ""

        try:
            last_dt = datetime.strptime(last_time_str, "%Y-%m-%d %H:%M:%S")
            elapsed = (now - last_dt).total_seconds()
            if elapsed < cooldown_seconds:
                remaining = int(cooldown_seconds - elapsed)
                return False, remaining, last_time_str
        except Exception:
            pass

    return True, 0, ""

async def check_reissue_cooldown(hwid: str, telegram_id: int = None, cooldown_minutes: int = None, username: str = None, **kwargs) -> tuple:
    return await asyncio.to_thread(_sync_check_reissue_cooldown, hwid, telegram_id, cooldown_minutes, username, **kwargs)

def _sync_reissue_license(hwid: str, telegram_id: int, tier: str = "BASE") -> tuple:
    """
    Перевыпуск лицензии:
    1. Переносит старую запись в архив licenses_archive со статусом 'revoked'
    2. Вычисляет новую версию (key_version + 1)
    3. Генерирует новый криптографический ключ с префиксом BASE- или PRO-
    4. Обновляет запись в licenses с last_reissue_at = now
    5. Записывает лог в admin_log.txt
    """
    clean_hwid = hwid.strip().upper()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with _get_conn() as db:
        old_rows = db.execute("SELECT * FROM licenses WHERE hwid = ?", (clean_hwid,)).fetchall()
        for old in old_rows:
            db.execute("""
                INSERT INTO licenses_archive 
                (original_id, hwid, license_key, telegram_id, tier, status, key_version, created_at, deleted_at, deleted_by, batch_id)
                VALUES (?, ?, ?, ?, ?, 'revoked', ?, ?, ?, 'system_reissue', ?)
            """, (
                old["id"], old["hwid"], old["license_key"], old["telegram_id"],
                old["tier"], old["key_version"], old["created_at"], now_str, "reissue_" + now_str
            ))

        c1 = db.execute("SELECT MAX(key_version) FROM licenses WHERE hwid = ?", (clean_hwid,)).fetchone()[0] or 0
        c2 = db.execute("SELECT MAX(key_version) FROM licenses_archive WHERE hwid = ?", (clean_hwid,)).fetchone()[0] or 0
        new_version = max(c1, c2) + 1

        from key_generator import generate_key_for_hwid
        new_key = generate_key_for_hwid(clean_hwid, version=new_version, tier=tier)

        if old_rows:
            db.execute("""
                UPDATE licenses 
                SET license_key = ?, telegram_id = ?, tier = ?, status = 'active', 
                    key_version = ?, is_revoked = 0, last_reissue_at = ?, updated_at = ?
                WHERE hwid = ?
            """, (new_key, telegram_id, tier, new_version, now_str, now_str, clean_hwid))
        else:
            db.execute("""
                INSERT INTO licenses (hwid, license_key, telegram_id, created_at, is_activated, tier, status, key_version, is_revoked, last_reissue_at, updated_at)
                VALUES (?, ?, ?, ?, 0, ?, 'active', ?, 0, ?, ?)
            """, (clean_hwid, new_key, telegram_id, now_str, tier, new_version, now_str, now_str))

        db.commit()

    _sync_log_action(
        "bot", 
        "REISSUE_KEY", 
        clean_hwid, 
        f"Reissued {tier} key: {new_key} (v{new_version}) for user {telegram_id}"
    )
    return new_key, new_version

async def reissue_license(hwid: str, telegram_id: int, tier: str = "BASE") -> tuple:
    return await asyncio.to_thread(_sync_reissue_license, hwid, telegram_id, tier)

def _sync_deactivate_license(hwid: str, license_key: str = None, reason: str = "user_logout"):
    """Деактивация ключа при выходе из аккаунта"""
    clean_hwid = hwid.strip().upper()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with _get_conn() as db:
        if license_key:
            db.execute("""
                UPDATE licenses 
                SET status = 'revoked', is_revoked = 1, revoked_at = ?, updated_at = ?
                WHERE (hwid = ? OR license_key = ?) AND status != 'revoked'
            """, (now_str, now_str, clean_hwid, license_key.strip().upper()))
        else:
            db.execute("""
                UPDATE licenses 
                SET status = 'revoked', is_revoked = 1, revoked_at = ?, updated_at = ?
                WHERE hwid = ? AND status != 'revoked'
            """, (now_str, now_str, clean_hwid))
        db.commit()

    _sync_log_action("client", "DEACTIVATE_LICENSE", clean_hwid, f"Reason: {reason} | Key: {license_key or 'all'}")

async def deactivate_license(hwid: str, license_key: str = None, reason: str = "user_logout"):
    await asyncio.to_thread(_sync_deactivate_license, hwid, license_key, reason)

def _sync_get_all_licenses(search: str = "", tier: str = "all", status: str = "all", limit: int = 100, offset: int = 0):
    """Полнотекстовый поиск, фильтрация по тарифам/статусам и пагинация"""
    with _get_conn() as db:
        where_clauses = []
        params = []
        
        if search:
            q = f"%{search.strip()}%"
            where_clauses.append("(l.hwid LIKE ? OR l.license_key LIKE ? OR CAST(l.telegram_id AS TEXT) LIKE ? OR u.username LIKE ? OR u.first_name LIKE ?)")
            params.extend([q, q, q, q, q])
            
        if tier and tier.lower() != "all":
            where_clauses.append("LOWER(l.tier) = LOWER(?)")
            params.append(tier)
            
        if status and status.lower() != "all":
            where_clauses.append("LOWER(l.status) = LOWER(?)")
            params.append(status)
            
        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        
        # Получаем общее количество записей
        count_sql = f"""
            SELECT COUNT(*) FROM licenses l 
            LEFT JOIN users u ON l.telegram_id = u.telegram_id 
            {where_sql}
        """
        total = db.execute(count_sql, params).fetchone()[0]
        
        # Получаем данные текущей страницы
        data_sql = f"""
            SELECT l.*, u.username, u.first_name 
            FROM licenses l
            LEFT JOIN users u ON l.telegram_id = u.telegram_id
            {where_sql}
            ORDER BY l.id DESC
            LIMIT ? OFFSET ?
        """
        cursor = db.execute(data_sql, params + [limit, offset])
        items = [dict(r) for r in cursor.fetchall()]
        return {"items": items, "total": total}

async def get_all_licenses(search: str = "", tier: str = "all", status: str = "all", limit: int = 100, offset: int = 0):
    return await asyncio.to_thread(_sync_get_all_licenses, search, tier, status, limit, offset)

def _sync_delete_license(hwid: str, admin_user: str = "admin"):
    """Удаление одного пользователя с авто-бэкапом, сохранением в архив и записью аудита"""
    clean_hwid = hwid.strip().upper()
    backup_path = _sync_create_backup()
    batch_id = uuid.uuid4().hex[:8]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with _get_conn() as db:
        # Находим запись
        row = db.execute("SELECT * FROM licenses WHERE hwid = ?", (clean_hwid,)).fetchone()
        if not row:
            return {"success": False, "message": "Пользователь с таким HWID не найден"}
            
        r_dict = dict(row)
        # Архивируем запись
        db.execute("""
            INSERT INTO licenses_archive 
            (original_id, hwid, license_key, telegram_id, tier, status, key_version, created_at, deleted_at, deleted_by, batch_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            r_dict["id"], r_dict["hwid"], r_dict["license_key"], r_dict["telegram_id"],
            r_dict.get("tier", "PRO"), r_dict.get("status", "active"), r_dict.get("key_version", 1),
            r_dict["created_at"], now, admin_user, batch_id
        ))
        
        # Удаляем из активной таблицы
        db.execute("DELETE FROM licenses WHERE hwid = ?", (clean_hwid,))
        db.commit()
        
    _sync_log_action(admin_user, "DELETE_USER", clean_hwid, f"Key: {r_dict['license_key']} | Batch: {batch_id} | Backup: {os.path.basename(backup_path)}")
    return {
        "success": True,
        "backup_path": backup_path,
        "batch_id": batch_id,
        "deleted_item": r_dict
    }

async def delete_license(hwid: str, admin_user: str = "admin"):
    return await asyncio.to_thread(_sync_delete_license, hwid, admin_user)

def _sync_bulk_delete_licenses(hwid_list: list, admin_user: str = "admin"):
    """Массовое удаление пользователей с авто-бэкапом, архивацией и аудитом"""
    if not hwid_list:
        return {"success": False, "message": "Список HWID пуст", "deleted_count": 0}
        
    clean_hwids = [h.strip().upper() for h in hwid_list if h and h.strip()]
    backup_path = _sync_create_backup()
    batch_id = uuid.uuid4().hex[:8]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    deleted_items = []
    
    with _get_conn() as db:
        for hwid in clean_hwids:
            row = db.execute("SELECT * FROM licenses WHERE hwid = ?", (hwid,)).fetchone()
            if row:
                r_dict = dict(row)
                deleted_items.append(r_dict)
                db.execute("""
                    INSERT INTO licenses_archive 
                    (original_id, hwid, license_key, telegram_id, tier, status, key_version, created_at, deleted_at, deleted_by, batch_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    r_dict["id"], r_dict["hwid"], r_dict["license_key"], r_dict["telegram_id"],
                    r_dict.get("tier", "PRO"), r_dict.get("status", "active"), r_dict.get("key_version", 1),
                    r_dict["created_at"], now, admin_user, batch_id
                ))
                db.execute("DELETE FROM licenses WHERE hwid = ?", (hwid,))
        db.commit()
        
    count = len(deleted_items)
    _sync_log_action(admin_user, "BULK_DELETE", f"{count} users", f"Batch: {batch_id} | HWIDs: {', '.join(clean_hwids[:5])}... | Backup: {os.path.basename(backup_path)}")
    return {
        "success": True,
        "deleted_count": count,
        "batch_id": batch_id,
        "backup_path": backup_path,
        "deleted_items": deleted_items
    }

async def bulk_delete_licenses(hwid_list: list, admin_user: str = "admin"):
    return await asyncio.to_thread(_sync_bulk_delete_licenses, hwid_list, admin_user)

def _sync_clear_all_licenses(admin_user: str = "admin"):
    """Полная очистка базы данных лицензий с созданием бэкапа и сохранением в архив"""
    backup_path = _sync_create_backup()
    batch_id = uuid.uuid4().hex[:8]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    deleted_items = []
    
    with _get_conn() as db:
        rows = db.execute("SELECT * FROM licenses").fetchall()
        for row in rows:
            r_dict = dict(row)
            deleted_items.append(r_dict)
            db.execute("""
                INSERT INTO licenses_archive 
                (original_id, hwid, license_key, telegram_id, tier, status, key_version, created_at, deleted_at, deleted_by, batch_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r_dict["id"], r_dict["hwid"], r_dict["license_key"], r_dict["telegram_id"],
                r_dict.get("tier", "PRO"), r_dict.get("status", "active"), r_dict.get("key_version", 1),
                r_dict["created_at"], now, admin_user, batch_id
            ))
        db.execute("DELETE FROM licenses")
        db.commit()
        
    count = len(deleted_items)
    _sync_log_action(admin_user, "CLEAR_ALL_DATABASE", f"{count} users wiped", f"Batch: {batch_id} | Backup: {os.path.basename(backup_path)}")
    return {
        "success": True,
        "deleted_count": count,
        "batch_id": batch_id,
        "backup_path": backup_path,
        "deleted_items": deleted_items
    }

async def clear_all_licenses(admin_user: str = "admin"):
    return await asyncio.to_thread(_sync_clear_all_licenses, admin_user)

def _sync_revoke_license(hwid: str, admin_user: str = "admin"):
    """Отзыв лицензии (деактивация ключа без удаления)"""
    clean_hwid = hwid.strip().upper()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _get_conn() as db:
        row = db.execute("SELECT * FROM licenses WHERE hwid = ?", (clean_hwid,)).fetchone()
        if not row:
            return {"success": False, "message": "Лицензия не найдена"}
        db.execute("""
            UPDATE licenses 
            SET status = 'revoked', revoked_at = ?, updated_at = ?
            WHERE hwid = ?
        """, (now, now, clean_hwid))
        db.commit()
    _sync_log_action(admin_user, "REVOKE_KEY", clean_hwid, f"Key: {row['license_key']} marked REVOKED")
    return {"success": True, "hwid": clean_hwid, "status": "revoked"}

async def revoke_license(hwid: str, admin_user: str = "admin"):
    return await asyncio.to_thread(_sync_revoke_license, hwid, admin_user)

def _sync_unbind_license(hwid: str, admin_user: str = "admin"):
    """Отвязка HWID от лицензионного ключа для переноса на другой компьютер"""
    clean_hwid = hwid.strip().upper()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _get_conn() as db:
        row = db.execute("SELECT * FROM licenses WHERE hwid = ?", (clean_hwid,)).fetchone()
        if not row:
            return {"success": False, "message": "Лицензия не найдена"}
        db.execute("""
            UPDATE licenses 
            SET hwid = 'UNBOUND', status = 'unbound', is_activated = 0, updated_at = ?
            WHERE hwid = ?
        """, (now, clean_hwid))
        db.commit()
    _sync_log_action(admin_user, "UNBIND_HWID", clean_hwid, f"Key: {row['license_key']} unbound from HWID")
    return {"success": True, "hwid": clean_hwid, "status": "unbound"}

async def unbind_license(hwid: str, admin_user: str = "admin"):
    return await asyncio.to_thread(_sync_unbind_license, hwid, admin_user)

def _sync_undo_deletion(batch_id: str = None, admin_user: str = "admin"):
    """Восстановление ранее удаленных лицензий из архива (Undo)"""
    with _get_conn() as db:
        if not batch_id:
            # Берем последний batch_id
            last_batch = db.execute("SELECT batch_id FROM licenses_archive ORDER BY archive_id DESC LIMIT 1").fetchone()
            if not last_batch or not last_batch[0]:
                return {"success": False, "message": "Нет удаленных записей для восстановления", "restored_count": 0}
            batch_id = last_batch[0]
            
        rows = db.execute("SELECT * FROM licenses_archive WHERE batch_id = ?", (batch_id,)).fetchall()
        if not rows:
            return {"success": False, "message": f"Пакет {batch_id} не найден в архиве", "restored_count": 0}
            
        restored_count = 0
        for r in rows:
            r_dict = dict(r)
            try:
                db.execute("""
                    INSERT INTO licenses 
                    (hwid, license_key, telegram_id, created_at, is_activated, tier, status, key_version, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    r_dict["hwid"], r_dict["license_key"], r_dict["telegram_id"],
                    r_dict["created_at"], 1 if r_dict.get("status") == "active" else 0,
                    r_dict.get("tier", "PRO"), r_dict.get("status", "active"),
                    r_dict.get("key_version", 1), datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))
                restored_count += 1
            except sqlite3.IntegrityError:
                pass
                
        # Удаляем восстановленные записи из архива
        db.execute("DELETE FROM licenses_archive WHERE batch_id = ?", (batch_id,))
        db.commit()
        
    _sync_log_action(admin_user, "UNDO_RESTORE", f"Batch {batch_id}", f"Restored {restored_count} licenses")
    return {"success": True, "restored_count": restored_count, "batch_id": batch_id}

async def undo_deletion(batch_id: str = None, admin_user: str = "admin"):
    return await asyncio.to_thread(_sync_undo_deletion, batch_id, admin_user)

def _sync_verify_license_in_db(hwid: str, license_key: str):
    """
    Онлайн-проверка статуса лицензии:
    - Проверяет существование ключа в базе
    - Проверяет статус (active, revoked, unbound)
    - Проверяет соответствие HWID
    """
    clean_hwid = (hwid or "").strip().upper()
    clean_key = (license_key or "").strip().upper()
    
    with _get_conn() as db:
        # Проверяем, есть ли такой ключ вообще
        row = db.execute("SELECT * FROM licenses WHERE license_key = ?", (clean_key,)).fetchone()
        if not row:
            # Проверяем архив: возможно ключ был удален администратором
            arch = db.execute("SELECT * FROM licenses_archive WHERE license_key = ?", (clean_key,)).fetchone()
            if arch:
                return {
                    "valid": False, 
                    "status": "deleted", 
                    "message": "Данный лицензионный ключ был аннулирован администратором."
                }
            return {
                "valid": False, 
                "status": "not_found", 
                "message": "Лицензионный ключ не найден в базе данных."
            }
            
        r = dict(row)
        if r["status"] == "revoked":
            return {
                "valid": False,
                "status": "revoked",
                "message": f"Лицензия отозвана администратором ({r.get('revoked_at', 'ранее')})."
            }
            
        if r["status"] == "unbound" or r["hwid"] == "UNBOUND":
            # Ключ отвязан, привязываем его к новому компьютеру клиента
            if clean_hwid:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                db.execute("""
                    UPDATE licenses 
                    SET hwid = ?, status = 'active', is_activated = 1, updated_at = ?
                    WHERE license_key = ?
                """, (clean_hwid, now, clean_key))
                db.commit()
                _sync_log_action("client", "BIND_NEW_HWID", clean_hwid, f"Key {clean_key} rebound to new HWID")
                return {
                    "valid": True,
                    "status": "rebound",
                    "tier": r.get("tier", "PRO"),
                    "message": "Лицензия успешно привязана к новому компьютеру!"
                }
            return {
                "valid": True,
                "status": "unbound",
                "tier": r.get("tier", "PRO"),
                "message": "Ключ активен и ожидает привязки к оборудованию."
            }
            
        if r["hwid"] != clean_hwid:
            return {
                "valid": False,
                "status": "mismatch",
                "message": "Лицензионный ключ привязан к другому аппаратному идентификатору (HWID)."
            }
            
        # Ключ валиден и совпадает
        if not r.get("is_activated"):
            db.execute("UPDATE licenses SET is_activated = 1 WHERE id = ?", (r["id"],))
            db.commit()
            
        return {
            "valid": True,
            "status": "active",
            "tier": r.get("tier", "PRO"),
            "created_at": r.get("created_at"),
            "message": "Лицензия действительна и активна."
        }

async def verify_license_in_db(hwid: str, license_key: str):
    return await asyncio.to_thread(_sync_verify_license_in_db, hwid, license_key)

def _sync_get_user_licenses(telegram_id: int):
    with _get_conn() as db:
        cursor = db.execute(
            "SELECT * FROM licenses WHERE telegram_id = ? ORDER BY id DESC", 
            (telegram_id,)
        )
        return [dict(r) for r in cursor.fetchall()]

async def get_user_licenses(telegram_id: int):
    return await asyncio.to_thread(_sync_get_user_licenses, telegram_id)

def _sync_get_stats():
    with _get_conn() as db:
        users_count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        licenses_count = db.execute("SELECT COUNT(*) FROM licenses").fetchone()[0]
        active_count = db.execute("SELECT COUNT(*) FROM licenses WHERE status = 'active'").fetchone()[0]
        revoked_count = db.execute("SELECT COUNT(*) FROM licenses WHERE status = 'revoked'").fetchone()[0]
        unbound_count = db.execute("SELECT COUNT(*) FROM licenses WHERE status = 'unbound'").fetchone()[0]
        archived_count = db.execute("SELECT COUNT(*) FROM licenses_archive").fetchone()[0]
        return {
            "users": users_count,
            "licenses": licenses_count,
            "active": active_count,
            "revoked": revoked_count,
            "unbound": unbound_count,
            "archived": archived_count
        }

async def get_stats():
    return await asyncio.to_thread(_sync_get_stats)
