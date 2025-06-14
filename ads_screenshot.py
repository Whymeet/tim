from playwright.sync_api import sync_playwright
import os

def is_captcha(page):
    # Проверяем наличие капчи по разным селекторам
    return page.locator('input[name="captcha_key"], .page_block_captcha, [id*="captcha"], :text("Я не робот")').count() > 0

def screenshot_group_stats(group_name, output_file, ads_url):
    """Take a screenshot of the VK Ads dashboard page."""
    with sync_playwright() as p:
        # Используем сессию из vk_storage.json
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state="vk_storage.json", viewport={"width": 1400, "height": 900})
        page = context.new_page()

        print(f"Открываю VK Ads: {ads_url}")
        page.goto(ads_url, timeout=60000)

        try:
            page.wait_for_load_state("networkidle", timeout=3000)
        except:
            print("Предупреждение: networkidle не наступил для VK Ads, продолжаем...")

        page.wait_for_timeout(4000)

        print("Если есть капча или нужно авторизоваться - сделай это сейчас")
        input("Когда страница VK Ads полностью загрузилась, нажми Enter...")

        try:
            context.storage_state(path="vk_storage.json")

            print(f"Ищу компанию '{group_name}' через поиск...")
            search_input = page.locator("input[type='search']")
            if search_input.count() > 0:
                search_input.first.fill(group_name)
                page.wait_for_timeout(1000)

                variant = page.locator("[data-testid='search-contains-menu-item']")
                if variant.count() > 0:
                    variant.first.click()
                    page.wait_for_timeout(2000)
                else:
                    print("❌ Не найден вариант 'Содержит', пробуем дальше без выбора...")
            else:
                print("❌ Поле поиска не найдено, пробуем без него...")

            print(f"Ищу кнопку статистики у компании '{group_name}'...")
            stats_icon = page.locator("svg.vkuiIcon--poll_outline_20")
            if stats_icon.count() > 0:
                stats_icon.first.click()
                print("✅ Клик по иконке статистики выполнен")
                page.wait_for_timeout(3000)
                input("Проверь, что окно статистики открылось правильно, нажми Enter для скриншота...")
            else:
                print("❌ Не найден svg с классом vkuiIcon--poll_outline_20, найди и нажми вручную")
                input("Когда статистика откроется, нажми Enter...")

            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            page.screenshot(path=output_file, full_page=True)
            print(f"✅ Скриншот VK Ads сохранен: {output_file}")

        except Exception as e:
            print(f"❌ Ошибка при создании скриншота VK Ads: {e}")
            try:
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                page.screenshot(path=output_file, full_page=True)
                print(f"✅ Скриншот (резервный) сохранен: {output_file}")
            except:
                raise e
        finally:
            browser.close()
