import json
import logging
import argparse
from tabulate import tabulate
from db_models import get_db_manager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def format_json(json_data, max_length=50):
    """Форматирует JSON-данные для вывода в таблицу."""
    if not json_data:
        return "Нет данных"
    
    try:
        # Если это строка JSON, преобразуем ее в объект
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data
            
        # Преобразуем обратно в строку для отображения
        formatted = json.dumps(data, ensure_ascii=False, indent=2)
        
        # Ограничиваем длину для отображения в таблице
        if len(formatted) > max_length:
            return formatted[:max_length] + "..."
        return formatted
    except Exception as e:
        logger.error(f"Ошибка при форматировании JSON: {e}")
        return str(json_data)[:max_length] + "..."

def view_data(limit=10, format_type="table", show_raw=False):
    """Просмотр данных из базы PostgreSQL."""
    try:
        # Инициализируем подключение к БД
        db_manager = get_db_manager()
        
        # Получаем данные
        data = db_manager.get_all_user_data(limit=limit)
        
        if not data:
            logger.info("Данные не найдены.")
            return
        
        # Отображаем данные в зависимости от выбранного формата
        if format_type == "json":
            # Вывести данные в формате JSON
            for item in data:
                print(f"ID: {item.id}")
                print(f"Время: {item.timestamp}")
                print(f"IP: {item.ip_address}")
                print(f"Данные экрана: {item.screen_data}")
                print(f"Данные пользователя: {item.user_data}")
                if show_raw:
                    print(f"Исходные данные: {item.raw_data}")
                print("-" * 50)
        else:
            # Формируем таблицу
            table_data = []
            for item in data:
                row = [
                    item.id,
                    item.timestamp,
                    item.ip_address,
                    format_json(item.screen_data),
                    format_json(item.user_data)
                ]
                table_data.append(row)
            
            headers = ["ID", "Время", "IP-адрес", "Данные экрана", "Данные пользователя"]
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
            
            # Если нужно показать исходные данные
            if show_raw:
                record_id = input("\nВведите ID записи для просмотра исходных данных: ")
                try:
                    record_id = int(record_id)
                    for item in data:
                        if item.id == record_id:
                            print(f"\nИсходные данные для записи {record_id}:")
                            print(format_json(item.raw_data, max_length=10000))
                            break
                    else:
                        print(f"Запись с ID {record_id} не найдена.")
                except ValueError:
                    print("Некорректный ID записи.")
    except Exception as e:
        logger.error(f"Ошибка при получении данных: {e}")

if __name__ == "__main__":
    # Настраиваем аргументы командной строки
    parser = argparse.ArgumentParser(description="Просмотр данных из PostgreSQL")
    
    parser.add_argument("--limit", type=int, default=10, 
                        help="Ограничение количества записей (по умолчанию: 10)")
    parser.add_argument("--format", type=str, choices=["table", "json"], default="table",
                        help="Формат вывода: table или json (по умолчанию: table)")
    parser.add_argument("--raw", action="store_true", 
                        help="Показать исходные данные")
    
    args = parser.parse_args()
    
    # Отображаем данные
    view_data(limit=args.limit, format_type=args.format, show_raw=args.raw) 