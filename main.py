from post_loader import load_posts
from vk_screenshot import batch_screenshots
from ads_screenshot import screenshot_group_stats
from report_generator import generate_report
import os
import logging
import sys
from datetime import datetime


def main() -> None:
    """Полный цикл: загружаем XLSX, делаем скрины постов и VK Ads, формируем Word‑отчёт."""
    
    # Настройка логирования
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"vk_ads_log_{timestamp}.txt"
    
    # Настраиваем логгер для записи в файл и консоль
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Создаем логгер
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Запуск программы VK Ads Report Generator")
    logger.info(f"📝 Логи записываются в файл: {log_filename}")

    posts_file = "posts.xlsx"
    output_dir = "assets"
    output_doc = "Отчет.docx"
    ads_url = (
        "https://ads.vk.com/hq/dashboard/ad_groups"
        "?sudo=vkads_3012708486%40mailru"
        "&mode=ads&attribution=conversion"
        "&date_from=01.06.2025&date_to=18.08.2025"
        "&sort=-created"
    )

    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"📁 Рабочая папка: {output_dir}")

    logger.info("⏳ Читаю таблицу…")
    posts = load_posts(posts_file)
    logger.info(f"✅ Найдено {len(posts)} строк / ссылок")

    logger.info("📸 Делаю скрины постов…")
    batch_screenshots(posts, output_dir)
    logger.info("✅ Скрины постов готовы")

    done_groups: set[str] = set()
    for idx, post in enumerate(posts, 1):
        group_name = (post.get("Группа") or post.get("Название поста") or "").upper()
        if not group_name or group_name in done_groups:
            continue

        logger.info(f"📊 [{idx}/{len(posts)}] VK Ads для группы '{group_name}'…")
        try:
            screenshot_group_stats(
                group_name, 
                output_dir, 
                ads_url,
                demography_zoom=0.6,  # Сильно уменьшенный масштаб для демографии
                geo_zoom=0.7,         # Уменьшенный масштаб для географии (было 0.8)
                viewport_width=1920,
                viewport_height=1200
            )
            done_groups.add(group_name)
            logger.info("   ✅ Готово")
        except Exception as e:
            logger.error(f"   ⚠️  Не вышло: {e}")

    logger.info("📝 Собираю DOCX…")
    try:
        generate_report(posts, output_doc, assets_dir=output_dir, inner_image="inner.png")
    except TypeError:
        # Fallback для старой версии функции
        generate_report(posts, output_doc)

    logger.info("✅ Отчёт готов!")
    logger.info("🏁 Программа завершена успешно")


if __name__ == "__main__":
    main()
