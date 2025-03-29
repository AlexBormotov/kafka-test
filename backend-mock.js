/**
 * Простой сервер Node.js для имитации API бэкенда
 * и логирования координат мыши, а также отправки их в Kafka
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const { Kafka } = require('kafkajs');

// Создаем директорию для логов, если её нет
const logDir = path.join(__dirname, 'logs');
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir);
}

// Путь к файлу логов
const logFile = path.join(logDir, 'mouse-coordinates.log');

// Настройка Kafka
const kafka = new Kafka({
  clientId: 'mouse-tracker-api',
  brokers: ['kafka1:9092', 'kafka2:9093'],
  retry: {
    initialRetryTime: 300,
    retries: 10
  }
});

// Создаем продюсера
const producer = kafka.producer();

// Флаг, указывающий, подключены ли мы к Kafka
let kafkaConnected = false;

// Подключаемся к Kafka
async function connectToKafka() {
  try {
    await producer.connect();
    console.log('Успешное подключение к Kafka');
    kafkaConnected = true;
  } catch (error) {
    console.error('Ошибка при подключении к Kafka:', error);
    // Пробуем переподключиться через некоторое время
    setTimeout(connectToKafka, 5000);
  }
}

// Вызываем функцию подключения
connectToKafka();

// Отправляем сообщение в Kafka
async function sendToKafka(topic, message) {
  if (!kafkaConnected) {
    console.log('Нет подключения к Kafka, сообщение не отправлено');
    return false;
  }
  
  try {
    await producer.send({
      topic,
      messages: [
        { value: JSON.stringify(message) }
      ],
    });
    console.log(`Сообщение успешно отправлено в топик ${topic}`);
    return true;
  } catch (error) {
    console.error(`Ошибка при отправке сообщения в Kafka: ${error}`);
    return false;
  }
}

// Создаем HTTP сервер
const server = http.createServer((req, res) => {
  // Устанавливаем CORS-заголовки для доступа с других источников
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  // Обрабатываем OPTIONS-запросы для поддержки CORS
  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }
  
  // Обрабатываем только POST-запросы к /api/coordinates
  if (req.method === 'POST' && req.url === '/api/coordinates') {
    let body = '';
    
    // Собираем фрагменты данных
    req.on('data', chunk => {
      body += chunk.toString();
    });
    
    // Обрабатываем полученные данные
    req.on('end', async () => {
      try {
        const data = JSON.parse(body);
        const timestamp = new Date().toISOString();
        
        // Добавляем временную метку
        data.timestamp = timestamp;
        
        // Добавляем IP-адрес
        data.ip_address = req.socket.remoteAddress;
        
        // Добавляем User-Agent если доступен
        data.user_agent = req.headers['user-agent'] || '';
        
        // Формируем строку лога с меткой времени
        const logEntry = JSON.stringify(data) + '\n';
        
        // Записываем в лог-файл
        fs.appendFile(logFile, logEntry, err => {
          if (err) {
            console.error('Ошибка записи в лог:', err);
          }
        });
        
        console.log(`Получены координаты: X=${data.x}, Y=${data.y} от пользователя ${data.userId}`);
        
        // Отправляем данные в Kafka
        const kafkaResult = await sendToKafka('mouse_coordinates', data);
        
        // Отправляем ответ
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ 
          status: 'success', 
          message: 'Координаты получены и записаны',
          kafka_sent: kafkaResult
        }));
      } catch (error) {
        console.error('Ошибка обработки данных:', error);
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ 
          status: 'error', 
          message: 'Некорректный формат данных' 
        }));
      }
    });
  } else {
    // Для всех остальных запросов возвращаем 404
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ 
      status: 'error', 
      message: 'Endpoint не найден' 
    }));
  }
});

// Порт сервера
const PORT = process.env.PORT || 3000;

// Запускаем сервер
server.listen(PORT, () => {
  console.log(`Сервер запущен на порту ${PORT}`);
  console.log(`Логи координат будут записаны в: ${logFile}`);
}); 