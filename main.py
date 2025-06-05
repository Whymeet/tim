from post_loader import load_posts
from vk_screenshot import batch_screenshots
from report_generator import generate_report

def main():
    file_path = "posts.xlsx"  # Имя файла с постами
    output_dir = "assets"
    output_report = "Отчет.docx"

    print("Загрузка постов из файла...")
    posts = load_posts(file_path)

    print("Создание скриншотов постов...")
    batch_screenshots(posts, output_dir)

    print("Формирование отчёта...")
    generate_report(posts, output_report)

    print("Готово!")

if __name__ == "__main__":
    main()
