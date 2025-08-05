#!/usr/bin/env python3
"""
Быстрый тест только для географии с разными масштабами
"""

from ads_screenshot import screenshot_group_stats

def main():
    group_name = "ЦР25_ИЗМАЙЛОВО_БЛАГОУСТРОЙСТВО"
    output_dir = "test_geo_fix"
    ads_url = (
        "https://ads.vk.com/hq/dashboard/ad_groups"
        "?sudo=vkads_3012708486%40mailru"
        "&mode=ads&attribution=conversion"
        "&date_from=01.04.2025&date_to=04.05.2025"
        "&sort=-created"
    )
    
    print("🧪 Тестирование исправленной географии...")
    
    # Тестируем несколько масштабов
    zoom_levels = [0.8, 0.7, 0.6, 0.5]
    
    for zoom in zoom_levels:
        print(f"\n🗺️ Тест географии с масштабом {zoom}...")
        test_dir = f"{output_dir}_zoom_{int(zoom*100)}"
        
        screenshot_group_stats(
            group_name,
            test_dir,
            ads_url,
            tabs=("geo",),  # Только география
            demography_zoom=0.6,
            geo_zoom=zoom,
            viewport_width=1920,
            viewport_height=1200
        )
        print(f"✅ География с масштабом {zoom} сохранена в {test_dir}")
    
    print(f"\n🎯 Тест завершен! Проверьте папки test_geo_fix_zoom_*")
    print("📊 Рекомендуется выбрать лучший результат и обновить main.py")

if __name__ == "__main__":
    main()
