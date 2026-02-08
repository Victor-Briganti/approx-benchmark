import numpy as np
import sys
import os
import duckdb
import yaml
import json
import subprocess
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
        INSERT INTO ExecutionGroup(type, approx_rate, compile_command, num_threads, server, bench_name, bench_version)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        RETURNING id;
        """,
        (
            exec_info["type"],
            exec_info["approx_rate"],
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


def mape(reference: str, prediction: str):
    ref = duckdb.read_parquet(reference).df()
    pred = duckdb.read_parquet(prediction).df()
    ref_vals, pred_vals = (
        ref.to_numpy(dtype=np.float64),
        pred.to_numpy(dtype=np.float64),
    )
    mask = ref_vals != 0
    return np.mean(np.abs((ref_vals[mask] - pred_vals[mask]) / ref_vals[mask])) * 100.0


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

        for variant in entry["variants"]:
            is_base = variant.get("baseline") is not None
            threads = [1] if is_base else entry["num_threads"]
            iterations = 1 if is_base else entry["num_executions"]

            for t in threads:
                for rate in variant.get("approx_rates", [None]):
                    group_meta = {
                        "type": variant["type"],
                        "approx_rate": rate,
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
                    save_exec_input(conn, gid, entry["inputs"])
                    save_exec_envs(conn, gid, variant["env_vars"])

                    for id in range(iterations):
                        save_execution_run(conn, gid, id)
                        run_benchmark(conn, gid, id, group_meta)
                        update_exec_endtime(conn, gid, id)

                        pos_process(
                            variant["pos-processing"]
                            .replace("$PATH", bench_path)
                            .replace("$NUM_THREADS", str(t))
                            .replace("$APPROX_RATE", str(rate))
                            .replace("$ID_RUN", str(id))
                            .replace("$ID_GROUP", str(gid))
                        )
                        # Metrics logic... (omitted for brevity, same pattern)


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
