#!/bin/bash
# Скрипт для очистки Docker перед запуском docker-compose
# Автор: Claude-проект
# Версия: 1.0

# Остановка всех контейнеров
echo "Останавливаем все контейнеры..."
docker-compose down

# Удаление всех контейнеров проекта
echo "Удаляем контейнеры проекта..."
docker rm -f $(docker ps -a -q --filter name=kafka-test) 2>/dev/null || true

# Поиск и удаление конфликтующих сетей
echo "Ищем и удаляем конфликтующие сети..."
NETWORKS=$(docker network ls --filter name=mouse-tracker -q)
if [ -n "$NETWORKS" ]; then
  echo "Найдены сети для удаления: $NETWORKS"
  for NET in $NETWORKS; do
    echo "Удаление сети: $NET"
    docker network rm $NET || true
  done
fi

# Поиск и удаление конфликтующих kafka сетей
KAFKA_NETWORKS=$(docker network ls --filter name=kafka-net -q)
if [ -n "$KAFKA_NETWORKS" ]; then
  echo "Найдены kafka сети для удаления: $KAFKA_NETWORKS"
  for NET in $KAFKA_NETWORKS; do
    echo "Удаление сети: $NET"
    docker network rm $NET || true
  done
fi

# Проверка существующих сетей
echo "Оставшиеся сети:"
docker network ls

echo "Очистка завершена. Теперь можно запустить docker-compose up -d" 