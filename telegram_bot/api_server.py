import uvicorn
from fastapi import FastAPI, HTTPException, Header, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from config import API_HOST, API_PORT, API_SECRET_KEY
from database import (
    init_db,
    get_all_licenses,
    get_license_by_hwid,
    get_license_by_key,
    get_next_key_version,
    save_license,
    delete_license,
    bulk_delete_licenses,
    clear_all_licenses,
    revoke_license,
    unbind_license,
    undo_deletion,
    verify_license_in_db,
    get_stats,
    _sync_create_backup,
    _sync_log_action
)
from key_generator import is_valid_hwid, generate_key_for_hwid

app = FastAPI(
    title="OptiCleaner Licensing REST API",
    description="Высокопроизводительный REST API сервер для удаленного управления лицензиями и пользователями OptiCleaner.",
    version="3.0.0"
)

# Разрешаем CORS для десктопных и веб-клиентов
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Защита эндпоинтов администратора =====
def verify_admin_key(x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    if not API_SECRET_KEY:
        return True
    if not x_admin_key or x_admin_key != API_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный или отсутствующий токен доступа администратора (X-Admin-Key)"
        )
    return True

# ===== Pydantic Модели =====
class CreateLicenseRequest(BaseModel):
    hwid: str = Field(..., description="Аппаратный идентификатор ПК (OC-XXXX-XXXX-XXXX-XXXX)")
    tier: str = Field("PRO", description="Тарифный план: PRO, Universal, Maximum")
    telegram_id: Optional[int] = Field(None, description="Telegram ID пользователя")
    admin_user: str = Field("api_admin", description="Имя администратора")

class BulkDeleteRequest(BaseModel):
    hwids: List[str] = Field(..., description="Список HWID для пакетного удаления")
    admin_user: str = Field("api_admin", description="Имя администратора")

class WipeDatabaseRequest(BaseModel):
    confirmation_word: str = Field(..., description="Слово-подтверждение ('DELETE' или 'УДАЛИТЬ')")
    admin_user: str = Field("api_admin", description="Имя администратора")

class UndoRequest(BaseModel):
    batch_id: Optional[str] = Field(None, description="ID пакета удаления (если пустой, восстановит последний)")
    admin_user: str = Field("api_admin", description="Имя администратора")

class VerifyRequest(BaseModel):
    hwid: str = Field(..., description="Аппаратный HWID клиента")
    license_key: str = Field(..., description="Лицензионный ключ (KEY-XXXX...)")

# ===== Эндпоинты API =====

@app.on_event("startup")
async def on_startup():
    await init_db()

@app.get("/", tags=["System"])
async def root():
    return {
        "service": "OptiCleaner Licensing REST API",
        "version": "3.0.0",
        "status": "online",
        "docs_url": "/docs"
    }

@app.get("/api/v1/stats", tags=["System"], dependencies=[Depends(verify_admin_key)])
async def get_system_stats():
    """Получить общую статистику лицензий и пользователей"""
    return await get_stats()

@app.get("/api/v1/licenses", tags=["Licenses"], dependencies=[Depends(verify_admin_key)])
async def list_licenses(
    search: str = Query("", description="Поиск по HWID, ключу, Telegram ID, имени"),
    tier: str = Query("all", description="Фильтр по тарифу: all, PRO, Universal, Maximum"),
    status: str = Query("all", description="Фильтр по статусу: all, active, revoked, unbound"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Список лицензий с фильтрацией, поиском и пагинацией"""
    return await get_all_licenses(search, tier, status, limit, offset)

@app.post("/api/v1/licenses", tags=["Licenses"], dependencies=[Depends(verify_admin_key)])
async def create_license(req: CreateLicenseRequest):
    """Генерация и сохранение новой лицензии"""
    if not is_valid_hwid(req.hwid):
        raise HTTPException(status_code=400, detail="Неверный формат HWID! Должен быть OC-XXXX-XXXX-XXXX-XXXX")
        
    version = await get_next_key_version(req.hwid)
    key = generate_key_for_hwid(req.hwid, version=version)
    await save_license(req.hwid, key, req.telegram_id or 0, req.tier, version)
    _sync_log_action(req.admin_user, "API_CREATE_LICENSE", req.hwid, f"Key: {key} | Tier: {req.tier}")
    return {
        "success": True,
        "hwid": req.hwid.upper(),
        "license_key": key,
        "tier": req.tier,
        "version": version
    }

@app.get("/api/v1/licenses/{hwid}", tags=["Licenses"], dependencies=[Depends(verify_admin_key)])
async def get_license(hwid: str):
    """Информация о лицензии по HWID"""
    lic = await get_license_by_hwid(hwid)
    if not lic:
        raise HTTPException(status_code=404, detail="Лицензия для данного HWID не найдена")
    return lic

@app.delete("/api/v1/licenses/{hwid}", tags=["Licenses"], dependencies=[Depends(verify_admin_key)])
async def delete_single_license(hwid: str, admin_user: str = "api_admin"):
    """Удаление пользователя по HWID с авто-бэкапом и архивацией"""
    result = await delete_license(hwid, admin_user=admin_user)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message"))
    return result

@app.post("/api/v1/licenses/bulk-delete", tags=["Licenses"], dependencies=[Depends(verify_admin_key)])
async def bulk_delete(req: BulkDeleteRequest):
    """Массовое удаление пользователей по списку HWID"""
    return await bulk_delete_licenses(req.hwids, admin_user=req.admin_user)

@app.post("/api/v1/licenses/wipe", tags=["Licenses"], dependencies=[Depends(verify_admin_key)])
async def wipe_all_database(req: WipeDatabaseRequest):
    """Полная очистка базы данных с защитой словом DELETE/УДАЛИТЬ"""
    word = req.confirmation_word.strip().upper()
    if word not in ("DELETE", "УДАЛИТЬ"):
        raise HTTPException(status_code=400, detail="Неверное контрольное слово. Требуется 'DELETE' или 'УДАЛИТЬ'.")
    return await clear_all_licenses(admin_user=req.admin_user)

@app.post("/api/v1/licenses/{hwid}/revoke", tags=["Licenses"], dependencies=[Depends(verify_admin_key)])
async def revoke_user_license(hwid: str, admin_user: str = "api_admin"):
    """Отозвать лицензию (деактивировать ключ без удаления записи)"""
    result = await revoke_license(hwid, admin_user=admin_user)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message"))
    return result

@app.post("/api/v1/licenses/{hwid}/unbind", tags=["Licenses"], dependencies=[Depends(verify_admin_key)])
async def unbind_user_hwid(hwid: str, admin_user: str = "api_admin"):
    """Развязать лицензию с HWID для переноса на другой ПК"""
    result = await unbind_license(hwid, admin_user=admin_user)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message"))
    return result

@app.post("/api/v1/licenses/{hwid}/tier", tags=["Licenses"], dependencies=[Depends(verify_admin_key)])
async def change_license_tier(hwid: str, tier: str = Query("PRO", description="BASE или PRO"), admin_user: str = "api_admin"):
    """Смена тарифа лицензии (BASE или PRO)"""
    from database import set_license_tier
    clean_tier = tier.strip().upper()
    if clean_tier not in ("BASE", "PRO"):
        raise HTTPException(status_code=400, detail="Тариф должен быть BASE или PRO")
    result = await set_license_tier(hwid, clean_tier, admin_user=admin_user)
    return result


@app.post("/api/v1/licenses/undo", tags=["Licenses"], dependencies=[Depends(verify_admin_key)])
async def undo_delete(req: UndoRequest):
    """Восстановление ранее удаленных записей из архива (Undo)"""
    result = await undo_deletion(batch_id=req.batch_id, admin_user=req.admin_user)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result

@app.post("/api/v1/licenses/backup", tags=["Licenses"], dependencies=[Depends(verify_admin_key)])
async def manual_backup(admin_user: str = "api_admin"):
    """Принудительное создание резервной копии базы данных"""
    path = _sync_create_backup()
    _sync_log_action(admin_user, "MANUAL_BACKUP", None, f"Created backup: {path}")
    return {"success": True, "backup_path": path}

# ===== Клиентская онлайн-проверка лицензии (публичный эндпоинт) =====
@app.post("/api/v1/license/verify", tags=["Client Verification"])
async def verify_license(req: VerifyRequest):
    """
    Онлайн-проверка подлинности и активности ключа на клиентском приложении OptiCleaner.
    Возвращает статус: active, revoked, unbound, rebound, deleted, not_found.
    """
    return await verify_license_in_db(req.hwid, req.license_key)

def start_server():
    uvicorn.run("api_server:app", host=API_HOST, port=API_PORT, reload=False)

if __name__ == "__main__":
    start_server()
