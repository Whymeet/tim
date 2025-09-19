import os
import json
import logging
from playwright.sync_api import sync_playwright
from screenshot_utils import draw_browser_bar

def load_vk_cookies():
    with open('vk_storage.json', 'r', encoding='utf-8') as f:
        storage_data = json.load(f)
        return storage_data.get('cookies', [])

def take_screenshot_with_views(url, output_file):
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

        cookies = load_vk_cookies()
        context.add_cookies(cookies)

        page = context.new_page()
        logging.info(f"Открываю пост: {url}")
        try:
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
        except Exception as e:
            logging.error(f"Ошибка загрузки страницы: {e}")
            browser.close()
            return

        page.wait_for_timeout(4000)

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

def check_current_ip(context):
    """Проверяет текущий IP через 2ip.ru"""
    page = context.new_page()
    try:
        page.goto("https://2ip.ru", timeout=30000)
        ip = page.locator('.ip').inner_text()
        logging.info(f"🌐 Текущий IP адрес: {ip}")
    except Exception as e:
        logging.error(f"Ошибка при проверке IP: {e}")
    finally:
        page.close()

def batch_screenshots(posts, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
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
        
        # Проверяем IP перед началом работы
        check_current_ip(context)
        
        for i, post in enumerate(posts):
            url = post['Ссылка']
            file_name = f"post_{i+1}.png"
            file_path = os.path.join(output_dir, file_name)
            logging.info(f"[{i+1}/{len(posts)}] Скриншот: {url} -> {file_path}")
            
            # Каждые 5 постов проверяем IP
            if i > 0 and i % 5 == 0:
                check_current_ip(context)
            
            # Создаем новую страницу для каждого поста
            page = context.new_page()
            try:
                take_screenshot_with_page(page, url, file_path)
            finally:
                page.close()
            
            post['Скриншот'] = file_path
        
        browser.close()

def take_screenshot_with_page(page, url, output_file):
    """Делает скриншот поста на заданной странице"""
    logging.info(f"Открываю пост: {url}")
    try:
        page.goto(url, timeout=60000, wait_until="domcontentloaded")
    except Exception as e:
        logging.error(f"Ошибка загрузки страницы: {e}")
        return

    page.wait_for_timeout(4000)

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

    draw_browser_bar(output_file, url)
