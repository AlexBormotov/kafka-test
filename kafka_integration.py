from kafka import KafkaProducer
import json
import logging

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KafkaClient:
    """Класс для работы с Kafka."""
    
    def __init__(self, bootstrap_servers='kafka:9092', topic='user-data'):
        """
        Инициализация клиента Kafka.
        
        Args:
            bootstrap_servers (str): Адрес брокера Kafka
            topic (str): Название топика по умолчанию
        """
        self.bootstrap_servers = bootstrap_servers
        self.default_topic = topic
        self.producer = None
        
        # Инициализируем продюсера
        self._init_producer()
    
    def _init_producer(self):
        """Инициализирует Kafka продюсера."""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',  # Подтверждение от всех реплик
                retries=3,   # Количество повторных попыток
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

def init_kafka(bootstrap_servers='kafka:9092', topic='user-data'):
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