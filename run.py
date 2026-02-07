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

SERVER_HOSTNAME = "Armagedon"
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


def next_run_id(conn, bench_name: str, bench_version: int):
    return conn.execute(
        """
        SELECT max(id) FROM run WHERE benchmark_name = ? AND benchmark_version = ?;        """,
        (
            bench_name,
            bench_version,
        ),
    ).fetchone()[0]


def insert_run_entry(
    conn,
    bench_name: str,
    bench_version: int,
    thread: int,
    run_type: str,
    approx_tech: str | None = None,
    approx_rate: float | None = None,
):
    id = next_run_id(conn, bench_name, bench_version)
    id = 0 if id is None else id + 1
    conn.execute(
        """
        INSERT INTO run(
            id,
            benchmark_name,
            benchmark_version,
            server_name,
            thread,
            type,
            approx_technique,
            approx_rate,
            start_time
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, current_localtimestamp());
        """,
        (
            id,
            bench_name,
            bench_version,
            SERVER_HOSTNAME,
            thread,
            run_type,
            approx_tech,
            approx_rate,
        ),
    )
    return next_run_id(conn, bench_name, bench_version)


def update_run_end_time(conn, id: int, bench_name: str, bench_version: int):
    conn.execute(
        "UPDATE run SET end_time = current_localtimestamp() WHERE id = ? AND benchmark_name = ? AND benchmark_version = ?;",
        (
            id,
            bench_name,
            bench_version,
        ),
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


def application_input_arguments(conn, bench_name: str, bench_version: int):
    args = conn.execute(
        """
        SELECT arguments FROM input WHERE benchmark_name = ? AND benchmark_version = ?;
        """,
        (
            bench_name,
            bench_version,
        ),
    ).fetchone()

    return json.loads(args[0])


def run_perf(
    app: str,
    args: list[str],
    bench_name: str,
    bench_version: int,
    run_id: int,
    is_text: bool = True,
):
    output_path = os.path.join(
        APPLICATION_DIR,
        app,
        PERFORMANCE_DIR,
        f"perf_{bench_name}_v{bench_version}_{run_id}.txt",
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


def save_performance_stat(
    conn,
    run_id: int,
    bench_name: str,
    bench_version: int,
    metric_name: str,
    metric_value: float,
):
    _ = conn.execute(
        """
            INSERT INTO performance_stat(run_id, benchmark_name, benchmark_version, metric_name, metric_value)
            VALUES (?, ?, ?, ?, ?)
            """,
        (run_id, bench_name, bench_version, metric_name, metric_value),
    )


def save_performance(
    conn, run_id: int, bench_name: str, bench_version: int, perf_path: str
):
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
                save_performance_stat(
                    conn, run_id, bench_name, bench_version, "task_clock", task_clock
                )
            elif idx == 7:
                data = line.strip().split()
                context_switches = float(data[0].replace(",", ""))
                save_performance_stat(
                    conn,
                    run_id,
                    bench_name,
                    bench_version,
                    "context_switches",
                    context_switches,
                )
            elif idx == 8:
                data = line.strip().split()
                cpu_migrations = float(data[0].replace(",", ""))
                save_performance_stat(
                    conn,
                    run_id,
                    bench_name,
                    bench_version,
                    "cpu_migrations",
                    cpu_migrations,
                )
            elif idx == 9:
                data = line.strip().split()
                page_faults = float(data[0].replace(",", ""))
                save_performance_stat(
                    conn, run_id, bench_name, bench_version, "page_faults", page_faults
                )
            elif idx == 10:
                data = line.strip().split()
                cycles = float(data[0].replace(",", ""))
                save_performance_stat(
                    conn, run_id, bench_name, bench_version, "cycles", cycles
                )
            elif idx == 11:
                data = line.strip().split()
                instructions = float(data[0].replace(",", ""))
                save_performance_stat(
                    conn,
                    run_id,
                    bench_name,
                    bench_version,
                    "instructions",
                    instructions,
                )
            elif idx == 12:
                data = line.strip().split()
                branches = float(data[0].replace(",", ""))
                save_performance_stat(
                    conn, run_id, bench_name, bench_version, "branches", branches
                )
            elif idx == 13:
                data = line.strip().split()
                branch_misses = float(data[0].replace(",", ""))
                save_performance_stat(
                    conn,
                    run_id,
                    bench_name,
                    bench_version,
                    "branch_misses",
                    branch_misses,
                )
            elif idx == 15:
                data = line.strip().split()
                real_time = float(data[0].replace(",", ""))
                save_performance_stat(
                    conn, run_id, bench_name, bench_version, "real_time", real_time
                )
            elif idx == 17:
                data = line.strip().split()
                user_time = float(data[0].replace(",", ""))
                save_performance_stat(
                    conn, run_id, bench_name, bench_version, "user_time", user_time
                )
            elif idx == 18:
                data = line.strip().split()
                sys_time = float(data[0].replace(",", ""))
                save_performance_stat(
                    conn, run_id, bench_name, bench_version, "sys_time", sys_time
                )


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
            print("[ERROR] Failed to save the output of 2mm. Missing number of thread.")
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
            print("[ERROR] Failed to save the output of pi. Missing number of thread.")
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
                "[ERROR] Failed to save the output of mandelbrot. Missing number of thread."
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
                "[ERROR] Failed to save the output of mandelbrot. Missing number of thread."
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
                "[ERROR] Failed to save the output of correlation. Missing number of thread."
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
    output_path = os.path.join(APPLICATION_DIR, "jacobi2d", OUTPUT_DIR)

    if type == ApplicationType.COMMON:
        output_path += f"/jacobi2d_id{run_id}_{type.value}_exec{exec_id}.parquet"
    elif type == ApplicationType.OMP:
        if thread is None:
            print(
                "[ERROR] Failed to save the output of jacobi2d. Missing number of thread."
            )
            exit(-1)

        output_path += (
            f"/jacobi2d_id{run_id}_{type.value}_thread{thread}_exec{exec_id}.parquet"
        )

    df = pd.read_csv(StringIO(input), header=None)
    df.columns = [f"col_{idx}" for idx in range(df.shape[1])]
    df.to_parquet(output_path, index=False)


def save_deriche_output(
    input: str,
    run_id: int,
    exec_id: int,
    type: ApplicationType,
    thread: int | None = None,
):
    base_path = os.path.join(APPLICATION_DIR, "deriche", OUTPUT_DIR)

    new_image = ""
    if type == ApplicationType.COMMON:
        new_image = base_path + f"/deriche_id{run_id}_{type.value}_exec{exec_id}.jpg"
    elif type == ApplicationType.OMP:
        if thread is None:
            print(
                "[ERROR] Failed to save the output of deriche. Missing number of thread."
            )
            exit(-1)

        new_image = base_path + (
            f"/deriche_id{run_id}_{type.value}_thread{thread}_exec{exec_id}.jpg"
        )

    current_image = base_path + "/output.jpg"
    os.rename(current_image, new_image)


################################################################################
# Applications
################################################################################


def run_2mm(
    conn,
    bench_name: str,
    bench_version: int,
    run_id: int,
    type: ApplicationType,
    thread: int | None = None,
    approx_tech: str | None = None,
    approx_level: float | None = None,
):
    if type == ApplicationType.COMMON:
        run_make("2mm")
    elif type == ApplicationType.OMP:
        if thread is None:
            print("[ERROR] Failed to compile 2mm with OpenMP. Missing number of thread")
            exit(-1)

        run_make("2mm", ["omp", f"NUM_THREADS={thread}"])
    else:
        if thread is None:
            print("[ERROR] Failed to compile 2mm with OpenMP. Missing number of thread")
            exit(-1)

        if approx_tech is None or approx_level is None:
            print(
                "[ERROR] Failed to compile 2mm with OpenMP. Missing parameter for approx technique"
            )
            exit(-1)

        run_make(
            "2mm", [f"{approx_tech}", f"NUM_THREADS={thread}", f"DROP={approx_level}"]
        )

    arguments = application_input_arguments(conn, bench_name, bench_version)

    app_path = os.path.join(APPLICATION_DIR, "2mm")
    cmd = [f"{app_path}/2mm.a", f"{arguments['matrix_size']}"]

    return run_perf("2mm", cmd, bench_name, bench_version, run_id)


def run_pi(
    conn,
    app_id: int,
    run_id: int,
    type: ApplicationType,
    thread: int | None = None,
    approx_tech: str | None = None,
    approx_level: float | None = None,
):
    if type == ApplicationType.COMMON:
        run_make("pi")
    elif type == ApplicationType.OMP:
        if thread is None:
            print("[ERROR] Failed to compile pi with OpenMP. Missing number of thread")
            exit(-1)

        run_make("pi", ["omp", f"NUM_THREADS={thread}"])
    else:
        if thread is None:
            print("[ERROR] Failed to compile pi with OpenMP. Missing number of thread")
            exit(-1)

        if approx_tech is None or approx_level is None:
            print(
                "[ERROR] Failed to compile pi with OpenMP. Missing parameter for approx technique"
            )
            exit(-1)

        run_make(
            "pi", [f"{approx_tech}", f"NUM_THREADS={thread}", f"DROP={approx_level}"]
        )

    arguments = application_input_arguments(conn, app_id)

    app_path = os.path.join(APPLICATION_DIR, "pi")
    cmd = [f"{app_path}/pi.a", f"{arguments['num_iterations']}"]

    return run_perf("pi", cmd, run_id)


def run_mandelbrot(
    conn,
    app_id: int,
    run_id: int,
    type: ApplicationType,
    thread: int | None = None,
    approx_tech: str | None = None,
    approx_level: float | None = None,
):
    if type == ApplicationType.COMMON:
        run_make("mandelbrot")
    elif type == ApplicationType.OMP:
        if thread is None:
            print(
                "[ERROR] Failed to compile mandelbrot with OpenMP. Missing number of thread"
            )
            exit(-1)

        run_make("mandelbrot", ["omp", f"NUM_THREADS={thread}"])
    else:
        if thread is None:
            print(
                "[ERROR] Failed to compile mandelbrot with OpenMP. Missing number of thread"
            )
            exit(-1)

        if approx_tech is None or approx_level is None:
            print(
                "[ERROR] Failed to compile mandelbrot with OpenMP. Missing parameter for approx technique"
            )
            exit(-1)

        run_make(
            "mandelbrot",
            [f"{approx_tech}", f"NUM_THREADS={thread}", f"DROP={approx_level}"],
        )

    arguments = application_input_arguments(conn, app_id)

    app_path = os.path.join(APPLICATION_DIR, "mandelbrot")
    cmd = [f"{app_path}/mandelbrot.a", f"{arguments['image_size']}"]

    return run_perf("mandelbrot", cmd, run_id, False)


def run_kmeans(
    conn,
    app_id: int,
    run_id: int,
    type: ApplicationType,
    thread: int | None = None,
    approx_tech: str | None = None,
    approx_level: float | None = None,
):
    if type == ApplicationType.COMMON:
        run_make("kmeans")
    elif type == ApplicationType.OMP:
        if thread is None:
            print(
                "[ERROR] Failed to compile kmeans with OpenMP. Missing number of thread"
            )
            exit(-1)

        run_make("kmeans", ["omp", f"NUM_THREADS={thread}"])
    else:
        if thread is None:
            print(
                "[ERROR] Failed to compile kmeans with OpenMP. Missing number of thread"
            )
            exit(-1)

        if approx_tech is None or approx_level is None:
            print(
                "[ERROR] Failed to compile kmeans with OpenMP. Missing parameter for approx technique"
            )
            exit(-1)

        run_make(
            "kmeans",
            [f"{approx_tech}", f"NUM_THREADS={thread}", f"DROP={approx_level}"],
        )

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
    conn,
    app_id: int,
    run_id: int,
    type: ApplicationType,
    thread: int | None = None,
    approx_tech: str | None = None,
    approx_level: float | None = None,
):
    if type == ApplicationType.COMMON:
        run_make("correlation")
    elif type == ApplicationType.OMP:
        if thread is None:
            print(
                "[ERROR] Failed to compile correlation with OpenMP. Missing number of thread"
            )
            exit(-1)

        run_make("correlation", ["omp", f"NUM_THREADS={thread}"])
    else:
        if thread is None:
            print(
                "[ERROR] Failed to compile correlation with OpenMP. Missing number of thread"
            )
            exit(-1)

        if approx_tech is None or approx_level is None:
            print(
                "[ERROR] Failed to compile correlation with OpenMP. Missing parameter for approx technique"
            )
            exit(-1)

        run_make(
            "correlation",
            [f"{approx_tech}", f"NUM_THREADS={thread}", f"DROP={approx_level}"],
        )

    arguments = application_input_arguments(conn, app_id)

    app_path = os.path.join(APPLICATION_DIR, "correlation")
    cmd = [
        f"{app_path}/correlation.a",
        f"{arguments['csv_file']}",
    ]

    return run_perf("correlation", cmd, run_id)


def run_jacobi2d(
    conn,
    app_id: int,
    run_id: int,
    type: ApplicationType,
    thread: int | None = None,
    approx_tech: str | None = None,
    approx_level: float | None = None,
):
    if type == ApplicationType.COMMON:
        run_make("jacobi2d")
    elif type == ApplicationType.OMP:
        if thread is None:
            print(
                "[ERROR] Failed to compile jacobi2d with OpenMP. Missing number of thread"
            )
            exit(-1)

        run_make("jacobi2d", ["omp", f"NUM_THREADS={thread}"])
    else:
        if thread is None:
            print(
                "[ERROR] Failed to compile jacobi2d with OpenMP. Missing number of thread"
            )
            exit(-1)

        if approx_tech is None or approx_level is None:
            print(
                "[ERROR] Failed to compile jacobi2d with OpenMP. Missing parameter for approx technique"
            )
            exit(-1)

        run_make(
            "jacobi2d",
            [f"{approx_tech}", f"NUM_THREADS={thread}", f"DROP={approx_level}"],
        )

    arguments = application_input_arguments(conn, app_id)

    app_path = os.path.join(APPLICATION_DIR, "jacobi2d")
    cmd = [
        f"{app_path}/jacobi2d.a",
        f"{arguments['matrix_size']}",
        f"{arguments['number_steps']}",
    ]

    return run_perf("jacobi2d", cmd, run_id)


def run_deriche(
    conn,
    app_id: int,
    run_id: int,
    type: ApplicationType,
    thread: int | None = None,
    approx_tech: str | None = None,
    approx_level: float | None = None,
):
    if type == ApplicationType.COMMON:
        run_make("deriche")
    elif type == ApplicationType.OMP:
        if thread is None:
            print(
                "[ERROR] Failed to compile deriche with OpenMP. Missing number of thread"
            )
            exit(-1)

        run_make("deriche", ["omp", f"NUM_THREADS={thread}"])
    else:
        if thread is None:
            print(
                "[ERROR] Failed to compile deriche with OpenMP. Missing number of thread"
            )
            exit(-1)

        if approx_tech is None or approx_level is None:
            print(
                "[ERROR] Failed to compile deriche with OpenMP. Missing parameter for approx technique"
            )
            exit(-1)

        run_make(
            "deriche",
            [f"{approx_tech}", f"NUM_THREADS={thread}", f"DROP={approx_level}"],
        )

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
        # "pi": {
        #     "exec": run_pi,
        #     "output": save_pi_output,
        # },
        # "mandelbrot": {
        #     "exec": run_mandelbrot,
        #     "output": save_mandelbrot_output,
        # },
        # "kmeans": {
        #     "exec": run_kmeans,
        #     "output": save_kmeans_output,
        # },
        # "correlation": {
        #     "exec": run_correlation,
        #     "output": save_correlation_output,
        # },
        # "jacobi2d": {
        #     "exec": run_jacobi2d,
        #     "output": save_jacobi2d_output,
        # },
        # "deriche": {
        #     "exec": run_deriche,
        #     "output": save_deriche_output,
        # },
    }

    with get_database_connection() as conn:
        for type in ApplicationType:
            for thread in [1] if type == ApplicationType.COMMON else THREADS:
                for approx_tech in (
                    [None] if type != ApplicationType.APPROX else ["perfo_default"]
                ):
                    for approx_level in (
                        [None] if type != ApplicationType.APPROX else range(1, 6)
                    ):
                        for app_name, app_version in zip(
                            applications["name"], applications["version"]
                        ):
                            for exec_idx in range(0, 10):
                                run_id = insert_run_entry(
                                    conn,
                                    app_name,
                                    app_version,
                                    thread,
                                    type.value,
                                    approx_tech,
                                    approx_level,
                                )

                                info = ""
                                if approx_tech is None:
                                    info = f"[INFO] {app_name}: run_id({run_id}) type({type.value}) thread({thread}) exec_num({exec_idx})"
                                else:
                                    info = f"[INFO] {app_name}: run_id({run_id}) type({type.value}) approx_tech({approx_tech}) approx_level({approx_level}) thread({thread}) exec_num({exec_idx})"

                                print(info)
                                (result, perf_path) = benchmark_func[app_name]["exec"](
                                    conn,
                                    app_name,
                                    app_version,
                                    run_id,
                                    type,
                                    thread,
                                    approx_tech,
                                    approx_level,
                                )

                                update_run_end_time(conn, run_id, app_name, app_version)
                                if result.returncode != 0:
                                    log_run_error(
                                        conn, run_id, result.returncode, result.stderr
                                    )
                                    exit(-1)

                                benchmark_func[app_name]["output"](
                                    result.stdout, run_id, exec_idx, type, thread
                                )
                                save_performance(conn, run_id, perf_path)


################################################################################
# Main
################################################################################

if __name__ == "__main__":
    with get_database_connection() as conn:
        applications = conn.execute(
            "SELECT DISTINCT name, version FROM benchmark WHERE canceled = false AND name='2mm';"
        ).df()

    # setup_environment(applications)
    run(applications)
