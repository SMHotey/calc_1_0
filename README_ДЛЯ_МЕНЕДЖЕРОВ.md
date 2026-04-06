# 🚀 МеталлоКальк PRO v2.0 — Инструкция по запуску и использованию

## 📦 Системные требования
- Windows 10/11, macOS 12+, Linux (Ubuntu 20.04+)
- Python 3.10 или новее
- Оперативная память: 512 МБ свободно
- Дисковое пространство: 50 МБ (для БД SQLite и приложения)

## 🔧 Быстрый запуск (для технических специалистов)
1. Убедитесь, что установлен Python 3.10+
2. Откройте терминал в папке проекта:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   python main.py