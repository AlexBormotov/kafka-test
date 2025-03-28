/**
 * Простой сервер Node.js для имитации API бэкенда
 * и логирования координат мыши
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

// Создаем директорию для логов, если её нет
const logDir = path.join(__dirname, 'logs');
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir);
}

// Путь к файлу логов
const logFile = path.join(logDir, 'mouse-coordinates.log');

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
    req.on('end', () => {
      try {
        const data = JSON.parse(body);
        const timestamp = new Date().toISOString();
        
        // Формируем строку лога с меткой времени
        const logEntry = `${timestamp} | User: ${data.userId} | X: ${data.x}, Y: ${data.y}\n`;
        
        // Записываем в лог-файл
        fs.appendFile(logFile, logEntry, err => {
          if (err) {
            console.error('Ошибка записи в лог:', err);
          }
        });
        
        console.log(`Получены координаты: X=${data.x}, Y=${data.y} от пользователя ${data.userId}`);
        
        // Отправляем ответ
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ 
          status: 'success', 
          message: 'Координаты получены и записаны' 
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