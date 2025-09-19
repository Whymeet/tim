from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        executable_path=r"C:\Users\matve\AppData\Local\Yandex\YandexBrowser\Application\browser.exe",
        args=['--no-sandbox']
    )
    context = browser.new_context(
        viewport={"width": 1280, "height": 1000},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 YaBrowser/23.9.0.0 Safari/537.36",
        proxy={
            "server": "195.64.127.163:3939",
            "username": "user324020",
            "password": "n1dhr6"
        }
    )
    
    page = context.new_page()
    print("Открываем 2ip.ru...")
    page.goto("https://2ip.ru")
    print(f"Текущий IP: {page.locator('.ip').inner_text()}")
    time.sleep(10)  # Ждем 10 секунд, чтобы увидеть результат
    browser.close()