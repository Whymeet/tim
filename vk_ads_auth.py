from playwright.sync_api import sync_playwright

from vk_ads_context import create_vk_ads_context


def auth_vk_ads():
    """Авторизация специально для VK Ads и сохранение сессии."""

    with sync_playwright() as p:
        context = create_vk_ads_context(p)
        try:
            page = context.new_page()

            print("Открываю VK Ads для авторизации...")
            page.goto("https://ads.vk.com/hq/dashboard/ad_groups")

            print("Войди в свой VK-аккаунт через VK Ads.")
            print("Пройди все проверки, двухфакторку если нужно.")
            print("Дождись полной загрузки страницы с рекламными группами.")

            input("Когда страница VK Ads полностью загрузится и ты авторизован, нажми Enter...")

            # Сохраняем сессию специально для VK Ads
            context.storage_state(path="vk_storage.json")
            print("✅ Сессия VK Ads сохранена в vk_storage.json")
        finally:
            context.close()


if __name__ == "__main__":
    auth_vk_ads()
