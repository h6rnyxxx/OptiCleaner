<div align="center">

# ⚡ OptiCleaner v4.0

**Высокопроизводительный модульный системный комбайн и твикер для Windows & Linux**

[![GitHub release (latest by date)](https://img.shields.io/github/v/release/h6rnyxxx/OptiCleaner?style=for-the-badge&color=00E5FF)](https://github.com/h6rnyxxx/OptiCleaner/releases)
[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PyQt5%20%2B%20Native%20QPainter-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)
[![Security](https://img.shields.io/badge/Security-Ed25519%20Asymmetric-A855F7?style=for-the-badge&logo=security&logoColor=white)](#-безопасность-и-лицензирование)
[![License](https://img.shields.io/badge/License-MIT-F59E0B?style=for-the-badge)](LICENSE)

[🌐 Официальный сайт & Web Dashboard](website/index.html) • [📥 Скачать релиз v4.0](https://github.com/h6rnyxxx/OptiCleaner/releases) • [🛠 Архитектура](#-архитектура-проекта-v40) • [🔒 Аудит AppSec](#-отчет-по-безопасности-и-аудиту-appsec)

</div>

---

## 🚀 О проекте (Overview)

**OptiCleaner v4.0** — результат полного архитектурного рефакторинга кодовой базы. Проект преобразован из монолитного скрипта в защищенный, компонентный системный комбайн уровня *Process Hacker / BleachBit / CCleaner Pro*.

### Ключевые преимущества v4.0:
* **🛡️ 100% защита от сбоев (Disaster Recovery):** Создание официальных контрольных точек восстановления Windows (`System Restore Point`) и JSON-снимков реестра перед каждым изменением.
* **⚡ Ультранизкая задержка (0.5 мс):** Прямые системные вызовы `NtSetTimerResolution` для минимизации input lag в киберспортивных играх.
* **🎨 Легковесный нативный интерфейс:** Замена 120-мегабайтного QtWebEngine на аппаратный `QPainter` HUD с неоновыми круговыми индикаторами.
* **🔐 Асимметричная криптография Ed25519:** В клиентском приложении полностью отсутствуют симметричные секреты и соли — валидация лицензий выполняется строго по публичному ключу.

---

## 🔒 Отчет по безопасности и аудиту AppSec

В ходе глубокого аудита безопасности устранены критические уязвимости:

| Уязвимость в v3.0 | Статус v4.0 | Исправление в новой архитектуре |
| :--- | :--- | :--- |
| **Утечка токена бота и ID** | 🟢 ИСПРАВЛЕНО | Сервер и бот полностью изолированы в закрытый приватный репозиторий. Публичный клиент не содержит серверных файлов. |
| **Симметричная соль в клиенте** | 🟢 ИСПРАВЛЕНО | Симметричный HMAC заменён на асимметричную подпись **Ed25519**. Клиент хранит только публичный ключ. |
| **Монолит на 21 000 строк** | 🟢 ИСПРАВЛЕНО | Декомпозиция на независимые модули: `core/`, `modules/`, `security/`, `ui/`. |
| **Откат без точек восстановления** | 🟢 ИСПРАВЛЕНО | Реализован `RestorePointManager` и `SnapshotEngine` для автоматического резервного копирования. |
| **Открытое хранение настроек** | 🟢 ИСПРАВЛЕНО | Локальные конфигурации шифруются через Windows DPAPI (`CryptProtectData`). |

---

## 🛠️ Архитектура проекта v4.0

```text
OptiCleaner/
├── .gitignore                      # Строгие правила исключения секретов и артефактов
├── LICENSE                         # MIT Лицензия
├── README.md                       # Главная документация
├── requirements.txt                # Оптимизированные зависимости (без WebEngine)
├── build_linux_appimage.py         # Сборщик Linux AppImage
├── images/                         # Иконки и графические ресурсы
├── website/                        # Официальный SaaS лендинг и Web Dashboard
│   ├── index.html                  # Главная страница экосистемы
│   ├── styles.css                  # Неоновый Cyberpunk стиль с адаптивной сеткой
│   └── app.js                      # Интерактивные графики и демонстрационный чекаут
└── src/                            # Модульное ядро десктопного приложения
    ├── main.py                     # Точка входа: UAC Elevation, синглтон мьютекс, splash
    ├── app.py                      # Модульный перенаправитель
    ├── OptiCleaner.spec            # Спецификация сборщика PyInstaller
    ├── core/                       # Низкоуровневый OS движок
    │   ├── base_engine.py          # Базовый интерфейс (ABC)
    │   ├── windows/                # Специфика Windows (WinAPI, WMI, ctypes)
    │   │   ├── win_engine.py       # Реализация движка Windows
    │   │   ├── registry_manager.py # Транзакционный реестр с экспортом .reg
    │   │   ├── service_controller.py # Управление службами и телеметрией
    │   │   ├── network_tweak_engine.py # Оптимизация TCP/IP и сброс DNS
    │   │   ├── memory_engine.py    # Очистка Standby List и Working Sets
    │   │   ├── timer_resolution.py # NtSetTimerResolution (стабильные 0.5 мс)
    │   │   └── restore_point_manager.py # Точки восстановления Windows
    │   ├── linux/                  # Специфика Linux (systemd, sysctl, кэш)
    │   │   └── linux_engine.py
    │   └── safety/                 # Модули катастрофоустойчивости
    │       ├── snapshot_engine.py  # JSON-снимки состояния ДО твиков
    │       ├── rollback_service.py # Сервис моментального отката изменений
    │       └── crash_reporter.py   # Локальный безопасный логгер сбоев
    ├── modules/                    # Функциональные компоненты
    │   ├── cleaner/                # Движок сканирования и очистки мусора
    │   │   ├── rules_manifest.json # Шаблоны временных файлов и кэша
    │   │   ├── disk_scanner.py     # Многопоточный обход дисков
    │   │   ├── browser_engine.py   # Очистка Chrome, Edge, Firefox, Yandex
    │   │   └── secure_file_eraser.py # Шреддер файлов (DoD 5220.22-M / 1-pass)
    │   ├── optimizer/              # Профили производительности
    │   │   ├── presets_manager.py  # Gaming, Work, Balanced
    │   │   ├── game_booster_daemon.py # Фоновый демон приоритета 3D-игр
    │   │   └── power_plan_manager.py # Схема Ultimate Performance
    │   ├── uninstaller/            # Менеджер деинсталляции
    │   │   ├── app_scanner.py      # Поиск Win32 и UWP приложений
    │   │   └── remnant_hunter.py   # Поиск хвостов в AppData/ProgramData
    │   ├── hardware/               # Мониторинг комплектующих
    │   │   ├── telemetry_worker.py # Фоновый сбор CPU, GPU, RAM, дисков
    │   │   └── driver_exporter.py  # Экспорт OEM-драйверов через DISM
    │   ├── task_manager/           # Встроенный диспетчер задач
    │   │   └── process_monitor.py
    │   └── software_catalog/       # Каталог тихой установки софта (winget)
    │       └── winget_manager.py
    ├── security/                   # Безопасность и лицензирование
    │   ├── hwid_generator.py       # Стабильный аппаратный HWID
    │   ├── asymmetric_license.py   # Асимметричная Ed25519 валидация
    │   └── encrypted_settings.py   # Шифрование настроек через DPAPI
    └── ui/                         # Интерфейс PyQt5
        ├── styles/themes.py        # QSS-темы (Cyberpunk HUD, OLED Black)
        ├── components/             # Нативные виджеты (CyberGauge на QPainter)
        ├── views/                  # Экраны разделов
        │   ├── cleaner_view.py
        │   ├── optimizer_view.py
        │   ├── hardware_view.py
        │   ├── uninstaller_view.py
        │   └── task_manager_view.py
        └── main_window.py          # Главное окно с Navigation Rail
```

---

## 💻 Быстрый старт и запуск

### 1. Запуск из исходного кода:
```bash
git clone https://github.com/h6rnyxxx/OptiCleaner.git
cd OptiCleaner

# Создание и активация виртуального окружения
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Linux

# Установка зависимостей
pip install -r requirements.txt

# Запуск приложения
python src/main.py
```

### 2. Сборка автономного `.exe` (PyInstaller):
```bash
cd src
pyinstaller OptiCleaner.spec
```
Готовый переносимый бинарник появится в `src/dist/OptiCleaner.exe`.

---

## 🌐 Веб-сайт экосистемы (SaaS Landing & Dashboard)

Для предварительного просмотра официального веб-сайта откройте файл:
```text
website/index.html
```
Включает в себя интерактивную демонстрацию дашборда, динамические графики, сравнение тарифных планов и форму оформления лицензий (Stripe / Crypto).

---

## 📄 Лицензия

Проект распространяется под открытой лицензией **MIT**. Подробности в файле [LICENSE](LICENSE).

Автор и архитектор: **h6rnyx** ([GitHub Profile](https://github.com/h6rnyxxx))
