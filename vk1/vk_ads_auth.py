from playwright.sync_api import sync_playwright

def auth_vk_ads():
    """Авторизация специально для VK Ads и сохранение сессии"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        print("Открываю VK Ads для авторизации...")
        page.goto("https://ads.vk.com/hq/dashboard/ad_groups")
        
        print("Войди в свой VK-аккаунт через VK Ads.")
        print("Пройди все проверки, двухфакторку если нужно.")
        print("Дождись полной загрузки страницы с рекламными группами.")
        
        input("Когда страница VK Ads полностью загрузится и ты авторизован, нажми Enter...")
        
        # Сохраняем сессию специально для VK Ads
        context.storage_state(path="vk_ads_storage.json")
        print("✅ Сессия VK Ads сохранена в vk_ads_storage.json")
        
        browser.close()

if __name__ == "__main__":
    auth_vk_ads()