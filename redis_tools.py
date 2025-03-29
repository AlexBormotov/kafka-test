#!/usr/bin/env python3
"""
Утилита для работы с Redis.
Позволяет выполнять базовые операции и проверять наличие данных в Redis.
"""

import argparse
import json
import redis
import sys

# Конфигурация Redis
REDIS_HOST = 'redis'  # Имя сервиса в docker-compose
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None  # Установите пароль, если он требуется
REDIS_KEY = 'latest_mouse_position'  # Ключ по умолчанию

def connect_to_redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASSWORD):
    """Устанавливает соединение с Redis."""
    try:
        client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True  # Декодируем ответы для удобства отображения
        )
        # Проверяем соединение
        client.ping()
        print(f"Соединение с Redis установлено: {host}:{port}")
        return client
    except Exception as e:
        print(f"Ошибка при подключении к Redis: {e}")
        return None

def get_value(client, key=REDIS_KEY):
    """Получает значение по ключу из Redis."""
    try:
        value = client.get(key)
        if value:
            # Пытаемся распарсить JSON, если это возможно
            try:
                json_value = json.loads(value)
                return json.dumps(json_value, indent=2, ensure_ascii=False)
            except:
                return value
        else:
            return f"Ключ '{key}' не существует в Redis."
    except Exception as e:
        return f"Ошибка при получении значения из Redis: {e}"

def set_value(client, key, value):
    """Устанавливает значение по ключу в Redis."""
    try:
        client.set(key, value)
        return f"Значение для ключа '{key}' успешно установлено."
    except Exception as e:
        return f"Ошибка при установке значения в Redis: {e}"

def delete_key(client, key):
    """Удаляет ключ из Redis."""
    try:
        if client.exists(key):
            client.delete(key)
            return f"Ключ '{key}' успешно удален."
        else:
            return f"Ключ '{key}' не существует в Redis."
    except Exception as e:
        return f"Ошибка при удалении ключа из Redis: {e}"

def list_keys(client, pattern="*"):
    """Выводит список ключей в Redis, соответствующих шаблону."""
    try:
        keys = client.keys(pattern)
        if keys:
            return "\n".join(keys)
        else:
            return f"Ключи по шаблону '{pattern}' не найдены."
    except Exception as e:
        return f"Ошибка при получении списка ключей из Redis: {e}"

def main():
    """Основная функция утилиты."""
    # Настраиваем аргументы командной строки
    parser = argparse.ArgumentParser(description="Утилита для работы с Redis")
    
    # Параметры подключения к Redis
    parser.add_argument("--host", default=REDIS_HOST, help="Хост Redis сервера")
    parser.add_argument("--port", type=int, default=REDIS_PORT, help="Порт Redis сервера")
    parser.add_argument("--db", type=int, default=REDIS_DB, help="Номер БД Redis")
    parser.add_argument("--password", default=REDIS_PASSWORD, help="Пароль Redis")
    
    # Команды
    subparsers = parser.add_subparsers(dest="command", help="Команда")
    
    # get - получить значение по ключу
    get_parser = subparsers.add_parser("get", help="Получить значение по ключу")
    get_parser.add_argument("key", nargs="?", default=REDIS_KEY, help="Ключ для получения")
    
    # set - установить значение по ключу
    set_parser = subparsers.add_parser("set", help="Установить значение по ключу")
    set_parser.add_argument("key", help="Ключ для установки")
    set_parser.add_argument("value", help="Значение для установки")
    
    # delete - удалить ключ
    delete_parser = subparsers.add_parser("delete", help="Удалить ключ")
    delete_parser.add_argument("key", help="Ключ для удаления")
    
    # list - вывести список ключей
    list_parser = subparsers.add_parser("list", help="Вывести список ключей")
    list_parser.add_argument("pattern", nargs="?", default="*", help="Шаблон для поиска ключей")

    # Разбор аргументов
    args = parser.parse_args()
    
    # Подключаемся к Redis
    client = connect_to_redis(args.host, args.port, args.db, args.password)
    if not client:
        sys.exit(1)
    
    # Выполняем команду
    if args.command == "get":
        print(get_value(client, args.key))
    elif args.command == "set":
        print(set_value(client, args.key, args.value))
    elif args.command == "delete":
        print(delete_key(client, args.key))
    elif args.command == "list":
        print(list_keys(client, args.pattern))
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 