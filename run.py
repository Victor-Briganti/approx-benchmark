from zipfile import ZipFile
import os
import random as rand

APPLICATIONS: list[str] = [
    "2mm",
    "correlation",
    "deriche",
    "jacobi2d",
    "kmeans",
    "mandelbrot",
    "pi",
]

APPLICATION_DIR: str = "applications"  # src of the apps
OUTPUT_DIR: str = "output"  # outputs of the running apps
PERFORMANCE_DIR: str = "performance"  # perf metrics of the running apps
REPORT_DIR: str = "report"  # graphs and analytics

NUM_EXEC: int = 10
THREADS: list[int] = [1, 2, 4, 8]


def create_dir():
    for app in APPLICATIONS:
        for dir in [OUTPUT_DIR, PERFORMANCE_DIR, REPORT_DIR]:
            if not os.path.exists(f"{dir}/{app}"):
                os.makedirs(f"{dir}/{app}/common")
                os.makedirs(f"{dir}/{app}/omp")
                os.makedirs(f"{dir}/{app}/approx")

                if app == "2mm":
                    os.makedirs(f"{dir}/{app}/base")

    if not os.path.exists(f"{APPLICATION_DIR}/correlation/input"):
        os.makedirs(f"{APPLICATION_DIR}/correlation/input")


def unzip_file(input_path: str, output_path: str):
    with ZipFile(input_path, "r") as zip:
        zip.extractall(output_path)


def generate_csv(rows: int, columns: int, output_path: str):
    rand.seed(0)
    with open(f"{output_path}", "w") as file:
        _ = file.write(f"{columns} {rows}\n")

        for _ in range(rows):
            for i in range(0, columns):
                _ = file.write(str(rand.random()))

                if i + 1 == columns:
                    _ = file.write("\n")
                else:
                    _ = file.write(",")


def setup():
    create_dir()
    unzip_file(
        f"{APPLICATION_DIR}/kmeans/input/kdd_cup.csv.zip",
        f"{APPLICATION_DIR}/kmeans/input/",
    )
    generate_csv(8192, 256, f"{APPLICATION_DIR}/correlation/input/input.csv")




#def run():




if __name__ == "__main__":
    setup()
