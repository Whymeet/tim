from post_loader import load_posts
from vk_screenshot import batch_screenshots
from report_generator import generate_report

def main():
    file_path = "posts.xlsx"
    output_dir = "assets"
    output_report = "Отчет.docx"
    ads_url = "https://ads.vk.com/hq/dashboard/ad_groups?sudo=vkads_3012708486%40mailru&mode=ads&attribution=conversion&date_from=01.04.2025&date_to=04.05.2025&sort=-created"

    print("Загрузка постов из файла...")
    posts = load_posts(file_path)

    print("Создание скриншотов постов и статистики групп...")
    batch_screenshots(posts, output_dir, ads_url)

    print("Формирование отчёта...")
    generate_report(posts, output_report)

    print("Готово!")

if __name__ == "__main__":
    main()
