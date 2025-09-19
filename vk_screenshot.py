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
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 1000})

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
                    page_width = page.evaluate("document.documentElement.scrollWidth") or 0
                    viewport_width = page.evaluate("window.innerWidth") or 0
                    if viewport_width <= 0:
                        viewport_width = 1280  # fallback to the configured viewport
                    if page_width <= 0:
                        page_width = viewport_width

                    full_width = max(page_width, viewport_width, 1200)  # Минимум 1200px
                    clip_width = min(full_width, viewport_width)

                    post_center_x = post_box["x"] + post_box["width"] / 2
                    max_x_offset = max(page_width - clip_width, 0)
                    clip_x = max(0, min(post_center_x - clip_width / 2, max_x_offset))

                    # Создаем расширенную область
                    expanded_area = {
                        "x": clip_x,
                        "y": max(0, post_box["y"] - 50),  # Отступ сверху
                        "width": clip_width,
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
