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
// Deriche
//
// Deriche is a edge detector algorithm based on the canny edge detector
// algorithm.
// It replaces the Gaussian smoothing step in Canny with an IIR (infinite
// impulse response) filter, which provides better computational efficiency and
// precision, especially for real-time applications.
//
// Usage: ./deriche <alpha> <input_image> <output_image>
//
//===----------------------------------------------------------------------===//

#define STB_IMAGE_IMPLEMENTATION
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image.h"
#include "stb_image_write.h"

#include <algorithm>
#include <cstdint>
#include <iostream>
#include <unistd.h>

//===------------------------------------------------------------------------===
// Helper Functions
//===------------------------------------------------------------------------===

float *grayscale(const uint8_t *image, int width, int height, int channels) {
  constexpr float RED_WEIGHT = 0.299f;
  constexpr float GREEN_WEIGHT = 0.587f;
  constexpr float BLUE_WEIGHT = 0.114f;

  float *grayImage = new float[width * height];

  for (int i = 0; i < height; i++) {
    for (int j = 0; j < width; j++) {
      int index = (i * width + j) * channels;
      float red = image[index];
      float green = (channels > 1) ? image[index + 1] : red;
      float blue = (channels > 2) ? image[index + 2] : red;

      grayImage[i * width + j] =
          red * RED_WEIGHT + green * GREEN_WEIGHT + blue * BLUE_WEIGHT;
    }
  }

  return grayImage;
}

unsigned char *convert(const float *image, int width, int height) {
  unsigned char *outputImage = new unsigned char[width * height];

  for (int i = 0; i < height; i++) {
    for (int j = 0; j < width; j++) {
      outputImage[i * width + j] = static_cast<unsigned char>(
          std::clamp(image[i * width + j], 0.0f, 255.0f));
    }
  }

  return outputImage;
}

//===------------------------------------------------------------------------===
// Deriche
//===------------------------------------------------------------------------===

float *deriche(const float *imageIn, int width, int height, float alpha) {
  float *imageOut = new float[width * height]();

  const float k = (1.0f - expf(-alpha)) * (1.0f - expf(-alpha)) /
                  (1.0f + 2.0f * alpha * expf(-alpha) - expf(-2.0f * alpha));
  const float a1 = k;
  const float a2 = k * expf(-alpha) * (alpha - 1.0f);
  const float a3 = k * expf(-alpha) * (alpha + 1.0f);
  const float a4 = -k * expf(-2.0f * alpha);
  const float a5 = a1;
  const float a6 = a2;
  const float a7 = a3;
  const float a8 = a4;
  const float b1 = powf(2.0f, -alpha);
  const float b2 = -expf(-2.0f * alpha);

#pragma omp parallel shared(imageOut)
  {
#pragma omp for schedule(static)
    for (int i = 0; i < width; i++) {
      float xm1 = 0.0f;
      float ym1 = 0.0f;
      float ym2 = 0.0f;
      for (int j = 0; j < height; j++) {
        imageOut[j * width + i] =
            a1 * imageIn[j * width + i] + a2 * xm1 + b1 * ym1 + b2 * ym2;
        xm1 = imageIn[j * width + i];
        ym2 = ym1;
        ym1 = imageOut[j * width + i];
      }
    }

#pragma omp for schedule(static)
    for (int i = 0; i < width; i++) {
      float xp1 = 0.0f;
      float xp2 = 0.0f;
      float yp1 = 0.0f;
      float yp2 = 0.0f;
      for (int j = height - 1; j >= 0; j--) {
        const float prev = imageOut[j * width + i];
        const float res = a3 * xp1 + a4 * xp2 + b1 * yp1 + b2 * yp2;
        imageOut[j * width + i] += res;
        xp2 = xp1;
        xp1 = res;
        yp2 = yp1;
        yp1 = prev;
      }
    }

#pragma omp for schedule(static)
    for (int j = 0; j < height; j++) {
      float tm1 = 0.0f;
      float ym1 = 0.0f;
      float ym2 = 0.0f;
      for (int i = 0; i < width; i++) {
        const float prev = imageOut[j * width + i];
        const float res =
            a5 * imageOut[j * width + i] + a6 * tm1 + b1 * ym1 + b2 * ym2;
        imageOut[j * width + i] += res;
        tm1 = prev;
        ym2 = ym1;
        ym1 = res;
      }
    }

#pragma omp for schedule(static)
    for (int j = 0; j < height; j++) {
      float tp1 = 0.0f;
      float tp2 = 0.0f;
      float yp1 = 0.0f;
      float yp2 = 0.0f;
      for (int i = width - 1; i >= 0; i--) {
        const float prev = imageOut[j * width + i];
        const float res = a7 * tp1 + a8 * tp2 + b1 * yp1 + b2 * yp2;
        imageOut[j * width + i] += res;
        tp2 = tp1;
        tp1 = prev;
        yp2 = yp1;
        yp1 = res;
      }
    }
  }

  return imageOut;
}

//===------------------------------------------------------------------------===
// Main
//===------------------------------------------------------------------------===

int main(int argc, char **argv) {
  if (argc < 4) {
    std::cerr << "Invalid number of arguments!\n";
    std::cerr << "Usage: " << argv[0]
              << " <alpha> <input_image> <output_image>\n";
    return -1;
  }

  int width, height, channels;
  uint8_t *image = stbi_load(argv[2], &width, &height, &channels, 0);
  if (!image) {
    std::cerr << "Could not load the image " << argv[2] << "\n";
    return -1;
  }

  float *grayImage = grayscale(image, width, height, channels);
  stbi_image_free(image);

  float alpha = std::stof(argv[1]);
  float *filteredImage = deriche(grayImage, width, height, alpha);
  delete[] grayImage;

  unsigned char *output = convert(filteredImage, width, height);
  stbi_write_jpg(argv[3], width, height, 1, output, 100);
  delete[] output;

  return 0;
}
