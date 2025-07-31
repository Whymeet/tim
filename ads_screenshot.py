# ads_screenshot.py
from playwright.sync_api import sync_playwright
import os
import time

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
        print(f"⚠️  Ошибка при создании скриншота с TopLine: {e}")
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
        print(f"⚠️  Ошибка при создании скриншота с подписью: {e}")
        target.screenshot(path=path)


# ────────────────────────────── main routine ────────────────────────────────


def screenshot_group_stats(
    group_name: str,
    output_dir: str,
    ads_url: str,
    tabs: tuple[str, ...] | None = ("overview", "demography", "geo", "phrases"),
):
    """Save screenshots of *group_name* stats into *output_dir*."""

    # Убеждаемся, что папка существует
    _safe_mkdir(output_dir)
    print(f"📁 Папка {output_dir} создана/проверена")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(
            storage_state="vk_storage.json", viewport={"width": 1400, "height": 900}
        )
        page = ctx.new_page()

        print(f"➡️  Opening VK Ads: {ads_url}")
        page.goto(ads_url, timeout=60_000)
        try:
            page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:
            print("⚠️  networkidle wasn't reached – continuing …")
        page.wait_for_timeout(3_000)

        # Captcha -----------------------------------------------------------
        if _is_captcha(page):
            print("🛑 Captcha detected – solve it …")
            page.wait_for_timeout(30_000)
            ctx.storage_state(path="vk_storage.json")

        # Search ------------------------------------------------------------
        def _apply_search(q: str):
            print(f"🔍 Поиск рекламного плана: '{q}'")

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
                    print(f"✅ Найдено поле поиска: {selector}")
                    break

            if not inp or inp.count() == 0:
                print("❌ Поле поиска не найдено, попробуем продолжить без поиска")
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
                    print("✅ Выбран вариант 'содержит'")

                return True
            except Exception as e:
                print(f"⚠️  Ошибка при поиске: {e}")
                return False

        _apply_search(group_name)
        page.wait_for_timeout(2_000)

        # Поиск рекламного плана ----------------------------------------
        print(f"🔍 Ищем рекламный план '{group_name}' в таблице...")

        link_selectors = [
            f"[data-testid='name-link']:has-text('{group_name}')",
            f"a:has-text('{group_name}')",
            f"[data-testid='name-link']",
            f"td a:has-text('{group_name}')",
            f"tr:has-text('{group_name}') [data-testid='name-link']",
        ]

        link = None
        for selector in link_selectors:
            link = page.locator(selector).first
            if link.count() > 0 and group_name in (link.text_content() or ""):
                print(f"✅ Найден план: {link.text_content().strip()}")
                break

        if not link or link.count() == 0:
            raise RuntimeError(
                f"❌ Рекламный план '{group_name}' не найден! Проверьте название."
            )

        # Находим родительскую строку таблицы
        row = link.locator("xpath=ancestor::tr").first
        if row.count() == 0:
            row = link.locator("..").locator("..").first

        try:
            row.scroll_into_view_if_needed(timeout=10_000)
            page.wait_for_timeout(400)
        except Exception as e:
            print(f"⚠️  Ошибка при прокрутке к строке: {e}")

        # ─── Новое: ховерим строку, чтобы появились иконки действий ────
        try:
            row.hover(timeout=5_000)
            page.wait_for_timeout(300)
            print("🖱️  Навели курсор на строку плана — иконки должны появиться")
        except Exception as e:
            print(f"⚠️  Не удалось навести курсор на строку: {e}")

        # Поиск кнопки статистики --------------------------------------
        print("📊 Открываем статистику...")

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
                    print(f"✅ Найдена кнопка статистики: {sel}")
                    return btn
            return None

        btn = _find_stats_button(row) or _find_stats_button(page)
        if not btn:
            # Быстрая диагностика: покажем, какие svg-иконки есть в строке
            svgs = row.locator("svg").all()
            print(f"❔ В строке найдено SVG-иконок: {len(svgs)}")
            for i, svg in enumerate(svgs[:5], 1):
                try:
                    print(f"  {i}. {svg.get_attribute('class')}")
                except Exception:
                    pass
            raise RuntimeError(
                "❌ Кнопка статистики не найдена – возможно, изменился интерфейс"
            )

        try:
            btn.click()
            page.wait_for_timeout(4_000)
            print("✅ Статистика открыта")
        except Exception as e:
            raise RuntimeError(f"⚠️  Ошибка при клике на статистику: {e}") from e

        # Убеждаемся, что папка всё ещё существует
        _safe_mkdir(output_dir)

        # Iterate tabs --------------------------------------------------
        for tab in tabs or ("overview",):
            print(f"📑 Обрабатываем вкладку: {tab}")

            tab_btn = page.locator(f"#tab_{tab}")
            if tab_btn.count():
                tab_btn.click()
                page.wait_for_timeout(1_000)
                print(f"✅ Вкладка {tab} открыта")
            else:
                print(f"⚠️  Вкладка '{tab}' не найдена – пропускаем")
                continue

            if tab == "overview":
                # Воронка конверсий
                caption = page.locator("text=Воронка конверсий").first
                funnel = page.locator("div[class^='ConversionsChart_wrap']").first
                if caption.count() and funnel.count():
                    funnel_path = os.path.join(
                        output_dir, f"{group_name}_overview_funnel.png"
                    )
                    _shot_with_caption(page, caption, funnel, funnel_path)
                    print(f"✅ Воронка сохранена: {funnel_path}")
            elif tab != "overview":
                # Полный скриншот вкладки (только для не-overview вкладок)
                _scroll_to_bottom(page)
                tab_path = os.path.join(output_dir, f"{group_name}_{tab}.png")
                _safe_mkdir(output_dir)
                page.screenshot(path=tab_path, full_page=True)
                print(f"✅ Скриншот вкладки сохранён: {tab_path}")

        print("✅ Все скриншоты VK Ads созданы успешно")
        browser.close()
