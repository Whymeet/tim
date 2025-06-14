from playwright.sync_api import sync_playwright
import os

def is_captcha(page):
    # Проверяем наличие капчи по разным селекторам
    return page.locator('input[name="captcha_key"], .page_block_captcha, [id*="captcha"], :text("Я не робот")').count() > 0

def screenshot_group_stats(group_name, output_file, ads_url):
    """Take a screenshot of the VK Ads dashboard page."""
    with sync_playwright() as p:
        # Используем отдельный файл сессии для VK Ads
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state="vk_ads_storage.json", viewport={"width": 1400, "height": 900})
        page = context.new_page()
        
        print(f"Открываю VK Ads: {ads_url}")
        page.goto(ads_url, timeout=60000)
        
        # Ждем загрузки как в vk_screenshot.py
        try:
            page.wait_for_load_state("networkidle", timeout=1500)
        except:
            print("Предупреждение: networkidle не наступил для VK Ads, продолжаем...")
        
        page.wait_for_timeout(4000)

        # Всегда даем возможность пройти капчу вручную
        print("Если есть капча или нужно что-то сделать на странице VK Ads - сделай это сейчас")
        input("Когда страница VK Ads полностью загрузилась, нажми Enter для создания скриншота...")

        try:
            # Обновляем сессию после возможных действий
            context.storage_state(path="vk_ads_storage.json")
            
            # Создаем директорию если нужно
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            # Делаем скриншот всей страницы
            page.screenshot(path=output_file, full_page=True)
            print(f"✅ Скриншот VK Ads сохранен: {output_file}")
        except Exception as e:
            print(f"❌ Ошибка при создании скриншота VK Ads: {e}")
            raise e
        finally:
            browser.close()