//===-------------------------------------------------------------------------===
// Copyright © 2004-2008 Brent Fulgham, 2005-2024 Isaac Gouy All rights
// reserved.
//
// Modified in 2025 by Victor Briganti
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
// 3. Neither the name "The Computer Language Benchmarks Game" nor the name "The
// Benchmarks Game" nor the name "The Computer Language Shootout Benchmarks" nor
// the names of its contributors may be used to endorse or promote products
// derived from this software without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
// AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
// IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
// ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
// LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
// CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
// SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
// INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
// CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
// ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
// POSSIBILITY OF SUCH DAMAGE.
//===----------------------------------------------------------------------===//
// PI
//
// Calculates the PI number based on the Monte Carlo distribution.
//
// Usage: ./pi <num_iterations>
//
//===----------------------------------------------------------------------===//

#include <cstdint>
#include <fstream>
#include <iostream>
#include <string>
#include <unistd.h>

#if _OPENMP
#include <omp.h>
#endif // _OPENMP

#ifdef MEMO
// This is a random number generator based on the xorshiftr128+ algorithm.
// Reference: https://en.wikipedia.org/wiki/Xorshift#xorshiftr+
inline uint64_t xorshiftr128plus(uint64_t state0, uint64_t state1) {
  uint64_t x = state0;
  const uint64_t y = state1;
  state0 = y;
  x ^= x << 23; // shift & xor
  x ^= x >> 17; // shift & xor
  x ^= y;       // xor
  state1 = x + y;
  return x;
}

inline double randomDouble(uint64_t state0, uint64_t state1) {
  return static_cast<double>(xorshiftr128plus(state0, state1)) / UINT64_MAX;
}

#else
struct RandState {
  uint64_t seed[2];
};

// This is a random number generator based on the xorshiftr128+ algorithm.
// Reference: https://en.wikipedia.org/wiki/Xorshift#xorshiftr+
inline uint64_t xorshiftr128plus(RandState &state) {
  uint64_t x = state.seed[0];
  const uint64_t y = state.seed[1];
  state.seed[0] = y;
  x ^= x << 23; // shift & xor
  x ^= x >> 17; // shift & xor
  x ^= y;       // xor
  state.seed[1] = x + y;
  return x;
}

inline double randomDouble(RandState &state) {
  return static_cast<double>(xorshiftr128plus(state)) / UINT64_MAX;
}
#endif

double piMonteCarlo(uint64_t numIterations) {
  uint64_t hit = 0;

#pragma omp parallel reduction(+ : hit) num_threads(NUM_THREADS)
  {
#if _OPENMP
    uint64_t ompID = omp_get_thread_num();
#else
    uint64_t ompID = 0;
#endif // _OPENMP

#ifdef MEMO
    uint64_t state0 = ompID;
    uint64_t state1 = ompID + 1;
#else
    RandState state = {ompID, ompID + 1};
#endif

#ifdef PERFO_LARGE
#pragma omp for approx perfo(large, DROP) schedule(static)
#endif
#ifdef PERFO_INIT
#pragma omp for approx perfo(init, DROP) schedule(static)
#endif
#ifdef PERFO_FINI
#pragma omp for approx perfo(fini, DROP) schedule(static)
#endif
#ifdef OMP
#pragma omp for schedule(static)
#endif
    for (uint64_t i = 0; i < numIterations; i++) {
#ifdef FASTMATH
#pragma omp approx fastmath
      {
#endif
#ifdef MEMO
#pragma omp approx memo(DROP) output(hit)
        {
          const double x = randomDouble(state0, state1);
          const double y = randomDouble(state0, state1);
#else
      const double x = randomDouble(state);
      const double y = randomDouble(state);
#endif

          if ((x * x + y * y) <= 1) {
            hit++;
          }
#ifdef MEMO
        }
#endif
#ifdef FASTMATH
      }
#endif
    }
  }

  return 4.0 * hit / numIterations;
}

int main(int argc, char **argv) {
  if (argc < 3) {
    std::cerr << "Invalid number of arguments!\n";
    std::cerr << "Usage: " << argv[0] << " <num_iterations> <file_output>\n";
    return -1;
  }

  uint64_t numIterations = std::stoul(argv[1]);
  std::ofstream outfile(argv[2], std::ios::out | std::ios::binary);
  if (!outfile) {
    std::cerr << "Error: Could not open file" << argv[2] << "for writing!\n";
    return 1;
  }

  outfile << piMonteCarlo(numIterations);
  return 0;
}
