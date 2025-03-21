from kafka import KafkaProducer, KafkaConsumer
import json
import time
import logging

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Константы
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
KAFKA_TOPIC = 'user-data'  # Топик, куда будем писать данные пользователей

def test_kafka_producer():
    """Тестирование отправки сообщения в Kafka."""
    try:
        # Создаем продюсера с сериализацией в JSON
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        # Тестовые данные - имитация данных от пользователя
        test_data = {
            'screen': {
                'width': 1920,
                'height': 1080
            },
            'user': {
                'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'language': 'ru-RU'
            },
            'timestamp': time.time(),
            'ip_address': '127.0.0.1'
        }
        
        # Отправляем сообщение
        future = producer.send(KAFKA_TOPIC, test_data)
        producer.flush()  # Дожидаемся отправки всех сообщений
        
        # Получаем результат
        record_metadata = future.get(timeout=10)
        logger.info(f"Сообщение успешно отправлено в топик {record_metadata.topic} "
                   f"раздел {record_metadata.partition} "
                   f"со смещением {record_metadata.offset}")
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")
        return False
    
def test_kafka_consumer():
    """Тестирование получения сообщения из Kafka."""
    try:
        # Создаем консьюмера
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset='earliest',  # Начинаем чтение с самого начала топика
            group_id='test-group',  # ID группы консьюмеров
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            consumer_timeout_ms=10000  # Таймаут в миллисекундах (10 секунд)
        )
        
        logger.info(f"Слушаем топик {KAFKA_TOPIC}...")
        
        # Читаем сообщения
        for message in consumer:
            logger.info(f"Получено сообщение: {message.value}")
            return True
        
        logger.warning("Сообщения не были получены за отведенное время")
        return False
    except Exception as e:
        logger.error(f"Ошибка при получении сообщения: {e}")
        return False

if __name__ == "__main__":
    logger.info("Запуск тестирования Kafka...")
    
    # Тестируем отправку сообщения
    if test_kafka_producer():
        logger.info("Тест отправки сообщения пройден успешно")
    else:
        logger.error("Тест отправки сообщения не пройден")
    
    # Небольшая пауза для обработки сообщения брокером
    time.sleep(2)
    
    # Тестируем получение сообщения
    if test_kafka_consumer():
        logger.info("Тест получения сообщения пройден успешно")
    else:
        logger.error("Тест получения сообщения не пройден") 