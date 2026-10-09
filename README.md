<div align="center">

# ⚡ OptiCleaner

**Кроссплатформенный комбайн для комплексной очистки, оптимизации и тонкого твикинга Windows & Linux**

[![GitHub release (latest by date)](https://img.shields.io/github/v/release/h6rnyxxx/OptiCleaner?style=for-the-badge&color=00E5FF)](https://github.com/h6rnyxxx/OptiCleaner/releases)
[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PyQt5%20%2B%20CustomTheme-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/h6rnyxxx/OptiCleaner/releases)
[![License](https://img.shields.io/badge/License-MIT-F59E0B?style=for-the-badge)](LICENSE)

</div>

---

## 📖 О проекте (Overview)

**OptiCleaner** — современное приложение для пользователей, которым требуется максимальная производительность системы, абсолютная чистота дискового пространства и полный контроль над фоновыми процессами и службами.

Интерфейс выполнен в премиальном темном матовом стиле с неоновыми киберпанк-акцентами и интуитивной навигацией.

---

## ✨ Основные возможности (Features)

### 🧹 1. Очистка системы (System Cleaning)
- **Умный дашборд**: Быстрый аудит и экспресс-очистка временных файлов (`%TEMP%`, кэш шейдеров, дампы памяти, дампы сбоев).
- **Глубокая очистка (Deep Clean)**: Удаление старых точек восстановления Windows, остатков обновлений (`SoftwareDistribution`), истории буфера обмена и префетча (`Prefetch`).
- **Очистка веб-браузеров**: Полноценная очистка кэша, куки, истории загрузок и сессий для Google Chrome, Mozilla Firefox, Microsoft Edge, Яндекс.Браузера, Opera и др.
- **Менеджер удаления софта**: Продвинутый деинсталлятор с отслеживанием скрытых программ и зачисткой остаточных файлов после удаления.
- **Журнал истории**: Полная прозрачность и статистика каждого цикла очистки с подсчетом освобожденных гигабайт.

### 🚀 2. Оптимизация и твикинг (Optimization & Tweaks)
- **Готовые системные пресеты**:
  - 🎮 **Gaming Mode**: Отключение фоновой телеметрии, таймеров энергосбережения, оптимизация приоритета видеокарты и процессора для максимального FPS и минимальной задержки (input lag).
  - 💼 **Work Mode**: Стабильная работа без агрессивных твиков с фокусом на плавность и надежность.
  - ⚡ **Ultra / Balanced**: Сбалансированные профили под любые задачи.
- **Оптимизация Сети и Wi-Fi**: Тонкая настройка сетевого стека TCP/IP, TCP Window Size, MTU, отключение сетевого троттлинга Windows и мгновенный сброс DNS.
- **Менеджер служб**: Отключение ненужных системных сервисов (телеметрия, диагностика, трекинг пользователей).

### 🖥️ 3. Мониторинг и инструменты (Monitoring & Tools)
- **Интерактивный Диспетчер задач**: Мониторинг процессов, использования памяти, нагрузки на процессор и диск в реальном времени.
- **Спецификации ПК (Hardware Info)**: Быстрый просмотр детальной информации о комплектующих (CPU, GPU, RAM, материнская плата, накопители, версия ОС).
- **Менеджер драйверов**: Просмотр установленных устройств и резервное копирование системных драйверов.
- **Каталог софта**: Встроенная установка популярных бесплатных утилит (7-Zip, Notepad++, Everything, CPU-Z, Process Hacker, VLC и др.) в один клик.
- **Windows Update & Таймер сна**: Управление центром обновлений и таймер автовыключения/перезагрузки ПК.

### 🤖 4. Лицензирование и Telegram-бот
- Модуль автоматической активации по аппаратному идентификатору (**HWID**).
- Интегрированный микросервис на FastAPI и Telegram-бот на базе **aiogram 3.x** с разделением уровней доступа (`BASE`, `PRO`, `MAXIMUM`).

---

## 📥 Загрузка и установка (Download)

Готовые скомпилированные релизы доступны на странице **[GitHub Releases](https://github.com/h6rnyxxx/OptiCleaner/releases)**:

| Платформа | Пакет | Инструкция |
| :--- | :--- | :--- |
| **Windows 10 / 11** | `OptiCleaner-v3.0.0-Windows.exe` | Скачайте и запустите от имени Администратора (установка не требуется) |
| **Linux (Все дистрибутивы)** | `OptiCleaner-v3.0.0-Linux.AppImage` | `chmod +x OptiCleaner-v3.0.0-Linux.AppImage && ./OptiCleaner-v3.0.0-Linux.AppImage` |

---

## 🛠️ Запуск из исходного кода (Build & Run)

### 1. Клонирование репозитория
```bash
git clone https://github.com/h6rnyxxx/OptiCleaner.git
cd OptiCleaner
```

### 2. Создание виртуального окружения
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Linux:
source venv/bin/activate
```

### 3. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 4. Запуск приложения
```bash
python src/app.py
```

---

## 📦 Сборка дистрибутивов (Packaging)

### Сборка Windows `.exe` (PyInstaller):
```bash
cd src
pyinstaller OptiCleaner.spec
```
Готовый файл появится в каталоге `src/dist/OptiCleaner.exe`.

### Сборка Linux `AppImage`:
```bash
python build_linux_appimage.py
```
Или используйте готовый bash-скрипт:
```bash
cd Linux
bash build_appimage.sh
```

---

## 🤖 Запуск Telegram-бота и API лицензий

Для развертывания собственного сервера авторизации:

```bash
cd telegram_bot
pip install -r requirements.txt
cp .env.example .env
```

Отредактируйте `.env`:
```env
BOT_TOKEN=ВАШ_ТОКЕН_ОТ_BOTFATHER
ADMIN_IDS=ВАШ_TELEGRAM_USER_ID
COOLDOWN_MINUTES=15
```

Запуск в фоновом режиме / через трей:
```bash
# Windows
run_bot.bat

# Либо напрямую:
python main.py
```

Подробная документация по бэкенду находится в [telegram_bot/README.md](telegram_bot/README.md).

---

## 📂 Структура проекта (Project Tree)

```text
OptiCleaner/
├── .gitignore                  # Исключения Git (кэш, логи, базы, бинарники)
├── LICENSE                     # MIT Лицензия
├── README.md                   # Главная документация проекта
├── requirements.txt            # Зависимости настольного приложения
├── build_linux_appimage.py     # Скрипт кроссплатформенной сборки Linux AppImage
├── images/                     # Иконки и графические ресурсы UI
│   ├── icon.ico
│   ├── icon.png
│   ├── opticleaner.png
│   └── cyber_visuals.html
├── src/                        # Исходный код десктопного клиента
│   ├── app.py                  # Главное GUI-приложение (PyQt5)
│   ├── OptiCleaner.spec        # Конфигурация сборки PyInstaller
│   ├── opticleaner_settings.json
│   └── images/                 # Ресурсы интерфейса
├── Linux/                      # Файлы дистрибутива Linux
│   ├── AppRun                  # Точка входа AppImage
│   ├── build_appimage.sh       # Shell-скрипт сборщика
│   ├── install.sh              # Скрипт интеграции в меню и автозапуск
│   ├── opticleaner.desktop     # Desktop Entry файл
│   └── README_LINUX.md         # Руководство пользователя Linux
└── telegram_bot/               # Бэкенд лицензий и Telegram-бот
    ├── .env.example            # Пример переменных окружения
    ├── api_server.py           # FastAPI REST API
    ├── config.py               # Конфигурация сервиса
    ├── database.py             # SQLite хранилище лицензий
    ├── key_generator.py        # Криптографический генератор HMAC ключей
    ├── main.py                 # Главный запуск бота (aiogram 3.x)
    ├── tray_runner.py          # Трей-агент управления
    ├── requirements.txt        # Зависимости бота
    └── README.md               # Руководство по боту
```

---

## 📄 Лицензия (License)

Проект распространяется под лицензией **MIT**. Подробности в файле [LICENSE](LICENSE).

Автор: **h6rnyx** ([GitHub Profile](https://github.com/h6rnyxxx))
