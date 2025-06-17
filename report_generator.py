from collections import defaultdict
from docx import Document
from docx.shared import Inches
import os

def generate_report(posts: list[dict],
                    output_file: str = "Отчёт.docx",
                    assets_dir: str = "assets") -> None:
    doc = Document()
    doc.add_heading("Отчёт по рекламным кампаниям VK", level=0)

    # группируем посты по компании
    grouped = defaultdict(list)
    for p in posts:
        grouped[p["Компания"]].append(p)

    for company, items in grouped.items():
        doc.add_heading(company, level=1)

        for idx, post in enumerate(items, start=1):
            subtitle = f"{idx}. {post['Группа']}"
            doc.add_heading(subtitle, level=2)
            doc.add_paragraph(post["Ссылка"])

            # скрин поста
            if os.path.exists(post.get("Скриншот", "")):
                doc.add_picture(post["Скриншот"], width=Inches(5))

            # все скрины статистики, начинающиеся с имени группы
            prefix = post["Группа"].lower()
            stats = sorted(
                f for f in os.listdir(assets_dir)
                if f.lower().startswith(prefix) and f.lower().endswith(".png")
            )
            for fname in stats:
                doc.add_picture(os.path.join(assets_dir, fname), width=Inches(5))

            doc.add_paragraph("—" * 40)

    doc.save(output_file)
    print(f"📄 Отчёт сохранён: {output_file}")
