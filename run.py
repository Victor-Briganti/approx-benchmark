from enum import Enum
from io import StringIO
import json
import os
import errno
import duckdb
import subprocess as subproc
from zipfile import ZipFile
import pandas as pd


################################################################################
# Globals
################################################################################


class ApplicationType(Enum):
    COMMON = "common"
    OMP = "omp"
    APPROX = "approx"


APPLICATION_DIR = "applications"
OUTPUT_DIR = "output"
PERFORMANCE_DIR = "performance"
REPORT_DIR = "report"

NUM_EXEC = 10
THREADS = [1, 2, 4, 8]

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
    report_paths = [
        os.path.join(REPORT_DIR, app_name, t.value) for t in ApplicationType
    ]

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


def run_make(app: str, args: list[str] | None = None):
    cmd = ["make", "-C", os.path.join(APPLICATION_DIR, app)]
    if args:
        cmd += args

    result = subproc.run(cmd)
    if result.returncode != 0:
        print(f"[ERROR] Failed to compile {app}")
        exit(-1)


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


def save_2mm_output(
    input: str,
    run_id: int,
    exec_id: int,
    type: ApplicationType,
    thread: int | None = None,
):
    output_path = os.path.join(APPLICATION_DIR, "2mm", OUTPUT_DIR)

    if type == ApplicationType.COMMON:
        output_path += f"/2mm_id{run_id}_{type.value}_exec{exec_id}.parquet"
    elif type == ApplicationType.OMP:
        if thread is None:
            print(
                f"[ERROR] Failed to save the output of 2mm. Missing number of thread."
            )
            exit(-1)

        output_path += (
            f"/2mm_id{run_id}_{type.value}_thread{thread}_exec{exec_id}.parquet"
        )

    df = pd.read_csv(StringIO(input), header=None)
    df.columns = [f"col_{idx}" for idx in range(df.shape[1])]
    df.to_parquet(output_path, index=False)


def save_pi_output(
    input: str,
    run_id: int,
    exec_id: int,
    type: ApplicationType,
    thread: int | None = None,
):
    output_path = os.path.join(APPLICATION_DIR, "pi", OUTPUT_DIR)

    if type == ApplicationType.COMMON:
        output_path += f"/pi_id{run_id}_{type.value}_exec{exec_id}.txt"
    elif type == ApplicationType.OMP:
        if thread is None:
            print(f"[ERROR] Failed to save the output of pi. Missing number of thread.")
            exit(-1)

        output_path += f"/pi_id{run_id}_{type.value}_thread{thread}_exec{exec_id}.txt"

    with open(output_path, "w") as file:
        _ = file.write(input)


def save_mandelbrot_output(
    input: str,
    run_id: int,
    exec_id: int,
    type: ApplicationType,
    thread: int | None = None,
):
    output_path = os.path.join(APPLICATION_DIR, "mandelbrot", OUTPUT_DIR)

    if type == ApplicationType.COMMON:
        output_path += f"/mandelbrot_id{run_id}_{type.value}_exec{exec_id}.bmp"
    elif type == ApplicationType.OMP:
        if thread is None:
            print(
                f"[ERROR] Failed to save the output of mandelbrot. Missing number of thread."
            )
            exit(-1)

        output_path += (
            f"/mandelbrot_id{run_id}_{type.value}_thread{thread}_exec{exec_id}.bmp"
        )

    with open(output_path, "wb") as file:
        _ = file.write(input)


def save_kmeans_output(
    input: str,
    run_id: int,
    exec_id: int,
    type: ApplicationType,
    thread: int | None = None,
):
    output_path = os.path.join(APPLICATION_DIR, "kmeans", OUTPUT_DIR)

    if type == ApplicationType.COMMON:
        output_path += f"/mandelbrot_id{run_id}_{type.value}_exec{exec_id}.bmp"
    elif type == ApplicationType.OMP:
        if thread is None:
            print(
                f"[ERROR] Failed to save the output of mandelbrot. Missing number of thread."
            )
            exit(-1)

        output_path += (
            f"/mandelbrot_id{run_id}_{type.value}_thread{thread}_exec{exec_id}.bmp"
        )

    df = pd.DataFrame()
    for line in input.splitlines():
        header = line[0 : line.find(":")]
        line_df = pd.DataFrame(line[line.find(":") + 2 :].split(","))
        line_df = line_df.map(lambda x: float(x))
        df[f"cluster{header}"] = line_df

    df.to_csv(output_path, index=False)


def save_correlation_output(
    input: str,
    run_id: int,
    exec_id: int,
    type: ApplicationType,
    thread: int | None = None,
):
    output_path = os.path.join(APPLICATION_DIR, "correlation", OUTPUT_DIR)

    if type == ApplicationType.COMMON:
        output_path += f"/correlation_id{run_id}_{type.value}_exec{exec_id}.parquet"
    elif type == ApplicationType.OMP:
        if thread is None:
            print(
                f"[ERROR] Failed to save the output of correlation. Missing number of thread."
            )
            exit(-1)

        output_path += (
            f"/correlation_id{run_id}_{type.value}_thread{thread}_exec{exec_id}.parquet"
        )

    df = pd.read_csv(StringIO(input), header=None)
    df.columns = [f"col_{idx}" for idx in range(df.shape[1])]
    df.to_parquet(output_path, index=False)


def save_jacobi2d_output(
    input: str,
    run_id: int,
    exec_id: int,
    type: ApplicationType,
    thread: int | None = None,
):
    output_path = os.path.join(APPLICATION_DIR, "kmeans", OUTPUT_DIR)

    if type == ApplicationType.COMMON:
        output_path += f"/correlation_id{run_id}_{type.value}_exec{exec_id}.parquet"
    elif type == ApplicationType.OMP:
        if thread is None:
            print(
                f"[ERROR] Failed to save the output of correlation. Missing number of thread."
            )
            exit(-1)

        output_path += (
            f"/correlation_id{run_id}_{type.value}_thread{thread}_exec{exec_id}.parquet"
        )

    df = pd.read_csv(StringIO(input), header=None)
    df.columns = [f"col_{idx}" for idx in range(df.shape[1])]
    df.to_parquet(output_path, index=False)


def save_deriche_output(run_id: int, exec_id: int, input: str):
    base_path = os.path.join(APPLICATION_DIR, "deriche", OUTPUT_DIR)
    current_image = base_path + "/output.jpg"
    new_image = base_path + f"/deriche_{run_id}_common{exec_id}.jpg"
    os.rename(current_image, new_image)


################################################################################
# Applications
################################################################################


def run_2mm(
    conn, app_id: int, run_id: int, type: ApplicationType, thread: int | None = None
):
    if type == ApplicationType.COMMON:
        run_make("2mm")
    elif type == ApplicationType.OMP:
        if thread == None:
            print(
                f"[ERROR] Failed to compile 2mm with OpenMP. Missing number of thread"
            )
            exit(-1)

        run_make("2mm", ["omp", f"NUM_THREADS={thread}"])

    arguments = application_input_arguments(conn, app_id)

    app_path = os.path.join(APPLICATION_DIR, "2mm")
    cmd = [f"{app_path}/2mm.a", f"{arguments['matrix_size']}"]

    return run_perf("2mm", cmd, run_id)


def run_pi(
    conn, app_id: int, run_id: int, type: ApplicationType, thread: int | None = None
):
    if type == ApplicationType.COMMON:
        run_make("pi")
    elif type == ApplicationType.OMP:
        if thread == None:
            print(f"[ERROR] Failed to compile pi with OpenMP. Missing number of thread")
            exit(-1)

        run_make("pi", ["omp", f"NUM_THREADS={thread}"])

    arguments = application_input_arguments(conn, app_id)

    app_path = os.path.join(APPLICATION_DIR, "pi")
    cmd = [f"{app_path}/pi.a", f"{arguments['num_iterations']}"]

    return run_perf("pi", cmd, run_id)


def run_mandelbrot(
    conn, app_id: int, run_id: int, type: ApplicationType, thread: int | None = None
):
    if type == ApplicationType.COMMON:
        run_make("mandelbrot")
    elif type == ApplicationType.OMP:
        if thread == None:
            print(
                f"[ERROR] Failed to compile mandelbrot with OpenMP. Missing number of thread"
            )
            exit(-1)

        run_make("mandelbrot", ["omp", f"NUM_THREADS={thread}"])

    arguments = application_input_arguments(conn, app_id)

    app_path = os.path.join(APPLICATION_DIR, "mandelbrot")
    cmd = [f"{app_path}/mandelbrot.a", f"{arguments['image_size']}"]

    return run_perf("mandelbrot", cmd, run_id, False)


def run_kmeans(
    conn, app_id: int, run_id: int, type: ApplicationType, thread: int | None = None
):
    if type == ApplicationType.COMMON:
        run_make("kmeans")
    elif type == ApplicationType.OMP:
        if thread == None:
            print(
                f"[ERROR] Failed to compile kmeans with OpenMP. Missing number of thread"
            )
            exit(-1)

        run_make("kmeans", ["omp", f"NUM_THREADS={thread}"])

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


def run_correlation(
    conn, app_id: int, run_id: int, type: ApplicationType, thread: int | None = None
):
    if type == ApplicationType.COMMON:
        run_make("correlation")
    elif type == ApplicationType.OMP:
        if thread == None:
            print(
                f"[ERROR] Failed to compile correlation with OpenMP. Missing number of thread"
            )
            exit(-1)

        run_make("correlation", ["omp", f"NUM_THREADS={thread}"])

    arguments = application_input_arguments(conn, app_id)

    app_path = os.path.join(APPLICATION_DIR, "correlation")
    cmd = [
        f"{app_path}/correlation.a",
        f"{arguments['csv_file']}",
    ]

    return run_perf("correlation", cmd, run_id)


def run_jacobi2d(
    conn, app_id: int, run_id: int, type: ApplicationType, thread: int | None = None
):
    if type == ApplicationType.COMMON:
        run_make("jacobi2d")
    elif type == ApplicationType.OMP:
        if thread == None:
            print(
                f"[ERROR] Failed to compile jacobi2d with OpenMP. Missing number of thread"
            )
            exit(-1)

        run_make("jacobi2d", ["omp", f"NUM_THREADS={thread}"])

    arguments = application_input_arguments(conn, app_id)

    app_path = os.path.join(APPLICATION_DIR, "jacobi2d")
    cmd = [
        f"{app_path}/jacobi2d.a",
        f"{arguments['matrix_size']}",
        f"{arguments['number_steps']}",
    ]

    return run_perf("jacobi2d", cmd, run_id)


def run_deriche(conn, app_id: int, run_id: int):
    run_make("deriche")
    arguments = application_input_arguments(conn, app_id)

    app_path = os.path.join(APPLICATION_DIR, "deriche")
    cmd = [
        f"{app_path}/deriche.a",
        f"{arguments['alpha']}",
        f"{arguments['input_image']}",
        f"{arguments['output_image']}",
    ]

    return run_perf("deriche", cmd, run_id)


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
        "correlation": {
            "exec": run_correlation,
            "output": save_correlation_output,
        },
        "jacobi2d": {
            "exec": run_jacobi2d,
            "output": save_jacobi2d_output,
        },
        # "deriche": {
        #     "exec": run_deriche,
        #     "output": save_deriche_output,
        # },
    }

    with get_database_connection() as conn:
        run_id = -1
        # TODO: Remember to restore this to ApplicationType
        for type in [ApplicationType.OMP]:
            if type == ApplicationType.APPROX:
                continue

            for thread in [None] if type == ApplicationType.COMMON else THREADS:
                for app_id, app in zip(applications["id"], applications["name"]):
                    for exec_idx in range(0, 10):
                        run_id = insert_run_entry(conn, app_id, 1, type.value, exec_idx)
                        print(
                            f"[INFO] {app}: run_id({run_id}) type({type.value}) thread({thread}) exec_num({exec_idx})"
                        )
                        (result, perf_path) = benchmark_func[app]["exec"](
                            conn, app_id, run_id, type, thread
                        )

                        update_run_end_time(conn, run_id)
                        if result.returncode != 0:
                            log_run_error(
                                conn, run_id, result.returncode, result.stderr
                            )
                            exit(-1)

                        benchmark_func[app]["output"](
                            result.stdout, run_id, exec_idx, type, thread
                        )
                        # save_performance(conn, run_id, perf_path)


################################################################################
# Main
################################################################################

if __name__ == "__main__":
    with get_database_connection() as conn:
        applications = conn.execute(
            "SELECT DISTINCT id, name FROM benchmark WHERE canceled = false AND name='kmeans';"
        ).df()

    # setup_environment(applications)
    run(applications)
