import time
from playwright.sync_api import sync_playwright

def emulate_human_behavior(page):
    """Эмулирует поведение реального пользователя"""
    # Случайные движения мышью
    page.mouse.move(200, 100)
    time.sleep(0.5)
    page.mouse.move(400, 300)
    time.sleep(0.3)
    
    # Эмуляция скролла
    page.mouse.wheel(0, 100)
    time.sleep(0.7)
    page.mouse.wheel(0, -50)
    time.sleep(0.5)
    
    # Добавляем fingerprint webgl и canvas
    page.evaluate("""() => {
        const webglVendor = 'Yandex';
        const webglRenderer = 'YaBrowser Direct3D11';
        
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) return webglVendor;
            if (parameter === 37446) return webglRenderer;
            return getParameter.apply(this, arguments);
        };
    }""")
    
    # Эмулируем типичные свойства браузера
    page.evaluate("""() => {
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {description: "Yandex PDF Viewer"},
                {description: "Yandex Media Player"}
            ],
        });
    }""")

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        executable_path=r"C:\Users\matve\AppData\Local\Yandex\YandexBrowser\Application\browser.exe",
        args=[
            '--no-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-site-isolation-trials',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu',
            '--window-size=1920,1080',
            '--start-maximized',
            '--lang=ru-RU,ru',
            f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 YaBrowser/23.9.0.0 Safari/537.36',
        ]
    )
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        locale="ru-RU",
        timezone_id="Europe/Moscow",
        color_scheme='light',
        accept_downloads=True,
        ignore_https_errors=True,
        java_script_enabled=True,
        has_touch=False,
        permissions=['geolocation', 'notifications'],
        extra_http_headers={
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'sec-ch-ua': '"YaBrowser";v="23.9", "Chromium";v="117"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1'
        },
        proxy={
            "server": "195.64.127.163:3939",
            "username": "user324020",
            "password": "n1dhr6"
        }
    )
    
    # Устанавливаем обработчик для каждой новой страницы
    context.on("page", lambda page: emulate_human_behavior(page))
    
    page = context.new_page()
    
    print("\n1. Сначала авторизуемся во ВКонтакте...")
    page.goto("https://vk.com/login", wait_until="networkidle", timeout=60000)
    print("📝 Войдите в свой VK-аккаунт...")
    input("[Нажмите Enter после входа в аккаунт]")
    time.sleep(2)
    
    # Проверяем успешность авторизации
    page.goto("https://vk.com/feed", wait_until="networkidle", timeout=60000)
    time.sleep(3)
    
    if "feed" not in page.url:
        print("❌ Похоже, авторизация не удалась. Попробуйте ещё раз.")
        browser.close()
        exit(1)
    
    print("✅ Авторизация во ВКонтакте успешна!")
    
    print("\n2. Теперь авторизуемся в рекламном кабинете...")
    page.goto("https://ads.vk.com/hq/dashboard/ad_plans", wait_until="networkidle", timeout=60000)
    print("⏳ Ожидание загрузки рекламного кабинета...")
    time.sleep(5)
    
    # Добавляем дополнительное ожидание и проверки
    if "auth" in page.url or "login" in page.url:
        print("🔄 Требуется дополнительная авторизация...")
        input("[Нажмите Enter после завершения авторизации]")
        time.sleep(3)
    
    print("\n3. Проверяем доступ к рекламному кабинету...")
    if "dashboard" not in page.url:
        print("❌ Не удалось получить доступ к рекламному кабинету!")
        print("🔍 Текущий URL:", page.url)
        browser.close()
        exit(1)
    
    print("✅ Доступ к рекламному кабинету получен!")
    print("\n4. Сохраняем данные авторизации...")
    context.storage_state(path="vk_storage.json")
    print("✅ Данные авторизации сохранены в vk_storage.json")
    
    # Даем время на визуальную проверку
    print("\n⏳ Можете проверить, что всё работает корректно...")
    input("[Нажмите Enter для завершения]")
    browser.close()
