from post_loader import load_posts
from vk_screenshot import batch_screenshots
from ads_screenshot import screenshot_multiple_groups_stats
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
        "?sudo=vkads_3061384711%40mailru"
        "&mode=ads&attribution=conversion"
        "&date_from=01.01.2026&date_to=28.02.2026"
        "&sort=-stats.total.base.spent"
    )

    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"📁 Рабочая папка: {output_dir}")

    logger.info("⏳ Читаю таблицу…")
    posts = load_posts(posts_file)
    logger.info(f"✅ Найдено {len(posts)} строк / ссылок")

    # Фильтруем строки - оставляем только с корректными названиями групп и ID
    valid_posts = []
    skipped_count = 0
    
    for idx, post in enumerate(posts, 1):
        group_name = (post.get("Группа") or "").strip()
        group_id = (post.get("ID_Группы") or "").strip()
        
        # Проверяем, что название группы содержит "ЦР26" или "ЦК26" и есть ID группы
        upper_name = group_name.upper()
        if not group_name or ("ЦР26" not in upper_name and "ЦК26" not in upper_name):
            skipped_count += 1
            logger.error(f"SKIPPED_NO_GROUP_NAME: [{idx}] Ссылка {post.get('Ссылка', 'N/A')} - название группы '{group_name}' не содержит ЦР26/ЦК26, пропускаю")
            continue
        
        if not group_id:
            skipped_count += 1
            logger.error(f"SKIPPED_NO_GROUP_ID: [{idx}] Ссылка {post.get('Ссылка', 'N/A')} - отсутствует ID группы, пропускаю")
            continue
            
        valid_posts.append(post)
    
    if skipped_count > 0:
        logger.warning(f"⚠️  Пропущено {skipped_count} строк без ЦР26/ЦК26 в названии. Ищите по 'SKIPPED_NO_GROUP_NAME' для просмотра")

    logger.info(f"✅ К обработке: {len(valid_posts)} строк с ЦР26/ЦК26 в названии групп")

    if not valid_posts:
        logger.error("❌ Не найдено ни одной строки с ЦР26/ЦК26 в названии группы!")
        return

    logger.info("📸 Делаю скрины постов…")
    batch_screenshots(valid_posts, output_dir)
    logger.info("✅ Скрины постов готовы")

    # Собираем уникальные группы (ID + название) для оптимизированной обработки
    unique_groups = []
    seen_groups = set()
    
    for post in valid_posts:
        group_id = post.get("ID_Группы", "").strip()
        group_name = post.get("Группа", "").upper()
        
        # Используем ID как ключ уникальности, но передаем и ID и название
        if group_id and group_id not in seen_groups:
            unique_groups.append({
                "id": group_id,
                "name": group_name,
                "display_name": post.get("Группа", "")
            })
            seen_groups.add(group_id)

    logger.info(f"📊 Обрабатываем {len(unique_groups)} уникальных групп в одном браузере...")
    
    # Используем оптимизированную функцию для всех групп сразу
    successful_groups, failed_groups = screenshot_multiple_groups_stats(
        groups=unique_groups,
        output_dir=output_dir,
        ads_url=ads_url,
        demography_zoom=1.0,  # Без масштабирования для демографии
        geo_zoom=1.0,         # Без масштабирования для географии
        viewport_width=1920,
        viewport_height=1200
    )
    
    logger.info(f"✅ VK Ads статистика готова. Успешно: {len(successful_groups)}, Ошибки: {len(failed_groups)}")

    # Фильтруем посты - оставляем только те, для которых успешно создали скрины статистики
    posts_for_report = []
    skipped_campaigns = 0
    
    for post in valid_posts:
        group_name = post.get("Группа", "")
        # Проверяем, есть ли группа среди успешно обработанных (по display_name)
        group_found = any(
            group.get("display_name", "") == group_name 
            for group in successful_groups
        )
        
        if group_found:
            posts_for_report.append(post)
        else:
            skipped_campaigns += 1
            logger.warning(f"🚫 Пропускаю кампанию '{group_name}' из отчета - не удалось получить статистику")
    
    if skipped_campaigns > 0:
        logger.warning(f"⚠️  Пропущено {skipped_campaigns} кампаний из отчета из-за ошибок статистики")
    
    logger.info(f"📝 Собираю DOCX для {len(posts_for_report)} успешных кампаний…")
    try:
        generate_report(posts_for_report, output_doc, assets_dir=output_dir, inner_image="inner.png")
    except TypeError:
        # Fallback для старой версии функции
        generate_report(posts_for_report, output_doc)

    logger.info("✅ Отчёт готов!")
    logger.info("🏁 Программа завершена успешно")


if __name__ == "__main__":
    main()
