import pandas as pd

def load_posts(file_path):
    df = pd.read_excel(file_path, header=None)
    posts = []

    for i, row in df.iterrows():
        # Первый столбец — это название (например, "Про Измайлово" или "Про Богородское")
        title = row[0]
        # Остальные ячейки — ссылки (или пусто)
        for val in row[1:]:
            if isinstance(val, str) and "vk.com/wall" in val:
                link = val.strip().split()[0]  # убираем лишние символы после ссылки
                posts.append({
                    "Название поста": title,
                    "Ссылка": link
                })
    if not posts:
        raise ValueError("В таблице не найдено ни одной ссылки формата vk.com/wall...")
    return posts
