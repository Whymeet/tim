from playwright.sync_api import sync_playwright
import os

###############################################################################
#  VK Ads — automatic screenshots with **strict** ad‑plan matching            #
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
        page.locator('input[name="captcha_key"], .page_block_captcha, [id*="captcha"], :text("Я не робот")').count()
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
    top = _topline_loc(page)
    if not top.count():
        target.screenshot(path=path)
        return
    target.scroll_into_view_if_needed(); page.wait_for_timeout(250)
    bt, bb = top.bounding_box(), target.bounding_box()
    if bt is None or bb is None:
        target.screenshot(path=path)
        return
    page.screenshot(path=path, clip=_union_clip(bt, bb))


def _shot_with_caption(page, caption, target, path):
    caption.scroll_into_view_if_needed(); target.scroll_into_view_if_needed(); page.wait_for_timeout(200)
    bc, bt = caption.bounding_box(), target.bounding_box()
    if bc is None or bt is None:
        target.screenshot(path=path)
        return
    page.screenshot(path=path, clip=_union_clip(bc, bt))

# ────────────────────────────── main routine ────────────────────────────────


def screenshot_group_stats(
    group_name: str,
    output_dir: str,
    ads_url: str,
    tabs: tuple[str, ...] | None = ("overview", "demography", "geo", "phrases"),
):
    """Save screenshots of *group_name* stats into *output_dir*."""

    _safe_mkdir(output_dir)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(storage_state="vk_storage.json", viewport={"width": 1400, "height": 900})
        page = ctx.new_page()

        print(f"➡️  Opening VK Ads: {ads_url}")
        page.goto(ads_url, timeout=60_000)
        try:
            page.wait_for_load_state("networkidle", timeout=5_000)
        except Exception:
            print("⚠️  networkidle wasn't reached – continuing …")
        page.wait_for_timeout(2_000)

        # Captcha -----------------------------------------------------------
        if _is_captcha(page):
            print("🛑 Captcha detected – solve it …")
            page.wait_for_timeout(30_000)
            ctx.storage_state(path="vk_storage.json")

        # Search ------------------------------------------------------------
        def _apply_search(q: str):
            inp = page.locator("input[type='search']").first
            if not inp.count():
                return
            inp.click(); inp.fill(""); inp.fill(q)
            page.keyboard.press("Enter"); page.wait_for_timeout(1_000)
            contains = page.locator("[data-testid='search-contains-menu-item']").first
            if contains.count():
                contains.click(); page.wait_for_timeout(900)

        print(f"🔍 Searching: '{group_name}' …")
        _apply_search(group_name)

        # Wait for the filtered list to render -----------------------------
        page.wait_for_timeout(600)  # small pause for virtualized table

        link = page.locator("[data-testid='name-link']").filter(has_text=group_name).first
        if not link.count():
            raise RuntimeError(f"❌ Ad plan '{group_name}' not found!")
        row = link.locator("xpath=ancestor::tr").first
        row.scroll_into_view_if_needed(); page.wait_for_timeout(400)

        # Open stats --------------------------------------------------------
        btn = row.locator("a[data-testid='stats']").first
        if not btn.count():
            btn = row.locator("svg.vkuiIcon--poll_outline_20, svg[class*='poll_outline']").first
        if not btn.count():
            raise RuntimeError("❌ Statistics button not found – layout changed?")
        btn.click(); page.wait_for_timeout(3_000)

        # Iterate tabs ------------------------------------------------------
        for tab in tabs or ("overview",):
            tab_btn = page.locator(f"#tab_{tab}")
            if tab_btn.count():
                tab_btn.click(); page.wait_for_timeout(700)
            else:
                print(f"⚠️  Tab '{tab}' missing – skipped …")

            if tab == "overview":
                graph = page.locator("canvas[role='img']").first
                if graph.count():
                    _shot_with_topline(page, graph, os.path.join(output_dir, f"{group_name}_overview_graph.png"))
                caption = page.locator("text=Воронка конверсий").first
                funnel = page.locator("div[class^='ConversionsChart_wrap']").first
                if caption.count() and funnel.count():
                    _shot_with_caption(page, caption, funnel, os.path.join(output_dir, f"{group_name}_overview_funnel.png"))

            _scroll_to_bottom(page)
            page.screenshot(path=os.path.join(output_dir, f"{group_name}_{tab}.png"), full_page=True)

        browser.close()
