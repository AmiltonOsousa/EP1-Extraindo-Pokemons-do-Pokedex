import pandas as pd
import json

df = pd.read_json("pokemon.json")

df = df.drop_duplicates(subset="id", keep="first")
df['id'] = df['id'].astype(int)
df = df.sort_values(by='id').reset_index(drop=True)

df['altura'] = (
    df['altura']
    .str.replace("NBSP", "", regex=False)
    .str.replace("\xa0", "", regex=False)
    .str.replace(r"\s*\(.*?\)", "", regex=True)
    .str.replace(r"\s+", "", regex=True)
)

df['peso'] = (
    df['peso']
    .str.replace("NBSP", "", regex=False)
    .str.replace("\xa0", "", regex=False)
    .str.replace(r"\s*\(.*?\)", "", regex=True)
    .str.replace(r"\s+", "", regex=True)
)

df['url'] = df['url'].str.replace(r"\\", "", regex=True)
df['url'] = df['url'].str.replace("https:/+", "https:/", regex=True)

with open("pokemon_tratado.json", "w", encoding="utf-8") as f:
    json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=4)

print("Arquivo 'pokemon_tratado.json' criado com sucesso!")
