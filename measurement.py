import duckdb
import sys
import matplotlib.pyplot as plt
import pandas as pd

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


# ============================================================
# Graphs
# ============================================================


def plot_quality_metrics(
    app_name, app_version, approx_type, approx_rate, metrics
):
    if not metrics:
        print("[WARN] No metrics to plot.")
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
        f"report/{app_name}/{app_name}v{app_version}_{approx_type}_{approx_rate}.pdf"
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
                    print(
                        f"Processing {app.bench_name} {type.approx_type} {approx_rate} threads={num_thread.num_threads}.\nQuality Metrics:\n{metric}\n"
                    )
                    metric["threads"] = num_thread.num_threads
                    quality_metrics.append(metric)

                # for metric in quality_metrics:
                #     if metric.empty:
                #         print(
                #             f"[WARN] No metrics for {app.bench_name} {type.approx_type} {approx_rate} threads={num_thread.num_threads}"
                #         )
                #         sys.exit(-1)

                #     plot_quality_metrics(
                #         app.bench_name,
                #         app.bench_version,
                #         type.approx_type,
                #         approx_rate,
                #         quality_metrics,
                #     )


if __name__ == "__main__":
    if len(sys.argv) < 1:
        sys.exit("Usage: python script.py <db>")
    with duckdb.connect(sys.argv[1]) as conn:
        run(conn)
