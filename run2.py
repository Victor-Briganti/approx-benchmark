import sys
import os
import duckdb
import yaml
import json
import subprocess
from typing import Dict, List, Tuple, Optional


# ============================================================
# Utils
# ============================================================


def replace_variables(input: str, list_vars: Dict[str, str]):
    return ""


# ============================================================
# SQL Search
# ============================================================


def select_benchmark(
    conn, name: str, version: int
) -> Optional[Tuple[str, int, str]]:
    return conn.execute(
        """
        SELECT name, version, path FROM Benchmark WHERE name = ? AND version = ?;
        """,
        (name, version),
    ).fetchone()


# ============================================================
# Bookeping
# ============================================================


def save_experiment(conn, plan: Dict[str, any]):
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    conn.execute(
        """
            INSERT INTO Experiment(yaml_snapshot, 
                                   commit)
            VALUES (?, ?);
        """,
        (
            plan,
            commit.stdout,
        ),
    )
    print("[INFO] Saved YAML plan")


def save_server(conn, server: Dict[str, any]):
    hostname = conn.execute(
        """
    SELECT hostname FROM Server WHERE hostname = ?;
    """,
        (server["hostname"],),
    ).fetchone()

    if hostname is None:
        print(f"[INFO] Saving server {server['hostname']}")
        conn.execute(
            """
                INSERT INTO Server(hostname, 
                                   cpu_description, 
                                   hertz, 
                                   cores,
                                   threads,
                                   ram_memory,
                                   operating_system)
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
        print(
            f"[INFO] Server {server['hostname']} already exists on the system"
        )


def save_benchmarks(conn, benchmarks: List[Dict[str, any]]):
    for bench in benchmarks:
        query_res = select_benchmark(conn, bench["name"], bench["version"])

        if query_res is None:
            print(
                f"[INFO] Saving benchmark {bench['name']} v{bench['version']}"
            )
            conn.execute(
                """
                    INSERT INTO Benchmark(name, 
                                          version, 
                                          path, 
                                          setup,
                                          description)
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
        else:
            print(
                f"[INFO] Benchmark {bench['name']} v{bench['version']} already exists on the system"
            )

        print(
            f"[INFO] Applying {bench['name']} v{bench['version']} setup: '{bench['setup'].replace('$PATH', bench['path'])}'"
        )
        cmd = bench["setup"].replace("$PATH", bench["path"])
        subprocess.run(cmd, shell=True, executable="/bin/bash", check=True)


def save_execution(conn, exec: Dict[str, any]):
    conn.execute(
        """
        INSERT INTO Execution(type, 
                              approx_rate, 
                              compile_command, 
                              exec_num,
                              num_threads,
                              server,
                              bench_name,
                              bench_version,
                              exp_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, (SELECT MAX(id) FROM Experiment));
        """,
        (
            exec["type"],
            exec["approx_rate"],
            exec["compile_command"],
            exec["exec_num"],
            exec["num_threads"],
            exec["server"],
            exec["bench_name"],
            exec["bench_version"],
        ),
    )

    return conn.execute(
        """
        SELECT max(id) FROM Execution;
        """
    ).fetchone()


def save_exec_input(conn, exec_id, input: Dict[str, any]):
    conn.execute(
        """
        INSERT INTO ExecutionInput(exec_id, input)
        VALUES (?, ?);
        """,
        (exec_id, input),
    )


def save_performance(conn, run_id: int, name: str, value: int):
    conn.execute(
        """
        INSERT INTO Performance(exec_id, name, value)
        VALUES (?, ?, ?);
        """,
        (run_id, name, value),
    )


def save_exec_envs(conn, exec_id, envs: Dict[str, any]):
    for env, value in envs.items():
        conn.execute(
            """
            INSERT INTO ExecutionEnv(exec_id, name, value)
            VALUES (?, ?, ?);
            """,
            (exec_id, env, value),
        )


def save_exec_error(conn, run_id: int, errno: int, stderr: str):
    conn.execute(
        """
        INSERT INTO ExecutionError(exec_id, errno, code, description)
        VALUES (?, ?, ?, ?);
        """,
        (run_id, errno, os.strerror(-errno), stderr),
    )


def update_exec_endtime(conn, id: int):
    conn.execute(
        """
        UPDATE Execution
        SET end_time = CURRENT_TIMESTAMP
        WHERE id = ?;
        """,
        (id,),
    )


# ============================================================
# Execution
# ============================================================


def make(cmd: str):
    comp = subprocess.run(cmd, shell=True, executable="/bin/bash", check=True)
    if comp.returncode != 0:
        print(
            f"[ERROR] Compilation failed with error code ({comp.returncode}).\nOutput: {comp.stderr}"
        )
        sys.exit(-1)


def run(conn, run_id: int, exec_info: Dict[str, any]):
    cmd = '/usr/bin/time -f \'{"elapsed": %e, "user": %U, "sys": %S}\''
    cmd = f'{cmd} perf stat -j'
    cmd = f"{cmd} $PATH/{exec_info['bench_name']}".replace(
        "$PATH", exec_info["bench_path"]
    )

    for _, value in exec_info["inputs"].items():
        cmd = f"{cmd} {str(value).replace('$PATH', exec_info['bench_path'])}"

    result = None
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            executable="/bin/bash",
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        save_exec_error(conn, run_id, e.returncode, e.stderr)
        print("[ERROR] Could not execute benchmark")
        print(f"[ERROR] Command: {cmd}")
        print(f"[ERROR] Return code: {e.returncode}")
        print(f"[ERROR] STDERR:\n{e.stderr}")
        sys.exit(1)

    lines = result.stderr.strip().splitlines()
    records = [json.loads(line) for line in lines]
    for i, r in enumerate(records):
        if i == len(records) - 1:
            save_performance(conn, run_id, "elapsed", r["elapsed"])
            save_performance(conn, run_id, "user", r["user"])
            save_performance(conn, run_id, "sys", r["sys"])
        else:
            save_performance(conn, run_id, r["event"], r["counter-value"])


def run_pos_processing(cmd: str):
    result = subprocess.run(cmd, shell=True, executable="/bin/bash", check=True)
    if result.returncode < 0:
        print(
            f"[ERROR] Could not execute command {cmd}.\nError: {result.stderr}"
        )
        sys.exit(-1)


def execution(conn, executions: List[Dict[str, any]], server: str):
    for exec in executions:
        _, _, bench_path = select_benchmark(
            conn, exec["bench_name"], exec["bench_version"]
        )
        if bench_path is None:
            print(
                f"[ERROR] Could not retrieve the $PATH of {exec['bench_name']} v{exec['bench_version']}"
            )
            return

        for thread in exec["num_threads"]:
            for num_exec in range(exec["num_executions"]):
                for variant in exec["variants"]:
                    for approx_rate in variant.get("approx_rates", [None]):
                        exec_info = {
                            "type": variant["type"],
                            "approx_rate": approx_rate,
                            "compile_command": variant["compile"],
                            "exec_num": num_exec,
                            "num_threads": thread,
                            "server": server,
                            "bench_name": exec["bench_name"],
                            "bench_version": exec["bench_version"],
                        }
                        make(variant["compile"].replace("$PATH", bench_path))

                        run_id = save_execution(conn, exec_info)[0]
                        save_exec_input(conn, run_id, exec["inputs"])
                        save_exec_envs(conn, run_id, variant["env_vars"])

                        exec_info["inputs"] = exec["inputs"]
                        exec_info["envs"] = variant["env_vars"]
                        exec_info["bench_path"] = bench_path
                        run(conn, run_id, exec_info)
                        update_exec_endtime(conn, run_id)

                        pos_processing = variant.get("pos-processing", None)
                        if pos_processing is not None:
                            pos_processing = pos_processing.replace(
                                "$PATH", bench_path
                            ).replace("$ID_RUN", str(run_id))
                            run_pos_processing(pos_processing)


def run_plan(conn, plan_path: str):
    with open(plan_path, "r") as file:
        plan = yaml.safe_load(file)["experiment"]
        save_experiment(conn, plan)
        save_server(conn, plan["server"])
        save_benchmarks(conn, plan["benchmarks"])
        execution(conn, plan["executions"], plan["server"]["hostname"])


# ============================================================
# Main
# ============================================================


def get_database_connection(db_path: str):
    return duckdb.connect(db_path, read_only=False)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Incorrect number of arguments!")
        print(f"{sys.argv[0]} <database> <plan.yaml>")
        sys.exit(-1)

    with get_database_connection(sys.argv[1]) as conn:
        run_plan(conn, sys.argv[2])
