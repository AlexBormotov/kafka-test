/**
 * Модуль для прямой отправки координат мыши на выделенный API-эндпоинт
 * с ограничением частоты событий через троттлинг
 */

// Функция для ограничения частоты вызовов (троттлинг)
function throttle(callback, delay) {
  let lastCall = 0;
  return function(...args) {
    const now = Date.now();
    if (now - lastCall >= delay) {
      lastCall = now;
      callback.apply(this, args);
    }
  };
}

// Получение идентификатора пользователя из localStorage или генерация нового
function getUserId() {
  let userId = localStorage.getItem('userId');
  if (!userId) {
    userId = 'user-' + Math.random().toString(36).substring(2, 10);
    localStorage.setItem('userId', userId);
  }
  return userId;
}

// Отправка координат на сервер
function sendCoordinatesToAPI(x, y) {
  const payload = {
    userId: getUserId(),
    x,
    y
  };

  // Используем выделенный API-эндпоинт для координат
  const apiUrl = '/api/coordinates';

  fetch(apiUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
  .then(response => {
    if (!response.ok) {
      throw new Error('Ошибка при отправке данных');
    }
    return response.json();
  })
  .then(data => {
    console.log('Ответ сервера (прямой API):', data);
    // Генерируем событие для обновления статуса
    const event = new CustomEvent('direct-mousetracker:status', {
      detail: { success: true, message: 'Координаты успешно отправлены' }
    });
    window.dispatchEvent(event);
  })
  .catch(error => {
    console.error('Ошибка при отправке координат:', error);
    // Генерируем событие для обновления статуса
    const event = new CustomEvent('direct-mousetracker:status', {
      detail: { success: false, message: 'Ошибка: ' + error.message }
    });
    window.dispatchEvent(event);
  });
}

// Обработчик движения мыши с ограничением частоты
const handleDirectMouseMove = throttle(event => {
  const { clientX, clientY } = event;
  sendCoordinatesToAPI(clientX, clientY);
}, 250);

// Инициализация: подключение обработчика событий
function initDirectMouseTracker() {
  document.addEventListener('mousemove', handleDirectMouseMove);
  console.log('Прямое отслеживание движения мыши активировано');
}

// Отключение отслеживания
function stopDirectMouseTracker() {
  document.removeEventListener('mousemove', handleDirectMouseMove);
  console.log('Прямое отслеживание движения мыши остановлено');
} 