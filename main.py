from post_loader import load_posts
from vk_screenshot import batch_screenshots
from ads_screenshot import screenshot_group_stats
from report_generator import generate_report
import os


def main() -> None:
    """Entry‑point: makes screenshots & assembles Word report."""

    posts_file   = "posts.xlsx"            # таблица со ссылками
    output_dir   = "assets"                # куда кладём PNG‑и
    output_doc   = "Отчет.docx"            # итоговый DOCX
    ads_url      = (
        "https://ads.vk.com/hq/dashboard/ad_plans"
        "?sudo=vkads_3012708486%40mailru"
        "&mode=ads&attribution=conversion"
        "&date_from=01.04.2025&date_to=04.05.2025"
        "&sort=-created"
    )
    ad_plan_name = "Про_Роговское"         # точное имя рекламного плана

    # ensure workspace exists -------------------------------------------------
    os.makedirs(output_dir, exist_ok=True)

    print("Загрузка постов из файла…")
    posts = load_posts(posts_file)

    print("Создание скриншотов постов…")
    batch_screenshots(posts, output_dir)

    print("Съёмка статистики VK Ads…")
    # передаём ПАПКУ с результатами, чтобы ничего не удалялось по пути
    screenshot_group_stats(ad_plan_name, output_dir, ads_url)

    print("Формирование отчёта…")
    # generate_report ждёт posts, имя отчёта и (необяз.) assets_dir
    generate_report(posts, output_doc, assets_dir=output_dir)

    print(f"Готово! Отчёт сохранён как {output_doc}")


if __name__ == "__main__":
    main()
