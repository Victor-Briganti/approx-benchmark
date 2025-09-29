import duckdb
from zipfile import ZipFile
import os
import random as rand
import pandas as pd
import numpy as np

DATABASE = duckdb.connect("database.db", read_only=False)

APPLICATION_DIR: str = "applications"  # src of the apps
OUTPUT_DIR: str = "output"  # outputs of the running apps
PERFORMANCE_DIR: str = "performance"  # perf metrics of the running apps
REPORT_DIR: str = "report"  # graphs and analytics

NUM_EXEC: int = 10
THREADS: list[int] = [1, 2, 4, 8]

def create_dir(applications):
    # Create the default directories for all applications
    for app in applications['name']:
        for dir in [APPLICATION_DIR, REPORT_DIR]:
            if dir == APPLICATION_DIR:
                if not os.path.exists(f"{dir}/{app}/{OUTPUT_DIR}"):
                    os.makedirs(f"{dir}/{app}/{OUTPUT_DIR}")
                    
                if not os.path.exists(f"{dir}/{app}/{PERFORMANCE_DIR}"):
                    os.makedirs(f"{dir}/{app}/{PERFORMANCE_DIR}")

            elif dir == REPORT_DIR:
                if not os.path.exists(f"{dir}/{app}"):
                    os.makedirs(f"{dir}/{app}/common")
                    os.makedirs(f"{dir}/{app}/omp")
                    os.makedirs(f"{dir}/{app}/approx")

                if app == "2mm" and not os.path.exists(f"{dir}/{app}/base"):
                    os.makedirs(f"{dir}/{app}/base")


def unzip_file(input_path: str, output_path: str):
    with ZipFile(input_path, "r") as zip:
        zip.extractall(output_path)


def setup(applications):
    create_dir(applications)
    unzip_file(
        f"{APPLICATION_DIR}/correlation/input/input.zip",
        f"{APPLICATION_DIR}/correlation/input/",
    )
    unzip_file(
        f"{APPLICATION_DIR}/kmeans/input/kdd_cup.zip",
        f"{APPLICATION_DIR}/kmeans/input/",
    )


if __name__ == "__main__":
    applications = DATABASE.execute("""
        SELECT DISTINCT name FROM benchmark WHERE canceled = false;
    """).df()
    
    setup(applications)
