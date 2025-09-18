import pandas as pd

def load_posts(file_path: str) -> list[dict]:
    """Читает Excel-таблицу вида:
       ┌──────────────┬────────────────────────────┬ … ┐
       │ Про_Измайлово│ https://…  ЦР25_…          │   │
       └──────────────┴────────────────────────────┴ … ┘

    Возвращает список словарей:
    {
        "Компания": "Про_Измайлово",
        "Ссылка":   "https://vk.com/wall-…",
        "Группа":   "ЦР25_ИЗМАЙЛОВО_БЛАГОУСТРОЙСТВО"
    }
    """
    df = pd.read_excel(file_path, header=None)
    posts: list[dict] = []

    for _, row in df.iterrows():
        company = str(row[0]).strip()
        for cell in row[1:]:
            if isinstance(cell, str) and "vk.com/wall" in cell:
                link, *rest = cell.strip().split(maxsplit=1)
                group = rest[0] if rest else "Без_имени"
                posts.append(
                    {"Компания": company, "Ссылка": link, "Группа": group}
                )

    if not posts:
        raise ValueError(
            "В таблице не найдено ни одной ячейки формата "
            "'https://vk.com/wall… <название группы>'"
        )
    return posts
