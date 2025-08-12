# config.py - Конфигурационный файл для настройки прокси и других параметров

# ==================== НАСТРОЙКИ ПРОКСИ ====================

# Включить/отключить использование прокси (True/False)
USE_PROXY = True

# Настройки прокси
PROXY_CONFIG = {
    "server": "http://176.114.220.207:1080",  # Адрес прокси-сервера
    # "username": "your_username",              # Имя пользователя (если нужна аутентификация)
    # "password": "your_password",              # Пароль (если нужна аутентификация)
}

# Альтернативная конфигурация прокси для разных сценариев
PROXY_CONFIGS = {
    "default": {
        "server": "http://176.114.220.207:1080",
        # "username": "user1",
        # "password": "pass1"
    },
    "backup": {
        "server": "http://backup-proxy.example.com:8080",
        # "username": "user2", 
        # "password": "pass2"
    },
    "socks": {
        "server": "socks5://socks-proxy.example.com:1080",
        # "username": "user3",
        # "password": "pass3"
    }
}

# Какую конфигурацию прокси использовать (если USE_PROXY = True)
ACTIVE_PROXY_CONFIG = "default"

# ==================== ДРУГИЕ НАСТРОЙКИ ====================

# Настройки браузера
BROWSER_CONFIG = {
    "headless": False,  # Запускать браузер в скрытом режиме
    "viewport_width": 1920,
    "viewport_height": 1200,
    "user_agent": None,  # Можно задать custom user agent
}

# Настройки таймаутов
TIMEOUTS = {
    "page_load": 60000,  # Таймаут загрузки страницы (мс)
    "network_idle": 10000,  # Таймаут ожидания сети (мс)
    "screenshot_delay": 2000,  # Задержка перед скриншотом (мс)
}

# Настройки VK Ads скриншотов
VK_ADS_CONFIG = {
    "demography_zoom": 0.6,  # Масштаб для демографии
    "geo_zoom": 0.7,         # Масштаб для географии
    "overview_zoom": 0.8,    # Общий масштаб
}


def get_proxy_config():
    """Возвращает активную конфигурацию прокси или None если прокси отключен"""
    if not USE_PROXY:
        return None
    
    if ACTIVE_PROXY_CONFIG in PROXY_CONFIGS:
        return PROXY_CONFIGS[ACTIVE_PROXY_CONFIG]
    else:
        return PROXY_CONFIG


def get_browser_config():
    """Возвращает конфигурацию браузера"""
    return BROWSER_CONFIG


def get_timeouts():
    """Возвращает настройки таймаутов"""
    return TIMEOUTS


def get_vk_ads_config():
    """Возвращает настройки VK Ads"""
    return VK_ADS_CONFIG