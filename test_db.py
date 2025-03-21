#!/usr/bin/env python3
"""
Скрипт для проверки подключения к базе данных PostgreSQL и просмотра данных в таблице analytics.
"""

import json
import logging
from tabulate import tabulate
from db_models import get_db_manager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def test_connection():
    """Проверяет подключение к базе данных."""
    try:
        db_manager = get_db_manager()
        db_manager.init_db()
        logger.info("Подключение к базе данных успешно установлено")
        return True
    except Exception as e:
        logger.error(f"Ошибка при подключении к базе данных: {e}")
        return False

def display_analytics_data(limit=10):
    """Отображает аналитические данные из таблицы analytics."""
    try:
        db_manager = get_db_manager()
        records = db_manager.get_all_analytics(limit=limit)
        
        if not records:
            logger.info("В таблице analytics нет данных")
            return
        
        # Подготовка данных для табличного вывода
        headers = ["ID", "Время", "IP", "Тип события", "User Agent", "URL", "Реферер", "Сессия"]
        rows = []
        
        for record in records:
            # Сокращение длинных строк для более компактного отображения
            user_agent = record.user_agent[:30] + '...' if record.user_agent and len(record.user_agent) > 30 else record.user_agent
            page_url = record.page_url[:30] + '...' if record.page_url and len(record.page_url) > 30 else record.page_url
            
            rows.append([
                record.id,
                record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                record.ip_address,
                record.event_type,
                user_agent,
                page_url,
                record.referrer,
                record.session_id
            ])
        
        # Вывод данных в виде таблицы
        print("\nДанные из таблицы analytics:")
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        logger.info(f"Отображено {len(rows)} записей из таблицы analytics")
        
    except Exception as e:
        logger.error(f"Ошибка при получении данных из таблицы analytics: {e}")

if __name__ == "__main__":
    if test_connection():
        display_analytics_data()
    else:
        logger.error("Не удалось подключиться к базе данных") 