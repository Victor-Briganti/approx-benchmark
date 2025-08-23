//===----------------------------------------------------------------------===//
// 2MM
//
// Multiply two matrixes with this result multiply with another matrix and
// output the result as a csv like structure (without the header).
//
// Usage: ./2mm <matrix_size>
//
//===----------------------------------------------------------------------===//
//
// Copyright 2025 Victor Briganti
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//
// 1. Redistributions of source code must retain the above copyright notice,
// this list of conditions and the following disclaimer.
//
// 2. Redistributions in binary form must reproduce the above copyright notice,
// this list of conditions and the following disclaimer in the documentation
// and/or other materials provided with the distribution.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS”
// AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
// IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
// ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
// LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
// CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
// SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
// INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
// CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
// ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
// POSSIBILITY OF SUCH DAMAGE.
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
#pragma omp for collapse(2)
    for (size_t i = 0; i < matrixSize; ++i) {
      for (size_t k = 0; k < matrixSize; ++k) {
        uint64_t columnVal = A[i * matrixSize + k];
        for (size_t j = 0; j < matrixSize; ++j) {
          C[i * matrixSize + j] += columnVal * B[k * matrixSize + j];
        }
      }
    }

#pragma omp for collapse(2)
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
