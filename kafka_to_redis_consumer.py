#!/usr/bin/env python3
"""
Консьюмер Kafka для чтения координат мыши из топика mouse_coordinates
и сохранения последней позиции в Redis.

Этот скрипт:
1. Подключается к Kafka и читает сообщения из топика mouse_coordinates
2. Устанавливает соединение с Redis
3. При получении сообщения, обновляет ключ latest_mouse_position в Redis
"""

import json
import logging
import time
from kafka import KafkaConsumer
import redis

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация Kafka
KAFKA_BOOTSTRAP_SERVERS = 'kafka1:9092,kafka2:9093'
KAFKA_TOPIC = 'mouse_coordinates'
KAFKA_GROUP_ID = 'redis-updater'

# Конфигурация Redis
REDIS_HOST = 'redis'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None  # Установите пароль, если он требуется
REDIS_KEY = 'latest_mouse_position'

def create_kafka_consumer():
    """Создает и возвращает консьюмер Kafka для чтения сообщений из топика координат мыши."""
    max_retries = 10
    current_retry = 0
    
    while current_retry < max_retries:
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=KAFKA_GROUP_ID,
                auto_offset_reset='latest',  # Начинаем с последних сообщений
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                enable_auto_commit=True,
                auto_commit_interval_ms=1000,  # Автоматически коммитим каждую секунду
                session_timeout_ms=30000,  # Таймаут сессии
                heartbeat_interval_ms=10000,  # Интервал сердцебиения
                max_poll_interval_ms=300000  # Максимальный интервал между poll()
            )
            logger.info(f"Kafka консьюмер создан. Топик: {KAFKA_TOPIC}, сервер: {KAFKA_BOOTSTRAP_SERVERS}")
            return consumer
        except Exception as e:
            current_retry += 1
            wait_time = 5 * current_retry  # Увеличиваем время ожидания с каждой попыткой
            logger.error(f"Ошибка при создании Kafka консьюмера (попытка {current_retry}/{max_retries}): {e}")
            logger.info(f"Повторная попытка через {wait_time} секунд...")
            time.sleep(wait_time)
    
    logger.error(f"Не удалось создать Kafka консьюмер после {max_retries} попыток")
    return None

def create_redis_client():
    """Создает и возвращает клиент Redis."""
    max_retries = 5
    current_retry = 0
    
    while current_retry < max_retries:
        try:
            client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=False  # Не декодируем ответы, так как храним JSON как строку
            )
            # Проверяем соединение
            client.ping()
            logger.info(f"Redis клиент создан. Хост: {REDIS_HOST}, порт: {REDIS_PORT}")
            return client
        except Exception as e:
            current_retry += 1
            wait_time = 3 * current_retry
            logger.error(f"Ошибка при создании Redis клиента (попытка {current_retry}/{max_retries}): {e}")
            logger.info(f"Повторная попытка через {wait_time} секунд...")
            time.sleep(wait_time)
    
    logger.error(f"Не удалось создать Redis клиент после {max_retries} попыток")
    return None

def process_messages(consumer, redis_client):
    """Обрабатывает сообщения из Kafka и обновляет данные в Redis."""
    try:
        logger.info("Начало обработки сообщений с координатами мыши...")
        
        # Начинаем чтение сообщений
        for message in consumer:
            try:
                # Получаем данные сообщения
                data = message.value
                
                # Логируем полученное сообщение
                logger.info(f"Получено сообщение: {data}")
                
                # Преобразуем данные обратно в JSON строку для хранения в Redis
                json_data = json.dumps(data)
                
                # Обновляем ключ в Redis
                redis_client.set(REDIS_KEY, json_data)
                
                # Логируем информацию
                logger.info(f"Обновлена позиция в Redis: X={data.get('x')}, Y={data.get('y')} от пользователя {data.get('userId')}")
                
            except Exception as e:
                logger.error(f"Ошибка при обработке сообщения: {e}")
    except KeyboardInterrupt:
        logger.info("Обработка координат остановлена пользователем")
    except Exception as e:
        logger.error(f"Ошибка при чтении сообщений из Kafka: {e}")
    finally:
        # Закрываем соединения при выходе
        if consumer:
            consumer.close()
            logger.info("Kafka консьюмер закрыт")

def main():
    """Основная функция скрипта."""
    logger.info("Запуск обработчика координат мыши Kafka -> Redis")
    
    # Непрерывный цикл для переподключения при сбоях
    while True:
        # Создаем Kafka консьюмер
        consumer = create_kafka_consumer()
        if not consumer:
            logger.error("Не удалось создать Kafka консьюмер. Повторная попытка через 10 секунд...")
            time.sleep(10)
            continue
        
        # Создаем Redis клиент
        redis_client = create_redis_client()
        if not redis_client:
            logger.error("Не удалось создать Redis клиент. Повторная попытка через 10 секунд...")
            if consumer:
                consumer.close()
            time.sleep(10)
            continue
        
        # Инициализируем ключ в Redis, если он не существует
        try:
            if not redis_client.exists(REDIS_KEY):
                redis_client.set(REDIS_KEY, json.dumps({"status": "waiting", "timestamp": time.time()}))
                logger.info(f"Инициализирован ключ {REDIS_KEY} в Redis")
        except Exception as e:
            logger.error(f"Ошибка при инициализации ключа в Redis: {e}")
        
        # Запускаем обработку сообщений
        try:
            process_messages(consumer, redis_client)
        except Exception as e:
            logger.error(f"Ошибка в основном процессе: {e}")
            logger.info("Перезапуск процесса через 10 секунд...")
            time.sleep(10)

if __name__ == "__main__":
    main() 