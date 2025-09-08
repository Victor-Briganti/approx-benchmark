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
// Mandelbrot
//
// Calculates the mandelbrot set and ouputs it as a 1-bit P4 portable bitmap
// image.
//
// Each pixel is mapped from a rectangular region of the complex plane, and the
// Mandelbrot iteration determines whether the pixel is black (in the set) or
// white (escaped).
//
// Usage: ./mandelbrot <image_size>
//
//===----------------------------------------------------------------------===//

#include <cstddef>
#include <cstdint>
#include <iostream>
#include <vector>

// This is the limit that pixels will need to exceed in order to escape from the
// Mandelbrot set.
constexpr double LIMIT = 4.0;

// Controls the maximum amount of iterations that are done for each pixel.
constexpr double MAX_ITERATIONS = 100;

// The real part of the mandelbrot set is in the set [-2.0, 1.0]
constexpr double REAL_INIT_RANGE = -2.0;
constexpr double REAL_FINAL_RANGE = 1.0;

// The imaginary part of the mandelbrot set is in the set [-1.5, 1.5]
constexpr double IMAG_INIT_RANGE = -1.5;
constexpr double IMAG_FINAL_RANGE = 1.5;

struct Complex {
  double real;
  double imag;
};

//===------------------------------------------------------------------------===
// Helper Functions
//===------------------------------------------------------------------------===

inline void two_exponential(Complex &number) {
  double realPart = number.real * number.real - number.imag * number.imag;
  double imagPart = 2.0 * number.real * number.imag;
  number.real = realPart;
  number.imag = imagPart;
}

inline double fast_abs(const Complex &number) {
  return number.real * number.real + number.imag * number.imag;
}

//===------------------------------------------------------------------------===
// Mandelbrot Set
//===------------------------------------------------------------------------===

inline bool mandelbrot(const Complex &c) {
  Complex z = {0.0, 0.0};

  for (int i = 0; i < MAX_ITERATIONS; i++) {
    two_exponential(z);
    z.real += c.real;
    z.imag += c.imag;

    if (fast_abs(z) > LIMIT) {
      return false;
    }
  }

  return true;
}

//===------------------------------------------------------------------------===
// Main
//===------------------------------------------------------------------------===

int main(int argc, char **argv) {
  if (argc < 2) {
    std::cerr << "Invalid number of arguments!\n";
    std::cerr << "Usage: " << argv[0] << " <image_size>\n";
    return -1;
  }

  // Get the size of the image as a multiple of 8
  size_t imageSize = (atol(argv[1]) + 7) / 8 * 8;
  std::vector<uint8_t> pixels(imageSize * imageSize / 8, 0x00);

  double scaleX = (REAL_FINAL_RANGE - REAL_INIT_RANGE) / imageSize;
  double scaleY = (IMAG_FINAL_RANGE - IMAG_INIT_RANGE) / imageSize;

#pragma omp parallel for shared(pixels)
  for (int pixel = 0; pixel < pixels.size(); pixel++) {
    uint8_t byte = 0;

    size_t byteRow = imageSize / 8;
    size_t pixelColumn = pixel % byteRow;

    double y = pixel / byteRow;

#pragma unroll(8)
    for (int bit = 0; bit < 8; bit++) {
      double x = pixelColumn * 8 + bit;

      double cx = REAL_INIT_RANGE + x * scaleX;
      double cy = IMAG_INIT_RANGE + y * scaleX;

      if (mandelbrot({cx, cy})) {
        byte |= (1 << (7 - bit));
      }
    }

    pixels[pixel] = byte;
  }

  // Write the image to the file
  std::cout << "P4\n" << imageSize << " " << imageSize << "\n";
  std::cout.write(reinterpret_cast<char *>(pixels.data()), pixels.size());
  std::cout.flush();
  return 0;
}
