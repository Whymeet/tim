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
    print(f"📁 Рабочая папка создана: {output_dir}")

    try:
        print("📋 Загрузка постов из файла…")
        posts = load_posts(posts_file)
        print(f"✅ Загружено постов: {len(posts)}")

        print("📸 Создание скриншотов постов…")
        batch_screenshots(posts, output_dir)
        print("✅ Скриншоты постов созданы")

        # Проверяем, что папка всё ещё существует
        if not os.path.exists(output_dir):
            print(f"⚠️  Папка {output_dir} исчезла, создаём заново")
            os.makedirs(output_dir, exist_ok=True)
        
        print("📊 Съёмка статистики VK Ads…")
        screenshot_group_stats(ad_plan_name, output_dir, ads_url)
        print("✅ Статистика VK Ads получена")

        # Финальная проверка папки
        if not os.path.exists(output_dir):
            print(f"❌ Критическая ошибка: папка {output_dir} удалена во время работы")
            os.makedirs(output_dir, exist_ok=True)
            print(f"📁 Папка {output_dir} восстановлена")

        print("📄 Формирование отчёта…")
        generate_report(posts, output_doc, assets_dir=output_dir)
        print("✅ Отчёт сформирован")

        print(f"🎉 Готово! Отчёт сохранён как {output_doc}")
        
        # Показываем содержимое папки assets
        if os.path.exists(output_dir):
            files = os.listdir(output_dir)
            print(f"📁 Файлы в {output_dir}: {len(files)} шт.")
            for f in sorted(files):
                print(f"  - {f}")
        else:
            print(f"❌ Папка {output_dir} не существует!")

    except Exception as e:
        print(f"❌ Ошибка выполнения: {e}")
        # Показываем состояние папки при ошибке
        if os.path.exists(output_dir):
            files = os.listdir(output_dir)  
            print(f"📁 Файлы в {output_dir} на момент ошибки: {files}")
        else:
            print(f"📁 Папка {output_dir} не существует на момент ошибки")
        raise


if __name__ == "__main__":
    main()