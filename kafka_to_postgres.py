import json
import logging
import time
import socket
from kafka import KafkaConsumer
from db_models import get_db_manager
import os

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Параметры подключения к Kafka
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')  # Имя сервиса из docker-compose
KAFKA_TOPIC = 'user-data'
MAX_WAIT_TIME = 60  # Максимальное время ожидания в секундах

def process_message(msg_value):
    """Обрабатывает сообщение из Kafka и сохраняет его в PostgreSQL."""
    try:
        # Преобразуем сообщение из JSON
        if isinstance(msg_value, bytes):
            data = json.loads(msg_value.decode('utf-8'))
        else:
            data = json.loads(msg_value)
            
        # Логируем полученные данные
        logger.info(f"Получены данные: {data.get('ip_address', 'нет IP')}, событие: {data.get('event_type', 'нет типа')}")
        logger.debug(f"Полные данные: {data}")
        
        # Форматируем данные для таблицы analytics
        analytics_data = {
            'ip_address': data.get('ip_address', ''),
            'event_type': data.get('event_type', 'page_view'),
            'user_agent': data.get('user_agent', ''),
            'page_url': data.get('page_url', ''),
            'referrer': data.get('referrer', ''),
            'session_id': data.get('session_id', ''),
            'data': data  # Сохраняем все данные полностью
        }
        
        # Сохраняем данные в PostgreSQL
        db_manager = get_db_manager()
        record_id = db_manager.save_analytics(analytics_data)
        logger.info(f"Аналитические данные сохранены в PostgreSQL, ID: {record_id}")
        
        return record_id
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}", exc_info=True)
        return None

def wait_for_services():
    """Проверяет доступность сервисов Kafka и PostgreSQL."""
    start_time = time.time()
    
    # Ждем пока сервисы будут доступны или истечет время ожидания
    while time.time() - start_time < MAX_WAIT_TIME:
        # Проверяем Kafka
        try:
            # Пробуем подключиться к Kafka
            socket.create_connection(('kafka', 9092), timeout=5)
            logger.info("Kafka доступна")
            
            # Проверяем PostgreSQL
            try:
                db_manager = get_db_manager()
                db_manager.init_db()
                logger.info("PostgreSQL доступна")
                return True
            except Exception as e:
                logger.warning(f"PostgreSQL недоступна: {e}")
        except Exception as e:
            logger.warning(f"Kafka недоступна: {e}")
        
        # Ждем 5 секунд перед повторной проверкой
        logger.info("Ожидание доступности сервисов...")
        time.sleep(5)
    
    logger.error(f"Время ожидания истекло ({MAX_WAIT_TIME} секунд)")
    return False

def consume_messages():
    """Потребляет сообщения из Kafka и сохраняет их в PostgreSQL."""
    try:
        # Инициализируем подключение к БД
        db_manager = get_db_manager()
        db_manager.init_db()
        
        # Создаем потребителя Kafka
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='kafka_to_postgres',
            value_deserializer=lambda x: x
        )
        
        logger.info(f"Запущен потребитель Kafka для темы '{KAFKA_TOPIC}'")
        logger.info(f"Подключение к Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
        
        # Слушаем сообщения
        for message in consumer:
            try:
                record_id = process_message(message.value)
                if record_id:
                    logger.info(f"Успешно обработано сообщение, ID записи: {record_id}")
            except Exception as e:
                logger.error(f"Ошибка при обработке сообщения: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Ошибка при запуске потребителя Kafka: {e}", exc_info=True)

if __name__ == "__main__":
    if wait_for_services():
        logger.info("Запуск потребителя Kafka -> PostgreSQL")
        consume_messages()
    else:
        logger.error("Не удалось подключиться к сервисам, завершение работы") 