from flask import Flask, render_template, request, jsonify
import datetime
import logging
from kafka_integration import init_kafka
import uuid
import json

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Инициализация Kafka клиента
kafka_client = None

@app.route('/')
def index():
    """Отображает главную страницу с кнопкой."""
    # Инициализируем Kafka клиент при первом запросе, если еще не инициализирован
    global kafka_client
    if kafka_client is None:
        logger.info("Инициализация Kafka клиента...")
        kafka_client = init_kafka(bootstrap_servers='kafka:9092', topic='user-data')
        logger.info("Kafka клиент инициализирован")
    
    return render_template('index.html')

@app.route('/api/send-data', methods=['POST'])
def send_data():
    """Обрабатывает данные, отправленные с клиента."""
    # Проверяем, инициализирован ли Kafka клиент
    global kafka_client
    if kafka_client is None:
        logger.info("Инициализация Kafka клиента...")
        kafka_client = init_kafka(bootstrap_servers='kafka:9092', topic='user-data')
        logger.info("Kafka клиент инициализирован")
    
    # Логируем заголовки и содержимое запроса
    logger.info(f"Получен запрос: {request.method} {request.path}")
    logger.info(f"Заголовки: {dict(request.headers)}")
    
    try:
        data = request.json or {}
        logger.info(f"Тело запроса: {data}")
        
        # Добавляем время получения запроса
        data['timestamp'] = datetime.datetime.now().isoformat()
        
        # Получаем IP-адрес пользователя
        data['ip_address'] = request.remote_addr
        
        # Добавляем информацию о пользовательском агенте
        data['user_agent'] = request.headers.get('User-Agent', '')
        
        # Добавляем информацию о странице и реферере
        data['page_url'] = request.headers.get('Referer', request.url)
        data['referrer'] = request.referrer
        
        # Получаем или генерируем user_id (для совместимости с mouseTracker)
        if 'userId' in data:
            data['user_id'] = data.pop('userId')  # Переименовываем userId в user_id
        
        # Генерируем или получаем session_id
        if 'session_id' not in data:
            data['session_id'] = str(uuid.uuid4())
        
        # Устанавливаем тип события по умолчанию, если не указан
        if 'event_type' not in data:
            data['event_type'] = 'page_view'
        
        # Обработка событий движения мыши
        if data['event_type'] == 'mouse_move':
            # Сохраняем координаты как отдельные поля
            data['mouse_x'] = data.get('x', 0)
            data['mouse_y'] = data.get('y', 0)
            
            # Дополнительно сохраняем в лог файл
            log_mouse_movement(data)
        
        # Выводим данные в консоль
        logger.info(f"Подготовленные данные для отправки: {data}")
        
        # Отправляем данные в Kafka
        if kafka_client:
            success = kafka_client.send_message(data)
            if success:
                logger.info("Данные успешно отправлены в Kafka")
            else:
                logger.error("Ошибка при отправке данных в Kafka")
        else:
            logger.error("Kafka клиент не инициализирован")
        
        return jsonify({"status": "success", "message": "Данные успешно получены"})
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}", exc_info=True)
        return jsonify({"status": "error", "message": f"Ошибка: {str(e)}"}), 500

def log_mouse_movement(data):
    """Логирует движения мыши в отдельный файл для анализа"""
    try:
        # Создаем запись лога в формате JSON
        log_entry = {
            'timestamp': data.get('timestamp'),
            'user_id': data.get('user_id'),
            'session_id': data.get('session_id'),
            'x': data.get('mouse_x'),
            'y': data.get('mouse_y'),
            'ip_address': data.get('ip_address'),
            'user_agent': data.get('user_agent')
        }
        
        # Записываем в файл
        with open('logs/mouse-movements.log', 'a') as log_file:
            log_file.write(json.dumps(log_entry) + '\n')
            
        logger.info(f"Координаты мыши сохранены в лог: X={data.get('mouse_x')}, Y={data.get('mouse_y')}")
    except Exception as e:
        logger.error(f"Ошибка при записи в лог движений мыши: {e}", exc_info=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0') 