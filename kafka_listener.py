from kafka import KafkaConsumer
import json
import logging
import os
import time
import socket
import platform

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Константы
# Определяем, запущены ли мы в Docker или локально
IN_DOCKER = os.path.exists('/.dockerenv')
HOST_PLATFORM = platform.system()  # Windows, Linux, Darwin (macOS)

# Подбираем правильные адреса
if IN_DOCKER:
    DEFAULT_BOOTSTRAP_SERVERS = 'kafka:9092'
else:
    # Для локального запуска используем порт 29092 (внешний порт)
    DEFAULT_BOOTSTRAP_SERVERS = 'localhost:29092' 

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', DEFAULT_BOOTSTRAP_SERVERS)
KAFKA_TOPIC = 'user-data'  # Топик с данными пользователей
MAX_RETRIES = 30
RETRY_INTERVAL = 5  # секунд

def is_kafka_available(bootstrap_servers):
    """Проверяет доступность Kafka сервера."""
    server = bootstrap_servers.split(',')[0]
    host, port = server.split(':')
    try:
        socket.create_connection((host, int(port)), timeout=3)
        logger.info(f"Kafka сервер {bootstrap_servers} доступен")
        return True
    except (socket.timeout, socket.error) as e:
        logger.warning(f"Kafka сервер {bootstrap_servers} недоступен: {e}")
        return False

def listen_kafka_topic():
    """Слушает топик Kafka и выводит полученные сообщения."""
    logger.info(f"Платформа: {HOST_PLATFORM}, Docker: {IN_DOCKER}")
    
    # Возможные адреса Kafka
    servers = [
        KAFKA_BOOTSTRAP_SERVERS,  # Основной адрес (из переменной)
        'localhost:29092',        # Локальный внешний адрес
        'localhost:9092',         # Локальный адрес 
        'kafka:9092'              # Адрес для Docker
    ]
    
    # Проверяем каждый адрес Kafka
    kafka_server = None
    available_servers = []
    
    # Сначала соберем все доступные серверы
    for server in set(servers):
        if is_kafka_available(server):
            available_servers.append(server)
    
    # Затем выберем наиболее подходящий сервер
    if available_servers:
        if IN_DOCKER and 'kafka:9092' in available_servers:
            # В Docker предпочитаем внутренний адрес
            kafka_server = 'kafka:9092'
        elif 'localhost:29092' in available_servers:
            # Для локального запуска предпочитаем внешний порт
            kafka_server = 'localhost:29092'
        else:
            # Иначе берем первый доступный
            kafka_server = available_servers[0]
    
    if not kafka_server:
        logger.error("Не удалось подключиться ни к одному серверу Kafka")
        for retry in range(MAX_RETRIES):
            logger.info(f"Повторная попытка подключения ({retry+1}/{MAX_RETRIES})...")
            time.sleep(RETRY_INTERVAL)
            
            for server in set(servers):
                if is_kafka_available(server):
                    kafka_server = server
                    break
            
            if kafka_server:
                break
        
        if not kafka_server:
            logger.error(f"Не удалось подключиться к Kafka после {MAX_RETRIES} попыток")
            return
    
    logger.info(f"Использую сервер Kafka: {kafka_server}")
    
    try:
        # Создаем консьюмера
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=kafka_server,
            auto_offset_reset='earliest',  # Читаем все сообщения, включая ранее отправленные
            group_id='web-listener',  # ID группы консьюмеров
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            request_timeout_ms=90000,      # Увеличиваем тайм-аут (должен быть больше session_timeout_ms)
            session_timeout_ms=60000,
            heartbeat_interval_ms=20000,
            # Отключаем автоматический поиск других узлов
            api_version_auto_timeout_ms=30000,
            # Игнорируем ошибки DNS, так как мы уже проверили соединение
            reconnect_backoff_ms=1000,
            reconnect_backoff_max_ms=10000
        )
        
        logger.info(f"Слушаем топик {KAFKA_TOPIC}...")
        
        # Бесконечный цикл для чтения сообщений
        for message in consumer:
            logger.info(f"Получено сообщение: {message.value}")
            
    except KeyboardInterrupt:
        logger.info("Прослушивание прервано пользователем")
    except Exception as e:
        logger.error(f"Ошибка при прослушивании: {e}")
        # Перезапускаем прослушивание при ошибке
        time.sleep(5)
        listen_kafka_topic()

if __name__ == "__main__":
    listen_kafka_topic() 