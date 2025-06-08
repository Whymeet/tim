import os
from playwright.sync_api import sync_playwright
from screenshot_utils import draw_browser_bar

def take_screenshot_with_views(url, output_file):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="vk_storage.json", viewport={"width": 1280, "height": 1000})
        page = context.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_timeout(4000)
        try:
            date_elem = page.locator('[data-testid="post_date_block_preview"]')
            if date_elem.count() > 0:
                date_elem.hover()
                page.wait_for_timeout(1500)
            else:
                print("Не найден элемент с датой для наведения!")
        except Exception as e:
            print(f"Ошибка при поиске и наведении на дату: {e}")
        post = page.locator('.Post, .wall_post_text, .post')
        if post.count() > 0:
            post.first.screenshot(path=output_file)
        else:
            page.screenshot(path=output_file, full_page=True)
        browser.close()
    draw_browser_bar(output_file, url)

def batch_screenshots(posts, output_dir, ads_url):
    from ads_screenshot import screenshot_group_stats
    os.makedirs(output_dir, exist_ok=True)
    for i, post in enumerate(posts):
        url = post['Ссылка']
        file_name = f"post_{i+1}.png"
        file_path = os.path.join(output_dir, file_name)
        print(f"[{i+1}/{len(posts)}] Скриншот: {url} -> {file_path}")
        take_screenshot_with_views(url, file_path)
        post['Скриншот'] = file_path

        # Теперь делаем скрин статистики группы
        group_name = post['Название поста']
        group_stats_path = os.path.join(output_dir, f"group_stats_{i+1}.png")
        screenshot_group_stats(group_name, group_stats_path, ads_url)
        post['Групповая статистика'] = group_stats_path
