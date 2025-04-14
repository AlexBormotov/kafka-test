import logging
import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Параметры подключения к базе данных
DB_USER = 'postgres'
DB_PASS = 'postgres'
DB_HOST = 'postgres'  # Имя сервиса из docker-compose
DB_PORT = '5433'
DB_NAME = 'mousetracker'  # Соответствует POSTGRES_DB в docker-compose

# Настройка соединения с базой данных
DATABASE_URL = f"postgresql+pg8000://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# База для моделей SQLAlchemy
Base = declarative_base()

# Модель для хранения данных пользователя
class UserData(Base):
    __tablename__ = 'user_data'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(50))
    screen_data = Column(Text)
    user_data = Column(Text)
    raw_data = Column(Text)

    def __repr__(self):
        return f"<UserData(id={self.id}, timestamp={self.timestamp}, ip={self.ip_address})>"

# Модель для хранения аналитических данных
class Analytics(Base):
    __tablename__ = 'analytics'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(50))
    event_type = Column(String(100))
    user_agent = Column(Text)
    page_url = Column(String(255))
    referrer = Column(String(255), nullable=True)
    session_id = Column(String(100), nullable=True)
    data = Column(Text)  # JSON данные с дополнительной информацией
    
    def __repr__(self):
        return f"<Analytics(id={self.id}, timestamp={self.timestamp}, event_type={self.event_type})>"

# Класс для управления базой данных
class DBManager:
    def __init__(self):
        self.engine = None
        self.Session = None
        self.initialized = False
        
    def init_db(self):
        """Инициализирует соединение с базой данных и создает таблицы."""
        try:
            logger.info(f"Подключение к базе данных: {DATABASE_URL}")
            self.engine = create_engine(DATABASE_URL)
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
            self.initialized = True
            logger.info("База данных успешно инициализирована")
        except Exception as e:
            logger.error(f"Ошибка при инициализации базы данных: {e}")
            raise
            
    def save_user_data(self, data):
        """Сохраняет данные пользователя в базу."""
        if not self.initialized:
            self.init_db()
        
        try:
            session = self.Session()
            user_data = UserData(
                ip_address=data.get('ip_address', ''),
                screen_data=json.dumps(data.get('screen_data', {})),
                user_data=json.dumps(data.get('user_data', {})),
                raw_data=json.dumps(data)
            )
            session.add(user_data)
            session.commit()
            logger.info(f"Данные пользователя сохранены, ID: {user_data.id}")
            return user_data.id
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при сохранении данных: {e}")
            raise
        finally:
            session.close()
            
    def get_all_user_data(self, limit=100):
        """Получает все записи данных пользователей с ограничением."""
        if not self.initialized:
            self.init_db()
            
        try:
            session = self.Session()
            data = session.query(UserData).order_by(UserData.timestamp.desc()).limit(limit).all()
            return data
        except Exception as e:
            logger.error(f"Ошибка при получении данных: {e}")
            raise
        finally:
            session.close()

    def save_analytics(self, data):
        """Сохраняет аналитические данные в базу."""
        if not self.initialized:
            self.init_db()
        
        try:
            session = self.Session()
            analytics = Analytics(
                ip_address=data.get('ip_address', ''),
                event_type=data.get('event_type', 'page_view'),
                user_agent=data.get('user_agent', ''),
                page_url=data.get('page_url', ''),
                referrer=data.get('referrer', ''),
                session_id=data.get('session_id', ''),
                data=json.dumps(data)
            )
            session.add(analytics)
            session.commit()
            logger.info(f"Аналитические данные сохранены, ID: {analytics.id}")
            return analytics.id
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка при сохранении аналитических данных: {e}")
            raise
        finally:
            session.close()
    
    def get_all_analytics(self, limit=100):
        """Получает все записи аналитических данных с ограничением."""
        if not self.initialized:
            self.init_db()
            
        try:
            session = self.Session()
            data = session.query(Analytics).order_by(Analytics.timestamp.desc()).limit(limit).all()
            return data
        except Exception as e:
            logger.error(f"Ошибка при получении аналитических данных: {e}")
            raise
        finally:
            session.close()

# Глобальный экземпляр менеджера базы данных
db_manager = None

def get_db_manager():
    """Возвращает экземпляр менеджера базы данных."""
    global db_manager
    if db_manager is None:
        db_manager = DBManager()
    return db_manager 