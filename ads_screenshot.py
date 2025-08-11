# ads_screenshot.py
from playwright.sync_api import sync_playwright
import os
import time
import logging

###############################################################################
#  VK Ads — automatic screenshots with **strict** ad-plan matching            #
###############################################################################
#  Stores every PNG into *output_dir*.                                        #
#  Extra shots for the «overview» tab:                                        #
#       ▸ traffic graph   → *_overview_graph.png (with TopLine)               #
#       ▸ conversion funnel → *_overview_funnel.png (caption + chart only)    #
###############################################################################

__all__ = ["screenshot_group_stats"]


# ────────────────────────────── helpers ─────────────────────────────────────


def _safe_mkdir(path: str):
    if path and not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def _scroll_to_bottom(page, step: int = 700):
    page.evaluate(
        """
        async step => {
            for (let y = 0; y < document.body.scrollHeight; y += step) {
                window.scrollTo({top: y, behavior: 'instant'});
                await new Promise(r => setTimeout(r, 120));
            }
            window.scrollTo({top: document.body.scrollHeight, behavior: 'instant'});
        }
        """,
        step,
    )
    page.wait_for_timeout(400)


def _is_captcha(page):
    return (
        page.locator(
            'input[name="captcha_key"], .page_block_captcha, [id*="captcha"], :text("Я не робот")'
        ).count()
        > 0
    )


# ────────────────────────────── shot helpers ────────────────────────────────


def _topline_loc(page):
    return page.locator("div[class^='TopLine_topline']").first


def _union_clip(a: dict, b: dict):
    x1, y1 = min(a["x"], b["x"]), min(a["y"], b["y"])
    x2 = max(a["x"] + a["width"], b["x"] + b["width"])
    y2 = max(a["y"] + a["height"], b["y"] + b["height"])
    return {"x": int(x1), "y": int(y1), "width": int(x2 - x1), "height": int(y2 - y1)}


def _shot_with_topline(page, target, path):
    try:
        top = _topline_loc(page)
        if not top.count():
            target.screenshot(path=path)
            return
        target.scroll_into_view_if_needed()
        page.wait_for_timeout(250)
        bt, bb = top.bounding_box(), target.bounding_box()
        if bt is None or bb is None:
            target.screenshot(path=path)
            return
        page.screenshot(path=path, clip=_union_clip(bt, bb))
    except Exception as e:
        logging.error(f"⚠️  Ошибка при создании скриншота с TopLine: {e}")
        target.screenshot(path=path)


def _shot_with_caption(page, caption, target, path):
    try:
        caption.scroll_into_view_if_needed()
        target.scroll_into_view_if_needed()
        page.wait_for_timeout(200)
        bc, bt = caption.bounding_box(), target.bounding_box()
        if bc is None or bt is None:
            target.screenshot(path=path)
            return
        page.screenshot(path=path, clip=_union_clip(bc, bt))
    except Exception as e:
        logging.error(f"⚠️  Ошибка при создании скриншота с подписью: {e}")
        target.screenshot(path=path)


def _shot_demography_section(page, path, demography_zoom=0.6):
    """Специальный скриншот для демографии: от названия компании до нижней статистики
    
    Args:
        page: Playwright page объект
        path: Путь для сохранения скриншота
        demography_zoom: Масштаб для демографии (по умолчанию 0.6)
    """
    try:
        # Сохраняем текущий масштаб
        original_zoom = page.evaluate("document.body.style.zoom")
        
        # Устанавливаем масштаб для демографии
        page.evaluate(f"document.body.style.zoom = '{demography_zoom}'")
        page.wait_for_timeout(1000)  # Ждем применения масштаба
        # Прокручиваем в самый верх страницы
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(300)
        
        # Ищем весь контейнер со статистикой
        main_container = page.locator("div[class^='ViewPoints_layout']").first
        
        if main_container.count():
            # Прокручиваем к контейнеру
            main_container.scroll_into_view_if_needed()
            page.wait_for_timeout(500)
            
            # Ищем заголовок с названием компании более широко
            title_selectors = [
                "span[class^='TopLine_title']:has-text('ЦР25')",
                "span.vkuiTitle:has-text('ЦР25')",
                "[class*='title']:has-text('ЦР25')",
                "span:has-text('ЦР25_')"
            ]
            
            title_element = None
            for selector in title_selectors:
                title_element = page.locator(selector).first
                if title_element.count():
                    logging.info(f"✅ Найден заголовок: {selector}")
                    break
            
            # Ищем нижний блок статистики
            bottom_selectors = [
                "div[class^='Compare_layout']",
                "div[class^='Demography_wrap']",
                "div[class*='demography']"
            ]
            
            bottom_element = None
            for selector in bottom_selectors:
                elements = page.locator(selector).all()
                if elements:
                    bottom_element = elements[-1]  # Берем последний элемент
                    logging.info(f"✅ Найден нижний блок: {selector}")
                    break
            
            if title_element and title_element.count() and bottom_element:
                # Прокручиваем к заголовку
                title_element.scroll_into_view_if_needed()
                page.wait_for_timeout(300)
                
                # Получаем координаты
                title_box = title_element.bounding_box()
                bottom_box = bottom_element.bounding_box()
                
                if title_box and bottom_box:
                    # Получаем размеры страницы для корректных границ
                    page_width = page.evaluate("document.documentElement.scrollWidth")
                    page_height = page.evaluate("document.documentElement.scrollHeight")
                    viewport_width = page.evaluate("window.innerWidth")
                    
                    # Находим оптимальную ширину для контента демографии
                    demo_container = page.locator("div[class^='Demography_wrap'], div[class^='ViewPoints_panel']").first
                    container_box = demo_container.bounding_box() if demo_container.count() else None
                    
                    # Определяем область более аккуратно
                    if container_box:
                        # Используем границы контейнера с небольшими отступами
                        start_x = max(0, container_box["x"] - 20)
                        content_width = min(container_box["width"] + 40, page_width - start_x)
                    else:
                        # Fallback: центрируем относительно заголовка
                        start_x = max(0, title_box["x"] - 100)
                        content_width = min(800, page_width - start_x)
                    
                    # Определяем высоту строго по контенту
                    start_y = max(0, title_box["y"] - 50)
                    end_y = min(bottom_box["y"] + bottom_box["height"] + 30, page_height)
                    content_height = end_y - start_y
                    
                    # Создаем область только с реальным контентом
                    content_area = {
                        "x": int(start_x),
                        "y": int(start_y),
                        "width": int(content_width),
                        "height": int(content_height)
                    }
                    
                    logging.info(f"📐 Область скриншота: x={content_area['x']}, y={content_area['y']}, w={content_area['width']}, h={content_area['height']}")
                    
                    page.screenshot(path=path, clip=content_area)
                    logging.info(f"✅ Скриншот демографии (без масштабирования): {path}")
                    return
        
        # Если не получилось найти элементы, делаем скриншот всего контейнера
        logging.warning("⚠️  Не удалось найти точные элементы, делаем скриншот основного контейнера")
        container = page.locator("div[class^='ViewPoints_layout'], div[class^='ViewPoints_main']").first
        if container.count():
            container.scroll_into_view_if_needed()
            page.wait_for_timeout(300)
            container.screenshot(path=path)
        else:
            page.screenshot(path=path, full_page=True)
        
    except Exception as e:
        logging.error(f"⚠️  Ошибка при создании скриншота демографии: {e}")
        page.screenshot(path=path, full_page=True)
    finally:
        # Восстанавливаем оригинальный масштаб
        try:
            page.evaluate(f"document.body.style.zoom = '{original_zoom if original_zoom else 'initial'}'")
        except:
            pass


def _shot_geo_section(page, path, geo_zoom=0.8):
    """Специальный скриншот для географии с настраиваемым масштабом
    
    Args:
        page: Playwright page объект
        path: Путь для сохранения скриншота
        geo_zoom: Масштаб для географии (по умолчанию 0.8)
    """
    try:
        # Сохраняем текущий масштаб
        original_zoom = page.evaluate("document.body.style.zoom")
        
        # Устанавливаем масштаб для географии
        page.evaluate(f"document.body.style.zoom = '{geo_zoom}'")
        page.wait_for_timeout(1000)  # Ждем применения масштаба
        
        # Прокручиваем в самый верх страницы
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(300)
        
        # Ждем завершения сетевых запросов (карты часто загружаются через API)
        try:
            logging.info("⏳ Ожидание сетевых запросов...")
            page.wait_for_load_state("networkidle", timeout=5000)
            logging.info("✅ Сетевые запросы завершены")
        except Exception:
            logging.warning("⚠️  Timeout сетевых запросов, продолжаем...")
        
        # Ищем основной контейнер географии
        geo_selectors = [
            "div[class^='ViewPoints_layout']",
            "div[class^='ViewPoints_main']", 
            "div[class*='geography']",
            "div[class*='Geography']",
            "div[class*='geo']"
        ]
        
        main_container = None
        for selector in geo_selectors:
            container = page.locator(selector).first
            if container.count():
                main_container = container
                logging.info(f"✅ Найден контейнер географии: {selector}")
                break
        
        if main_container:
            # Прокручиваем к контейнеру
            main_container.scroll_into_view_if_needed()
            page.wait_for_timeout(500)
            
            # Ждем загрузки карты - ищем элементы карты
            logging.info("⏳ Ожидание загрузки карты...")
            map_selectors = [
                "canvas",  # Карты часто рендерятся в canvas
                "img[src*='map']",  # Изображения карт
                "div[class*='map']",  # Контейнеры карт
                "div[class*='Map']",
                "[class*='leaflet']",  # Leaflet карты
                "[class*='mapbox']",   # Mapbox карты
                "[class*='google-map']" # Google Maps
            ]
            
            # Ждем появления любого элемента карты
            map_loaded = False
            for attempt in range(10):  # Максимум 10 попыток (10 секунд)
                for selector in map_selectors:
                    map_elements = page.locator(selector)
                    if map_elements.count() > 0:
                        logging.info(f"✅ Карта найдена: {selector} ({map_elements.count()} элементов)")
                        map_loaded = True
                        break
                
                if map_loaded:
                    break
                    
                logging.info(f"⏳ Попытка {attempt + 1}/10 - ждем карту...")
                page.wait_for_timeout(1000)
            
            if not map_loaded:
                logging.warning("⚠️  Карта не найдена, но продолжаем...")
            
            # Дополнительное ожидание для полной загрузки карты
            page.wait_for_timeout(2000)
            
            # Попытка принудительно обновить карты через JavaScript
            try:
                page.evaluate("""
                    // Принудительное обновление карт
                    const mapElements = document.querySelectorAll('canvas, [class*="map"], [class*="Map"]');
                    mapElements.forEach(el => {
                        if (el.style) el.style.display = 'none';
                        setTimeout(() => { if (el.style) el.style.display = ''; }, 100);
                    });
                """)
                page.wait_for_timeout(1000)
            except Exception:
                pass
            
            logging.info("✅ Ожидание завершено, создаем скриншот")
            
            # Получаем координаты контейнера
            container_box = main_container.bounding_box()
            
            if container_box:
                # Получаем размеры страницы
                page_width = page.evaluate("document.documentElement.scrollWidth")
                page_height = page.evaluate("document.documentElement.scrollHeight")
                
                # Создаем расширенную область для географии
                start_x = max(0, container_box["x"] - 50)
                start_y = max(0, container_box["y"] - 50)
                content_width = min(container_box["width"] + 100, page_width - start_x)
                content_height = min(container_box["height"] + 100, page_height - start_y)
                
                content_area = {
                    "x": int(start_x),
                    "y": int(start_y), 
                    "width": int(content_width),
                    "height": int(content_height)
                }
                
                logging.info(f"📐 Область скриншота географии: x={content_area['x']}, y={content_area['y']}, w={content_area['width']}, h={content_area['height']}")
                
                # Принудительная перерисовка для обновления карт
                page.evaluate("window.dispatchEvent(new Event('resize'))")
                page.wait_for_timeout(500)
                
                page.screenshot(path=path, clip=content_area)
                logging.info(f"✅ Скриншот географии с масштабом {geo_zoom}: {path}")
                return
            else:
                # Fallback: скриншот контейнера
                main_container.screenshot(path=path)
                logging.info(f"✅ Скриншот контейнера географии с масштабом {geo_zoom}: {path}")
                return
        
        # Если контейнер не найден, делаем полный скриншот
        logging.warning("⚠️  Контейнер географии не найден, делаем полный скриншот")
        page.screenshot(path=path, full_page=True)
        logging.info(f"✅ Полный скриншот географии с масштабом {geo_zoom}: {path}")
        
    except Exception as e:
        print(f"⚠️  Ошибка при создании скриншота географии: {e}")
        page.screenshot(path=path, full_page=True)
    finally:
        # Восстанавливаем оригинальный масштаб
        try:
            page.evaluate(f"document.body.style.zoom = '{original_zoom if original_zoom else 'initial'}'")
        except:
            pass


# ────────────────────────────── main routine ────────────────────────────────


def screenshot_group_stats(
    group_name: str,
    output_dir: str,
    ads_url: str,
    tabs: tuple[str, ...] | None = ("overview", "demography", "geo"),
    viewport_width: int = 1920,
    viewport_height: int = 1080,
    zoom_level: float = 0.8,
    demography_zoom: float = 0.6,
    geo_zoom: float = 0.8,
):
    """Save screenshots of *group_name* stats into *output_dir*.
    
    Args:
        group_name: Название группы для поиска
        output_dir: Папка для сохранения скриншотов
        ads_url: URL страницы VK Ads
        tabs: Список вкладок для скриншотов
        viewport_width: Ширина окна браузера (по умолчанию 1920)
        viewport_height: Высота окна браузера (по умолчанию 1080)
        zoom_level: Уровень масштабирования страницы (по умолчанию 0.8)
        demography_zoom: Масштаб для демографии (по умолчанию 0.6)
        geo_zoom: Масштаб для географии (по умолчанию 0.8)
    """

    # Убеждаемся, что папка существует
    _safe_mkdir(output_dir)
    logging.info(f"📁 Папка {output_dir} создана/проверена")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(
            storage_state="vk_storage.json", viewport={"width": viewport_width, "height": viewport_height}
        )
        page = ctx.new_page()

        print(f"➡️  Opening VK Ads: {ads_url}")
        page.goto(ads_url, timeout=60_000)
        try:
            page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:
            logging.warning("⚠️  networkidle wasn't reached – continuing …")
        
        # Устанавливаем масштаб страницы для лучшего отображения графиков
        page.evaluate(f"document.body.style.zoom = '{zoom_level}'")
        page.wait_for_timeout(3_000)

        # Captcha -----------------------------------------------------------
        if _is_captcha(page):
            logging.warning("🛑 Captcha detected – solve it …")
            page.wait_for_timeout(30_000)
            ctx.storage_state(path="vk_storage.json")

        # Search ------------------------------------------------------------
        def _apply_search(q: str):
            logging.info(f"🔍 Поиск рекламного плана: '{q}'")

            search_selectors = [
                "input[type='search']",
                "input[placeholder*='Поиск']",
                "input[placeholder*='поиск']",
                "[data-testid*='search'] input",
                ".search input",
                "input[name*='search']",
            ]

            inp = None
            for selector in search_selectors:
                inp = page.locator(selector).first
                if inp.count() > 0:
                    logging.info(f"✅ Найдено поле поиска: {selector}")
                    break

            if not inp or inp.count() == 0:
                logging.error("❌ Поле поиска не найдено, попробуем продолжить без поиска")
                return False

            try:
                inp.click()
                page.wait_for_timeout(500)
                inp.fill("")
                page.wait_for_timeout(300)
                inp.fill(q)
                page.wait_for_timeout(500)
                page.keyboard.press("Enter")
                page.wait_for_timeout(2_000)

                contains = page.locator(
                    "[data-testid='search-contains-menu-item']"
                ).first
                if contains.count():
                    contains.click()
                    page.wait_for_timeout(1_000)
                    logging.info("✅ Выбран вариант 'содержит'")

                return True
            except Exception as e:
                logging.error(f"⚠️  Ошибка при поиске: {e}")
                return False

        # Приводим название группы к верхнему регистру для поиска
        group_name_upper = group_name.upper()
        _apply_search(group_name_upper)
        page.wait_for_timeout(2_000)

        # Поиск рекламного плана ----------------------------------------
        logging.info(f"🔍 Ищем рекламный план '{group_name_upper}' в таблице...")

        link_selectors = [
            f"[data-testid='name-link']:has-text('{group_name_upper}')",
            f"a:has-text('{group_name_upper}')",
            f"[data-testid='name-link']",
            f"td a:has-text('{group_name_upper}')",
            f"tr:has-text('{group_name_upper}') [data-testid='name-link']",
        ]

        link = None
        for selector in link_selectors:
            link = page.locator(selector).first
            if link.count() > 0 and group_name_upper in (link.text_content() or "").upper():
                logging.info(f"✅ Найден план: {link.text_content().strip()}")
                break

        if not link or link.count() == 0:
            raise RuntimeError(
                f"❌ Рекламный план '{group_name_upper}' не найден! Проверьте название."
            )

        # Находим родительскую строку таблицы
        row = link.locator("xpath=ancestor::tr").first
        if row.count() == 0:
            row = link.locator("..").locator("..").first

        try:
            row.scroll_into_view_if_needed(timeout=10_000)
            page.wait_for_timeout(400)
        except Exception as e:
            logging.warning(f"⚠️  Ошибка при прокрутке к строке: {e}")

        # ─── Новое: ховерим строку, чтобы появились иконки действий ────
        try:
            row.hover(timeout=5_000)
            page.wait_for_timeout(300)
            logging.info("🖱️  Навели курсор на строку плана — иконки должны появиться")
        except Exception as e:
            logging.warning(f"⚠️  Не удалось навести курсор на строку: {e}")

        # Поиск кнопки статистики --------------------------------------
        logging.info("📊 Открываем статистику...")

        stats_selectors = [
            "a[data-testid='stats']",
            "[data-testid='stats']",
            "button[title*='Статистика']",
            "a[title*='Статистика']",
            "svg.vkuiIcon--poll_outline_20",
            "svg[class*='poll_outline']",
            "svg[aria-label*='Статистика']",
            "button:has(svg[class*='poll_outline'])",
        ]

        def _find_stats_button(scope):
            for sel in stats_selectors:
                btn = scope.locator(sel).first
                if btn.count() > 0:
                    logging.info(f"✅ Найдена кнопка статистики: {sel}")
                    return btn
            return None

        btn = _find_stats_button(row) or _find_stats_button(page)
        if not btn:
            # Быстрая диагностика: покажем, какие svg-иконки есть в строке
            svgs = row.locator("svg").all()
            logging.warning(f"❔ В строке найдено SVG-иконок: {len(svgs)}")
            for i, svg in enumerate(svgs[:5], 1):
                try:
                    logging.info(f"  {i}. {svg.get_attribute('class')}")
                except Exception:
                    pass
            raise RuntimeError(
                "❌ Кнопка статистики не найдена – возможно, изменился интерфейс"
            )

        try:
            btn.click()
            page.wait_for_timeout(4_000)
            logging.info("✅ Статистика открыта")
        except Exception as e:
            raise RuntimeError(f"⚠️  Ошибка при клике на статистику: {e}") from e

        # Убеждаемся, что папка всё ещё существует
        _safe_mkdir(output_dir)

        # Iterate tabs --------------------------------------------------
        for tab in tabs or ("overview",):
            logging.info(f"📑 Обрабатываем вкладку: {tab}")

            tab_btn = page.locator(f"#tab_{tab}")
            if tab_btn.count():
                tab_btn.click()
                if tab == "geo":
                    # Дополнительное ожидание для географии (карты загружаются дольше)
                    logging.info("⏳ Дополнительное ожидание для загрузки карт...")
                    page.wait_for_timeout(3_000)
                else:
                    page.wait_for_timeout(1_000)
                logging.info(f"✅ Вкладка {tab} открыта")
            else:
                logging.warning(f"⚠️  Вкладка '{tab}' не найдена – пропускаем")
                continue

            if tab == "overview":
                # Воронка конверсий
                caption = page.locator("text=Воронка конверсий").first
                funnel = page.locator("div[class^='ConversionsChart_wrap']").first
                if caption.count() and funnel.count():
                    funnel_path = os.path.join(
                        output_dir, f"{group_name_upper}_overview_funnel.png"
                    )
                    _shot_with_caption(page, caption, funnel, funnel_path)
                    logging.info(f"✅ Воронка сохранена: {funnel_path}")
            elif tab == "demography":
                # Специальный скриншот для демографии: от названия компании до статистики
                tab_path = os.path.join(output_dir, f"{group_name_upper}_{tab}.png")
                _safe_mkdir(output_dir)
                _shot_demography_section(page, tab_path, demography_zoom)
            elif tab == "geo":
                # Специальный скриншот для географии с настраиваемым масштабом
                tab_path = os.path.join(output_dir, f"{group_name_upper}_{tab}.png")
                _safe_mkdir(output_dir)
                _shot_geo_section(page, tab_path, geo_zoom)
            elif tab != "overview":
                # Полный скриншот вкладки (только для остальных вкладок)
                _scroll_to_bottom(page)
                tab_path = os.path.join(output_dir, f"{group_name_upper}_{tab}.png")
                _safe_mkdir(output_dir)
                page.screenshot(path=tab_path, full_page=True)
                logging.info(f"✅ Скриншот вкладки сохранён: {tab_path}")

        logging.info("✅ Все скриншоты VK Ads созданы успешно")
        browser.close()
