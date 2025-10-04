from io import StringIO
import json
import os
import errno
import duckdb
import subprocess as subproc
from zipfile import ZipFile
import pandas as pd

################################################################################
# Config
################################################################################

APPLICATION_DIR = "applications"
OUTPUT_DIR = "output"
PERFORMANCE_DIR = "performance"
REPORT_DIR = "report"

NUM_EXEC = 10
THREADS = [1, 2, 4, 8]
APPLICATION_TYPE = ["common", "omp", "approx"]

HARDWARE_ID = 1
DATABASE_PATH = "database.db"

################################################################################
# Database
################################################################################


def get_database_connection():
    return duckdb.connect(DATABASE_PATH, read_only=False)


################################################################################
# Filesystem Setup
################################################################################


def create_application_dirs(app_name: str):
    output_path = os.path.join(APPLICATION_DIR, app_name, OUTPUT_DIR)
    performance_path = os.path.join(APPLICATION_DIR, app_name, PERFORMANCE_DIR)
    report_paths = [os.path.join(REPORT_DIR, app_name, t) for t in APPLICATION_TYPE]

    for path in [output_path, performance_path, *report_paths]:
        os.makedirs(path, exist_ok=True)


def unzip_file(zip_path: str, extract_to: str):
    with ZipFile(zip_path, "r") as zip_file:
        zip_file.extractall(extract_to)


def setup_environment(applications: pd.DataFrame):
    for app in applications["name"]:
        create_application_dirs(app)

    unzip_file(
        f"{APPLICATION_DIR}/correlation/input/input.zip",
        f"{APPLICATION_DIR}/correlation/input/",
    )
    unzip_file(
        f"{APPLICATION_DIR}/kmeans/input/kdd_cup.zip",
        f"{APPLICATION_DIR}/kmeans/input/",
    )


################################################################################
# Compilation & Execution
################################################################################


def run_make(app: str, args: str | None = None):
    cmd = ["make", "-C", os.path.join(APPLICATION_DIR, app)]
    if args:
        cmd.append(args)

    result = subproc.run(cmd)
    if result.returncode != 0:
        print(f"[ERROR] Failed to compile {app}")
        exit(1)


def insert_run_entry(
    conn,
    bench_id: int,
    thread: int,
    run_type: str,
    exec_num: int,
    approx_tech: str | None = None,
    approx_level: float | None = None,
):
    conn.execute(
        """
        INSERT INTO run(
            benchmark_id, hardware_id, thread, type,
            execution_num, approx_technique, approx_level,
            start_time
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, current_localtimestamp());
        """,
        (bench_id, HARDWARE_ID, thread, run_type, exec_num, approx_tech, approx_level),
    )
    run_id = conn.execute("SELECT max(id) FROM run").fetchone()[0]
    return run_id


def update_run_end_time(conn, run_id: int):
    conn.execute(
        "UPDATE run SET end_time = current_localtimestamp() WHERE id = ?;", (run_id,)
    )


def log_run_error(conn, run_id: int, returncode: int, stderr: str):
    conn.execute(
        """
        INSERT INTO run_error(run_id, error_num, error_code, error_string)
        VALUES (?, ?, ?, ?);
        """,
        (
            run_id,
            returncode,
            errno.errorcode.get(returncode, "UNKNOWN"),
            stderr,
        ),
    )


def application_input_arguments(conn, benchmark_id: int):
    args = conn.execute(
        """
        SELECT arguments FROM input WHERE benchmark_id = ?;
        """,
        (benchmark_id,),
    ).fetchone()

    return json.loads(args[0])


def run_perf(app: str, args: list[str], run_id: int, is_text: bool = True):
    output_path = os.path.join(
        APPLICATION_DIR, app, PERFORMANCE_DIR, f"perf_{run_id}.txt"
    )
    cmd = ["perf", "stat", "-o", output_path]
    cmd += args

    result = subproc.run(cmd, capture_output=True, text=is_text)
    if result.returncode != 0:
        print(f"[ERROR] Benchmark {app} failed.")

    return (result, output_path)


################################################################################
# Database Insert
################################################################################


def save_performance_stat(conn, run_id, metric_name, metric_value):
    _ = conn.execute(
        """
            INSERT INTO performance_stat(run_id, metric_name, metric_value)
            VALUES (?, ?, ?)
            """,
        (run_id, metric_name, metric_value),
    )


def save_performance(conn, run_id: int, perf_path: str):
    with open(f"{perf_path}", "r") as file:
        task_clock: float = 0
        context_switches: float = 0
        cpu_migrations: float = 0
        page_faults: float = 0
        cycles: float = 0
        instructions: float = 0
        branches: float = 0
        branch_misses: float = 0
        real_time: float = 0
        user_time: float = 0
        sys_time: float = 0

        for idx, line in enumerate(file, 1):
            if idx == 6:
                data = line.strip().split()
                task_clock = float(data[0].replace(",", ""))
                save_performance_stat(conn, run_id, "task_clock", task_clock)
            elif idx == 7:
                data = line.strip().split()
                context_switches = float(data[0].replace(",", ""))
                save_performance_stat(
                    conn, run_id, "context_switches", context_switches
                )
            elif idx == 8:
                data = line.strip().split()
                cpu_migrations = float(data[0].replace(",", ""))
                save_performance_stat(conn, run_id, "cpu_migrations", cpu_migrations)
            elif idx == 9:
                data = line.strip().split()
                page_faults = float(data[0].replace(",", ""))
                save_performance_stat(conn, run_id, "page_faults", page_faults)
            elif idx == 10:
                data = line.strip().split()
                cycles = float(data[0].replace(",", ""))
                save_performance_stat(conn, run_id, "cycles", cycles)
            elif idx == 11:
                data = line.strip().split()
                instructions = float(data[0].replace(",", ""))
                save_performance_stat(conn, run_id, "instructions", instructions)
            elif idx == 12:
                data = line.strip().split()
                branches = float(data[0].replace(",", ""))
                save_performance_stat(conn, run_id, "branches", branches)
            elif idx == 13:
                data = line.strip().split()
                branch_misses = float(data[0].replace(",", ""))
                save_performance_stat(conn, run_id, "branch_misses", branch_misses)
            elif idx == 15:
                data = line.strip().split()
                real_time = float(data[0].replace(",", ""))
                save_performance_stat(conn, run_id, "real_time", real_time)
            elif idx == 17:
                data = line.strip().split()
                user_time = float(data[0].replace(",", ""))
                save_performance_stat(conn, run_id, "user_time", user_time)
            elif idx == 18:
                data = line.strip().split()
                sys_time = float(data[0].replace(",", ""))
                save_performance_stat(conn, run_id, "sys_time", sys_time)


def save_2mm_output(run_id: int, exec_id: int, input: str):
    output_path = os.path.join(APPLICATION_DIR, "2mm", OUTPUT_DIR)
    df = pd.read_csv(StringIO(input), header=None)
    df.columns = [f"col_{idx}" for idx in range(df.shape[1])]
    df.to_parquet(f"{output_path}/2mm_{run_id}_common{exec_id}.parquet", index=False)


def save_pi_output(run_id: int, exec_id: int, input: str):
    output_path = os.path.join(APPLICATION_DIR, "pi", OUTPUT_DIR)
    output_path += f"/pi_{run_id}_common{exec_id}.txt"
    with open(output_path, "w") as file:
        _ = file.write(input)


def save_mandelbrot_output(run_id: int, exec_id: int, input: str):
    output_path = os.path.join(APPLICATION_DIR, "mandelbrot", OUTPUT_DIR)
    output_path += f"/mandelbrot_{run_id}_common{exec_id}.bmp"
    with open(output_path, "wb") as file:
        _ = file.write(input)


def save_kmeans_output(run_id: int, exec_id: int, input: str):
    output_path = os.path.join(APPLICATION_DIR, "kmeans", OUTPUT_DIR)
    output_path += f"/kmeans_{run_id}_common{exec_id}.csv"

    df = pd.DataFrame()
    for line in input.splitlines():
        header = line[0 : line.find(":")]
        line_df = pd.DataFrame(line[line.find(":") + 2 :].split(","))
        line_df = line_df.map(lambda x: float(x))
        df[f"cluster{header}"] = line_df

    df.to_csv(output_path, index=False)


################################################################################
# Applications
################################################################################


def run_2mm(conn, app_id: int, run_id: int):
    run_make("2mm")
    arguments = application_input_arguments(conn, app_id)

    app_path = os.path.join(APPLICATION_DIR, "2mm")
    cmd = [f"{app_path}/2mm.a", f"{arguments['matrix_size']}"]

    return run_perf("2mm", cmd, run_id)


def run_pi(conn, app_id: int, run_id: int):
    run_make("pi")
    arguments = application_input_arguments(conn, app_id)

    app_path = os.path.join(APPLICATION_DIR, "pi")
    cmd = [f"{app_path}/pi.a", f"{arguments['num_iterations']}"]

    return run_perf("pi", cmd, run_id)


def run_mandelbrot(conn, app_id: int, run_id: int):
    run_make("mandelbrot")
    arguments = application_input_arguments(conn, app_id)

    app_path = os.path.join(APPLICATION_DIR, "mandelbrot")
    cmd = [f"{app_path}/mandelbrot.a", f"{arguments['image_size']}"]

    return run_perf("mandelbrot", cmd, run_id, False)


def run_kmeans(conn, app_id: int, run_id: int):
    run_make("kmeans")
    arguments = application_input_arguments(conn, app_id)

    app_path = os.path.join(APPLICATION_DIR, "kmeans")
    cmd = [
        f"{app_path}/kmeans.a",
        f"{arguments['num_clusters']}",
        f"{arguments['iteration']}",
        f"{arguments['threshold']}",
        f"{arguments['input_file']}",
    ]

    return run_perf("kmeans", cmd, run_id)


def run(applications: pd.DataFrame):
    benchmark_func = {
        "2mm": {
            "exec": run_2mm,
            "output": save_2mm_output,
        },
        "pi": {
            "exec": run_pi,
            "output": save_pi_output,
        },
        "mandelbrot": {
            "exec": run_mandelbrot,
            "output": save_mandelbrot_output,
        },
        "kmeans": {
            "exec": run_kmeans,
            "output": save_kmeans_output,
        },
    }

    with get_database_connection() as conn:
        run_id = -1
        for app_id, app in zip(applications["id"], applications["name"]):
            for exec_idx in range(0, 10):
                run_id = insert_run_entry(
                    conn, app_id, 1, APPLICATION_TYPE[0], exec_idx
                )
                print(
                    f"[INFO] {app}: run_id({run_id}) thread(1) type(common) exec_num({exec_idx})"
                )
                (result, perf_path) = benchmark_func[app]["exec"](conn, app_id, run_id)

                update_run_end_time(conn, run_id)
                if result.returncode != 0:
                    log_run_error(conn, run_id, result.returncode, result.stderr)
                    exit(-1)

                benchmark_func[app]["output"](run_id, exec_idx, result.stdout)
                save_performance(conn, run_id, perf_path)


################################################################################
# Main
################################################################################

if __name__ == "__main__":
    with get_database_connection() as conn:
        applications = conn.execute(
            "SELECT DISTINCT id, name FROM benchmark WHERE canceled = false AND name = 'kmeans';"
        ).df()

    # setup_environment(applications)
    run(applications)
