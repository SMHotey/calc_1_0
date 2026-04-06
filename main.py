"""Точка входа в приложение. Инициализация БД, логирования, UI и запуск цикла событий."""

import sys
import os
import logging
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

from db.database import init_db
from views.main_window import MainWindow
from constants import APP_NAME, APP_VERSION, LOG_FORMAT


def setup_logging() -> None:
    """Настраивает систему логирования для приложения."""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "app_runtime.log"), encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Снижаем уровень логирования SQLAlchemy, чтобы не засорять консоль
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)


def global_exception_handler(exc_type: type[BaseException], exc_value: BaseException, exc_tb) -> None:
    """Перехватывает необработанные исключения для безопасного завершения работы."""
    logger = logging.getLogger(__name__)
    logger.critical(f"Необработанное исключение: {exc_value}", exc_info=(exc_type, exc_value, exc_tb))

    if QApplication.instance() is not None:
        QMessageBox.critical(
            None,
            "Критическая ошибка",
            f"Произошла непредвиденная ошибка:\n\n{exc_value}\n\n"
            "Подробности записаны в файл logs/app_runtime.log."
        )


def main() -> None:
    """Основная функция запуска приложения."""
    setup_logging()
    sys.excepthook = global_exception_handler
    logger = logging.getLogger(__name__)
    logger.info(f"🚀 Запуск {APP_NAME} v{APP_VERSION}")

    try:
        # Инициализация БД и заполнение демо-данными при первом запуске
        logger.info("Инициализация базы данных...")
        init_db()
        logger.info("База данных готова к работе.")

        # Настройка Qt-приложения
        app = QApplication(sys.argv)
        app.setApplicationName(APP_NAME)
        app.setApplicationVersion(APP_VERSION)
        app.setStyle("Fusion")  # Кроссплатформенная базовая тема, переопределяется через QSS
        app.setQuitOnLastWindowClosed(True)

        # Запуск главного окна
        logger.info("Создание главного окна...")
        main_window = MainWindow()
        main_window.show()

        logger.info("✅ Приложение запущено успешно.")
        sys.exit(app.exec())

    except Exception as e:
        logger.critical(f"Ошибка запуска: {e}\n{traceback.format_exc()}")
        sys.exit(1)
    finally:
        logger.info("🔚 Завершение работы приложения.")


if __name__ == "__main__":
    main()