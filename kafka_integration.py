from kafka import KafkaProducer
import json
import logging
import os
import platform
import socket

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Определяем, запущены ли мы в Docker или локально
IN_DOCKER = os.path.exists('/.dockerenv')

# Подбираем правильные адреса
if IN_DOCKER:
    DEFAULT_BOOTSTRAP_SERVERS = 'kafka:9092'
else:
    # Для локального запуска используем порт 29092 (внешний порт)
    DEFAULT_BOOTSTRAP_SERVERS = 'localhost:29092'

class KafkaClient:
    """Класс для работы с Kafka."""
    
    def __init__(self, bootstrap_servers=None, topic='user-data'):
        """
        Инициализация клиента Kafka.
        
        Args:
            bootstrap_servers (str): Адрес брокера Kafka
            topic (str): Название топика по умолчанию
        """
        if bootstrap_servers is None:
            bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', DEFAULT_BOOTSTRAP_SERVERS)
            
        self.bootstrap_servers = bootstrap_servers
        self.default_topic = topic
        self.producer = None
        
        # Проверим доступность сервера перед инициализацией
        self._check_server_availability()
        
        # Инициализируем продюсера
        self._init_producer()
    
    def _check_server_availability(self):
        """Проверяет доступность Kafka сервера и корректирует адрес при необходимости."""
        # Возможные адреса Kafka
        servers = [
            self.bootstrap_servers,  # Основной адрес
            'localhost:29092',       # Локальный внешний адрес
            'localhost:9092',        # Локальный адрес
            'kafka:9092'             # Адрес для Docker
        ]
        
        # Исключаем дубликаты
        unique_servers = list(set(servers))
        
        # Проверяем каждый адрес
        for server in unique_servers:
            host, port = server.split(':')
            try:
                socket.create_connection((host, int(port)), timeout=3)
                logger.info(f"Kafka сервер {server} доступен")
                
                # Используем доступный сервер
                if server != self.bootstrap_servers:
                    logger.info(f"Переключаемся на доступный сервер: {server}")
                    self.bootstrap_servers = server
                
                return True
            except (socket.timeout, socket.error) as e:
                logger.warning(f"Kafka сервер {server} недоступен: {e}")
        
        # Возвращаемся к исходному серверу, если ни один не доступен
        return False
    
    def _init_producer(self):
        """Инициализирует Kafka продюсера."""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',  # Подтверждение от всех реплик
                retries=3,   # Количество повторных попыток
                reconnect_backoff_ms=1000,  # Время ожидания между повторными подключениями
                reconnect_backoff_max_ms=10000  # Максимальное время ожидания
            )
            logger.info(f"Kafka продюсер успешно создан (сервер: {self.bootstrap_servers})")
        except Exception as e:
            logger.error(f"Ошибка при создании Kafka продюсера: {e}")
            self.producer = None
    
    def send_message(self, data, topic=None):
        """
        Отправляет сообщение в Kafka.
        
        Args:
            data (dict): Данные для отправки
            topic (str, optional): Топик. Если не указан, используется топик по умолчанию.
            
        Returns:
            bool: True, если сообщение успешно отправлено, иначе False
        """
        if self.producer is None:
            logger.error("Kafka продюсер не инициализирован")
            # Пробуем переинициализировать продюсера
            self._check_server_availability()
            self._init_producer()
            if self.producer is None:
                return False
        
        if topic is None:
            topic = self.default_topic
        
        try:
            future = self.producer.send(topic, data)
            self.producer.flush()  # Ждем, пока сообщение будет отправлено
            
            # Получаем результат
            record_metadata = future.get(timeout=10)
            logger.info(f"Сообщение успешно отправлено в топик {record_metadata.topic} "
                      f"раздел {record_metadata.partition} "
                      f"со смещением {record_metadata.offset}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в Kafka: {e}")
            return False
    
    def close(self):
        """Закрывает соединение с Kafka."""
        if self.producer:
            self.producer.close()
            logger.info("Соединение с Kafka закрыто")

# Создаем глобальный экземпляр клиента Kafka
kafka_client = None

def init_kafka(bootstrap_servers=None, topic='user-data'):
    """
    Инициализирует глобальный экземпляр клиента Kafka.
    
    Args:
        bootstrap_servers (str): Адрес брокера Kafka
        topic (str): Название топика по умолчанию
    """
    global kafka_client
    kafka_client = KafkaClient(bootstrap_servers, topic)
    return kafka_client

def get_kafka_client():
    """
    Возвращает глобальный экземпляр клиента Kafka.
    
    Returns:
        KafkaClient: Клиент Kafka или None, если клиент не инициализирован
    """
    return kafka_client 