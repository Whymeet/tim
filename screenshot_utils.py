from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import os

def draw_browser_bar(image_path, url):
    # Настройки панели - увеличиваем высоту
    bar_height = 65  # Было 48, стало 65
    bg_color = (242, 242, 242)
    text_color = (44, 44, 44)
    radius = 10
    favicon_size = 28

    # Скачиваем favicon VK
    favicon_url = "https://vk.com/favicon.ico"
    try:
        fav_raw = requests.get(favicon_url, timeout=5).content
        favicon = Image.open(BytesIO(fav_raw)).convert("RGBA").resize((favicon_size, favicon_size))
    except Exception:
        favicon = None

    # Открываем скрин
    image = Image.open(image_path).convert("RGB")
    width, height = image.size

    # Новый холст с местом под "адресную строку"
    total_height = height + bar_height
    new_img = Image.new('RGB', (width, total_height), bg_color)
    new_img.paste(image, (0, bar_height))

    draw = ImageDraw.Draw(new_img)
    # "Округленная" адресная строка - центрируем в новой высокой панели
    bar_x, bar_y, bar_w, bar_h = 60, 16, width - 120, 32  # Сдвигаем bar_y с 10 на 16
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], radius, fill="white", outline=(220, 220, 220), width=1)

    # Favicon
    if favicon:
        new_img.paste(favicon, (bar_x + 8, bar_y + 2), favicon)

    # Текст (url)
    font_size = 18
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    url_x = bar_x + favicon_size + 16
    url_y = bar_y + (bar_h - font_size) // 2
    draw.text((url_x, url_y), url, font=font, fill=text_color)

    # Сохраняем поверх старого файла (или можно с другим именем)
    new_img.save(image_path)
