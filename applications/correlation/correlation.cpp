//===----------------------------------------------------------------------===//
// OHIO STATE UNIVERSITY SOFTWARE DISTRIBUTION LICENSE
//
// PolyBench/C, a collection of benchmarks containing static control
// parts (the “Software”)
// Copyright (c) 2010-2016, Ohio State University. All rights reserved.
//
// Modified in 2025 by Victor Briganti
//
// The Software is available for download and use subject to the terms
// and conditions of this License.  Access or use of the Software
// constitutes acceptance and agreement to the terms and conditions of
// this License.  Redistribution and use of the Software in source and
// binary forms, with or without modification, are permitted provided
// that the following conditions are met:
//
// 1. Redistributions of source code must retain the above copyright
// notice, this list of conditions and the capitalized paragraph below.
//
// 2. Redistributions in binary form must reproduce the above copyright
// notice, this list of conditions and the capitalized paragraph below in
// the documentation and/or other materials provided with the
// distribution.
//
// 3. The name of Ohio State University, or its faculty, staff or
// students may not be used to endorse or promote products derived from
// the Software without specific prior written permission.
//
// This software was produced with support from the U.S. Defense Advanced
// Research Projects Agency (DARPA), the U.S. Department of Energy (DoE)
// and the U.S. National Science Foundation. Nothing in this work should
// be construed as reflecting the official policy or position of the
// Defense Department, the United States government or Ohio State
// University.
//
// THIS SOFTWARE HAS BEEN APPROVED FOR PUBLIC RELEASE, UNLIMITED
// DISTRIBUTION.  THE SOFTWARE IS PROVIDED “AS IS” AND WITHOUT ANY
// EXPRESS, IMPLIED OR STATUTORY WARRANTIES, INCLUDING, BUT NOT LIMITED
// TO, WARRANTIES OF ACCURACY, COMPLETENESS, NONINFRINGEMENT,
// MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
// ACCESS OR USE OF THE SOFTWARE IS ENTIRELY AT THE USER’S RISK.  IN NO
// EVENT SHALL OHIO STATE UNIVERSITY OR ITS FACULTY, STAFF OR STUDENTS BE
// LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
// CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
// SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
// BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
// WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
// OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
// IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.  THE SOFTWARE USER SHALL
// INDEMNIFY, DEFEND AND HOLD HARMLESS OHIO STATE UNIVERSITY AND ITS
// FACULTY, STAFF AND STUDENTS FROM ANY AND ALL CLAIMS, ACTIONS, DAMAGES,
// LOSSES, LIABILITIES, COSTS AND EXPENSES, INCLUDING ATTORNEYS’ FEES AND
// COURT COSTS, DIRECTLY OR INDIRECTLY ARISING OUT OF OR IN CONNECTION
// WITH ACCESS OR USE OF THE SOFTWARE.
//===----------------------------------------------------------------------===//
// Correlation
//
// Calculate the correlation between all columns of a csv file.
// The formula used to calculate the correlation is:
//
// r = (n * sumXY - sumX * sumY) / sqrt((n * sumX2 - (sumX * sumX)) * (n * sumY2
// - (sumY * sumY)))
//
// Where:
// - sumX  = Sum of all the values of the column X;
// - sumY  = Sum of all the values of the column Y;
// - sumXY = Sum of all the values of the multiplication of the rows in the
//           columns X and Y;
// - sumX2 = Sum of all the values of column X squared;
// - sumY2 = Sum of all the values of column Y squared;
// - n     = The number of elements in both columns
//
// Usage: ./correlation <csv_file>
//
//===----------------------------------------------------------------------===//

#include <cmath>
#include <fstream>
#include <iostream>
#include <string>
#include <unistd.h>

//===------------------------------------------------------------------------===
// Correlation
//===------------------------------------------------------------------------===

double correlation(double *x, double *y, int rows) {
  double sumX = 0;
  double sumY = 0;
  double sumXY = 0;
  double sumX2 = 0;
  double sumY2 = 0;

  for (size_t i = 0; i < rows; i++) {
    sumX += x[i];
    sumY += y[i];
    sumXY += x[i] * y[i];
    sumX2 += x[i] * x[i];
    sumY2 += y[i] * y[i];
  }

  double numerador = rows * sumXY - sumX * sumY;
  double denominador = std::sqrt((rows * sumX2 - (sumX * sumX)) *
                                 (rows * sumY2 - (sumY * sumY)));
  return numerador / denominador;
}

double *correlationMatrix(double **&data, int columns, int rows) {
  double *matrix = new double[columns * rows]();

#pragma omp parallel for collapse(2) shared(matrix) schedule(static) num_threads(NUM_THREADS)
  for (int i = 0; i < columns; i++) {
    for (int j = i; j < columns; j++) {
      double r = (j == i) ? 1.0 : correlation(data[i], data[j], rows);
      matrix[i * columns + j] = r;
      matrix[j * columns + i] = r;
    }
  }

  return matrix;
}

//===------------------------------------------------------------------------===
// Helper Function
//===------------------------------------------------------------------------===

std::pair<int, int> readDimensions(std::ifstream &file) {
  std::string line;
  getline(file, line);

  int columnNum = std::stoi(line.substr(0, line.find(' ')));
  int rowNum = std::stoi(line.substr(line.find(' '), line.size()));

  return {columnNum, rowNum};
}

double **readData(std::ifstream &file, int columns, int rows) {
  double **data = new double *[columns];

  for (int i = 0; i < columns; i++) {
    data[i] = new double[rows];
  }

  int row = 0;
  std::string line;
  while (getline(file, line)) {
    int pos = 0;

    for (int column = 0; column < columns; column++) {
      if (column + 1 == columns) {
        data[column][row] = std::stod(line.substr(pos, line.size()));
      } else {
        data[column][row] =
            std::stod(line.substr(pos, line.find(',', pos) - pos));
        pos = line.find(',', pos) + 1;
      }
    }

    row++;
  }

  return data;
}

void print_matrix(double *matrix, int columns) {
  for (int i = 0; i < columns; i++) {
    for (int j = 0; j < columns; j++) {
      std::cout << matrix[i * columns + j] << (j + 1 == columns ? "\n" : ",");
    }
  }
}

//===------------------------------------------------------------------------===
// Main
//===------------------------------------------------------------------------===

int main(int argc, char **argv) {
  if (argc < 2) {
    std::cerr << "Invalid number of arguments!\n";
    std::cerr << "Usage: " << argv[0] << " <input_file>\n";
    return -1;
  }

  std::ifstream file(argv[1]);
  if (!file) {
    std::cerr << "Could not open file " << argv[1] << "\n";
    return -1;
  }

  auto [columns, rows] = readDimensions(file);
  double **data = readData(file, columns, rows);

  double *matrix = correlationMatrix(data, columns, rows);
  print_matrix(matrix, columns);

  return 0;
}
