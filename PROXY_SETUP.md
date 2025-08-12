# 🚀 Быстрый старт с прокси

## 1. Настройка прокси

### Простой способ (рекомендуется)
```bash
# Скопируйте пример конфигурации
copy config.example.py config.py

# Отредактируйте config.py:
# - Установите USE_PROXY = True
# - Укажите адрес прокси в PROXY_CONFIG
```

### Пример настройки в config.py:
```python
USE_PROXY = True

PROXY_CONFIG = {
    "server": "http://your-proxy-server.com:8080",
    # "username": "your_username",  # если нужна авторизация
    # "password": "your_password",  # если нужна авторизация
}
```

## 2. Проверка прокси

```bash
# Проверить подключение через прокси
python test_proxy.py
```

## 3. Переключение прокси

### Командная строка:
```bash
python proxy_toggle.py on   # включить
python proxy_toggle.py off  # отключить
python proxy_toggle.py      # статус
```

### Windows (графический интерфейс):
```bash
proxy_toggle.bat
```

## 4. Авторизация с прокси

```bash
# Обязательно настройте прокси ДО авторизации!
python vk_auth.py
```

## 5. Запуск основной программы

```bash
python main.py
```

## 📝 Типы прокси

- **HTTP**: `http://proxy.example.com:8080`
- **HTTPS**: `https://proxy.example.com:8080` 
- **SOCKS5**: `socks5://proxy.example.com:1080`

## 🔧 Множественные прокси

Можно настроить несколько прокси и переключаться между ними:

```python
PROXY_CONFIGS = {
    "default": {"server": "http://proxy1.com:8080"},
    "backup": {"server": "http://proxy2.com:3128"},
}

ACTIVE_PROXY_CONFIG = "default"  # какой использовать
```

## ❗ Важно

1. **Сначала настройте прокси, потом авторизуйтесь** - иначе куки могут быть недействительными
2. **Проверьте прокси** командой `python test_proxy.py` перед использованием
3. **Быстрое отключение**: `python proxy_toggle.py off` если что-то не работает

## 🔍 Диагностика проблем

```bash
# Проверить подключение
python test_proxy.py

# Посмотреть текущие настройки
python proxy_toggle.py

# Отключить прокси временно
python proxy_toggle.py off
```
