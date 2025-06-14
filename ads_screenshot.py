from playwright.sync_api import sync_playwright
import os
import shutil

###############################################################################
#  VK Ads — automatic screenshots with **strict** ad‑plan matching            #
###############################################################################
#  Uses exact *group_name* only. Handles virtualized DOM (BaseTable).         #
#  EXTRA ELEMENT SHOTS (overview):                                            #
#       ▸ traffic graph          → ``*_overview_graph.png``                   #
#       ▸ conversion funnel      → ``*_overview_funnel.png`` (now **without** #
#         TopLine; only funnel chart + its caption)                           #
###############################################################################

###############################################################################
# Helper utilities                                                             #
###############################################################################

def _safe_mkdir(path: str):
    """Create directory *path* when it doesn’t yet exist (parents included)."""
    if path and not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def _scroll_to_bottom(page, step: int = 700):
    """Gradually scroll down so virtualised tables & graphs are fully rendered."""
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
    """Return locator for the header block present on every stats page."""
    return page.locator("div[class^='TopLine_topline']").first


def _union_clip(box_a: dict, box_b: dict):
    """Return a Playwright clip dict that encloses *box_a* and *box_b*."""
    x1 = min(box_a["x"], box_b["x"])
    y1 = min(box_a["y"], box_b["y"])
    x2 = max(box_a["x"] + box_a["width"], box_b["x"] + box_b["width"])
    y2 = max(box_a["y"] + box_a["height"], box_b["y"] + box_b["height"])
    return {
        "x": int(x1),
        "y": int(y1),
        "width": int(x2 - x1),
        "height": int(y2 - y1),
    }


def _shot_with_topline(page, target_locator, path):
    """Take a screenshot that always contains TopLine + *target_locator*."""
    top = _topline_loc(page)
    if not top.count():
        target_locator.screenshot(path=path)
        return

    target_locator.scroll_into_view_if_needed(); page.wait_for_timeout(250)

    box_top = top.bounding_box()
    box_tgt = target_locator.bounding_box()
    if box_top is None or box_tgt is None:
        target_locator.screenshot(path=path); return

    clip = _union_clip(box_top, box_tgt)
    page.screenshot(path=path, clip=clip)


def _shot_with_caption(page, caption_locator, target_locator, path):
    """Screenshot containing *caption_locator* + *target_locator* (no TopLine)."""
    # ensure both nodes are rendered
    caption_locator.scroll_into_view_if_needed(); page.wait_for_timeout(200)
    target_locator.scroll_into_view_if_needed(); page.wait_for_timeout(200)

    box_cap = caption_locator.bounding_box()
    box_tgt = target_locator.bounding_box()
    if box_cap is None or box_tgt is None:
        # fallback – capture target only
        target_locator.screenshot(path=path); return

    clip = _union_clip(box_cap, box_tgt)
    page.screenshot(path=path, clip=clip)

###############################################################################
# Main function                                                                #
###############################################################################

def screenshot_group_stats(
    group_name: str,
    ads_screenshot_path: str,
    ads_url: str,
    tabs: tuple[str, ...] | None = (
        "overview",
        "demography",
        "geo",
        "phrases",
    ),
):
    """Capture screenshots of VK Ads statistics for *group_name*.

    ▸ For every *tab* in **tabs** a full‑page PNG is stored at
      ``{output_dir}/{group_name}_{tab}.png``.
    ▸ When *tab* is **overview**, two extra shots are stored:
        – traffic graph   → ``*_overview_graph.png``          (with TopLine)
        – conversion funnel → ``*_overview_funnel.png``       (caption + funnel)
    ▸ ``ads_screenshot_path`` duplicates the full Overview page so the
      downstream docx pipeline remains unchanged.
    """

    # ── Prepare fs ----------------------------------------------------------
    if os.path.isdir(ads_screenshot_path):
        shutil.rmtree(ads_screenshot_path)

    output_dir = os.path.dirname(ads_screenshot_path)
    _safe_mkdir(output_dir)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(
            storage_state="vk_storage.json", viewport={"width": 1400, "height": 900}
        )
        page = ctx.new_page()

        print(f"➡️  Opening VK Ads: {ads_url}")
        page.goto(ads_url, timeout=60_000)

        try:
            page.wait_for_load_state("networkidle", timeout=5_000)
        except Exception:
            print("⚠️  networkidle wasn't reached – continuing anyway …")
        page.wait_for_timeout(2_000)

        # ── Captcha ---------------------------------------------------------
        if _is_captcha(page):
            print("🛑 Captcha detected – solve it in the opened window …")
            page.wait_for_timeout(30_000)
            ctx.storage_state(path="vk_storage.json")

        # ── Exact search ----------------------------------------------------
        def _apply_search(query: str):
            input_box = page.locator("input[type='search']").first
            if input_box.count():
                input_box.fill("")
                input_box.fill(query)
                page.wait_for_timeout(1_000)
                contains = page.locator("[data-testid='search-contains-menu-item']").first
                if contains.count():
                    contains.click(); page.wait_for_timeout(1_000)

        print(f"🔍 Searching for ad plan: '{group_name}' …")
        _apply_search(group_name)

        row_selector = (
            "[data-entityid$='-AdPlan']:has([data-testid='name-link']:has-text('%s'))" % group_name
        )
        row = page.locator(row_selector).first
        if not row.count():
            raise RuntimeError(f"❌ Ad plan '{group_name}' not found – check the name!")

        row.scroll_into_view_if_needed(); page.wait_for_timeout(500)

        # ── Statistics icon -------------------------------------------------
        stats_btn = row.locator("a[data-testid='stats']").first
        if not stats_btn.count():
            stats_btn = row.locator("svg.vkuiIcon--poll_outline_20, svg[class*='poll_outline']").first
        if not stats_btn.count():
            raise RuntimeError(
                f"❌ Can't find statistics button for '{group_name}'. Selector may have changed."
            )
        stats_btn.click(); page.wait_for_timeout(3_000)

        # ── Iterate over tabs ----------------------------------------------
        for tab in tabs or ("overview",):
            tab_id = f"tab_{tab}"
            tab_btn = page.locator(f"#{tab_id}")
            if tab_btn.count():
                tab_btn.click(); page.wait_for_timeout(700)
            else:
                print(f"⚠️  Tab '{tab}' not present – skipping …")

            # extra shots for overview ------------------------------------
            if tab == "overview":
                # 1. traffic graph (keep TopLine)
                graph_el = page.locator("canvas[role='img']").first
                if graph_el.count():
                    g_path = os.path.join(output_dir, f"{group_name}_overview_graph.png")
                    _shot_with_topline(page, graph_el, g_path)
                    print(f"📈 Graph  → {g_path}")
                else:
                    print("⚠️  Graph canvas not found – skipped …")

                # 2. conversion funnel (caption + funnel only)
                caption = page.locator("text=Воронка конверсий").first
                funnel_container = page.locator("div[class^='ConversionsChart_wrap']").first
                if caption.count() and funnel_container.count():
                    f_path = os.path.join(output_dir, f"{group_name}_overview_funnel.png")
                    _shot_with_caption(page, caption, funnel_container, f_path)
                    print(f"🪣 Funnel → {f_path}")
                else:
                    print("⚠️  Conversion funnel not found – skipped …")

            # ── Standard full‑page capture (TopLine inherently included) ----
            _scroll_to_bottom(page)
            full_path = os.path.join(output_dir, f"{group_name}_{tab}.png")
            page.screenshot(path=full_path, full_page=True)
            print(f"📷 Saved  → {full_path}")

            if tab == "overview":
                page.screenshot(path=ads_screenshot_path, full_page=True)

        browser.close()
