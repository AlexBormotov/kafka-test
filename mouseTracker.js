/**
 * Модуль для отслеживания движения мыши с ограничением частоты событий
 * и отправки координат на сервер
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
function sendCoordinates(x, y) {
  const payload = {
    userId: getUserId(),
    x,
    y
  };

  // URL API сервиса для логирования координат
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
    console.log('Ответ сервера:', data);
  })
  .catch(error => {
    console.error('Ошибка при отправке координат:', error);
  });
}

// Обработчик движения мыши с ограничением частоты
const handleMouseMove = throttle(event => {
  const { clientX, clientY } = event;
  sendCoordinates(clientX, clientY);
}, 250);

// Инициализация: подключение обработчика событий
function initMouseTracker() {
  document.addEventListener('mousemove', handleMouseMove);
  console.log('Отслеживание движения мыши активировано');
}

// Отключение отслеживания
function stopMouseTracker() {
  document.removeEventListener('mousemove', handleMouseMove);
  console.log('Отслеживание движения мыши остановлено');
}

// Экспорт функций для использования в других модулях
export { initMouseTracker, stopMouseTracker }; 