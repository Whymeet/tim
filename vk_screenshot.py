import os
import json
import logging
from playwright.sync_api import sync_playwright
from screenshot_utils import draw_browser_bar
from config import get_proxy_config, get_browser_config, get_timeouts

def load_vk_cookies():
    with open('vk_storage.json', 'r', encoding='utf-8') as f:
        storage_data = json.load(f)
        return storage_data.get('cookies', [])

def take_screenshot_with_views(url, output_file):
    # Получаем конфигурации
    proxy_config = get_proxy_config()
    browser_config = get_browser_config()
    timeouts = get_timeouts()
    
    with sync_playwright() as p:
        # Конфигурация запуска браузера
        launch_args = {"headless": browser_config["headless"]}
        
        # Добавляем прокси если он настроен
        if proxy_config:
            launch_args["proxy"] = proxy_config
            logging.info(f"🌐 Используется прокси: {proxy_config['server']}")
        else:
            logging.info("🌐 Прокси не используется")
            
        browser = p.chromium.launch(**launch_args)
        
        # Создаем контекст с настройками viewport
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

        cookies = load_vk_cookies()
        context.add_cookies(cookies)

        page = context.new_page()
        logging.info(f"Открываю пост: {url}")
        try:
            page.goto(url, timeout=timeouts["page_load"], wait_until="domcontentloaded")
        except Exception as e:
            logging.error(f"Ошибка загрузки страницы: {e}")
            browser.close()
            return

        page.wait_for_timeout(timeouts["screenshot_delay"])

        try:
            date_elem = page.locator('[data-testid="post_date_block_preview"]')
            if date_elem.count() > 0:
                date_elem.hover()
                page.wait_for_timeout(1500)
        except Exception as e:
            logging.warning(f"Ошибка при наведении на дату: {e}")

        try:
            post = page.locator('.Post, .wall_post_text, .post')
            if post.count() > 0:
                # Получаем координаты поста
                post_box = post.first.bounding_box()
                if post_box:
                    # Расширяем область захвата для более широкого скриншота
                    page_width = page.evaluate("document.documentElement.scrollWidth")
                    viewport_width = page.evaluate("window.innerWidth")
                    full_width = max(page_width, viewport_width, 1200)  # Минимум 1200px
                    
                    # Создаем расширенную область
                    expanded_area = {
                        "x": 0,  # Начинаем с левого края
                        "y": max(0, post_box["y"] - 50),  # Отступ сверху
                        "width": full_width,  # Полная ширина
                        "height": post_box["height"] + 100  # Отступ снизу
                    }
                    
                    page.screenshot(path=output_file, clip=expanded_area)
                    logging.info(f"📸 Расширенный скриншот поста: {output_file}")
                else:
                    # Fallback: скриншот элемента поста
                    post.first.screenshot(path=output_file)
            else:
                page.screenshot(path=output_file, full_page=True)
        except Exception as e:
            logging.error(f"Ошибка при создании скрина: {e}")
        finally:
            browser.close()

    draw_browser_bar(output_file, url)

def batch_screenshots(posts, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    for i, post in enumerate(posts):
        url = post['Ссылка']
        file_name = f"post_{i+1}.png"
        file_path = os.path.join(output_dir, file_name)
        logging.info(f"[{i+1}/{len(posts)}] Скриншот: {url} -> {file_path}")
        take_screenshot_with_views(url, file_path)
        post['Скриншот'] = file_path
