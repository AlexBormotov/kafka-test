#!/usr/bin/env python3
"""
Консьюмер Kafka для чтения координат мыши из топика mouse_coordinates

Этот скрипт подключается к Kafka, читает сообщения из топика mouse_coordinates
и выводит их в консоль, демонстрируя, что данные успешно публикуются.
"""

import json
import logging
from kafka import KafkaConsumer
import time

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_consumer(bootstrap_servers='kafka:9092', topic='mouse_coordinates', group_id='coordinates-consumer'):
    """Создает и возвращает консьюмер Kafka для чтения сообщений из указанного топика."""
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            auto_offset_reset='latest',  # Начинаем с последних сообщений
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            enable_auto_commit=True,
            auto_commit_interval_ms=1000  # Автоматически коммитим каждую секунду
        )
        logger.info(f"Kafka консьюмер создан. Топик: {topic}, сервер: {bootstrap_servers}")
        return consumer
    except Exception as e:
        logger.error(f"Ошибка при создании Kafka консьюмера: {e}")
        return None

def process_mouse_coordinates(consumer):
    """Обрабатывает сообщения с координатами мыши."""
    try:
        logger.info("Начало чтения координат мыши из Kafka...")
        
        # Создаем файл для логирования координат
        with open('logs/consumed_coordinates.log', 'a') as log_file:
            log_file.write(f"--- Начало сессии {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        
        # Начинаем чтение сообщений
        for message in consumer:
            try:
                data = message.value
                
                # Выводим основную информацию в консоль
                logger.info(f"Получены координаты: X={data.get('x')}, Y={data.get('y')} от пользователя {data.get('userId')}")
                
                # Записываем полное сообщение в лог-файл
                with open('logs/consumed_coordinates.log', 'a') as log_file:
                    log_file.write(json.dumps(data) + '\n')
                
            except Exception as e:
                logger.error(f"Ошибка при обработке сообщения: {e}")
    except KeyboardInterrupt:
        logger.info("Чтение координат остановлено пользователем")
    except Exception as e:
        logger.error(f"Ошибка при чтении сообщений из Kafka: {e}")
    finally:
        # Закрываем консьюмер при выходе
        if consumer:
            consumer.close()
            logger.info("Kafka консьюмер закрыт")

if __name__ == "__main__":
    logger.info("Запуск консьюмера координат мыши")
    
    # Создаем консьюмер
    consumer = create_consumer()
    
    if consumer:
        # Обрабатываем сообщения
        process_mouse_coordinates(consumer)
    else:
        logger.error("Не удалось создать Kafka консьюмер. Выход.") 