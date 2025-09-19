# ads_screenshot.py
from playwright.sync_api import sync_playwright
from vk_ads_context import create_vk_ads_context
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
        page.wait_for_timeout(500)  # Увеличено в 2 раза
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
        page.wait_for_timeout(400)  # Увеличено в 2 раза
        bc, bt = caption.bounding_box(), target.bounding_box()
        if bc is None or bt is None:
            target.screenshot(path=path)
            return
        page.screenshot(path=path, clip=_union_clip(bc, bt))
    except Exception as e:
        logging.error(f"⚠️  Ошибка при создании скриншота с подписью: {e}")
        target.screenshot(path=path)


def _shot_demography_section(page, path, demography_zoom=1.0):
    """Специальный скриншот для демографии: от названия компании до нижней статистики
    
    Args:
        page: Playwright page объект
        path: Путь для сохранения скриншота
        demography_zoom: Масштаб для демографии (по умолчанию 1.0 - без масштабирования)
    """
    try:
        # Сохраняем текущий масштаб только если нужно изменить
        original_zoom = None
        if demography_zoom != 1.0:
            original_zoom = page.evaluate("document.body.style.zoom")
            page.evaluate(f"document.body.style.zoom = '{demography_zoom}'")
            page.wait_for_timeout(1000)  # Увеличено в 2 раза
        # Прокручиваем в самый верх страницы
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(600)  # Увеличено в 2 раза
        
        # Ищем основной контейнер демографии - более точные селекторы
        main_container_selectors = [
            "div[class*='ViewPoints'][class*='layout']",
            "div.ViewPoints\\.module_layout__YWJjY", 
            "div[class^='ViewPoints_layout']",
            "div[class^='ViewPoints_main']"
        ]
        
        main_container = None
        for selector in main_container_selectors:
            container = page.locator(selector).first
            if container.count():
                main_container = container
                logging.info(f"✅ Найден контейнер демографии: {selector}")
                break
        
        if main_container:
            # Ждем загрузки контента
            page.wait_for_timeout(2000)  # Увеличено в 2 раза
            
            # Находим заголовок с названием кампании 
            title_selectors = [
                "span[class*='TopLine'][class*='title']:has-text('ЦР25')",
                "span.TopLine\\.module_title__XzA2Y:has-text('ЦР25')",
                "span:has-text('ЦР25_')"
            ]
            
            title_element = None
            for selector in title_selectors:
                title_element = page.locator(selector).first
                if title_element.count():
                    logging.info(f"✅ Найден заголовок: {selector}")
                    break
            
            # Ищем нижние блоки статистики - более широкий поиск
            bottom_selectors = [
                "div[class*='Compare'][class*='layout']",
                "div.Compare\\.module_layout__YzVmZ",
                "div[class*='Demography'][class*='wrap']", 
                "div.Demography\\.module_wrap__YjkyN"
            ]
            
            bottom_elements = []
            for selector in bottom_selectors:
                elements = page.locator(selector).all()
                bottom_elements.extend(elements)
            
            if bottom_elements:
                logging.info(f"✅ Найдено {len(bottom_elements)} блоков статистики")
                bottom_element = bottom_elements[-1]  # Берем последний элемент
            else:
                bottom_element = None
            
            if title_element and title_element.count() and bottom_element:
                # Прокручиваем к заголовку 
                title_element.scroll_into_view_if_needed()
                page.wait_for_timeout(600)  # Увеличено в 2 раза
                
                # Получаем координаты
                title_box = title_element.bounding_box()
                bottom_box = bottom_element.bounding_box()
                
                if title_box and bottom_box:
                    # Определяем оптимальную область скриншота
                    viewport_width = page.evaluate("window.innerWidth")
                    
                    # Находим левую границу по контенту
                    content_left = min(title_box["x"], bottom_box["x"])
                    start_x = max(0, content_left - 20)  # Минимальный отступ
                    
                    # Ширина захватывает весь видимый контент
                    content_right = max(title_box["x"] + title_box["width"], 
                                      bottom_box["x"] + bottom_box["width"])
                    content_width = min(content_right - start_x + 40, viewport_width - start_x)
                    
                    # Высота строго по контенту
                    start_y = max(0, title_box["y"] - 20)
                    end_y = bottom_box["y"] + bottom_box["height"] + 20
                    content_height = end_y - start_y
                    
                    content_area = {
                        "x": int(start_x),
                        "y": int(start_y),
                        "width": int(content_width),
                        "height": int(content_height)
                    }
                    
                    logging.info(f"📐 Область демографии: x={content_area['x']}, y={content_area['y']}, w={content_area['width']}, h={content_area['height']}")
                    
                    page.screenshot(path=path, clip=content_area)
                    logging.info(f"✅ Скриншот демографии: {path}")
                    return
        
        # Если не получилось найти точные элементы, делаем скриншот основного контейнера
        logging.warning("⚠️  Не удалось найти точные элементы, делаем скриншот основного контейнера")
        if main_container:
            main_container.scroll_into_view_if_needed()
            page.wait_for_timeout(600)  # Увеличено в 2 раза
            main_container.screenshot(path=path)
            logging.info(f"✅ Скриншот контейнера демографии: {path}")
        else:
            # Последний fallback - весь viewport
            page.screenshot(path=path)
            logging.info(f"✅ Скриншот страницы демографии: {path}")
        
    except Exception as e:
        logging.error(f"⚠️  Ошибка при создании скриншота демографии: {e}")
        page.screenshot(path=path)
    finally:
        # Восстанавливаем оригинальный масштаб если он был изменен
        if original_zoom is not None:
            try:
                page.evaluate(f"document.body.style.zoom = '{original_zoom if original_zoom else 'initial'}'")
            except:
                pass


def _shot_geo_section(page, path, geo_zoom=1.0):
    """Специальный скриншот для географии с настраиваемым масштабом
    
    Args:
        page: Playwright page объект
        path: Путь для сохранения скриншота
        geo_zoom: Масштаб для географии (по умолчанию 1.0 - без масштабирования)
    """
    try:
        # Сохраняем текущий масштаб только если нужно изменить
        original_zoom = None
        if geo_zoom != 1.0:
            original_zoom = page.evaluate("document.body.style.zoom")
            page.evaluate(f"document.body.style.zoom = '{geo_zoom}'")
            page.wait_for_timeout(1000)  # Увеличено в 2 раза
        
        # Прокручиваем в самый верх страницы
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(600)  # Увеличено в 2 раза
        
        # Ждем завершения сетевых запросов (карты часто загружаются через API)
        try:
            logging.info("⏳ Ожидание сетевых запросов...")
            page.wait_for_load_state("networkidle", timeout=6000)  # Увеличено в 2 раза
            logging.info("✅ Сетевые запросы завершены")
        except Exception:
            logging.warning("⚠️  Timeout сетевых запросов, продолжаем...")
        
        # Ищем основной контейнер географии - более точные селекторы
        geo_container_selectors = [
            "div[class*='ViewPoints'][class*='layout']",
            "div.ViewPoints\\.module_layout__YWJjY",
            "div[class^='ViewPoints_layout']",
            "div[class^='ViewPoints_main']"
        ]
        
        main_container = None
        for selector in geo_container_selectors:
            container = page.locator(selector).first
            if container.count():
                main_container = container
                logging.info(f"✅ Найден контейнер географии: {selector}")
                break
        
        if main_container:
            # Прокручиваем к контейнеру
            main_container.scroll_into_view_if_needed()
            page.wait_for_timeout(1000)  # Увеличено в 2 раза
            
            # Ждем загрузки карты - ищем элементы карты
            logging.info("⏳ Ожидание загрузки карты...")
            map_selectors = [
                "canvas.mmrgl-canvas",  # Специфический класс для VK Maps
                "div.mmrgl-map",        # Контейнер карты
                "canvas",               # Общий canvas элемент
                "div[class*='GeoMap']", # Контейнер географической карты
                "div[class*='map']"     # Любой контейнер с map
            ]
            
            # Ждем появления карты
            map_loaded = False
            for attempt in range(16):  # Увеличено в 2 раза (было 8)
                for selector in map_selectors:
                    map_elements = page.locator(selector)
                    if map_elements.count() > 0:
                        logging.info(f"✅ Карта найдена: {selector} ({map_elements.count()} элементов)")
                        map_loaded = True
                        break
                
                if map_loaded:
                    break
                    
                logging.info(f"⏳ Попытка {attempt + 1}/16 - ждем карту...")
                page.wait_for_timeout(2000)  # Увеличено в 2 раза
            
            if not map_loaded:
                logging.warning("⚠️  Карта не найдена, но продолжаем...")
            
            # Дополнительное ожидание для полной загрузки карты
            page.wait_for_timeout(3000)  # Увеличено в 2 раза
            
            # Принудительное обновление карт через JavaScript
            try:
                page.evaluate("""
                    // Принудительное обновление карт
                    const mapElements = document.querySelectorAll('canvas, [class*="map"], [class*="Map"]');
                    mapElements.forEach(el => {
                        if (el.style) el.style.display = 'none';
                        setTimeout(() => { if (el.style) el.style.display = ''; }, 100);
                    });
                    // Trigger resize event
                    window.dispatchEvent(new Event('resize'));
                """)
                page.wait_for_timeout(2000)  # Увеличено в 2 раза
            except Exception:
                pass
            
            logging.info("✅ Ожидание завершено, создаем скриншот")
            
            # Получаем координаты контейнера для точного скриншота
            container_box = main_container.bounding_box()
            
            if container_box:
                # Определяем оптимальную область для географии
                viewport_width = page.evaluate("window.innerWidth")
                viewport_height = page.evaluate("window.innerHeight")
                
                # Минимальные отступы для захвата всего контента
                start_x = max(0, container_box["x"] - 10)
                start_y = max(0, container_box["y"] - 10)
                content_width = min(container_box["width"] + 20, viewport_width - start_x)
                content_height = min(container_box["height"] + 20, viewport_height - start_y)
                
                content_area = {
                    "x": int(start_x),
                    "y": int(start_y), 
                    "width": int(content_width),
                    "height": int(content_height)
                }
                
                logging.info(f"📐 Область скриншота географии: x={content_area['x']}, y={content_area['y']}, w={content_area['width']}, h={content_area['height']}")
                
                page.screenshot(path=path, clip=content_area)
                logging.info(f"✅ Скриншот географии: {path}")
                return
            else:
                # Fallback: скриншот контейнера
                main_container.screenshot(path=path)
                logging.info(f"✅ Скриншот контейнера географии: {path}")
                return
        
        # Если контейнер не найден, делаем скриншот страницы
        logging.warning("⚠️  Контейнер географии не найден, делаем скриншот страницы")
        page.screenshot(path=path)
        logging.info(f"✅ Скриншот страницы географии: {path}")
        
    except Exception as e:
        logging.error(f"⚠️  Ошибка при создании скриншота географии: {e}")
        page.screenshot(path=path)
    finally:
        # Восстанавливаем оригинальный масштаб если он был изменен
        if original_zoom is not None:
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
        ctx = create_vk_ads_context(
            p,
            storage_state="vk_storage.json",
            viewport={"width": viewport_width, "height": viewport_height},
        )
        try:
            page = ctx.new_page()
    
            print(f"➡️  Opening VK Ads: {ads_url}")
            page.goto(ads_url, timeout=60_000)
            try:
                page.wait_for_load_state("networkidle", timeout=10_000)
            except Exception:
                logging.warning("⚠️  networkidle wasn't reached – continuing …")
            
            # Устанавливаем масштаб страницы для лучшего отображения графиков
            page.evaluate(f"document.body.style.zoom = '{zoom_level}'")
            page.wait_for_timeout(6_000)  # Увеличено в 2 раза
    
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
                    page.wait_for_timeout(1000)  # Увеличено в 2 раза
                    inp.fill("")
                    page.wait_for_timeout(600)  # Увеличено в 2 раза
                    inp.fill(q)
                    page.wait_for_timeout(1000)  # Увеличено в 2 раза
                    page.keyboard.press("Enter")
                    page.wait_for_timeout(4_000)  # Увеличено в 2 раза
    
                    contains = page.locator(
                        "[data-testid='search-contains-menu-item']"
                    ).first
                    if contains.count():
                        contains.click()
                        page.wait_for_timeout(2_000)  # Увеличено в 2 раза
                        logging.info("✅ Выбран вариант 'содержит'")
    
                    return True
                except Exception as e:
                    logging.error(f"⚠️  Ошибка при поиске: {e}")
                    return False
    
            # Приводим название группы к верхнему регистру для поиска
            group_name_upper = group_name.upper()
            _apply_search(group_name_upper)
            page.wait_for_timeout(4_000)  # Увеличено в 2 раза
    
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
                row.scroll_into_view_if_needed(timeout=20_000)  # Увеличено в 2 раза
                page.wait_for_timeout(800)  # Увеличено в 2 раза
            except Exception as e:
                logging.warning(f"⚠️  Ошибка при прокрутке к строке: {e}")
    
            # ─── Новое: ховерим строку, чтобы появились иконки действий ────
            try:
                row.hover(timeout=10_000)  # Увеличено в 2 раза
                page.wait_for_timeout(600)  # Увеличено в 2 раза
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
                page.wait_for_timeout(8_000)  # Увеличено в 2 раза
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
                        page.wait_for_timeout(6_000)  # Увеличено в 2 раза
                    else:
                        page.wait_for_timeout(2_000)  # Увеличено в 2 раза
                    logging.info(f"✅ Вкладка {tab} открыта")
                else:
                    logging.warning(f"⚠️  Вкладка '{tab}' не найдена – пропускаем")
                    continue
    
                if tab == "overview":
                    # Воронка конверсий
                    caption = page.locator("text=Воронка конверсий").first
                    funnel_selectors = [
                        "div[class*='ConversionsChart'][class*='wrap']",
                        "div[class^='ConversionsChart_wrap']",
                        "div[class^='ConversionsChart.module_wrap']",
                        "div.ConversionsChart\\.module_wrap__XzgxY"
                    ]
                    
                    funnel = None
                    for selector in funnel_selectors:
                        funnel = page.locator(selector).first
                        if funnel.count() > 0:
                            logging.info(f"✅ Найден контейнер воронки: {selector}")
                            break
                    
                    if caption.count() and funnel and funnel.count():
                        funnel_path = os.path.join(
                            output_dir, f"{group_name_upper}_overview_funnel.png"
                        )
                        _shot_with_caption(page, caption, funnel, funnel_path)
                        logging.info(f"✅ Воронка сохранена: {funnel_path}")
                    else:
                        logging.warning(f"⚠️  Воронка конверсий не найдена для группы {group_name_upper}")
                        logging.warning(f"   Caption found: {caption.count() > 0}")
                        logging.warning(f"   Funnel found: {funnel.count() > 0 if funnel else False}")
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
        finally:
            ctx.close()
