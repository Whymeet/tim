#!/usr/bin/env python3
"""
Скрипт для тестирования масштабирования демографии и географии
"""

from ads_screenshot import screenshot_group_stats

def test_single_tab(group_name, output_dir, ads_url, tab_name, zoom_levels):
    """Тестирует разные уровни масштабирования для одной вкладки"""
    for zoom in zoom_levels:
        print(f"\n🔍 Тестируем {tab_name} с масштабом {zoom}...")
        test_dir = f"{output_dir}_{tab_name}_zoom_{int(zoom*100)}"
        
        kwargs = {
            'viewport_width': 1920,
            'viewport_height': 1200
        }
        
        if tab_name == "demography":
            kwargs['tabs'] = ("demography",)
            kwargs['demography_zoom'] = zoom
            kwargs['geo_zoom'] = 1.0
        elif tab_name == "geo":
            kwargs['tabs'] = ("geo",)
            kwargs['demography_zoom'] = 0.6
            kwargs['geo_zoom'] = zoom
        
        screenshot_group_stats(
            group_name,
            test_dir,
            ads_url,
            **kwargs
        )
        print(f"✅ {tab_name.title()} с масштабом {zoom} сохранен в {test_dir}")

def main():
    # Настройки (замените на ваши данные)
    group_name = "ЦР25_ИЗМАЙЛОВО_БЛАГОУСТРОЙСТВО"  # Замените на название вашей группы
    output_dir = "test_zoom"
    ads_url = (
        "https://ads.vk.com/hq/dashboard/ad_groups"
        "?sudo=vkads_3012708486%40mailru"
        "&mode=ads&attribution=conversion"
        "&date_from=01.04.2025&date_to=04.05.2025"
        "&sort=-created"
    )
    
    print("🧪 Запуск тестирования масштабирования...")
    print(f"📊 Группа: {group_name}")
    print("─" * 50)
    
    # Тестируем демографию с разными масштабами
    print("\n📈 ТЕСТИРОВАНИЕ ДЕМОГРАФИИ:")
    demography_zooms = [1.0, 0.8, 0.6, 0.5, 0.4]
    test_single_tab(group_name, output_dir, ads_url, "demography", demography_zooms)
    
    # Тестируем географию с разными масштабами
    print("\n🗺️ ТЕСТИРОВАНИЕ ГЕОГРАФИИ:")
    geo_zooms = [1.0, 0.9, 0.8, 0.7, 0.6]
    test_single_tab(group_name, output_dir, ads_url, "geo", geo_zooms)
    
    print(f"\n🎯 Все тестовые скриншоты созданы!")
    print("📁 Проверьте папки:")
    print("   - test_zoom_demography_zoom_* для демографии")
    print("   - test_zoom_geo_zoom_* для географии")

if __name__ == "__main__":
    main()
