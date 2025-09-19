from playwright.sync_api import sync_playwright
import os
import time
from vk_ads_context import create_vk_ads_context

with sync_playwright() as p:
    context = create_vk_ads_context(p, viewport={"width": 1280, "height": 720})
    page = context.new_page()
    page.goto("https://vk.com/login")
    print("Войди в свой VK-аккаунт, пройди двухфакторку, если надо.")
    print("Далее зайди на https://ads.vk.com/hq/dashboard/ad_groups")
    input("Когда страница полностью загрузится и ты авторизован, нажми Enter в терминале...")
    context.storage_state(path="vk_storage.json")
    context.close()
