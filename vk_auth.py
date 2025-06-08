from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://vk.com/login")
    print("Войди в свой VK-аккаунт, пройди двухфакторку, если надо.")
    print("Далее зайди на https://ads.vk.com/hq/dashboard/ad_groups")
    input("Когда страница полностью загрузится и ты авторизован, нажми Enter в терминале...")
    context.storage_state(path="vk_storage.json")
    browser.close()
