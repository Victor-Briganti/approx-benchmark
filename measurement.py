import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


def read_csv_numeric(path: str) -> pd.DataFrame:
    return pd.read_csv(
        path,
        converters={
            "media": lambda x: float(x.replace(",", ".")),
            "coeficiente_variacao": lambda x: float(x.replace(",", ".")),
        },
    )


def plot_bar(values, labels, title, xlabel, ylabel, output_path, color):
    plt.figure(figsize=(6, 4))
    y_pos = np.arange(len(labels))
    plt.bar(y_pos, values, color=color)
    plt.xticks(y_pos, labels)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


benchmarks = ["2mm", "kmeans"]
metrics = ["cycles", "time"]
threads = ("1", "2", "4", "8")
base_path = Path("./report/measurement")

for bench in benchmarks:
    for metric in metrics:
        csv_path = base_path / bench / f"{metric}.csv"
        df = read_csv_numeric(csv_path)

        media = df["media"]
        cv = df["coeficiente_variacao"]

        avg_pdf = f"{base_path}/{bench}/{metric}_avg.pdf"
        cv_pdf = f"{base_path}/{bench}/{metric}_std.pdf"

        if metric == "cycles":
            title_avg = "Média por Ciclo"
            title_cv = "Coeficiente de Variação por Ciclo"
            ylabel_avg = "Média"
        else:
            title_avg = "Média por Tempo de Execução"
            title_cv = "Coeficiente de Variação por Tempo de Execução"
            ylabel_avg = "Média (ms)"

        plot_bar(
            media,
            threads,
            title_avg,
            "Quantidade de Threads",
            ylabel_avg,
            avg_pdf,
            "skyblue",
        )
        plot_bar(
            cv,
            threads,
            title_cv,
            "Quantidade de Threads",
            "Coeficiente de Variação (%)",
            cv_pdf,
            "salmon",
        )
