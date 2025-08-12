from playwright.sync_api import sync_playwright
from config import get_proxy_config, get_browser_config

# Получаем конфигурацию прокси
proxy_config = get_proxy_config()
browser_config = get_browser_config()

print("🔐 Скрипт авторизации VK")
if proxy_config:
    print(f"🌐 Прокси включен: {proxy_config['server']}")
else:
    print("🌐 Прокси отключен")

with sync_playwright() as p:
    # Конфигурация запуска браузера
    launch_args = {"headless": browser_config["headless"]}
    
    # Добавляем прокси если он настроен
    if proxy_config:
        launch_args["proxy"] = proxy_config
        
    browser = p.chromium.launch(**launch_args)
    
    # Создаем контекст с настройками
    context_args = {
        "viewport": {
            "width": browser_config["viewport_width"], 
            "height": browser_config["viewport_height"]
        }
    }
    
    # Добавляем user agent если указан
    if browser_config.get("user_agent"):
        context_args["user_agent"] = browser_config["user_agent"]
        
    context = browser.new_context(**context_args)
    page = context.new_page()
    
    page.goto("https://vk.com/login")
    print("Войди в свой VK-аккаунт, пройди двухфакторку, если надо.")
    print("Далее зайди на https://ads.vk.com/hq/dashboard/ad_groups")
    input("Когда страница полностью загрузится и ты авторизован, нажми Enter в терминале...")
    context.storage_state(path="vk_storage.json")
    browser.close()
    print("✅ Авторизация сохранена в vk_storage.json")
