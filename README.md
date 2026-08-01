# Approx-Benchmark

Approx-Benchmark is a benchmark suite designed to evaluate the impact of approximation techniques and parallel execution on both the performance and output quality of different applications.

The suite includes applications from multiple computing domains, each selected based on two criteria:

* The application exhibits some degree of error tolerance, allowing approximation techniques to be applied.
* The application exposes parallelism that can be exploited using OpenMP.

The benchmark automates compilation, execution, result collection, and stores all measurements in a DuckDB database for further analysis.

## Applications

The suite currently contains seven applications spanning a diverse set of computing domains.

| Application        | Domain                     | Quality Metric |
| ------------------ | -------------------------- | -------------- |
| **2MM**            | Linear Algebra             | MAPE           |
| **Correlation**    | Statistics and Probability | MAPE           |
| **Deriche**        | Image Processing           | SSIM           |
| **Jacobi 2D**      | Numerical Analysis         | MAPE           |
| **K-means**        | Machine Learning           | MCR            |
| **Mandelbrot**     | Computer Graphics          | SSIM           |
| **Monte Carlo PI** | Statistics and Probability | MAPE           |

## Quality Metrics

The benchmark evaluates the quality degradation introduced by approximation using application-specific metrics.

| Metric   | Description                         |
| -------- | ----------------------------------- |
| **MAPE** | Mean Absolute Percentage Error      |
| **MCR**  | Misclassification Rate              |
| **SSIM** | Structural Similarity Index Measure |

Each application reports the metric that best reflects the correctness of its output.

## Requirements

Before running the benchmark, make sure the following dependencies are installed:

* LLVM/Clang with support for the `approx` directive
* Python 3
* `virtualenv`
* DuckDB command-line interface

## Building LLVM

The benchmark depends on a modified version of LLVM that implements the `approx` directive.

```bash
git clone https://github.com/Victor-Briganti/llvm-project
cd llvm-project
git switch approx

cmake --preset omp-approx -S llvm
cmake --build build
```

## Running the Benchmark

After building LLVM, configure the benchmark to use the generated compiler and runtime libraries by updating the corresponding paths in the benchmark configuration.

Then create a Python virtual environment, install the required packages, initialize the database, and execute the benchmark:

```bash
virtualenv .env
source .env/bin/activate

pip install -r requirements.txt

duckdb database.db < utils/database_creation.sql

python run.py database.db benchmark.yaml
```

## Configuration

The `benchmark.yaml` file contains the benchmark configuration, including:

* Machine metadata
* Compiler configuration
* Benchmark parameters
* Application settings
* Execution configuration

Adjust this file according to your experimental environment before running the benchmark.

## Output

All execution results are stored in the DuckDB database specified on the command line. This database contains performance measurements, quality metrics, execution metadata, and system information, enabling further analysis and visualization.

## LICENSE

Before you start using, modifying or distributing Approx-Benchmark, its programs or the supplied inputs in any way, make sure you understand all licenses involved. The Approx-Benchmark framework itself is available under a liberal open source license, as explained in the file LICENSE which is in the same directory as this README file. Each program uses its own license, which is different in some cases. Licenses for source code are put as an header in each source file.
