from kafka import KafkaConsumer
import json
import logging

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Константы
KAFKA_BOOTSTRAP_SERVERS = 'kafka:9092'
KAFKA_TOPIC = 'user-data'  # Топик с данными пользователей

def listen_kafka_topic():
    """Слушает топик Kafka и выводит полученные сообщения."""
    try:
        # Создаем консьюмера
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            auto_offset_reset='earliest',  # Читаем все сообщения, включая ранее отправленные
            group_id='web-listener',  # ID группы консьюмеров
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        
        logger.info(f"Слушаем топик {KAFKA_TOPIC}...")
        
        # Бесконечный цикл для чтения сообщений
        for message in consumer:
            logger.info(f"Получено сообщение: {message.value}")
            
    except KeyboardInterrupt:
        logger.info("Прослушивание прервано пользователем")
    except Exception as e:
        logger.error(f"Ошибка при прослушивании: {e}")

if __name__ == "__main__":
    listen_kafka_topic() 