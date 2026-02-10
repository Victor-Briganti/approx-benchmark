import numpy as np
import pandas as pd
import sys
import os
import duckdb
import yaml
import json
import subprocess
import cv2
from skimage.metrics import structural_similarity as similarity
from typing import Dict, List, Tuple, Optional, Any

# ============================================================
# Bookkeeping
# ============================================================


def save_experiment(conn, plan: Dict[str, Any]):
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    conn.execute(
        """
        INSERT INTO Experiment(yaml_snapshot, commit)
        VALUES (?, ?);
        """,
        (str(plan), commit.stdout.strip()),
    )
    print("[INFO] Saved YAML plan")


def save_server(conn, server: Dict[str, Any]):
    exists = conn.execute(
        "SELECT 1 FROM Server WHERE hostname = ?;", (server["hostname"],)
    ).fetchone()

    if not exists:
        print(f"[INFO] Saving server {server['hostname']}")
        conn.execute(
            """
            INSERT INTO Server(hostname, cpu_description, hertz, cores, threads, ram_memory, operating_system)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                server["hostname"],
                server["cpu_description"],
                server["hertz"],
                server["cores"],
                server["threads"],
                server["ram_memory"],
                server["operating_system"],
            ),
        )
    else:
        print(f"[INFO] Server {server['hostname']} already exists")


def select_benchmark(conn, name: str, version: int) -> Optional[Tuple[str, int, str]]:
    return conn.execute(
        "SELECT name, version, path FROM Benchmark WHERE name = ? AND version = ?;",
        (name, version),
    ).fetchone()


def save_benchmarks(conn, benchmarks: List[Dict[str, Any]]):
    for bench in benchmarks:
        if select_benchmark(conn, bench["name"], bench["version"]) is None:
            print(f"[INFO] Saving benchmark {bench['name']} v{bench['version']}")
            conn.execute(
                """
                INSERT INTO Benchmark(name, version, path, setup, description)
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    bench["name"],
                    bench["version"],
                    bench["path"],
                    bench["setup"].replace("$PATH", bench["path"]),
                    bench["description"],
                ),
            )
            # Run setup
            cmd = bench["setup"].replace("$PATH", bench["path"])
            subprocess.run(cmd, shell=True, executable="/bin/bash", check=True)


def save_execution_group(conn, exec_info: Dict[str, Any]) -> int:
    return conn.execute(
        """
        INSERT INTO ExecutionGroup(type, approx_rate, approx_type, compile_command, num_threads, server, bench_name, bench_version)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        RETURNING id;
        """,
        (
            exec_info["type"],
            exec_info["approx_rate"],
            exec_info["approx_type"],
            exec_info["compile_command"],
            exec_info["num_threads"],
            exec_info["server"],
            exec_info["bench_name"],
            exec_info["bench_version"],
        ),
    ).fetchone()[0]


def save_exec_input(conn, group_id: int, input_data: Dict[str, Any]):
    conn.execute(
        "INSERT INTO ExecutionInput(group_id, input) VALUES (?, ?);",
        (group_id, json.dumps(input_data)),
    )


def save_execution_run(conn, group_id: int, exec_id: int):
    """Saves the individual execution record using the composite key."""
    conn.execute(
        "INSERT INTO Execution(group_id, id, start_time) VALUES (?, ?, CURRENT_TIMESTAMP);",
        (group_id, exec_id),
    )


def save_exec_envs(conn, group_id: int, envs: Dict[str, Any]):
    for name, value in envs.items():
        conn.execute(
            "INSERT INTO ExecutionEnv(group_id, name, value) VALUES (?, ?, ?);",
            (group_id, name, value),
        )


def save_performance(conn, group_id: int, exec_id: int, name: str, value: float):
    conn.execute(
        "INSERT INTO Performance(group_id, exec_id, name, value) VALUES (?, ?, ?, ?);",
        (group_id, exec_id, name, value),
    )


def save_exec_error(conn, group_id: int, exec_id: int, errno: int, stderr: str):
    conn.execute(
        "INSERT INTO ExecutionError(group_id, exec_id, errno, code, description) VALUES (?, ?, ?, ?, ?);",
        (group_id, exec_id, errno, os.strerror(-errno) if errno < 0 else "N/A", stderr),
    )


def update_exec_endtime(conn, group_id: int, exec_id: int):
    conn.execute(
        "UPDATE Execution SET end_time = CURRENT_TIMESTAMP WHERE group_id = ? AND id = ?;",
        (group_id, exec_id),
    )


def save_metric(conn, group_id: int, exec_id: int, name: str, value: float):
    conn.execute(
        "INSERT INTO QualityMetrics(group_id, exec_id, name, value) VALUES (?, ?, ?, ?);",
        (group_id, exec_id, name, value),
    )


# ============================================================
# Metrics
# ============================================================


def load_file_type(path: str) -> np.ndarray:
    ext = os.path.splitext(path)[1].lower()

    df = []
    if ext == ".parquet":
        df = duckdb.read_parquet(path).df()
    elif ext == ".csv":
        df = pd.read_csv(path, header=None)
    elif ext in (".pkl", ".pickle"):
        df = pd.read_pickle(path)
    else:
        print(f"[ERROR] {path} has a unsuportted extension type.")
        sys.exit(-1)

    return df.to_numpy(dtype=np.float64)


def mape(reference: str, prediction: str):
    ref_vals = load_file_type(reference)
    pred_vals = load_file_type(prediction)
    if ref_vals.shape != pred_vals.shape:
        print(
            f"[ERROR] Shape mismatch (reference shape) {ref_vals.shape} != {pred_vals.shape} (prediction shape)."
        )
        sys.exit(-1)

    mask = ref_vals != 0
    return np.mean(np.abs((ref_vals[mask] - pred_vals[mask]) / ref_vals[mask])) * 100.0


def rmse(reference: str, prediction: str):
    ref_vals = load_file_type(reference)
    pred_vals = load_file_type(prediction)
    if ref_vals.shape != pred_vals.shape:
        print(
            f"[ERROR] Shape mismatch (reference shape) {ref_vals.shape} != {pred_vals.shape} (prediction shape)."
        )
        sys.exit(-1)

    return np.sqrt(np.mean((ref_vals - pred_vals) ** 2))


def mcr(reference: str, prediction: str):
    ref_vals = load_file_type(reference)
    pred_vals = load_file_type(prediction)
    if ref_vals.shape != pred_vals.shape:
        print(
            f"[ERROR] Shape mismatch (reference shape) {ref_vals.shape} != {pred_vals.shape} (prediction shape)."
        )
        sys.exit(-1)

    mismatches = np.sum(ref_vals != pred_vals)
    total_elements = ref_vals.size
    return (mismatches / total_elements) * 100.0


def ssim(reference: str, prediction: str):
    ref = cv2.imread(reference)
    pred = cv2.imread(prediction)
    ref_gray = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
    pred_gray = cv2.cvtColor(pred, cv2.COLOR_BGR2GRAY)
    return similarity(ref_gray, pred_gray)


def metric(
    conn,
    gid: int,
    exec_id: int,
    metric: str,
    reference: str,
    prediction: str,
):
    match metric:
        case "MAPE":
            save_metric(
                conn,
                gid,
                exec_id,
                metric,
                float(mape(reference, prediction)),
            )
        case "SSIM":
            save_metric(conn, gid, exec_id, metric, float(ssim(reference, prediction)))
        case "RMSE":
            save_metric(conn, gid, exec_id, metric, float(rmse(reference, prediction)))
        case "MCR":
            save_metric(conn, gid, exec_id, metric, float(mcr(reference, prediction)))
        case _:
            print(f"[ERROR] {metric} is currently not supported")


def make(cmd: str):
    subprocess.run(cmd, shell=True, executable="/bin/bash", check=True)


def run_benchmark(conn, group_id: int, exec_id: int, exec_info: Dict[str, Any]):
    # Build command
    cmd = '/usr/bin/time -f \'{"elapsed": %e, "user": %U, "sys": %S}\' perf stat -j '
    cmd += f"{exec_info['bench_path']}/{exec_info['bench_name']} "
    for _, val in exec_info["inputs"].items():
        cmd += f"{str(val).replace('$PATH', exec_info['bench_path'])} "

    try:
        res = subprocess.run(
            cmd,
            shell=True,
            executable="/bin/bash",
            capture_output=True,
            text=True,
            check=True,
        )

        # Parse output
        for line in res.stderr.strip().splitlines():
            try:
                data = json.loads(line)
                if "elapsed" in data:
                    for k in ["elapsed", "user", "sys"]:
                        save_performance(conn, group_id, exec_id, k, data[k])
                elif data.get("event"):
                    save_performance(
                        conn, group_id, exec_id, data["event"], data["counter-value"]
                    )
            except json.JSONDecodeError:
                continue
    except subprocess.CalledProcessError as e:
        save_exec_error(conn, group_id, exec_id, e.returncode, e.stderr)


def pos_process(cmd: str):
    try:
        subprocess.run(
            cmd,
            shell=True,
            executable="/bin/bash",
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(
            f"[ERROR] pos-processing command failed, with code ({e.returncode}).\n{e.stderr}"
        )
        sys.exit(-1)


# ============================================================
# Orchestration
# ============================================================


def execution(conn, executions: List[Dict[str, Any]], server: str):
    for entry in executions:
        res = select_benchmark(conn, entry["bench_name"], entry["bench_version"])
        if not res:
            continue
        _, _, bench_path = res

        if sum(1 for v in entry["variants"] if "baseline" in v) > 1:
            print("[ERROR] There should be only one baseline per variant")
            sys.exit(-1)

        baseline_gid = -1
        baseline_id = -1
        for variant in entry["variants"]:
            is_base = variant.get("baseline") is not None
            threads = [1] if is_base else entry["num_threads"]
            iterations = 1 if is_base else entry["num_executions"]

            for t in threads:
                for rate in variant.get("approx_rates", [None]):
                    group_meta = {
                        "type": variant["type"],
                        "approx_rate": rate,
                        "approx_type": variant.get("approx_type", None),
                        "compile_command": variant["compile"],
                        "num_threads": t,
                        "server": server,
                        "bench_name": entry["bench_name"],
                        "bench_version": entry["bench_version"],
                        "bench_path": bench_path,
                        "inputs": entry["inputs"],
                    }

                    make(
                        variant["compile"]
                        .replace("$PATH", bench_path)
                        .replace("$NUM_THREADS", str(t))
                        .replace("$APPROX_RATE", str(rate))
                    )
                    gid = save_execution_group(conn, group_meta)
                    if is_base:
                        baseline_gid = gid

                    save_exec_input(conn, gid, entry["inputs"])
                    save_exec_envs(conn, gid, variant["env_vars"])

                    for id in range(iterations):
                        save_execution_run(conn, gid, id)
                        run_benchmark(conn, gid, id, group_meta)
                        update_exec_endtime(conn, gid, id)

                        pos_process(
                            variant["pos_processing"]
                            .replace("$PATH", bench_path)
                            .replace("$NUM_THREADS", str(t))
                            .replace("$APPROX_RATE", str(rate))
                            .replace("$ID_RUN", str(id))
                            .replace("$ID_GROUP", str(gid))
                        )

                        if is_base:
                            baseline_id = id
                            continue

                        if variant.get("metric") is not None:
                            mtype = variant["metric"]["type"]
                            pred = (
                                variant["metric"]["prediction"]
                                .replace("$PATH", bench_path)
                                .replace("$APPROX_RATE", str(rate))
                                .replace("$NUM_THREADS", str(t))
                                .replace("$ID_GROUP_BASE", str(baseline_gid))
                                .replace("$ID_RUN", str(id))
                                .replace("$ID_GROUP", str(gid))
                                .replace("$ID_BASE", str(baseline_id))
                            )
                            ref = (
                                variant["metric"]["reference"]
                                .replace("$PATH", bench_path)
                                .replace("$APPROX_RATE", str(rate))
                                .replace("$NUM_THREADS", str(t))
                                .replace("$ID_GROUP_BASE", str(baseline_gid))
                                .replace("$ID_RUN", str(id))
                                .replace("$ID_GROUP", str(gid))
                                .replace("$ID_BASE", str(baseline_id))
                            )
                            metric(conn, gid, id, mtype, pred, ref)


def run_plan(conn, plan_path: str):
    with open(plan_path, "r") as f:
        plan = yaml.safe_load(f)["experiment"]
    save_experiment(conn, plan)
    save_server(conn, plan["server"])
    save_benchmarks(conn, plan["benchmarks"])
    execution(conn, plan["executions"], plan["server"]["hostname"])


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("Usage: python script.py <db> <plan.yaml>")
    with duckdb.connect(sys.argv[1]) as conn:
        run_plan(conn, sys.argv[2])
