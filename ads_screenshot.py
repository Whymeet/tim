from playwright.sync_api import sync_playwright
import os

def is_captcha(page):
    # Проверяем наличие капчи по разным селекторам
    return page.locator('input[name="captcha_key"], .page_block_captcha, [id*="captcha"], :text("Я не робот")').count() > 0

def screenshot_group_stats(group_name, output_file, ads_url):
    """Open the VK Ads dashboard, find a group and capture its stats.

    The function loads the dashboard at ``ads_url``, searches the table for
    ``group_name`` and clicks the icon with ``poll_outline_20`` class to open
    the statistics view. The resulting page is saved as ``output_file``.
    """
    with sync_playwright() as p:
        # 1. Сначала headless режим
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="vk_storage.json", viewport={"width": 1400, "height": 900})
        page = context.new_page()
        page.goto(ads_url, timeout=60000)
        page.wait_for_timeout(6000)

        if is_captcha(page):
            print("Обнаружена капча! Откроется окно браузера, пройди капчу вручную.")
            browser.close()  # Закроем headless браузер

            # 2. Открываем не headless
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(storage_state="vk_storage.json", viewport={"width": 1400, "height": 900})
            page = context.new_page()
            page.goto(ads_url, timeout=60000)
            input("Пройди капчу, после решения и загрузки страницы нажми Enter в терминале...")
            # Сохраним новую сессию, чтобы потом использовать без капчи:
            context.storage_state(path="vk_storage.json")
            page.wait_for_timeout(3000)

        # --- После капчи (или если её не было) продолжаем как обычно:
        try:
            # Используем неполное совпадение текста, чтобы учесть различия в названии
            group_row = page.locator(f"text={group_name}").first
            if group_row.count() > 0:
                stat_btn = (
                    group_row
                    .locator('xpath=ancestor::tr')
                    .locator('svg[class*="poll_outline_20"]')
                    .first
                )
                if stat_btn.count() > 0:
                    stat_btn.click()
                    page.wait_for_load_state("networkidle")
                    os.makedirs(os.path.dirname(output_file), exist_ok=True)
                    page.screenshot(path=output_file, full_page=True)
                else:
                    print(f"Не найден значок статистики у группы {group_name}")
            else:
                print(f"Группа {group_name} не найдена в рекламном кабинете!")
        except Exception as e:
            print(f"Ошибка поиска группы: {e}")
        browser.close()
