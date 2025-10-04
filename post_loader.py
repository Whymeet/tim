import pandas as pd

def load_posts(file_path: str) -> list[dict]:
    """Читает Excel-таблицу вида:
       ┌──────────────┬────────────────────────────┬────────────────┬──────────┐
       │ Про_Измайлово│ https://…  ЦР25_…          │ ЦР25_…        │ 118746396│
       └──────────────┴────────────────────────────┴────────────────┴──────────┘

    Возвращает список словарей:
    {
        "Компания": "Про_Измайлово",
        "Ссылка":   "https://vk.com/wall-…",
        "Группа":   "ЦР25_ИЗМАЙЛОВО_БЛАГОУСТРОЙСТВО",
        "ID_Группы": "118746396"
    }
    """
    df = pd.read_excel(file_path, header=None)
    posts: list[dict] = []

    for _, row in df.iterrows():
        company = str(row[0]).strip()
        # Ищем ячейку со ссылкой VK
        for i, cell in enumerate(row[1:], 1):
            if isinstance(cell, str) and "vk.com/wall" in cell:
                # Разделяем по переносам строк и пробелам
                lines = cell.strip().split('\n')
                
                link = ""
                group = "Без_имени" 
                group_id = ""
                
                # Парсим строки
                for line in lines:
                    line = line.strip()
                    if "vk.com/wall" in line:
                        link = line
                    elif line.startswith("ЦР25"):
                        group = line
                    elif line.isdigit():
                        group_id = line
                
                # Если не нашли все данные в одной ячейке, проверяем соседние ячейки
                if not group_id:
                    # Проверяем следующие ячейки на наличие ID (только цифры)
                    for j in range(i + 1, min(i + 3, len(row))):
                        next_cell = str(row[j]).strip() if pd.notna(row[j]) else ""
                        if next_cell.isdigit():
                            group_id = next_cell
                            break
                
                if link:  # Добавляем только если есть ссылка
                    posts.append({
                        "Компания": company, 
                        "Ссылка": link, 
                        "Группа": group,
                        "ID_Группы": group_id
                    })

    if not posts:
        raise ValueError(
            "В таблице не найдено ни одной ячейки формата "
            "'https://vk.com/wall… <название группы>'"
        )
    return posts
