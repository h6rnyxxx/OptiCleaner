import hmac
import hashlib
import re
from config import SECRET_LIC_SALT

HWID_PATTERN = re.compile(r"^OC-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}$")

def is_valid_hwid(hwid: str) -> bool:
    """
    Валидация формата аппаратного идентификатора:
    - Префикс: OC-
    - Длина: ровно 22 символа
    - 4 шестнадцатеричных блока по 4 символа: OC-XXXX-XXXX-XXXX-XXXX
    """
    if not hwid or not isinstance(hwid, str):
        return False
    clean = hwid.strip().upper()
    return bool(HWID_PATTERN.match(clean))

def generate_key_for_hwid(hwid: str, version: int = 1, tier: str = "BASE") -> str:
    """
    Криптографическая генерация лицензионного ключа на основе HWID клиента:
    - Использует HMAC-SHA256 с секретной солью SECRET_LIC_SALT
    - Поддерживает тарифы: BASE (Базовый) или PRO (Профессиональный)
    - Формирует ключ: BASE-XXXX-XXXX-XXXX-XXXX или PRO-XXXX-XXXX-XXXX-XXXX
    - Полная совместимость с валидатором validate_license_key() в OptiCleaner
    """
    clean = hwid.strip().upper()
    tier_upper = str(tier).upper()
    prefix = "PRO" if tier_upper == "PRO" else ("BASE" if tier_upper == "BASE" else "KEY")
    payload = f"BOUND:{prefix}:{clean}" if version <= 1 else f"BOUND:{prefix}:{clean}:V{version}"
    sig = hmac.new(
        SECRET_LIC_SALT, 
        payload.encode("utf-8"), 
        hashlib.sha256
    ).hexdigest().upper()
    return f"{prefix}-{sig[:4]}-{sig[4:8]}-{sig[8:12]}-{sig[12:16]}"

