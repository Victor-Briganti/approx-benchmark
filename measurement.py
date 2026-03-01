import duckdb
import sys
import matplotlib.pyplot as plt
import pandas as pd

PERFORMANCE_METRIC = "elapsed"

# ============================================================
# Database
# ============================================================


def get_approx_apps(conn):
    return conn.execute("""
        SELECT bench_name, MAX(bench_version) AS bench_version
        FROM ExecutionGroup
        WHERE approx_type IS NOT NULL
        GROUP BY bench_name
    """).df()


def get_approx_types(conn, app_name: str, app_version: int):
    return conn.execute(
        """
        SELECT approx_type
        FROM ExecutionGroup
        WHERE bench_name = ? AND bench_version = ? AND approx_type IS NOT NULL
        GROUP BY approx_type
    """,
        (app_name, app_version),
    ).df()


def get_approx_rates(conn, app_name: str, app_version: int, approx_type: str):
    return conn.execute(
        """
        SELECT approx_rate
        FROM ExecutionGroup
        WHERE bench_name = ? AND bench_version = ? AND approx_type = ?
        GROUP BY approx_rate
    """,
        (app_name, app_version, approx_type),
    ).df()


def get_num_threads(
    conn,
    app_name: str,
    app_version: int,
    approx_type: str,
    approx_rate: int | None = None,
):
    sql = """
        SELECT num_threads
        FROM ExecutionGroup
        WHERE bench_name = ? 
          AND bench_version = ? 
          AND approx_type = ? 
    """

    params = [app_name, app_version, approx_type]
    if approx_rate is None:
        sql += " AND approx_rate IS NULL"
    else:
        sql += " AND approx_rate = ?"
        params.append(approx_rate)

    sql += " GROUP BY num_threads"
    return conn.execute(sql, params).df()


def get_execution_group_id(
    conn,
    app_name: str,
    app_version: int,
    approx_type: str,
    num_threads: int,
    approx_rate: int | None = None,
):
    sql = """
        SELECT id
        FROM ExecutionGroup
        WHERE bench_name = ? 
          AND bench_version = ? 
          AND approx_type = ? 
          AND num_threads = ? 
    """

    params = [app_name, app_version, approx_type, num_threads]
    if approx_rate is None:
        sql += " AND approx_rate IS NULL"
    else:
        sql += " AND approx_rate = ?"
        params.append(approx_rate)

    df = conn.execute(sql, params).df()

    if df.empty:
        return None

    return int(df.iloc[0]["id"])


def get_base_execution_group_id(
    conn,
    app_name: str,
    app_version: int,
):
    sql = """
        SELECT id
        FROM ExecutionGroup
        WHERE bench_name = ? 
          AND bench_version = ? 
          AND type = 'omp'
          AND num_threads = 1 
    """
    params = [app_name, app_version]
    df = conn.execute(sql, params).df()

    if df.empty:
        return None

    return int(df.iloc[0]["id"])


def get_quality_metric(
    conn,
    group_id: int,
):
    return conn.execute(
        """
        SELECT name, group_id, MEAN(value) AS value
        FROM QualityMetrics
        WHERE group_id = ? 
        GROUP BY name, group_id
    """,
        (group_id,),
    ).df()


def get_performance_value(
    conn,
    group_id: int,
    value_name: str,
):
    return conn.execute(
        """
        SELECT group_id, MEAN(value) AS value
        FROM Performance
        WHERE group_id = ? AND name = ?
        GROUP BY group_id
    """,
        (group_id, value_name),
    ).df()


# ============================================================
# Graphs
# ============================================================


def plot_quality_metrics(
    app_name, app_version, approx_type, approx_rate, metrics
):
    if not metrics:
        print(f"[WARN] No metrics to plot. App: {app_name}, Type: {approx_type}, Rate: {approx_rate}")
        return

    df = pd.concat(metrics, ignore_index=True)
    plt.figure(figsize=(8, 5))
    all_threads = sorted(df["threads"].unique())

    for metric_name, g in df.groupby("name"):
        g_sorted = g.sort_values("threads")
        plt.plot(
            g_sorted["threads"],
            g_sorted["value"],
            marker="o",
            label=metric_name,
        )

    title = f"{app_name.upper()} {approx_type} "
    if approx_rate is not None:
        title += f"{approx_rate}"

    plt.title(title)
    plt.xlabel("Número de Threads")
    plt.ylabel(f"{df['name'].iloc[0].upper()} %")
    plt.xticks(all_threads)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        f"report/{app_name}/metric/{app_name}v{app_version}_{approx_type}_{approx_rate}.pdf"
    )
    plt.close()


def plot_performance(
    app_name,
    app_version,
    approx_type,
    approx_rate,
    performance,
    baseline: pd.DataFrame,
):
    if not performance:
        print(f"[WARN] No performance data to plot. App: {app_name}, Type: {approx_type}, Rate: {approx_rate}")
        return

    df = pd.concat(performance, ignore_index=True)
    plt.figure(figsize=(8, 5))
    all_threads = sorted(df["threads"].unique())
    df_sorted = df.sort_values("threads")

    plt.plot(
        df_sorted["threads"],
        df_sorted["value"],
        marker="o",
        label="Approx",
    )

    if baseline is not None and not baseline.empty:
        base_val = baseline["value"].iloc[0]
        plt.axhline(
            y=base_val,
            linestyle="--",
            color="black",
            label="Baseline",
        )

    title = f"{app_name.upper()} {approx_type}"
    if approx_rate is not None:
        title += f" {approx_rate}"

    plt.title(title)
    plt.xlabel("Número de Threads")
    plt.ylabel("Tempo de Execução (s)")
    plt.xticks(all_threads)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()

    plt.savefig(
        f"report/{app_name}/performance/{app_name}v{app_version}_{approx_type}_{approx_rate}.pdf"
    )
    plt.close()


# ============================================================
# Execution
# ============================================================


def run(conn):
    apps = get_approx_apps(conn)
    for app in apps.itertuples(index=False):
        types = get_approx_types(conn, app.bench_name, app.bench_version)
        for type in types.itertuples(index=False):
            rates = get_approx_rates(
                conn, app.bench_name, app.bench_version, type.approx_type
            )
            rates_iter = (
                rates.itertuples(index=False) if not rates.empty else [None]
            )
            for rate in rates_iter:
                approx_rate = None if rate is None else rate.approx_rate
                num_threads = get_num_threads(
                    conn,
                    app.bench_name,
                    app.bench_version,
                    type.approx_type,
                    approx_rate,
                )

                performance = []
                quality_metrics = []
                for num_thread in num_threads.itertuples(index=False):
                    group_id = get_execution_group_id(
                        conn,
                        app.bench_name,
                        app.bench_version,
                        type.approx_type,
                        num_thread.num_threads,
                        approx_rate,
                    )
                    metric = get_quality_metric(conn, group_id)
                    metric["threads"] = num_thread.num_threads
                    quality_metrics.append(metric)

                    perf = get_performance_value(
                        conn, group_id, PERFORMANCE_METRIC
                    )
                    perf["threads"] = num_thread.num_threads
                    performance.append(perf)

                plot_quality_metrics(
                    app.bench_name,
                    app.bench_version,
                    type.approx_type,
                    approx_rate,
                    quality_metrics,
                )

                base_group_id = get_base_execution_group_id(
                    conn, app.bench_name, app.bench_version
                )
                baseline = get_performance_value(
                    conn, base_group_id, PERFORMANCE_METRIC
                )
                plot_performance(
                    app.bench_name,
                    app.bench_version,
                    type.approx_type,
                    approx_rate,
                    performance,
                    baseline,
                )


if __name__ == "__main__":
    if len(sys.argv) < 1:
        sys.exit("Usage: python script.py <db>")
    with duckdb.connect(sys.argv[1]) as conn:
        run(conn)
