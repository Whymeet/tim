from post_loader import load_posts
from vk_screenshot import batch_screenshots
from ads_screenshot import screenshot_group_stats
from report_generator import generate_report
import os

def main():
    file_path = "posts.xlsx"  # Имя файла с постами
    output_dir = "assets"
    output_report = "Отчет.docx"
    
    # URL для статистики VK Ads
    ads_url = "https://ads.vk.com/hq/dashboard/ad_plans?sudo=vkads_3012708486%40mailru&mode=ads&attribution=conversion&date_from=01.04.2025&date_to=04.05.2025&sort=-created"
    ads_screenshot_path = os.path.join(output_dir, "vk_ads_stats.png")

    print("Загрузка постов из файла...")
    posts = load_posts(file_path)

    print("Создание скриншотов постов...")
    batch_screenshots(posts, output_dir)

    print("Создание скриншота статистики VK Ads...")
    ads_screenshot_success = False
    try:
        screenshot_group_stats("VK Ads Dashboard", ads_screenshot_path, ads_url)
        # Проверяем, что файл действительно создался
        if os.path.exists(ads_screenshot_path):
            file_size = os.path.getsize(ads_screenshot_path)
            print(f"✅ Скриншот VK Ads успешно создан: {ads_screenshot_path} (размер: {file_size} байт)")
            ads_screenshot_success = True
        else:
            print(f"❌ Файл скриншота не найден: {ads_screenshot_path}")
    except Exception as e:
        print(f"❌ Ошибка при создании скриншота VK Ads: {e}")

    print("Формирование отчёта...")
    # Передаем путь только если скриншот успешно создан
    final_ads_path = ads_screenshot_path if ads_screenshot_success else None
    generate_report(posts, output_report, final_ads_path)

    print("Готово!")
    print(f"Проверь отчет: {output_report}")
    if ads_screenshot_success:
        print(f"Скриншот VK Ads включен в отчет")
    else:
        print("⚠️ Скриншот VK Ads НЕ включен в отчет")

if __name__ == "__main__":
    main()