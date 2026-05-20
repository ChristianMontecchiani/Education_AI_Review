import pandas as pd 
from pathlib import Path
import matplotlib.pyplot as plt
import os


DB_LIST = ["OpenAlex", "GoogleScholar", "CrossRef", "ArXiv", "Scopus", "ACM", "EBSCO"]

MIN_YEAR = 1930
MAX_YEAR = 2026

directories_list = os.listdir()


def create_histogram_papers_per_year(df, database_name, save_path, show=False):
    if "year" not in df.columns:
        if df["published"].dtype == "float64":
            df = df.dropna(subset=["published"])
            df["year"] = df["published"].astype(int)
        else:
            df["year"] = df["published"].str.extract(r'(\d{4})').astype(int)
    
    df = df.dropna(subset=["year"])
    df = df[(df["year"] <= MAX_YEAR) & (df["year"] >= MIN_YEAR)]

    fig = plt.figure(figsize=(10, 6))
    df["year"].value_counts().sort_index().plot(kind="bar")

    plt.xlabel("Year")
    plt.ylabel("Number of Papers")
    plt.title(f"{database_name} - Papers Published per Year")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    if show:
        plt.show()
    fig.savefig(save_path)

    print(f"Histogram saved for DB: {database_name}")


for directory in directories_list:
    if directory in DB_LIST:
        print(f"Processing {directory}...")
        BASE_DIR = Path(__file__).parent / directory
        file_name = "result.csv"
        file_path = BASE_DIR / "results" / file_name
        save_path = BASE_DIR / "results" / f"papers_per_year_{directory}.png"

        df = pd.read_csv(file_path)
        create_histogram_papers_per_year(df, directory, save_path)
        



