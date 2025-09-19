"""Utilities for launching a realistic Playwright context for VK Ads."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

from playwright.sync_api import BrowserContext, Playwright

# User agent string of a recent stable Chrome build on Windows.
_CHROME_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

StorageState = Union[str, Dict[str, Any]]

_LOCAL_STORAGE_INIT_SCRIPT = """
(state) => {
    if (!state || !Array.isArray(state.origins)) {
        return;
    }
    const match = state.origins.find(
        (entry) => entry && entry.origin === window.location.origin
    );
    if (!match || !Array.isArray(match.localStorage)) {
        return;
    }
    for (const item of match.localStorage) {
        if (!item || typeof item.name !== 'string') {
            continue;
        }
        const hasValue = Object.prototype.hasOwnProperty.call(item, 'value');
        const value = hasValue && item.value !== undefined ? item.value : '';
        try {
            window.localStorage.setItem(item.name, value);
        } catch (error) {
            console.warn('[vk_ads_context] failed to restore localStorage', item.name, error);
        }
    }
}
""".strip()

_LOCAL_STORAGE_EVAL_SCRIPT = f"""
(state) => {{
    ({_LOCAL_STORAGE_INIT_SCRIPT})(state);
}}
""".strip()


def _resolve_storage_state(storage_state: StorageState) -> Optional[Dict[str, Any]]:
    """Load Playwright storage state from a path or in-memory dict."""

    if storage_state is None:
        return None

    if isinstance(storage_state, str):
        state_path = Path(storage_state)
        if not state_path.exists():
            raise FileNotFoundError(f"Storage state file not found: {state_path}")
        with state_path.open(encoding="utf-8") as fh:
            data: Any = json.load(fh)
    else:
        data = storage_state

    if not isinstance(data, dict):
        raise ValueError("storage_state must be a path or Playwright storage dict")

    return data


def _apply_storage_state(context: BrowserContext, state: Dict[str, Any]) -> None:
    """Inject cookies and localStorage data into a persistent context."""

    cookies = state.get("cookies")
    if cookies:
        context.add_cookies(cookies)

    if state.get("origins"):
        context.add_init_script(_LOCAL_STORAGE_INIT_SCRIPT, state)
        for page in context.pages:
            page.evaluate(_LOCAL_STORAGE_EVAL_SCRIPT, state)


def create_vk_ads_context(
    playwright: Playwright,
    *,
    storage_state: Optional[StorageState] = None,
    viewport: Optional[Dict[str, int]] = None,
    **overrides: Any,
) -> BrowserContext:
    """Create a persistent Playwright context tuned for VK Ads automation."""

    resolved_state = _resolve_storage_state(storage_state)

    launch_options: Dict[str, Any] = {
        "user_data_dir": ".playwright-profile",
        "channel": "chrome",
        "headless": False,
        "ignore_default_args": ["--enable-automation"],
        "args": ["--disable-blink-features=AutomationControlled"],
        "locale": "ru-RU",
        "timezone_id": "Europe/Moscow",
        "user_agent": _CHROME_USER_AGENT,
    }

    if viewport is not None:
        launch_options["viewport"] = viewport

    launch_options.update(overrides)

    context = playwright.chromium.launch_persistent_context(**launch_options)

    if resolved_state:
        _apply_storage_state(context, resolved_state)

    return context

