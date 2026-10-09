# OptiCleaner — Linux Distribution (AppImage)

OptiCleaner v3.0.0 теперь полностью оптимизирован для Linux!

## 🚀 Запуск без установки (Портативный режим):
1. Откройте терминал в папке `Linux/`
2. Дайте права на выполнение:
   ```bash
   chmod +x OptiCleaner.AppImage
   ```
3. Запустите:
   ```bash
   ./OptiCleaner.AppImage
   ```

## 📦 Установка в систему (1 клик):
Запустите скрипт установки:
```bash
chmod +x install.sh
./install.sh
```
Это автоматически:
- Скопирует `OptiCleaner` в `~/.local/bin`
- Создаст ярлык в меню приложений (`~/.local/share/applications/opticleaner.desktop`)
- Установит иконку `opticleaner.png`
- Создаст ярлык на рабочем столе (`~/Desktop`)

## 🛠 Системные требования:
- 64-битный Linux (Ubuntu 20.04+, Debian 11+, Fedora 36+, Arch Linux, Manjaro, Linux Mint и др.)
- Python 3 и PyQt5:
  - Ubuntu/Debian/Mint: `sudo apt install python3 python3-pyqt5 python3-psutil python3-requests`
  - Fedora: `sudo dnf install python3 python3-qt5 python3-psutil python3-requests`
  - Arch/Manjaro: `sudo pacman -S python python-pyqt5 python-psutil python-requests`
