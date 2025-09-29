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
// Jacobi 2D
//
// Performs a 2D Jacobi relaxation method on a square grid.
// Iteratively updates each cell in the grid to the average of its four
// neighbors. Used for solving partial differential equations such as Laplace's
// equation.
// Outputs the final 2D grid as a CSV format (without header).
//
// Usage: ./jacobi2d <matrix_size> <number_steps>
//
//===----------------------------------------------------------------------===//

#include <iostream>
#include <unistd.h>

//===------------------------------------------------------------------------===
// Helper Functions
//===------------------------------------------------------------------------===

void output_matrix(double *&matrix, size_t size) {
  for (int y = 0; y < size; y++) {
    for (int x = 0; x < size; x++) {
      std::cout << matrix[y * size + x] << (x + 1 == size ? '\n' : ',');
    }
  }
}

double *init_matrix(size_t size, int offset) {
  double *matrix = new double[size * size];

  for (size_t i = 0; i < size; i++) {
    for (size_t j = 0; j < size; j++) {
      matrix[i * size + j] =
          (i * (j + offset) + offset) / static_cast<double>(size);
    }
  }

  return matrix;
}

//===------------------------------------------------------------------------===
// Jacobi
//===------------------------------------------------------------------------===

void jacobi_2d(int steps, size_t size, double *A, double *B) {
#pragma omp parallel
  for (int t = 0; t < steps; t++) {
#pragma omp for collapse(2) schedule(static)
    for (size_t i = 1; i < size - 1; i++) {
      for (size_t j = 1; j < size - 1; j++) {
        B[i * size + j] = (A[i * size + j] + A[i * size + j - 1] +
                           A[(i - 1) * size + j] + A[(i + 1) * size + j]) /
                          4;
      }
    }

#pragma omp for collapse(2) schedule(static)
    for (size_t i = 1; i < size - 1; i++) {
      for (size_t j = 1; j < size - 1; j++) {
        A[i * size + j] = (B[i * size + j] + B[i * size + j - 1] +
                           B[(i - 1) * size + j] + B[(i + 1) * size + j]) /
                          4;
      }
    }
  }
}

//===------------------------------------------------------------------------===
// Main
//===------------------------------------------------------------------------===

int main(int argc, char **argv) {
  if (argc < 3) {
    std::cerr << "Invalid number of arguments!\n";
    std::cerr << "Usage: " << argv[0] << " <matrix_size> <number_steps>\n";
    return -1;
  }

  size_t size = atoi(argv[1]);
  int steps = atoi(argv[2]);

  double *A = init_matrix(size, 2);
  double *B = init_matrix(size, 3);

  jacobi_2d(steps, size, A, B);
  output_matrix(A, size);
  return 0;
}
