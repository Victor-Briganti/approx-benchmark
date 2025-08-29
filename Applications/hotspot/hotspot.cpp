//===------------------------------------------------------------------------===
// LICENSE TERMS
//
// Copyright (c)2008-2011 University of Virginia
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted without royalty fees or other restrictions,
// provided that the following conditions are met:
//
//     * Redistributions of source code must retain the above copyright notice,
//     this list of conditions and the following disclaimer.
//     * Redistributions in binary form must reproduce the above copyright
//     notice, this list of conditions and the following disclaimer in the
//     documentation and/or other materials provided with the distribution.
//     * Neither the name of the University of Virginia, the Dept. of Computer
//     Science, nor the names of its contributors may be used to endorse or
//     promote products derived from this software without specific prior
//     written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
// AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
// IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
// ARE DISCLAIMED. IN NO EVENT SHALL THE UNIVERSITY OF VIRGINIA OR THE SOFTWARE
// AUTHORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
// OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
// SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
// INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
// CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
// ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
// POSSIBILITY OF SUCH DAMAGE.
//
// If you use this software or a modified version of it, please cite the most
// relevant among the following papers:
//
// - M. A. Goodrum, M. J. Trotter, A. Aksel, S. T. Acton, and K. Skadron.
// Parallelization of Particle Filter Algorithms. In Proceedings of the 3rd
// Workshop on Emerging Applications and Many-core Architecture (EAMA), in
// conjunction with the IEEE/ACM International Symposium on Computer
// Architecture (ISCA), June 2010.
//
// - S. Che, M. Boyer, J. Meng, D. Tarjan, J. W. Sheaffer, Sang-Ha Lee and K.
// Skadron. "Rodinia: A Benchmark Suite for Heterogeneous Computing". IEEE
// International Symposium on Workload Characterization, Oct 2009.
//
// - J. Meng and K. Skadron. "Performance Modeling and Automatic Ghost Zone
// Optimization for Iterative Stencil Loops on GPUs." In Proceedings of the 23rd
// Annual ACM International Conference on Supercomputing (ICS), June 2009.
//
// - L.G. Szafaryn, K. Skadron and J. Saucerman. "Experiences Accelerating
// MATLAB Systems Biology Applications." in Workshop on Biomedicine in Computing
// (BiC) at the International Symposium on Computer Architecture (ISCA), June
// 2009.
//
// - M. Boyer, D. Tarjan, S. T. Acton, and K. Skadron. "Accelerating Leukocyte
// Tracking using CUDA: A Case Study in Leveraging Manycore Coprocessors." In
// Proceedings of the International Parallel and Distributed Processing
// Symposium (IPDPS), May 2009.
//
// - S. Che, M. Boyer, J. Meng, D. Tarjan, J. W. Sheaffer, and K. Skadron. "A
// Performance Study of General Purpose Applications on Graphics Processors
// using CUDA" Journal of Parallel and Distributed Computing, Elsevier, June
// 2008.
//===------------------------------------------------------------------------===
// Hotspot
//
// HotSpot is a widely used tool to estimate processor temperature based on an
// architectural floorplan and simulated power measurements. The thermal
// simulation iteratively solves a series of differential equations for block.
// Each output cell in the computational grid represents the average temperature
// value of the corresponding area of the chip.
//
// Usage: ./hotspot <grid> <num_iterations> <power_file> <temp_file>
//
//===------------------------------------------------------------------------===

#include <cstring>
#include <fstream>
#include <iostream>

/* maximum power density possible (say 300W for a 10mm x 10mm chip)	*/
constexpr double MAX_PD = 3.0e6;

/* required precision in degrees	*/
constexpr double PRECISION = 0.001;
constexpr double SPEC_HEAT_SI = 1.75e6;
constexpr double K_SI = 100;

/* capacitance fitting factor	*/
constexpr double FACTOR_CHIP = 0.5;

/* chip parameters	*/
constexpr double t_chip = 0.0005;
constexpr double chip_height = 0.016;
constexpr double chip_width = 0.016;

/* ambient temperature, assuming no package at all	*/
constexpr double amb_temp = 80.0;

//===------------------------------------------------------------------------===
// Helper Function
//===------------------------------------------------------------------------===

double *readData(std::ifstream &file, int size) {
  double *data = new double[size * size];

  int lineNum = 0;
  std::string line;
  while (getline(file, line)) {
    data[lineNum] = std::stod(line);
    lineNum++;
  }

  if (lineNum != (size * size)) {
    delete[] data;
    return nullptr;
  }

  return data;
}

//===------------------------------------------------------------------------===
// Hotspot
//===------------------------------------------------------------------------===

void singleIteration(double *result, double *temp, const double *power, int row,
                     int col, double Cap, double Rx, double Ry, double Rz,
                     double step) {
  const double stepCap = step / Cap;

  // Corner 1
  double deltaCorner1 =
      stepCap * (power[0] + (temp[1] - temp[0]) / Rx +
                 (temp[col] - temp[0]) / Ry + (amb_temp - temp[0]) / Rz);
  result[0] = temp[0] + deltaCorner1;

  // Corner 2
  double deltaCorner2 =
      stepCap * (power[col - 1] + (temp[col - 2] - temp[col - 1]) / Rx +
                 (temp[2 * col - 1] - temp[col - 1]) / Ry +
                 (amb_temp - temp[col - 1]) / Rz);
  result[col - 1] = temp[col - 1] + deltaCorner2;

  // Corner 3
  double deltaCorner3 =
      stepCap *
      (power[(row - 1) * col + col - 1] +
       (temp[(row - 1) * col + col - 2] - temp[(row - 1) * col + col - 1]) /
           Rx +
       (temp[(row - 2) * col + col - 1] - temp[(row - 1) * col + col - 1]) /
           Ry +
       (amb_temp - temp[(row - 1) * col + col - 1]) / Rz);
  result[(row - 1) * col + (col - 1)] =
      temp[(row - 1) * col + (col - 1)] + deltaCorner3;

  // Corner 4
  double deltaCorner4 =
      stepCap * (power[(row - 1) * col] +
                 (temp[(row - 1) * col + 1] - temp[(row - 1) * col]) / Rx +
                 (temp[(row - 2) * col] - temp[(row - 1) * col]) / Ry +
                 (amb_temp - temp[(row - 1) * col]) / Rz);
  result[(row - 1) * col] = temp[(row - 1) * col] + deltaCorner4;

#pragma omp parallel shared(result, temp, power)
  {
#pragma omp for schedule(static)
    for (int c = 1; c < col - 1; c++) {
      // Edge 1
      double deltaEdge1 =
          stepCap *
          (power[c] + (temp[c + 1] + temp[c - 1] - 2.0 * temp[c]) / Rx +
           (temp[col + c] - temp[c]) / Ry + (amb_temp - temp[c]) / Rz);

      result[c] = temp[c] + deltaEdge1;

      // Edge 3
      double deltaEdge3 =
          stepCap *
          (power[(row - 1) * col + c] +
           (temp[(row - 1) * col + c + 1] + temp[(row - 1) * col + c - 1] -
            2.0 * temp[(row - 1) * col + c]) /
               Rx +
           (temp[((row - 1) - 1) * col + c] - temp[(row - 1) * col + c]) / Ry +
           (amb_temp - temp[(row - 1) * col + c]) / Rz);

      result[(row - 1) * col + c] = temp[(row - 1) * col + c] + deltaEdge3;
    }

#pragma omp for schedule(static)
    for (int r = 1; r < row - 1; r++) {
      // Edge 2
      double deltaEdge2 =
          stepCap *
          (power[r * col + (col - 1)] +
           (temp[(r + 1) * col + (col - 1)] + temp[(r - 1) * col + (col - 1)] -
            2.0 * temp[r * col + (col - 1)]) /
               Ry +
           (temp[r * col + (col - 1) - 1] - temp[r * col + (col - 1)]) / Rx +
           (amb_temp - temp[r * col + (col - 1)]) / Rz);

      result[r * col + (col - 1)] = temp[r * col + (col - 1)] + deltaEdge2;

      // Edge 4
      double deltaEdge4 =
          stepCap *
          (power[r * col] +
           (temp[(r + 1) * col] + temp[(r - 1) * col] - 2.0 * temp[r * col]) /
               Ry +
           (temp[r * col + 1] - temp[r * col]) / Rx +
           (amb_temp - temp[r * col]) / Rz);

      result[r * col] = temp[r * col] + deltaEdge4;
    }

#pragma omp for schedule(static)
    for (int r = 1; r < row - 1; r++) {
#pragma omp simd
      for (int c = 1; c < col - 1; c++) {
        // Inside the Chip
        double deltaChip =
            stepCap * (power[r * col + c] +
                       (temp[(r + 1) * col + c] + temp[(r - 1) * col + c] -
                        2.0 * temp[r * col + c]) /
                           Ry +
                       (temp[r * col + c + 1] + temp[r * col + c - 1] -
                        2.0 * temp[r * col + c]) /
                           Rx +
                       (amb_temp - temp[r * col + c]) / Rz);

        result[r * col + c] = temp[r * col + c] + deltaChip;
      }
    }
  }

  std::memcpy(temp, result, sizeof(double) * row * col);
}

void computeThermalTemp(double *result, int iterations, double *power,
                        double *temp, int row, int col) {
  const double grid_height = chip_height / row;
  const double grid_width = chip_width / col;
  const double Cap =
      FACTOR_CHIP * SPEC_HEAT_SI * t_chip * grid_width * grid_height;
  const double Rx = grid_width / (2.0 * K_SI * t_chip * grid_height);
  const double Ry = grid_height / (2.0 * K_SI * t_chip * grid_width);
  const double Rz = t_chip / (K_SI * grid_height * grid_width);
  const double max_slope = MAX_PD / (FACTOR_CHIP * t_chip * SPEC_HEAT_SI);
  const double step = PRECISION / max_slope;

  for (int i = 0; i < iterations; i++) {
    singleIteration(result, temp, power, row, col, Cap, Rx, Ry, Rz, step);
  }
}

//===------------------------------------------------------------------------===
// Main
//===------------------------------------------------------------------------===

int main(int argc, char **argv) {
  if (argc < 4) {
    std::cerr << "Invalid number of arguments!\n";
    std::cerr << "Usage: " << argv[0]
              << " <grid> <num_iterations> <power_file> <temp_file>\n";
    return -1;
  }

  int gridSize = atoi(argv[1]);
  if (!gridSize || gridSize < 0) {
    std::cerr << "Grid is not a valid value\n";
    return -1;
  }

  int numIterations = atoi(argv[2]);
  if (!numIterations || numIterations < 0) {
    std::cerr << "Number of iterations is not a valid value\n";
    return -1;
  }

  std::ifstream powerFile(argv[3]);
  if (!powerFile) {
    std::cerr << "Could not open power file: " << argv[3] << "\n";
    return -1;
  }

  std::ifstream tempFile(argv[4]);
  if (!tempFile) {
    std::cerr << "Could not open temperature file: " << argv[4] << "\n";
    return -1;
  }

  double *power = readData(powerFile, gridSize);
  if (!power) {
    std::cerr << "The size of the power file does not match the grid size\n";
    return -1;
  }

  double *temp = readData(tempFile, gridSize);
  if (!temp) {
    std::cerr
        << "The size of the temperature file does not match the grid size\n";
    return -1;
  }

  double *result = new double[gridSize * gridSize];
  computeThermalTemp(result, numIterations, power, temp, gridSize, gridSize);

  for (int i = 0; i < gridSize * gridSize; i++) {
    std::cout << result[i] << "\n";
  }

  return 0;
}