from docx import Document
from docx.shared import Inches
import os

def generate_report(posts, output_file="Отчет.docx", ads_screenshot_path=None):
    doc = Document()
    doc.add_heading("Отчет по рекламным постам", level=0)
    
    # Добавляем все посты
    for i, post in enumerate(posts, 1):
        title = post.get("Название поста") or f"Пост {i}"
        url = post.get("Ссылка")
        screenshot = post.get("Скриншот")
        group_stats = post.get("Групповая статистика")

        doc.add_heading(title, level=2)
        doc.add_paragraph(url)
        
        if screenshot and os.path.exists(screenshot):
            doc.add_picture(screenshot, width=Inches(5))
            
        if group_stats and os.path.exists(group_stats):
            doc.add_paragraph("Статистика рекламной группы VK Ads:")
            doc.add_picture(group_stats, width=Inches(5))
            
        doc.add_paragraph("-" * 40)
    
    # Добавляем общую статистику VK Ads в конец отчета
    if ads_screenshot_path and os.path.exists(ads_screenshot_path):
        doc.add_page_break()  # Новая страница для статистики
        doc.add_heading("Статистика VK Ads Dashboard", level=1)
        doc.add_paragraph("Общая статистика по рекламным группам за период с 01.04.2025 по 04.05.2025:")
        doc.add_picture(ads_screenshot_path, width=Inches(6))
        doc.add_paragraph(f"Дата создания отчета: {__import__('datetime').datetime.now().strftime('%d.%m.%Y %H:%M')}")
    
    doc.save(output_file)
    print(f"Отчет сохранён как {output_file}")