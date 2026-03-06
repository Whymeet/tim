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


# ────────────────────────────── auth helpers ─────────────────────────────────


def _handle_vk_id_auth(page):
    """Обрабатывает первичную авторизацию через VK ID."""
    logging.info("🔐 Проверяем необходимость авторизации через VK ID...")
    
    # Ждем загрузки страницы
    page.wait_for_timeout(3000)
    
    # Проверяем, находимся ли мы на странице VK ID авторизации
    vk_id_indicators = [
        "title:has-text('VK ID')",
        "text=Продолжить как",
        "[class*='vkuiButton__content']:has-text('Продолжить как')",
        "body[scheme='space_gray']"
    ]
    
    is_vk_id_page = False
    for indicator in vk_id_indicators:
        if page.locator(indicator).count() > 0:
            is_vk_id_page = True
            logging.info(f"✅ Обнаружена страница VK ID по индикатору: {indicator}")
            break
    
    if not is_vk_id_page:
        logging.info("ℹ️  Страница VK ID не обнаружена, авторизация не требуется")
        return True
    
    # Ищем кнопку "Продолжить как [Имя]"
    continue_button_selectors = [
        "span.vkuiButton__content:has-text('Продолжить как')",
        "[class*='vkuiButton__content']:has-text('Продолжить как')",
        "button:has-text('Продолжить как')",
        "[role='button']:has-text('Продолжить как')",
        "span:has-text('Продолжить как Тимофей')",
        "[data-testid*='continue']",
        "[class*='Button']:has-text('Продолжить')"
    ]
    
    continue_button = None
    for selector in continue_button_selectors:
        elements = page.locator(selector).all()
        for element in elements:
            if element.is_visible() and "продолжить как" in element.text_content().lower():
                continue_button = element
                logging.info(f"✅ Найдена кнопка продолжения: {selector}")
                break
        if continue_button:
            break
    
    if not continue_button:
        logging.warning("⚠️  Кнопка 'Продолжить как...' не найдена")
        return False
    
    try:
        # Кликаем на кнопку "Продолжить как..."
        continue_button.scroll_into_view_if_needed()
        page.wait_for_timeout(1000)
        continue_button.click()
        logging.info("✅ Нажата кнопка 'Продолжить как...'")
        
        # Ждем появления модального окна
        page.wait_for_timeout(3000)
        
        # Обрабатываем страницу подтверждения VK ID
        return _handle_modal_confirmation(page)
        
    except Exception as e:
        logging.error(f"❌ Ошибка при нажатии кнопки продолжения: {e}")
        return False


def _handle_modal_confirmation(page):
    """Обрабатывает страницу подтверждения VK ID после нажатия 'Продолжить как...'."""
    logging.info("🪟 Обрабатываем страницу подтверждения VK ID...")
    
    # Ждем загрузки страницы подтверждения
    page.wait_for_timeout(3000)
    
    # Проверяем, находимся ли мы на странице подтверждения VK ID
    vkid_confirmation_indicators = [
        "title:has-text('VK ID')",
        "body[scheme='bright_light']",
        "text=Туркин Тимофей",
        "text=Физическое лицо",
        "span:has-text('Туркин Тимофей')",
        "[class*='vkuiSimpleCell']:has-text('Туркин Тимофей')",
        "text=Разрешить",
        "text=Подтвердить",
        "text=Войти"
    ]
    
    is_confirmation_page = False
    for indicator in vkid_confirmation_indicators:
        if page.locator(indicator).count() > 0:
            is_confirmation_page = True
            logging.info(f"✅ Обнаружена страница подтверждения VK ID по индикатору: {indicator}")
            break
    
    if not is_confirmation_page:
        logging.info("ℹ️  Страница подтверждения не обнаружена, возможно, авторизация прошла автоматически")
        return True
    
    # Ищем элемент с именем "Туркин Тимофей" или кнопки подтверждения на странице VK ID
    confirmation_selectors = [
        # Элемент с именем пользователя (приоритетный)
        "span:has-text('Туркин Тимофей')",
        "[class*='vkuiSimpleCell']:has-text('Туркин Тимофей')",
        "[class*='vkuiHeadline']:has-text('Туркин Тимофей')",
        "div:has-text('Туркин Тимофей')",
        
        # Селекторы по структуре из HTML
        "div.vkuiSimpleCell__middle:has-text('Туркин Тимофей')",
        "span.vkuiSimpleCell__children:has-text('Туркин Тимофей')",
        
        # Основные кнопки подтверждения
        "button:has-text('Разрешить')",
        "button:has-text('Подтвердить')",
        "button:has-text('Войти')",
        "button:has-text('Продолжить')",
        
        # VK UI кнопки
        "[class*='vkuiButton']:has-text('Разрешить')",
        "[class*='vkuiButton']:has-text('Подтвердить')",
        "[class*='vkuiButton']:has-text('Войти')",
        "[class*='vkuiButton']:has-text('Продолжить')",
        
        # Роли кнопок
        "[role='button']:has-text('Разрешить')",
        "[role='button']:has-text('Подтвердить')",
        "[role='button']:has-text('Войти')",
        "[role='button']:has-text('Продолжить')",
        
        # Кликабельные элементы с классами VK UI
        "[class*='vkuiTappable']",
        "[class*='vkuiRipple']",
        
        # Data атрибуты
        "[data-testid*='confirm']",
        "[data-testid*='continue']",
        "[data-testid*='allow']",
        "[data-testid*='authorize']",
        
        # Любые видимые кнопки на странице (как fallback)
        "button[type='submit']",
        "input[type='submit']"
    ]
    
    confirmation_element = None
    for selector in confirmation_selectors:
        logging.info(f"Проверяем селектор для подтверждения VK ID: {selector}")
        elements = page.locator(selector).all()
        for element in elements:
            if element.is_visible():
                text_content = element.text_content()
                logging.info(f"Найден элемент: {selector}, текст: {text_content}")
                
                # Если это элемент с именем пользователя - это приоритетный выбор
                if "Туркин Тимофей" in text_content:
                    logging.info("✅ Найден элемент с именем пользователя - используем его")
                    confirmation_element = element
                    break
                # Если не нашли имя пользователя, используем первый подходящий элемент
                elif not confirmation_element:
                    confirmation_element = element
                    logging.info(f"✅ Найден элемент подтверждения: {selector}")
        
        # Если нашли элемент с именем пользователя, прерываем поиск
        if confirmation_element and "Туркин Тимофей" in confirmation_element.text_content():
            break
    
    if not confirmation_element:
        logging.warning("⚠️  Кнопка подтверждения не найдена на странице VK ID")
        
        # Попробуем найти любую кнопку на странице
        all_buttons = page.locator("button, [role='button'], input[type='submit']").all()
        visible_buttons = [btn for btn in all_buttons if btn.is_visible()]
        
        if visible_buttons:
            logging.info(f"🔍 Найдено {len(visible_buttons)} видимых кнопок, пробуем первую")
            confirmation_element = visible_buttons[0]
        else:
            # Пробуем нажать Enter для подтверждения
            try:
                page.keyboard.press("Enter")
                page.wait_for_timeout(3000)
                logging.info("✅ Попытка подтверждения через Enter")
                return True
            except:
                logging.warning("⚠️  Enter не сработал")
                return True
    
    try:
        # Несколько методов клика для надежности
        success = False
        
        # Метод 1: Обычный клик
        try:
            confirmation_element.scroll_into_view_if_needed()
            page.wait_for_timeout(500)
            confirmation_element.click(timeout=5000)
            page.wait_for_timeout(3000)  # Увеличено время ожидания
            logging.info("✅ Подтверждение VK ID выполнено (обычный клик)")
            success = True
        except Exception as e:
            logging.warning(f"⚠️  Обычный клик не сработал: {e}")
        
        # Метод 2: JS клик
        if not success:
            try:
                page.evaluate("arguments[0].click()", confirmation_element.element_handle())
                page.wait_for_timeout(3000)
                logging.info("✅ Подтверждение VK ID выполнено (JS клик)")
                success = True
            except Exception as e:
                logging.warning(f"⚠️  JS клик не сработал: {e}")
        
        # Метод 3: Enter на элементе
        if not success:
            try:
                confirmation_element.focus()
                page.keyboard.press("Enter")
                page.wait_for_timeout(3000)
                logging.info("✅ Подтверждение VK ID выполнено (Enter)")
                success = True
            except Exception as e:
                logging.warning(f"⚠️  Enter не сработал: {e}")
        
        # Дополнительное ожидание после подтверждения
        if success:
            page.wait_for_timeout(2000)
            
            # Проверяем, что мы покинули страницу подтверждения
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
                logging.info("✅ Страница загружена после подтверждения")
            except:
                logging.warning("⚠️  networkidle не достигнут, но продолжаем")
        
        return success
        
    except Exception as e:
        logging.error(f"❌ Ошибка при подтверждении VK ID: {e}")
        return False


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
        if (demography_zoom != 1.0):
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
                "span[class*='TopLine'][class*='title']:has-text('ЦР26')",
                "span[class*='TopLine'][class*='title']:has-text('ЦК26')",
                "span:has-text('ЦР26_')",
                "span:has-text('ЦК26_')"
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
                
                if (title_box and bottom_box):
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
        
        # Обработка первичной авторизации VK ID
        if not _handle_vk_id_auth(page):
            logging.warning("⚠️  Возможны проблемы с авторизацией VK ID")
        
        # Дополнительное ожидание после авторизации
        try:
            page.wait_for_load_state("networkidle", timeout=15_000)
        except Exception:
            logging.warning("⚠️  networkidle после авторизации не достигнут – продолжаем...")
        
        # Устанавливаем масштаб страницы для лучшего отображения графиков
        page.evaluate(f"document.body.style.zoom = '{zoom_level}'")
        page.wait_for_timeout(6_000)  # Увеличено в 2 раза

        # Captcha -----------------------------------------------------------
        if _is_captcha(page):
            logging.warning("🛑 Captcha detected – solve it …")
            page.wait_for_timeout(30_000)
            ctx.storage_state(path="vk_storage.json")

        # Search ------------------------------------------------------------
        # Приводим название группы к верхнему регистру для поиска
        group_name_upper = group_name.upper()
        
        # Выполняем поиск
        if not _apply_search_optimized(page, group_name_upper):
            raise RuntimeError(f"❌ Не удалось выполнить поиск для группы: {group_name_upper}")
        
        page.wait_for_timeout(4_000)  # Увеличено в 2 раза

        # Открытие статистики с автоматической очисткой поиска при ненахождении
        if not _open_group_stats(page, group_name_upper):
            raise RuntimeError(f"❌ Рекламный план '{group_name_upper}' не найден! Проверьте название.")

        # Убеждаемся, что папка всё ещё существует
        _safe_mkdir(output_dir)

        # Ждём появления вкладок статистики (до 10 сек)
        try:
            page.wait_for_selector("#tab_overview", timeout=10_000)
            logging.info("✅ Вкладки статистики загружены")
        except Exception:
            logging.warning("⚠️  Вкладки статистики не появились за 10 сек, пробуем продолжить")

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
        browser.close()


def screenshot_multiple_groups_stats(
    groups: list[dict],
    output_dir: str,
    ads_url: str,
    tabs: tuple[str, ...] | None = ("overview", "demography", "geo"),
    viewport_width: int = 1920,
    viewport_height: int = 1080,
    zoom_level: float = 0.8,
    demography_zoom: float = 0.6,
    geo_zoom: float = 0.8,
):
    """Оптимизированная функция для скриншотов нескольких групп в одном браузере.
    
    Args:
        groups: Список словарей {"id": "118746396", "name": "ЦР25_...", "display_name": "..."}
        output_dir: Папка для сохранения скриншотов
        ads_url: URL страницы VK Ads
        tabs: Список вкладок для скриншотов
        viewport_width: Ширина окна браузера
        viewport_height: Высота окна браузера
        zoom_level: Уровень масштабирования страницы
        demography_zoom: Масштаб для демографии
        geo_zoom: Масштаб для географии
    """
    _safe_mkdir(output_dir)
    logging.info(f"📁 Папка {output_dir} создана/проверена")
    
    successful_groups = []
    failed_groups = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(
            storage_state="vk_storage.json", 
            viewport={"width": viewport_width, "height": viewport_height}
        )
        page = ctx.new_page()
        
        logging.info(f"➡️  Открываем VK Ads: {ads_url}")
        page.goto(ads_url, timeout=60_000)
        
        try:
            page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:
            logging.warning("⚠️  networkidle не достигнут – продолжаем...")
        
        # Обработка первичной авторизации VK ID
        if not _handle_vk_id_auth(page):
            logging.warning("⚠️  Возможны проблемы с авторизацией VK ID")
        
        # Дополнительное ожидание после авторизации
        try:
            page.wait_for_load_state("networkidle", timeout=15_000)
        except Exception:
            logging.warning("⚠️  networkidle после авторизации не достигнут – продолжаем...")
        
        # Устанавливаем масштаб страницы
        page.evaluate(f"document.body.style.zoom = '{zoom_level}'")
        page.wait_for_timeout(6_000)
        
        # Проверка на капчу
        if _is_captcha(page):
            logging.warning("🛑 Обнаружена капча – решите её...")
            page.wait_for_timeout(30_000)
            ctx.storage_state(path="vk_storage.json")
        
        # Обрабатываем каждую группу
        for idx, group in enumerate(groups, 1):
            group_id = group.get("id", "")
            group_name = group.get("name", "")
            display_name = group.get("display_name", group_name)
            
            logging.info(f"📊 [{idx}/{len(groups)}] Обрабатываем группу: '{display_name}' (ID: {group_id})")
            
            try:
                # Поиск группы по ID
                if not _apply_search_optimized(page, group_id):
                    logging.error(f"❌ Не удалось выполнить поиск по ID: {group_id}")
                    failed_groups.append(group)
                    continue
                
                page.wait_for_timeout(4_000)
                
                # Открытие статистики (ищем по ID, но также можем использовать название как fallback)
                if not _open_group_stats_by_id(page, group_id, display_name):
                    logging.error(f"❌ Не удалось открыть статистику по ID: {group_id}")
                    failed_groups.append(group)
                    continue
                
                # Создание скриншотов (используем display_name для имен файлов)
                _create_screenshots_for_group(page, display_name, output_dir, tabs, demography_zoom, geo_zoom)
                
                # Закрытие статистики
                _close_group_stats(page)
                
                # Очистка поиска (кроме последней группы)
                if idx < len(groups):
                    _clear_search(page)
                
                successful_groups.append(group)
                logging.info(f"✅ Группа {display_name} обработана успешно")
                
            except Exception as e:
                logging.error(f"❌ Ошибка при обработке группы {display_name}: {e}")
                failed_groups.append(group)
                
                # Пытаемся закрыть статистику в случае ошибки
                try:
                    _close_group_stats(page)
                except:
                    pass
        
        browser.close()
    
    logging.info(f"🏁 Обработка завершена. Успешно: {len(successful_groups)}, Ошибки: {len(failed_groups)}")
    if failed_groups:
        logging.warning(f"⚠️  Группы с ошибками: {', '.join(g.get('name', str(g)) if isinstance(g, dict) else str(g) for g in failed_groups)}")
    
    return successful_groups, failed_groups


def _apply_search_optimized(page, query: str) -> bool:
    """Оптимизированный поиск с логированием."""
    logging.info(f"🔍 Поиск рекламного плана: '{query}'")
    
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
        logging.error("❌ Поле поиска не найдено")
        return False
    
    try:
        inp.click()
        page.wait_for_timeout(1000)
        inp.fill("")
        page.wait_for_timeout(600)
        inp.fill(query)
        page.wait_for_timeout(1000)
        page.keyboard.press("Enter")
        page.wait_for_timeout(4_000)
        
        # Проверяем наличие опции "содержит"
        contains = page.locator("[data-testid='search-contains-menu-item']").first
        if contains.count():
            contains.click()
            page.wait_for_timeout(2_000)
            logging.info("✅ Выбран вариант 'содержит'")
        
        return True
        
    except Exception as e:
        logging.error(f"⚠️  Ошибка при поиске: {e}")
        return False


def _open_group_stats_by_id(page, group_id: str, display_name: str = "") -> bool:
    """Открывает статистику для указанной группы по ID."""
    logging.info(f"🔍 Ищем рекламный план по ID '{group_id}' (название: '{display_name}') в таблице...")
    
    # Сначала пытаемся найти по ID, если не получается - по названию
    search_patterns = [group_id]
    if display_name:
        search_patterns.append(display_name.upper())
    
    link = None
    found_text = ""
    
    for pattern in search_patterns:
        logging.info(f"🔍 Поиск по паттерну: '{pattern}'")
        
        link_selectors = [
            f"[data-testid='name-link']:has-text('{pattern}')",
            f"a:has-text('{pattern}')",
            f"td a:has-text('{pattern}')",
            f"tr:has-text('{pattern}') [data-testid='name-link']",
            # Общий поиск всех ссылок для проверки текста
            "[data-testid='name-link']",
        ]
        
        for selector in link_selectors:
            elements = page.locator(selector).all()
            for element in elements:
                element_text = (element.text_content() or "").strip()
                # Проверяем, содержит ли текст элемента искомый паттерн
                if pattern in element_text or element_text.upper().find(pattern.upper()) >= 0:
                    link = element
                    found_text = element_text
                    logging.info(f"✅ Найден план: '{found_text}' по паттерну '{pattern}'")
                    break
            
            if link:
                break
        
        if link:
            break
    
    if not link:
        logging.error(f"❌ Рекламный план с ID '{group_id}' или названием '{display_name}' не найден!")
        logging.info("🧹 Очищаем поиск для следующего запроса...")
        _clear_search(page)
        return False
    
    # Находим родительскую строку
    row = link.locator("xpath=ancestor::tr").first
    if row.count() == 0:
        row = link.locator("..").locator("..").first
    
    try:
        row.scroll_into_view_if_needed(timeout=20_000)
        page.wait_for_timeout(800)
    except Exception as e:
        logging.warning(f"⚠️  Ошибка при прокрутке к строке: {e}")
    
    # Ховерим строку для появления кнопок
    try:
        row.hover(timeout=10_000)
        page.wait_for_timeout(600)
        logging.info("🖱️  Навели курсор на строку плана")
    except Exception as e:
        logging.warning(f"⚠️  Не удалось навести курсор на строку: {e}")
    
    # Поиск кнопки статистики
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
        logging.error("❌ Кнопка статистики не найдена")
        logging.info("🧹 Очищаем поиск для следующего запроса...")
        _clear_search(page)
        return False
    
    try:
        btn.scroll_into_view_if_needed()
        page.wait_for_timeout(500)
        btn.click()
        page.wait_for_timeout(3_000)
        logging.info(f"✅ Статистика для '{found_text}' открыта")
        return True
    except Exception as e:
        logging.error(f"❌ Ошибка при клике по кнопке статистики: {e}")
        return False


def _open_group_stats(page, group_name_upper: str) -> bool:
    """Открывает статистику для указанной группы."""
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
        logging.error(f"❌ Рекламный план '{group_name_upper}' не найден!")
        logging.info("🧹 Очищаем поиск для следующего запроса...")
        _clear_search(page)
        return False
    
    # Находим родительскую строку
    row = link.locator("xpath=ancestor::tr").first
    if row.count() == 0:
        row = link.locator("..").locator("..").first
    
    try:
        row.scroll_into_view_if_needed(timeout=20_000)
        page.wait_for_timeout(800)
    except Exception as e:
        logging.warning(f"⚠️  Ошибка при прокрутке к строке: {e}")
    
    # Ховерим строку для появления кнопок
    try:
        row.hover(timeout=10_000)
        page.wait_for_timeout(600)
        logging.info("🖱️  Навели курсор на строку плана")
    except Exception as e:
        logging.warning(f"⚠️  Не удалось навести курсор на строку: {e}")
    
    # Поиск кнопки статистики
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
        logging.error("❌ Кнопка статистики не найдена")
        logging.info("🧹 Очищаем поиск для следующего запроса...")
        _clear_search(page)
        return False
    
    try:
        btn.click()
        page.wait_for_timeout(8_000)
        logging.info("✅ Статистика открыта")
        return True
    except Exception as e:
        logging.error(f"⚠️  Ошибка при клике на статистику: {e}")
        logging.info("🧹 Очищаем поиск для следующего запроса...")
        _clear_search(page)
        return False


def _create_screenshots_for_group(page, group_name_upper: str, output_dir: str, tabs, demography_zoom: float, geo_zoom: float):
    """Создает скриншоты для всех вкладок группы."""
    _safe_mkdir(output_dir)

    # Ждём появления вкладок статистики (до 10 сек)
    try:
        page.wait_for_selector("#tab_overview", timeout=10_000)
        logging.info("✅ Вкладки статистики загружены")
    except Exception:
        logging.warning("⚠️  Вкладки статистики не появились за 10 сек, пробуем продолжить")

    for tab in tabs or ("overview",):
        logging.info(f"📑 Обрабатываем вкладку: {tab}")

        tab_btn = page.locator(f"#tab_{tab}")
        if tab_btn.count():
            tab_btn.click()
            if tab == "geo":
                logging.info("⏳ Дополнительное ожидание для загрузки карт...")
                page.wait_for_timeout(6_000)
            else:
                page.wait_for_timeout(2_000)
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
                funnel_path = os.path.join(output_dir, f"{group_name_upper}_overview_funnel.png")
                _shot_with_caption(page, caption, funnel, funnel_path)
                logging.info(f"✅ Воронка сохранена: {funnel_path}")
            else:
                logging.warning(f"⚠️  Воронка конверсий не найдена для группы {group_name_upper}")
                
        elif tab == "demography":
            tab_path = os.path.join(output_dir, f"{group_name_upper}_{tab}.png")
            _safe_mkdir(output_dir)
            _shot_demography_section(page, tab_path, demography_zoom)
            
        elif tab == "geo":
            tab_path = os.path.join(output_dir, f"{group_name_upper}_{tab}.png")
            _safe_mkdir(output_dir)
            _shot_geo_section(page, tab_path, geo_zoom)
            
        elif tab != "overview":
            _scroll_to_bottom(page)
            tab_path = os.path.join(output_dir, f"{group_name_upper}_{tab}.png")
            _safe_mkdir(output_dir)
            page.screenshot(path=tab_path, full_page=True)
            logging.info(f"✅ Скриншот вкладки сохранён: {tab_path}")


def _close_group_stats(page):
    """Закрывает статистику группы по крестику."""
    logging.info("🔄 Закрываем статистику...")
    
    # Ждем стабилизации страницы
    page.wait_for_timeout(1000)
    
    # Сначала пытаемся убрать overlay, который может блокировать клик
    try:
        overlay_selectors = [
            "div.RightSidebar.module_overlay__ZmY2O",
            "[class*='overlay']",
            "[class*='backdrop']"
        ]
        for overlay_selector in overlay_selectors:
            overlay = page.locator(overlay_selector).first
            if overlay.count() > 0:
                logging.info(f"🔍 Найден блокирующий overlay: {overlay_selector}")
                # Скрываем overlay через CSS
                page.evaluate(f"document.querySelector('{overlay_selector}').style.display = 'none'")
                page.wait_for_timeout(500)
                break
    except Exception as e:
        logging.debug(f"Не удалось убрать overlay: {e}")
    
    # Более точные селекторы для кнопки закрытия (добавлен cancel_16)
    close_selectors = [
        # Точные селекторы для SVG с cancel (24 и 16)
        "svg.vkuiIcon--cancel_24",
        "svg.vkuiIcon--cancel_16", 
        "svg[class*='vkuiIcon--cancel_24']",
        "svg[class*='vkuiIcon--cancel_16']",
        "svg[class*='cancel_24']",
        "svg[class*='cancel_16']",
        # Кнопки, содержащие этот SVG
        "button:has(svg.vkuiIcon--cancel_24)",
        "button:has(svg.vkuiIcon--cancel_16)",
        "button:has(svg[class*='cancel_24'])",
        "button:has(svg[class*='cancel_16'])",
        "[role='button']:has(svg[class*='cancel_24'])",
        "[role='button']:has(svg[class*='cancel_16'])",
        # Родительские элементы с aria-label
        "button[aria-label*='Закрыть']",
        "button[aria-label*='закрыть']", 
        "button[aria-label*='Close']",
        "button[aria-label*='close']",
        # По data-testid
        "[data-testid*='close']",
        "[data-testid*='Close']",
        # Общие селекторы для модальных окон
        ".modal-close",
        ".close-button",
        ".dialog-close",
        # Поиск по viewBox SVG
        "svg[viewBox='0 0 24 24']:has(use[xlink:href='#cancel_24'])",
        "svg[viewBox='0 0 16 16']:has(use[xlink:href='#cancel_16'])",
        "button:has(svg[viewBox='0 0 24 24']:has(use[xlink:href='#cancel_24']))",
        "button:has(svg[viewBox='0 0 16 16']:has(use[xlink:href='#cancel_16']))"
    ]
    
    close_btn = None
    found_selector = None
    
    # Ищем кнопку закрытия
    for selector in close_selectors:
        try:
            elements = page.locator(selector).all()
            for element in elements:
                if element.is_visible():
                    close_btn = element
                    found_selector = selector
                    logging.info(f"✅ Найдена видимая кнопка закрытия: {selector}")
                    break
            if close_btn:
                break
        except Exception as e:
            logging.debug(f"Ошибка при поиске по селектору '{selector}': {e}")
            continue
    
    if not close_btn:
        logging.warning("⚠️  Кнопка закрытия статистики не найдена, пробуем альтернативные методы...")
        return _close_stats_fallback(page)
    
    # Пробуем несколько методов клика
    success = False
    
    # Метод 1: Принудительный клик (игнорирует перекрывающие элементы)
    try:
        logging.info(f"🖱️  Пробуем принудительный клик по: {found_selector}")
        close_btn.scroll_into_view_if_needed()
        page.wait_for_timeout(500)
        close_btn.click(force=True, timeout=5000)
        page.wait_for_timeout(2000)
        logging.info("✅ Статистика закрыта (принудительный клик)")
        success = True
    except Exception as e:
        logging.warning(f"⚠️  Принудительный клик не сработал: {e}")
        
    # Метод 1.5: Обычный клик (если принудительный не сработал)
    if not success:
        try:
            logging.info(f"🖱️  Пробуем обычный клик по: {found_selector}")
            close_btn.click(timeout=5000)
            page.wait_for_timeout(2000)
            logging.info("✅ Статистика закрыта (обычный клик)")
            success = True
        except Exception as e:
            logging.warning(f"⚠️  Обычный клик не сработал: {e}")
    
    # Метод 2: Принудительный клик через JavaScript
    if not success:
        try:
            logging.info("🖱️  Пробуем принудительный клик через JS...")
            page.evaluate("element => element.click()", close_btn.element_handle())
            page.wait_for_timeout(2000)
            logging.info("✅ Статистика закрыта (JS клик)")
            success = True
        except Exception as e:
            logging.warning(f"⚠️  JS клик не сработал: {e}")
    
    # Метод 3: Событие клика через dispatchEvent
    if not success:
        try:
            logging.info("🖱️  Пробуем событие клика через dispatchEvent...")
            page.evaluate("""
                element => element.dispatchEvent(new MouseEvent('click', {
                    view: window,
                    bubbles: true,
                    cancelable: true
                }))
            """, close_btn.element_handle())
            page.wait_for_timeout(2000)
            logging.info("✅ Статистика закрыта (dispatchEvent)")
            success = True
        except Exception as e:
            logging.warning(f"⚠️  dispatchEvent не сработал: {e}")
    
    # Метод 4: Клик по координатам
    if not success:
        try:
            logging.info("🖱️  Пробуем клик по координатам...")
            bbox = close_btn.bounding_box()
            if bbox:
                x = bbox['x'] + bbox['width'] / 2
                y = bbox['y'] + bbox['height'] / 2
                page.mouse.click(x, y)
                page.wait_for_timeout(2000)
                logging.info("✅ Статистика закрыта (клик по координатам)")
                success = True
        except Exception as e:
            logging.warning(f"⚠️  Клик по координатам не сработал: {e}")
    
    if not success:
        logging.warning("⚠️  Все методы клика неуспешны, пробуем fallback...")
        return _close_stats_fallback(page)
    
    return True


def _close_stats_fallback(page):
    """Альтернативные методы закрытия статистики."""
    logging.info("🔄 Пробуем альтернативные методы закрытия...")
    
    # Метод 1: ESC
    try:
        logging.info("⌨️  Пробуем ESC...")
        page.keyboard.press("Escape")
        page.wait_for_timeout(2000)
        logging.info("✅ Попытка закрытия через ESC")
        return True
    except Exception as e:
        logging.warning(f"⚠️  ESC не сработал: {e}")
    
    # Метод 2: Клик по overlay/backdrop
    try:
        logging.info("🖱️  Пробуем клик по overlay...")
        overlay_selectors = [
            ".modal-backdrop",
            ".overlay",
            ".dialog-backdrop",
            "[class*='overlay']",
            "[class*='backdrop']"
        ]
        
        for selector in overlay_selectors:
            overlay = page.locator(selector).first
            if overlay.count() > 0:
                overlay.click()
                page.wait_for_timeout(2000)
                logging.info(f"✅ Закрыто через overlay: {selector}")
                return True
    except Exception as e:
        logging.warning(f"⚠️  Клик по overlay не сработал: {e}")
    
    # Метод 3: Поиск любых кнопок с текстом "Закрыть"
    try:
        logging.info("🔍 Ищем кнопки с текстом 'Закрыть'...")
        close_text_selectors = [
            "button:has-text('Закрыть')",
            "button:has-text('закрыть')",
            "button:has-text('Close')",
            "button:has-text('close')",
            "[role='button']:has-text('Закрыть')",
            "a:has-text('Закрыть')"
        ]
        
        for selector in close_text_selectors:
            btn = page.locator(selector).first
            if btn.count() > 0 and btn.is_visible():
                btn.click()
                page.wait_for_timeout(2000)
                logging.info(f"✅ Закрыто через текстовую кнопку: {selector}")
                return True
    except Exception as e:
        logging.warning(f"⚠️  Поиск текстовых кнопок не сработал: {e}")
    
    # Метод 4: Попробуем вернуться назад в браузере
    try:
        logging.info("⬅️  Пробуем вернуться назад...")
        page.go_back()
        page.wait_for_timeout(3000)
        logging.info("✅ Возврат назад выполнен")
        return True
    except Exception as e:
        logging.warning(f"⚠️  Возврат назад не сработал: {e}")
    
    logging.error("❌ Все методы закрытия статистики неуспешны")
    return False


def _clear_search(page):
    """Очищает поле поиска по крестику."""
    logging.info("🧹 Очищаем поиск...")
    
    # Ищем крестик для очистки поиска (SVG с cancel_16)
    clear_selectors = [
        # Точные селекторы для VK cancel_16 SVG из вашего примера
        "svg.vkuiIcon--cancel_16",
        "svg[class*='vkuiIcon--cancel_16']",
        "svg[class*='vkuiIcon vkuiIcon--16 vkuiIcon--w-16 vkuiIcon--h-16 vkuiIcon--cancel_16']",
        "svg.vkuiIcon--16.vkuiIcon--cancel_16",
        # SVG с use и xlink:href для cancel_16
        "svg:has(use[xlink:href='#cancel_16'])",
        "svg[viewBox='0 0 16 16']:has(use[xlink:href='#cancel_16'])",
        # Кнопки, содержащие эти SVG
        "button:has(svg.vkuiIcon--cancel_16)",
        "button:has(svg[class*='cancel_16'])",
        "button:has(svg:has(use[xlink:href='#cancel_16']))",
        "[role='button']:has(svg[class*='cancel_16'])",
        # Дополнительные селекторы
        "[data-testid*='clear']",
        "[data-testid*='search-clear']",
        "input[type='search'] + button",
        ".search-clear",
        # Поиск по aria-label
        "button[aria-label*='очистить']",
        "button[aria-label*='Очистить']",
        "button[aria-label*='clear']",
        "button[aria-label*='Clear']"
    ]
    
    clear_btn = None
    found_selector = None
    
    # Ищем видимую кнопку очистки
    for selector in clear_selectors:
        try:
            elements = page.locator(selector).all()
            for element in elements:
                if element.is_visible():
                    clear_btn = element
                    found_selector = selector
                    logging.info(f"✅ Найдена видимая кнопка очистки поиска: {selector}")
                    break
            if clear_btn:
                break
        except Exception as e:
            logging.debug(f"Ошибка при поиске по селектору '{selector}': {e}")
            continue
    
    if clear_btn:
        try:
            # Пробуем несколько методов клика
            success = False
            
            # Метод 1: Обычный клик
            try:
                clear_btn.scroll_into_view_if_needed()
                page.wait_for_timeout(300)
                clear_btn.click(timeout=3000)
                page.wait_for_timeout(1500)
                logging.info("✅ Поиск очищен (обычный клик)")
                success = True
            except Exception as e:
                logging.warning(f"⚠️  Обычный клик не сработал: {e}")
            
            # Метод 2: JS клик
            if not success:
                try:
                    page.evaluate("arguments[0].click()", clear_btn.element_handle())
                    page.wait_for_timeout(1500)
                    logging.info("✅ Поиск очищен (JS клик)")
                    success = True
                except Exception as e:
                    logging.warning(f"⚠️  JS клик не сработал: {e}")
            
            # Метод 3: Клик по координатам
            if not success:
                try:
                    bbox = clear_btn.bounding_box()
                    if bbox:
                        x = bbox['x'] + bbox['width'] / 2
                        y = bbox['y'] + bbox['height'] / 2
                        page.mouse.click(x, y)
                        page.wait_for_timeout(1500)
                        logging.info("✅ Поиск очищен (клик по координатам)")
                        success = True
                except Exception as e:
                    logging.warning(f"⚠️  Клик по координатам не сработал: {e}")
            
            if not success:
                logging.warning("⚠️  Все методы клика неуспешны, пробуем fallback")
                _clear_search_fallback(page)
                
        except Exception as e:
            logging.warning(f"⚠️  Ошибка при очистке поиска: {e}")
            _clear_search_fallback(page)
    else:
        logging.warning("⚠️  Кнопка очистки поиска не найдена, пробуем fallback")
        _clear_search_fallback(page)


def _clear_search_fallback(page):
    """Fallback метод для очистки поиска."""
    search_selectors = [
        "input[type='search']",
        "input[placeholder*='Поиск']",
        "input[placeholder*='поиск']",
        "[data-testid*='search'] input",
        ".search input",
        "input[name*='search']",
    ]
    
    for selector in search_selectors:
        inp = page.locator(selector).first
        if inp.count() > 0:
            try:
                inp.click()
                page.wait_for_timeout(500)
                inp.fill("")
                page.wait_for_timeout(1000)
                logging.info("✅ Поиск очищен (fallback)")
                return
            except Exception as e:
                logging.warning(f"⚠️  Fallback очистка не удалась: {e}")
    
    logging.warning("⚠️  Не удалось очистить поиск")
