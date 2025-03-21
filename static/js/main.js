// Функция для отправки данных на сервер при нажатии кнопки
document.addEventListener('DOMContentLoaded', function() {
    // Находим кнопку отправки данных
    const sendDataButton = document.getElementById('send_data');
    const resultContainer = document.getElementById('results');
    const resultContent = document.getElementById('result_content');
    
    // Проверяем, что кнопка существует
    if (sendDataButton) {
        console.log('Кнопка найдена, добавляем обработчик события');
        // Обработка нажатия кнопки
        sendDataButton.addEventListener('click', function() {
            console.log('Кнопка нажата');
            // Собираем данные из формы
            const eventType = document.getElementById('event_type').value;
            let customData = {};
            
            try {
                const customDataInput = document.getElementById('custom_data').value;
                if (customDataInput) {
                    customData = JSON.parse(customDataInput);
                }
            } catch (e) {
                alert('Ошибка в формате JSON данных!');
                console.error('Ошибка JSON:', e);
                return;
            }
            
            // Создаем объект данных для отправки
            const data = {
                event_type: eventType,
                ...customData
            };
            
            console.log('Отправляем данные:', data);
            
            // Отправляем данные на сервер
            fetch('/api/send-data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
            .then(response => {
                console.log('Получен ответ:', response);
                if (!response.ok) {
                    throw new Error('Сетевая ошибка: ' + response.status);
                }
                return response.json();
            })
            .then(result => {
                // Отображаем результат
                console.log('Результат:', result);
                resultContent.textContent = JSON.stringify(result, null, 2);
                resultContainer.style.display = 'block';
            })
            .catch(error => {
                console.error('Ошибка при отправке данных:', error);
                resultContent.textContent = 'Ошибка: ' + error.message;
                resultContainer.style.display = 'block';
            });
        });
    } else {
        console.error('Кнопка отправки данных не найдена!');
    }
}); 