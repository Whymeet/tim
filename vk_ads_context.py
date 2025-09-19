"""Utilities for launching a realistic Playwright context for VK Ads."""

from __future__ import annotations

from typing import Any, Dict, Optional, Union

from playwright.sync_api import BrowserContext, Playwright

# User agent string of a recent stable Chrome build on Windows.
_CHROME_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

StorageState = Union[str, Dict[str, Any]]


def create_vk_ads_context(
    playwright: Playwright,
    *,
    storage_state: Optional[StorageState] = None,
    viewport: Optional[Dict[str, int]] = None,
    **overrides: Any,
) -> BrowserContext:
    """Create a persistent Playwright context tuned for VK Ads automation."""

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

    if storage_state is not None:
        launch_options["storage_state"] = storage_state
    if viewport is not None:
        launch_options["viewport"] = viewport

    launch_options.update(overrides)

    return playwright.chromium.launch_persistent_context(**launch_options)
