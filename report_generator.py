from docx import Document
from docx.shared import Inches
import os
from datetime import datetime


def generate_report(posts, output_file: str = "Отчет.docx", assets_dir: str = "assets") -> None:
    """Собирает DOCX‑отчёт.

    1. *posts* — таблица из `post_loader`, как раньше (скрин поста + ссылка).
    2. Все PNG‑файлы в *assets_dir* **кроме** `post_*.png` и `vk_ads_stats.png`
       добавляются в конце отчёта. Таким образом, в документ попадут:
           ▸ `*_overview.png`, `*_overview_graph.png`, `*_overview_funnel.png`,
             `*_demography.png`, `*_geo.png`, `*_phrases.png`, …
    """

    doc = Document()
    doc.add_heading("Отчет по рекламным постам", level=0)

    # ──────────────────────────────────────────────────────────────────
    # 1. Блок с опубликованными постами                                
    # ──────────────────────────────────────────────────────────────────
    for i, post in enumerate(posts, 1):
        title = post.get("Название поста") or f"Пост {i}"
        url: str | None = post.get("Ссылка")
        screenshot: str | None = post.get("Скриншот")
        group_stats: str | None = post.get("Групповая статистика")

        doc.add_heading(title, level=2)
        if url:
            doc.add_paragraph(url)

        if screenshot and os.path.exists(screenshot):
            doc.add_picture(screenshot, width=Inches(5))

        if group_stats and os.path.exists(group_stats):
            doc.add_paragraph("Статистика рекламной группы VK Ads:")
            doc.add_picture(group_stats, width=Inches(5))

        doc.add_paragraph("-" * 40)

    # ──────────────────────────────────────────────────────────────────
    # 2. Блок статистики VK Ads (все PNG‑файлы, кроме постов)         
    # ──────────────────────────────────────────────────────────────────
    pngs = [
        f for f in os.listdir(assets_dir)
        if f.lower().endswith(".png")
        and not f.startswith("post_")
        and f != "vk_ads_stats.png"
    ]

    if pngs:
        doc.add_page_break()
        doc.add_heading("Статистика VK Ads", level=1)

        for fname in sorted(pngs):
            fpath = os.path.join(assets_dir, fname)
            if not os.path.exists(fpath):
                continue

            # Красивый подписи — убираем расширение и подчёркивания
            caption = os.path.splitext(fname)[0].replace("_", " ")
            # Для капшена используем простой параграф, а не heading
            doc.add_paragraph(caption, style="Intense Quote")
            doc.add_picture(fpath, width=Inches(6))
            doc.add_paragraph("")  # небольшой отступ

    # ──────────────────────────────────────────────────────────────────
    # 3. Дата формирования отчёта                                      
    # ──────────────────────────────────────────────────────────────────
    doc.add_paragraph(
        f"Дата создания отчёта: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    # ──────────────────────────────────────────────────────────────────
    doc.save(output_file)
    print(f"Отчёт сохранён как {output_file}")
