import os
from playwright.sync_api import sync_playwright
from screenshot_utils import draw_browser_bar

def take_screenshot_with_views(url, output_file):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state="vk_storage.json", viewport={"width": 1280, "height": 1000})
        page = context.new_page()

        print(f"Открываю пост: {url}")
        page.goto(url, timeout=60000)

        try:
            page.wait_for_load_state("networkidle", timeout=1500)
        except:
            print("Предупреждение: networkidle не наступил, продолжаем...")

        page.wait_for_timeout(4000)

        try:
            post = page.locator('.Post, .wall_post_text, .post')
            if post.count() > 0:
                post.first.screenshot(path=output_file)
            else:
                page.screenshot(path=output_file, full_page=True)
        except Exception as e:
            print(f"Ошибка при создании скрина: {e}")
        finally:
            browser.close()

    draw_browser_bar(output_file, url)


def batch_screenshots(posts, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    for i, post in enumerate(posts):
        url = post['Ссылка']
        file_name = f"post_{i+1}.png"
        file_path = os.path.join(output_dir, file_name)
        print(f"[{i+1}/{len(posts)}] Скриншот: {url} -> {file_path}")
        take_screenshot_with_views(url, file_path)
        post['Скриншот'] = file_path
