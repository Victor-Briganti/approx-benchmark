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
// 2MM
//
// Multiply two matrixes with this result multiply with another matrix and
// output the result as a csv like structure (without the header).
//
// Usage: ./2mm <matrix_size>
//
//===----------------------------------------------------------------------===//

#include <cstdint>
#include <iostream>

//===------------------------------------------------------------------------===
// Helper Functions
//===------------------------------------------------------------------------===

void output_matrix(uint64_t *&matrix, size_t size) {
  for (int y = 0; y < size; y++) {
    for (int x = 0; x < size; x++) {
      std::cout << matrix[y * size + x] << (x + 1 == size ? '\n' : ',');
    }
  }
}

void init_matrix(uint64_t *&matrix, size_t size, bool fill = false) {
  matrix = new uint64_t[size * size];

  if (fill) {
#pragma omp parallel for collapse(2)
    for (size_t y = 0; y < size; y++) {
      for (size_t x = 0; x < size; x++) {
        matrix[y * size + x] = x + y;
      }
    }
  }
}

//===------------------------------------------------------------------------===
// Main
//===------------------------------------------------------------------------===

int main(int argc, char **argv) {
  if (argc < 2) {
    std::cerr << "Invalid number of arguments!\n";
    std::cerr << "Usage: " << argv[0] << " <matrix_size>\n";
    return -1;
  }

  size_t matrixSize = atol(argv[1]);

  uint64_t *A = nullptr;
  uint64_t *B = nullptr;
  uint64_t *C = nullptr;
  uint64_t *D = nullptr;
  uint64_t *E = nullptr;

  init_matrix(A, matrixSize, true);
  init_matrix(B, matrixSize, true);
  init_matrix(C, matrixSize);
  init_matrix(D, matrixSize, true);
  init_matrix(E, matrixSize);

#pragma omp parallel shared(A, B, C, D)
  {
#pragma omp for collapse(2) schedule(static)
    for (size_t i = 0; i < matrixSize; ++i) {
      for (size_t k = 0; k < matrixSize; ++k) {
        uint64_t columnVal = A[i * matrixSize + k];
        for (size_t j = 0; j < matrixSize; ++j) {
          C[i * matrixSize + j] += columnVal * B[k * matrixSize + j];
        }
      }
    }

#pragma omp for collapse(2) schedule(static)
    for (size_t i = 0; i < matrixSize; ++i) {
      for (size_t k = 0; k < matrixSize; ++k) {
        uint64_t columnVal = C[i * matrixSize + k];
        for (size_t j = 0; j < matrixSize; ++j) {
          E[i * matrixSize + j] += columnVal * D[k * matrixSize + j];
        }
      }
    }
  }

  output_matrix(E, matrixSize);
  return 0;
}
