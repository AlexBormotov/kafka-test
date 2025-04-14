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
    DEFAULT_BOOTSTRAP_SERVERS = 'kafka1:9092,kafka2:9093'
else:
    # Для локального запуска используем порты 29092 и 29093 (внешние порты)
    DEFAULT_BOOTSTRAP_SERVERS = 'localhost:29092,localhost:29093'

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
        # Обрабатываем случай, когда передана строка с несколькими серверами
        servers_to_check = []
        
        # Разбиваем строку bootstrap_servers, если в ней несколько серверов
        if ',' in self.bootstrap_servers:
            servers_to_check.extend(self.bootstrap_servers.split(','))
        else:
            servers_to_check.append(self.bootstrap_servers)
            
        # Добавляем другие возможные адреса Kafka
        servers_to_check.extend([
            'localhost:29092',  # Локальный внешний адрес
            'localhost:9092',   # Локальный адрес
            'kafka:9092'        # Адрес для Docker
        ])
        
        # Исключаем дубликаты
        unique_servers = list(set(servers_to_check))
        
        # Проверяем каждый адрес
        available_servers = []
        for server in unique_servers:
            server = server.strip()  # Убираем лишние пробелы
            try:
                host, port = server.split(':')
                socket.create_connection((host, int(port)), timeout=3)
                logger.info(f"Kafka сервер {server} доступен")
                available_servers.append(server)
            except ValueError as e:
                logger.error(f"Неверный формат адреса сервера {server}: {e}")
            except (socket.timeout, socket.error) as e:
                logger.warning(f"Kafka сервер {server} недоступен: {e}")
        
        # Если нашли доступные серверы, используем их
        if available_servers:
            if len(available_servers) > 1:
                # Если доступно несколько серверов, объединяем их обратно
                new_bootstrap_servers = ','.join(available_servers)
                if new_bootstrap_servers != self.bootstrap_servers:
                    logger.info(f"Переключаемся на доступные серверы: {new_bootstrap_servers}")
                    self.bootstrap_servers = new_bootstrap_servers
            else:
                # Если доступен только один сервер
                if available_servers[0] != self.bootstrap_servers:
                    logger.info(f"Переключаемся на доступный сервер: {available_servers[0]}")
                    self.bootstrap_servers = available_servers[0]
            return True
        
        # Возвращаемся к исходному серверу, если ни один не доступен
        logger.warning("Ни один из серверов Kafka не доступен")
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