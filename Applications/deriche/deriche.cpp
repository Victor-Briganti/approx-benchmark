#include <algorithm>
#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image_write.h"

#include <cstdint>
#include <iostream>

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
  float *imageOut = new float[width * height];
  float *y1 = new float[width * height];
  float *y2 = new float[width * height];

  float xm1, tm1, ym1, ym2;
  float xp1, xp2, yp1, yp2, tp1, tp2;

  float k = (1.0f - expf(-alpha)) * (1.0f - expf(-alpha)) /
            (1.0f + 2.0f * alpha * expf(-alpha) - expf(-2.0f * alpha));
  float a1 = k;
  float a2 = k * expf(-alpha) * (alpha - 1.0f);
  float a3 = k * expf(-alpha) * (alpha + 1.0f);
  float a4 = -k * expf(-2.0f * alpha);
  float a5 = a1;
  float a6 = a2;
  float a7 = a3;
  float a8 = a4;
  float b1 = powf(2.0f, -alpha);
  float b2 = -expf(-2.0f * alpha);

  for (int i = 0; i < width; i++) {
    xm1 = 0.0f;
    ym1 = 0.0f;
    ym2 = 0.0f;
    for (int j = 0; j < height; j++) {
      y1[j * width + i] =
          a1 * imageIn[j * width + i] + a2 * xm1 + b1 * ym1 + b2 * ym2;
      xm1 = imageIn[j * width + i];
      ym2 = ym1;
      ym1 = y1[j * width + i];
    }
  }

  for (int i = 0; i < width; i++) {
    xp1 = 0.0f;
    xp2 = 0.0f;
    yp1 = 0.0f;
    yp2 = 0.0f;
    for (int j = height - 1; j >= 0; j--) {
      y2[j * width + i] = a3 * xp1 + a4 * xp2 + b1 * yp1 + b2 * yp2;
      xp2 = xp1;
      xp1 = imageIn[j * width + i];
      yp2 = yp1;
      yp1 = y2[j * width + i];
    }
  }

  for (int i = 0; i < width; i++) {
    for (int j = 0; j < height; j++) {
      imageOut[j * width + i] = y1[j * width + i] + y2[j * width + i];
    }
  }

  for (int j = 0; j < height; j++) {
    tm1 = 0.0f;
    ym1 = 0.0f;
    ym2 = 0.0f;
    for (int i = 0; i < width; i++) {
      y1[j * width + i] =
          a5 * imageOut[j * width + i] + a6 * tm1 + b1 * ym1 + b2 * ym2;
      tm1 = imageOut[j * width + i];
      ym2 = ym1;
      ym1 = y1[j * width + i];
    }
  }

  for (int j = 0; j < height; j++) {
    tp1 = 0.0f;
    tp2 = 0.0f;
    yp1 = 0.0f;
    yp2 = 0.0f;
    for (int i = width - 1; i >= 0; i--) {
      y2[j * width + i] = a7 * tp1 + a8 * tp2 + b1 * yp1 + b2 * yp2;
      tp2 = tp1;
      tp1 = imageOut[j * width + i];
      yp2 = yp1;
      yp1 = y2[j * width + i];
    }
  }

  for (int i = 0; i < width; i++) {
    for (int j = 0; j < height; j++) {
      imageOut[j * width + i] = y1[j * width + i] + y2[j * width + i];
    }
  }

  delete[] y1;
  delete[] y2;
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